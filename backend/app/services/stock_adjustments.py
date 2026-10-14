from bson import ObjectId
from fastapi import HTTPException, status

from app.core.database import client, db
from app.services.stock_transactions import (
    create_stock_transaction,
)


async def adjust_batch_stock(
    medicine_id: str,
    batch_id: str,
    quantity_change: int,
    reason: str,
):
    """
    Adjust the quantity of one existing batch.

    A positive quantity_change adds stock.
    A negative quantity_change removes stock.

    The batch, medicine total, and transaction record
    are updated within one database transaction.
    """

    if (
        not isinstance(quantity_change, int)
        or isinstance(quantity_change, bool)
        or quantity_change == 0
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity change must be a non-zero integer",
        )

    cleaned_reason = reason.strip()

    if not cleaned_reason:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A reason is required",
        )

    try:
        medicine_object_id = ObjectId(medicine_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid medicine ID",
        )

    try:
        batch_object_id = ObjectId(batch_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid batch ID",
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

        batch = await db.stock_batches.find_one(
            {
                "_id": batch_object_id,
                "medicine_id": medicine_object_id,
            },
            session=session,
        )

        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Batch not found for this medicine",
            )

        previous_batch_quantity = batch.get(
            "quantity",
            0,
        )

        if (
            not isinstance(previous_batch_quantity, int)
            or isinstance(previous_batch_quantity, bool)
            or previous_batch_quantity < 0
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Batch quantity is invalid",
            )

        previous_stock = medicine.get(
            "stock",
            0,
        )

        if (
            not isinstance(previous_stock, int)
            or isinstance(previous_stock, bool)
            or previous_stock < 0
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Medicine stock is invalid",
            )

        new_batch_quantity = (
            previous_batch_quantity + quantity_change
        )

        new_stock = previous_stock + quantity_change

        if new_batch_quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Adjustment would make batch stock negative",
            )

        if new_stock < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Adjustment would make medicine stock negative",
            )

        batch_update = await db.stock_batches.update_one(
            {
                "_id": batch_object_id,
                "medicine_id": medicine_object_id,
                "quantity": previous_batch_quantity,
            },
            {
                "$set": {
                    "quantity": new_batch_quantity,
                    "is_active": new_batch_quantity > 0,
                }
            },
            session=session,
        )

        if batch_update.modified_count != 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Batch quantity changed. Please retry.",
            )

        medicine_filter = {
            "_id": medicine_object_id,
            "is_active": True,
        }

        if "stock" in medicine:
            medicine_filter["stock"] = previous_stock
        else:
            medicine_filter["stock"] = {
                "$exists": False,
            }

        medicine_update = await db.medicines.update_one(
            medicine_filter,
            {
                "$set": {
                    "stock": new_stock,
                }
            },
            session=session,
        )

        if medicine_update.modified_count != 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Medicine stock changed. Please retry.",
            )

        if quantity_change > 0:
            transaction_type = "STOCK_ADJUSTMENT_IN"
        else:
            transaction_type = "STOCK_ADJUSTMENT_OUT"

        await create_stock_transaction(
            medicine_id=medicine_id,
            batch_id=batch_id,
            transaction_type=transaction_type,
            quantity=abs(quantity_change),
            previous_stock=previous_stock,
            new_stock=new_stock,
            reason=cleaned_reason,
            session=session,
        )

        return {
            "medicine_id": medicine_id,
            "batch_id": batch_id,
            "batch_number": batch.get("batch_number", ""),
            "quantity_change": quantity_change,
            "previous_batch_quantity": previous_batch_quantity,
            "new_batch_quantity": new_batch_quantity,
            "previous_stock": previous_stock,
            "new_stock": new_stock,
            "reason": cleaned_reason,
        }

    async with await client.start_session() as session:
        return await session.with_transaction(
            transaction_work
        )