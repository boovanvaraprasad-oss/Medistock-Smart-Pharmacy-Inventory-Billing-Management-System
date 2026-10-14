from bson import ObjectId
from fastapi import HTTPException, status

from app.core.database import client, db
from app.services.stock_batches import create_stock_batch
from app.services.stock_transactions import create_stock_transaction


async def create_stock_batch_and_update_total(
    medicine_id: str,
    batch_number: str,
    quantity: int,
    purchase_price: float,
    manufacturing_date,
    expiry_date,
):
    """Create a batch and update medicine stock as one transaction."""

    try:
        medicine_object_id = ObjectId(medicine_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid medicine ID",
        )

    async def transaction_work(session):
        medicine = await db.medicines.find_one(
            {
                "_id": medicine_object_id,
                "is_active": True,
            },
            session=session,
        )

        if not medicine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medicine not found or inactive",
            )

        previous_stock = medicine.get("stock", 0)

        if (
            not isinstance(previous_stock, int)
            or isinstance(previous_stock, bool)
            or previous_stock < 0
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Medicine stock is invalid",
            )

        new_stock = previous_stock + quantity

        batch = await create_stock_batch(
            medicine_id=medicine_id,
            batch_number=batch_number,
            quantity=quantity,
            purchase_price=purchase_price,
            manufacturing_date=manufacturing_date,
            expiry_date=expiry_date,
            session=session,
        )

        medicine_filter = {
            "_id": medicine_object_id,
            "is_active": True,
        }

        if "stock" in medicine:
            medicine_filter["stock"] = previous_stock
        else:
            medicine_filter["stock"] = {"$exists": False}

        medicine_update = await db.medicines.update_one(
            medicine_filter,
            {"$set": {"stock": new_stock}},
            session=session,
        )

        if medicine_update.modified_count != 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Medicine stock changed. Please retry.",
            )

        transaction = await create_stock_transaction(
            medicine_id=medicine_id,
            batch_id=batch["id"],
            transaction_type="STOCK_IN",
            quantity=quantity,
            previous_stock=previous_stock,
            new_stock=new_stock,
            reason=f"Stock batch created: {batch_number}",
            session=session,
        )

        return {
            **batch,
            "previous_stock": previous_stock,
            "new_stock": new_stock,
            "stock_transaction_id": transaction["id"],
        }

    async with await client.start_session() as session:
        return await session.with_transaction(transaction_work)