from datetime import datetime, timezone

from bson import ObjectId
from fastapi import HTTPException, status

from app.core.database import client, db


MASTER_DATA_COLLECTIONS = {
    "medicines",
    "categories",
    "manufacturers",
    "units",
    "suppliers",
}


async def _has_reference(
    collection_name: str,
    field_name: str,
    value,
    session,
) -> bool:
    return await db[collection_name].find_one(
        {field_name: value},
        {"_id": 1},
        session=session,
    ) is not None


async def delete_master_data_record(
    collection_name: str,
    record_id: str,
    actor_id: str,
    actor_role: str,
) -> dict:
    """Permanently delete an unused master-data record and audit it."""

    if collection_name not in MASTER_DATA_COLLECTIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported master-data collection",
        )

    try:
        object_id = ObjectId(record_id)
        actor_object_id = ObjectId(actor_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid record or acting user ID",
        )

    async def transaction_work(session):
        record = await db[collection_name].find_one(
            {"_id": object_id},
            session=session,
        )

        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Record not found",
            )

        if collection_name == "medicines" and record.get("stock", 0) > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Medicine with stock cannot be permanently deleted",
            )

        references = []
        if collection_name == "medicines":
            medicine_id_text = str(object_id)
            references = [
                ("stock_batches", "medicine_id", object_id),
                ("stock_transactions", "medicine_id", medicine_id_text),
                ("bill_items", "medicine_id", object_id),
                ("bills", "batch_allocations.medicine_id", medicine_id_text),
                ("purchase_items", "medicine_id", object_id),
            ]
        elif collection_name in {
            "categories",
            "manufacturers",
            "units",
        }:
            medicine_reference_fields = {
                "categories": "category_id",
                "manufacturers": "manufacturer_id",
                "units": "unit_id",
            }
            references = [
                (
                    "medicines",
                    medicine_reference_fields[collection_name],
                    object_id,
                )
            ]
        elif collection_name == "suppliers":
            references = [
                ("medicines", "supplier_id", object_id),
                ("purchase_orders", "supplier_id", object_id),
            ]

        for reference_collection, reference_field, reference_value in references:
            if await _has_reference(
                reference_collection,
                reference_field,
                reference_value,
                session,
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "Record is referenced by existing business data; "
                        "deactivate it instead"
                    ),
                )

        result = await db[collection_name].delete_one(
            {"_id": object_id},
            session=session,
        )

        if result.deleted_count != 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Record changed while deletion was in progress; retry",
            )

        label = record.get("name") or record.get("email") or str(object_id)
        await db.audit_logs.insert_one(
            {
                "action": "MASTER_DATA_DELETE",
                "entity_type": collection_name,
                "entity_id": str(object_id),
                "entity_label": label,
                "actor_user_id": actor_object_id,
                "actor_role": actor_role,
                "created_at": datetime.now(timezone.utc),
            },
            session=session,
        )

        entity_label = {
            "medicines": "Medicine",
            "categories": "Category",
            "manufacturers": "Manufacturer",
            "units": "Unit",
            "suppliers": "Supplier",
        }[collection_name]
        return {
            "id": str(object_id),
            "message": f"{entity_label} permanently deleted",
        }

    async with await client.start_session() as session:
        return await session.with_transaction(transaction_work)
