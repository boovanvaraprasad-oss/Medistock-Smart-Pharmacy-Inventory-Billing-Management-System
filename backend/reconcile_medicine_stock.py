import asyncio

from bson import ObjectId
from fastapi import HTTPException, status

from app.core.database import client, db
from app.services.stock_transactions import create_stock_transaction


MEDICINE_ID = "6ac3495a71930cc1784a7283"


async def reconcile_medicine_stock():
    medicine_object_id = ObjectId(MEDICINE_ID)

    async def transaction_work(session):
        medicine = await db.medicines.find_one(
            {"_id": medicine_object_id},
            session=session,
        )

        if not medicine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medicine not found",
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

        batch_cursor = db.stock_batches.find(
            {"medicine_id": medicine_object_id},
            session=session,
        )

        batch_total = 0

        async for batch in batch_cursor:
            quantity = batch.get("quantity", 0)

            if (
                not isinstance(quantity, int)
                or isinstance(quantity, bool)
                or quantity < 0
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A batch has an invalid quantity",
                )

            batch_total += quantity

        if current_stock == batch_total:
            return {
                "medicine_id": MEDICINE_ID,
                "previous_stock": current_stock,
                "new_stock": batch_total,
                "changed": False,
                "message": "Medicine stock already matches its batches.",
            }

        medicine_filter = {"_id": medicine_object_id}

        if "stock" in medicine:
            medicine_filter["stock"] = current_stock
        else:
            medicine_filter["stock"] = {"$exists": False}

        update_result = await db.medicines.update_one(
            medicine_filter,
            {"$set": {"stock": batch_total}},
            session=session,
        )

        if update_result.modified_count != 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Medicine stock changed. Run the reconciliation again.",
            )

        difference = abs(batch_total - current_stock)

        transaction = await create_stock_transaction(
            medicine_id=MEDICINE_ID,
            transaction_type="STOCK_RECONCILIATION",
            quantity=difference,
            previous_stock=current_stock,
            new_stock=batch_total,
            reason="Reconciled medicine total against its batch quantities",
            session=session,
        )

        return {
            "medicine_id": MEDICINE_ID,
            "previous_stock": current_stock,
            "new_stock": batch_total,
            "changed": True,
            "stock_transaction_id": transaction["id"],
            "message": "Medicine stock now matches its batch quantities.",
        }

    async with await client.start_session() as session:
        return await session.with_transaction(transaction_work)


async def main():
    try:
        result = await reconcile_medicine_stock()
        print(result)
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())