from datetime import date, datetime, time

from bson import ObjectId
from fastapi import HTTPException, status

from app.core.database import client, db
from app.services.audit_log import create_audit_log


EDITABLE_ORDER_STATUSES = {"draft", "ordered"}


def date_to_datetime(value):
    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    return datetime.combine(value, time.min)


def datetime_to_date(value):
    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    return value


async def get_editable_purchase_order(purchase_order_id):
    try:
        order_object_id = ObjectId(purchase_order_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid purchase order ID",
        )

    purchase_order = await db.purchase_orders.find_one(
        {
            "_id": order_object_id,
            "is_active": True,
        }
    )

    if not purchase_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found or inactive",
        )

    if purchase_order.get("status") not in EDITABLE_ORDER_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Purchase items can only be changed for draft or ordered purchase orders",
        )

    return purchase_order


async def create_purchase_item(
    purchase_order_id: str,
    medicine_id: str,
    quantity: int,
    unit_price: float,
    batch_number: str,
    manufacturing_date,
    expiry_date,
    actor_user_id: str,
    actor_role: str,
):
    purchase_order = await get_editable_purchase_order(
        purchase_order_id
    )

    try:
        medicine_object_id = ObjectId(medicine_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid medicine ID",
        )

    medicine = await db.medicines.find_one(
        {
            "_id": medicine_object_id,
            "is_active": True,
        }
    )

    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Medicine not found or inactive",
        )

    if (
        manufacturing_date is not None
        and expiry_date <= manufacturing_date
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expiry date must be after manufacturing date",
        )

    total_price = quantity * unit_price

    purchase_item = {
        "purchase_order_id": purchase_order["_id"],
        "medicine_id": medicine_object_id,
        "quantity": quantity,
        "unit_price": unit_price,
        "total_price": total_price,
        "batch_number": batch_number,
        "manufacturing_date": date_to_datetime(
            manufacturing_date
        ),
        "expiry_date": date_to_datetime(expiry_date),
    }

    async def transaction_work(session):
        result = await db.purchase_items.insert_one(
            purchase_item,
            session=session,
        )
        await create_audit_log(
            action="PURCHASE_ORDER_ITEM_ADD",
            entity_type="purchase_orders",
            entity_id=str(purchase_order["_id"]),
            entity_label=str(purchase_order.get("order_number", purchase_order["_id"])),
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            details={
                "purchase_item_id": str(result.inserted_id),
                "medicine_name": medicine.get("name", "Unknown medicine"),
                "quantity": quantity,
                "unit_price": unit_price,
                "total_price": total_price,
            },
            session=session,
        )
        return result

    async with await client.start_session() as session:
        result = await session.with_transaction(transaction_work)

    return {
        "id": str(result.inserted_id),
        "purchase_order_id": purchase_order_id,
        "medicine_id": medicine_id,
        "quantity": quantity,
        "unit_price": unit_price,
        "total_price": total_price,
        "batch_number": batch_number,
        "manufacturing_date": manufacturing_date,
        "expiry_date": expiry_date,
    }


async def get_all_purchase_items():
    purchase_items = []

    cursor = db.purchase_items.find({})

    async for purchase_item in cursor:
        purchase_items.append(
            {
                "id": str(purchase_item["_id"]),
                "purchase_order_id": str(
                    purchase_item["purchase_order_id"]
                ),
                "medicine_id": str(
                    purchase_item["medicine_id"]
                ),
                "quantity": purchase_item["quantity"],
                "unit_price": purchase_item["unit_price"],
                "total_price": purchase_item["total_price"],
                "batch_number": purchase_item.get(
                    "batch_number"
                ),
                "manufacturing_date": datetime_to_date(
                    purchase_item.get("manufacturing_date")
                ),
                "expiry_date": datetime_to_date(
                    purchase_item.get("expiry_date")
                ),
            }
        )

    return purchase_items


