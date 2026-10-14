
import asyncio
from unittest.mock import patch

from bson import ObjectId
from fastapi import HTTPException

from app.core.database import client, db
from app.core.config import DATABASE_NAME, MONGO_URI
from app.services import purchase_orders


PURCHASE_ORDER_ID = "6acceaef919e364c5fb7156f"
MEDICINE_ID = "6ac3495a71930cc1784a7283"
BATCH_NUMBER = "ROLLBACK-TEST-2026-001"


async def main():
    try:
        print("Database name:", DATABASE_NAME)
        print("MongoDB URI configured:", bool(MONGO_URI))

        order_id = ObjectId(PURCHASE_ORDER_ID)
        medicine_id = ObjectId(MEDICINE_ID)

        order = await db.purchase_orders.find_one(
            {"_id": order_id}
        )
        medicine = await db.medicines.find_one(
            {"_id": medicine_id}
        )

        print("Test order found:", order is not None)
        print("Test medicine found:", medicine is not None)

        if order:
            print("Order status:", order.get("status"))
            print("Order ID:", order.get("_id"))

        if medicine:
            print("Medicine name:", medicine.get("name"))
            print("Medicine stock:", medicine.get("stock"))
            print("Medicine ID:", medicine.get("_id"))

        if not order or not medicine:
            print("STOP: No changes made.")
            return

        if order.get("status") not in {"draft", "ordered"}:
            print("STOP: Order is not eligible for receiving.")
            return

        if medicine.get("stock") != 3:
            print("STOP: Stock is not the expected baseline of 3.")
            return

        item = await db.purchase_items.find_one(
            {
                "purchase_order_id": order_id,
                "medicine_id": medicine_id,
                "batch_number": BATCH_NUMBER,
            }
        )

        if not item:
            print("STOP: Expected test purchase item was not found.")
            return

        existing_batch = await db.stock_batches.find_one(
            {
                "medicine_id": MEDICINE_ID,
                "batch_number": BATCH_NUMBER,
            }
        )

        if existing_batch:
            print("STOP: Test batch already exists.")
            return

        transaction_count = (
            await db.stock_transactions.count_documents(
                {
                    "medicine_id": MEDICINE_ID,
                    "reason": "Purchase order received",
                }
            )
        )

        async def fail_before_transaction_record(*args, **kwargs):
            raise RuntimeError("Intentional rollback test")

        print("\nBaseline checks passed.")
        print("Medicine stock before:", medicine.get("stock"))
        print("Order status before:", order.get("status"))
        print("Starting controlled failure test...")

        try:
            with patch.object(
                purchase_orders,
                "create_stock_transaction",
                fail_before_transaction_record,
            ):
                await purchase_orders.receive_purchase_order(
                    PURCHASE_ORDER_ID
                )
        except RuntimeError as error:
            if str(error) != "Intentional rollback test":
                raise
            print("Expected failure triggered.")

        order_after = await db.purchase_orders.find_one(
            {"_id": order_id}
        )
        medicine_after = await db.medicines.find_one(
            {"_id": medicine_id}
        )
        batch_after = await db.stock_batches.find_one(
            {
                "medicine_id": MEDICINE_ID,
                "batch_number": BATCH_NUMBER,
            }
        )
        transaction_count_after = (
            await db.stock_transactions.count_documents(
                {
                    "medicine_id": MEDICINE_ID,
                    "reason": "Purchase order received",
                }
            )
        )

        checks = {
            "Order remains draft/ordered": (
                order_after is not None
                and order_after.get("status") in {"draft", "ordered"}
            ),
            "Medicine stock unchanged": (
                medicine_after is not None
                and medicine_after.get("stock") == 3
            ),
            "Test batch was not saved": batch_after is None,
            "No new stock transaction": (
                transaction_count_after == transaction_count
            ),
        }

        print("\n--- ROLLBACK TEST RESULTS ---")
        for description, passed in checks.items():
            print(f"{'PASS' if passed else 'FAIL'}: {description}")

        if all(checks.values()):
            print("\nSUCCESS: Receiving changes were rolled back.")
        else:
            print("\nWARNING: One or more checks failed.")
            print("Do not retry receiving until the state is inspected.")

    except HTTPException as error:
        print("HTTP error:", error.status_code, error.detail)
        print("Test stopped. Inspect state before retrying.")

    except Exception as error:
        print("TEST ERROR:", type(error).__name__, str(error))
        print("Test stopped. Inspect state before retrying.")

    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
