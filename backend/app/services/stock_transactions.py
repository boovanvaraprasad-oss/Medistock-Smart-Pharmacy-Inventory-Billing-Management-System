from datetime import datetime, timezone

from bson import ObjectId

from app.core.database import db


async def create_stock_transaction(
    medicine_id: str,
    transaction_type: str,
    quantity: int,
    previous_stock: int,
    new_stock: int,
    reason: str,
):
    transaction = {
        "medicine_id": medicine_id,
        "transaction_type": transaction_type,
        "quantity": quantity,
        "previous_stock": previous_stock,
        "new_stock": new_stock,
        "reason": reason,
        "created_at": datetime.now(timezone.utc),
    }

    result = await db.stock_transactions.insert_one(
        transaction
    )

    return {
        "id": str(result.inserted_id),
        "medicine_id": medicine_id,
        "transaction_type": transaction_type,
        "quantity": quantity,
        "previous_stock": previous_stock,
        "new_stock": new_stock,
        "reason": reason,
        "created_at": transaction["created_at"],
    }


async def get_stock_transactions(
    medicine_id: str | None = None,
    transaction_type: str | None = None,
):
    transactions = []

    query = {}

    if medicine_id is not None:
        query["medicine_id"] = medicine_id

    if transaction_type is not None:
        query["transaction_type"] = transaction_type

    cursor = db.stock_transactions.find(
        query
    ).sort(
        "created_at",
        -1,
    )

    async for transaction in cursor:

        medicine = await db.medicines.find_one(
            {
                "_id": ObjectId(
                    transaction["medicine_id"]
                )
            }
        )

        medicine_name = "Unknown Medicine"

        if medicine:
            medicine_name = medicine["name"]

        transactions.append(
            {
                "id": str(transaction["_id"]),
                "medicine_id": transaction["medicine_id"],
                "medicine_name": medicine_name,
                "transaction_type": transaction[
                    "transaction_type"
                ],
                "quantity": transaction["quantity"],
                "previous_stock": transaction[
                    "previous_stock"
                ],
                "new_stock": transaction["new_stock"],
                "reason": transaction["reason"],
                "created_at": transaction["created_at"],
            }
        )

    return transactions