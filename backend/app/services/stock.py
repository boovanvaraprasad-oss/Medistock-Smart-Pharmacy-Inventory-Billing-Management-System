from datetime import datetime, time, timedelta, timezone

from bson import ObjectId
from fastapi import HTTPException, status

from app.core.database import client, db
from app.services.stock_transactions import (
    create_stock_transaction,
)


# India Standard Time (UTC+05:30)
INDIA_TIMEZONE = timezone(timedelta(hours=5, minutes=30))


async def reduce_stock(
    medicine_id: str,
    quantity: int,
):
    # Validate quantity.
    if (
        not isinstance(quantity, int)
        or isinstance(quantity, bool)
        or quantity <= 0
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity must be a positive integer",
        )

    # Validate medicine ID.
    try:
        object_id = ObjectId(medicine_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid medicine ID",
        )

    async def transaction_work(session):
        # Find the active medicine.
        medicine = await db.medicines.find_one(
            {
                "_id": object_id,
                "is_active": True,
            },
            session=session,
        )

        if not medicine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medicine not found or inactive",
            )

        current_stock = medicine.get("stock", 0)

        if (
            not isinstance(current_stock, int)
            or isinstance(current_stock, bool)
            or current_stock < 0
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Medicine stock is invalid",
            )

        if quantity > current_stock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient stock",
            )

        # Include batches expiring today or later in India.
        # Batch expiry dates are stored as midnight datetimes.
        today_start = datetime.combine(
            datetime.now(INDIA_TIMEZONE).date(),
            time.min,
        )

        # Find eligible batches in FEFO order:
        # First Expiry, First Out.
        batches = await db.stock_batches.find(
            {
                "medicine_id": object_id,
                "is_active": True,
                "quantity": {"$gt": 0},
                "expiry_date": {"$gte": today_start},
            },
            session=session,
        ).sort(
            [
                ("expiry_date", 1),
                ("_id", 1),
            ]
        ).to_list(length=None)

        # Count only positive integer batch quantities.
        available_batch_stock = sum(
            batch_quantity
            for batch in batches
            if isinstance(
                (batch_quantity := batch.get("quantity", 0)),
                int,
            )
            and not isinstance(batch_quantity, bool)
            and batch_quantity > 0
        )

        if available_batch_stock < quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient unexpired batch stock",
            )

        # Deduct from earliest-expiring batches first.
        remaining = quantity

        for batch in batches:
            if remaining == 0:
                break

            batch_quantity = batch.get("quantity", 0)

            if (
                not isinstance(batch_quantity, int)
                or isinstance(batch_quantity, bool)
                or batch_quantity <= 0
            ):
                continue

            quantity_to_take = min(
                remaining,
                batch_quantity,
            )

            new_batch_quantity = (
                batch_quantity - quantity_to_take
            )

            batch_update = await db.stock_batches.update_one(
                {
                    "_id": batch["_id"],
                    "medicine_id": object_id,
                    "is_active": True,
                    "quantity": batch_quantity,
                    "expiry_date": {"$gte": today_start},
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
                    detail="Batch stock changed. Please retry.",
                )

            remaining -= quantity_to_take

        if remaining != 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Batch stock changed. Please retry.",
            )

        # Update the medicine's aggregate stock.
        new_stock = current_stock - quantity

        stock_update = await db.medicines.update_one(
            {
                "_id": object_id,
                "is_active": True,
                "stock": current_stock,
            },
            {
                "$set": {
                    "stock": new_stock,
                }
            },
            session=session,
        )

        if stock_update.modified_count != 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Medicine stock changed. Please retry.",
            )

        # Record stock reduction in the same transaction.
        await create_stock_transaction(
            medicine_id=medicine_id,
            transaction_type="STOCK_OUT",
            quantity=quantity,
            previous_stock=current_stock,
            new_stock=new_stock,
            reason="Medicine issued",
            session=session,
        )

        return {
            "medicine_id": medicine_id,
            "previous_stock": current_stock,
            "quantity_reduced": quantity,
            "remaining_stock": new_stock,
        }

    async with await client.start_session() as session:
        return await session.with_transaction(
            transaction_work
        )