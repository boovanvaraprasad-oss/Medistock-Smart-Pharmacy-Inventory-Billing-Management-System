from datetime import datetime, timezone

from bson import ObjectId
from fastapi import HTTPException, status

from app.core.database import client, db
from app.services.stock_transactions import create_stock_transaction


async def return_bill_batch_stock(
    bill_id: str,
    batch_id: str,
    quantity: int,
    reason: str,
):
    """Return sold stock to its original batch and record the return."""

    try:
        bill_object_id = ObjectId(bill_id)
        batch_object_id = ObjectId(batch_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid bill ID or batch ID",
        )

    async def transaction_work(session):
        bill = await db.bills.find_one(
            {
                "_id": bill_object_id,
                "is_active": True,
                "status": "completed",
            },
            session=session,
        )

        if not bill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Completed bill not found",
            )

        allocations = bill.get("batch_allocations")

        if not allocations:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "This bill has no saved batch allocation information, "
                    "so its stock cannot be returned by batch."
                ),
            )

        allocation = next(
            (
                item
                for item in allocations
                if item.get("batch_id") == str(batch_object_id)
            ),
            None,
        )

        if not allocation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="That batch was not allocated to this bill",
            )

        quantity_sold = allocation.get("quantity_sold", 0)
        quantity_returned = allocation.get("quantity_returned", 0)

        if (
            not isinstance(quantity_sold, int)
            or isinstance(quantity_sold, bool)
            or not isinstance(quantity_returned, int)
            or isinstance(quantity_returned, bool)
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The bill's batch allocation data is invalid",
            )

        outstanding_quantity = quantity_sold - quantity_returned

        if quantity > outstanding_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Only {outstanding_quantity} unit(s) from this batch "
                    "remain eligible for return"
                ),
            )

        try:
            medicine_object_id = ObjectId(allocation["medicine_id"])
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The bill's medicine allocation data is invalid",
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
                detail="The original stock batch was not found",
            )

        medicine = await db.medicines.find_one(
            {"_id": medicine_object_id},
            session=session,
        )

        if not medicine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The medicine for this batch was not found",
            )

        previous_batch_quantity = batch.get("quantity", 0)
        previous_medicine_stock = medicine.get("stock", 0)

        if (
            not isinstance(previous_batch_quantity, int)
            or isinstance(previous_batch_quantity, bool)
            or not isinstance(previous_medicine_stock, int)
            or isinstance(previous_medicine_stock, bool)
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The current stock data is invalid",
            )

        new_batch_quantity = previous_batch_quantity + quantity
        new_medicine_stock = previous_medicine_stock + quantity

        # Claim the return quantity on the bill. The exact previous returned
        # quantity protects against two simultaneous returns exceeding the sale.
        bill_update = await db.bills.update_one(
            {
                "_id": bill_object_id,
                "status": "completed",
                "batch_allocations": {
                    "$elemMatch": {
                        "batch_id": str(batch_object_id),
                        "quantity_sold": quantity_sold,
                        "quantity_returned": quantity_returned,
                    }
                },
            },
            {
                "$inc": {
                    "batch_allocations.$.quantity_returned": quantity,
                }
            },
            session=session,
        )

        if bill_update.modified_count != 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Return data changed. Please retry the return.",
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
                    "is_active": True,
                }
            },
            session=session,
        )

        if batch_update.modified_count != 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Batch stock changed. Please retry the return.",
            )

        medicine_update = await db.medicines.update_one(
            {
                "_id": medicine_object_id,
                "stock": previous_medicine_stock,
            },
            {
                "$set": {
                    "stock": new_medicine_stock,
                }
            },
            session=session,
        )

        if medicine_update.modified_count != 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Medicine stock changed. Please retry the return.",
            )

        transaction = await create_stock_transaction(
            medicine_id=str(medicine_object_id),
            batch_id=str(batch_object_id),
            transaction_type="STOCK_RETURN",
            quantity=quantity,
            previous_stock=previous_medicine_stock,
            new_stock=new_medicine_stock,
            reason=reason,
            session=session,
        )

        return {
            "bill_id": str(bill_object_id),
            "invoice_number": bill.get("invoice_number", ""),
            "medicine_id": str(medicine_object_id),
            "batch_id": str(batch_object_id),
            "batch_number": batch.get("batch_number", ""),
            "quantity_returned": quantity,
            "batch_stock": new_batch_quantity,
            "medicine_stock": new_medicine_stock,
            "reason": reason,
            "stock_transaction_id": transaction["id"],
            "returned_at": datetime.now(timezone.utc),
        }

    async with await client.start_session() as session:
        return await session.with_transaction(transaction_work)