async def update_purchase_item(
    purchase_item_id: str,
    actor_user_id: str,
    actor_role: str,
    quantity: int | None = None,
    unit_price: float | None = None,
    batch_number: str | None = None,
    manufacturing_date=None,
    expiry_date=None,
):
    try:
        object_id = ObjectId(purchase_item_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid purchase item ID",
        )

    purchase_item = await db.purchase_items.find_one(
        {"_id": object_id}
    )

    if not purchase_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase item not found",
        )

    await get_editable_purchase_order(
        str(purchase_item["purchase_order_id"])
    )

    if (
        quantity is None
        and unit_price is None
        and batch_number is None
        and manufacturing_date is None
        and expiry_date is None
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    new_quantity = (
        quantity
        if quantity is not None
        else purchase_item["quantity"]
    )

    new_unit_price = (
        unit_price
        if unit_price is not None
        else purchase_item["unit_price"]
    )

    new_batch_number = (
        batch_number
        if batch_number is not None
        else purchase_item.get("batch_number")
    )

    existing_manufacturing_date = datetime_to_date(
        purchase_item.get("manufacturing_date")
    )

    existing_expiry_date = datetime_to_date(
        purchase_item.get("expiry_date")
    )

    new_manufacturing_date = (
        manufacturing_date
        if manufacturing_date is not None
        else existing_manufacturing_date
    )

    new_expiry_date = (
        expiry_date
        if expiry_date is not None
        else existing_expiry_date
    )

    if (
        new_manufacturing_date is not None
        and new_expiry_date is not None
        and new_expiry_date <= new_manufacturing_date
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expiry date must be after manufacturing date",
        )

    total_price = new_quantity * new_unit_price

    update_data = {
        "quantity": new_quantity,
        "unit_price": new_unit_price,
        "total_price": total_price,
        "batch_number": new_batch_number,
        "manufacturing_date": date_to_datetime(
            new_manufacturing_date
        ),
        "expiry_date": date_to_datetime(new_expiry_date),
    }
    changed_fields = [
        field
        for field, value in update_data.items()
        if purchase_item.get(field) != value
    ]

    medicine = await db.medicines.find_one({"_id": purchase_item["medicine_id"]})

    async def transaction_work(session):
        result = await db.purchase_items.update_one(
            {
                "_id": object_id,
                "quantity": purchase_item["quantity"],
                "unit_price": purchase_item["unit_price"],
            },
            {"$set": update_data},
            session=session,
        )
        if result.matched_count != 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Purchase item changed while the update was in progress; retry",
            )
        if changed_fields:
            await create_audit_log(
                action="PURCHASE_ORDER_ITEM_UPDATE",
                entity_type="purchase_orders",
                entity_id=str(purchase_item["purchase_order_id"]),
                entity_label=str(purchase_item["purchase_order_id"]),
                actor_user_id=actor_user_id,
                actor_role=actor_role,
                details={
                    "purchase_item_id": str(object_id),
                    "medicine_name": (medicine or {}).get("name", "Unknown medicine"),
                    "changed_fields": changed_fields,
                    "previous_quantity": purchase_item.get("quantity"),
                    "quantity": new_quantity,
                    "previous_unit_price": purchase_item.get("unit_price"),
                    "unit_price": new_unit_price,
                    "total_price": total_price,
                },
                session=session,
            )
        return await db.purchase_items.find_one(
            {"_id": object_id},
            session=session,
        )

    async with await client.start_session() as session:
        updated_item = await session.with_transaction(transaction_work)

    return {
        "id": str(updated_item["_id"]),
        "purchase_order_id": str(
            updated_item["purchase_order_id"]
        ),
        "medicine_id": str(updated_item["medicine_id"]),
        "quantity": updated_item["quantity"],
        "unit_price": updated_item["unit_price"],
        "total_price": updated_item["total_price"],
        "batch_number": updated_item.get("batch_number"),
        "manufacturing_date": datetime_to_date(
            updated_item.get("manufacturing_date")
        ),
        "expiry_date": datetime_to_date(
            updated_item.get("expiry_date")
        ),
    }
