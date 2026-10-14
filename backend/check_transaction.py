import asyncio
from uuid import uuid4

from app.core.database import client, db


async def main():
    collection_name = f"_transaction_rollback_test_{uuid4().hex}"
    collection = db[collection_name]

    try:
        # Create the temporary collection before the transaction.
        await collection.insert_one({"_id": "setup"})
        print("Temporary collection created.")

        async def transaction_work(session):
            print("Starting transaction...")

            await collection.insert_one(
                {"_id": "rollback_test", "value": 1},
                session=session,
            )

            print("Test document inserted inside transaction.")

            # Deliberately fail to test rollback.
            raise RuntimeError("Intentional rollback test")

        try:
            async with await client.start_session() as session:
                await session.with_transaction(transaction_work)

        except RuntimeError as error:
            if str(error) == "Intentional rollback test":
                print("Expected error triggered.")
            else:
                raise

        # Check whether the transaction's insert was rolled back.
        result = await collection.find_one(
            {"_id": "rollback_test"}
        )

        if result is None:
            print("SUCCESS: Transaction rolled back.")
            print("The test document was not saved.")
        else:
            print("FAILED: Test document still exists.")

    except Exception as error:
        print("ROLLBACK TEST FAILED")
        print("Error type:", type(error).__name__)
        print("Error:", error)

    finally:
        try:
            await db.drop_collection(collection_name)
            print("Temporary collection cleaned up.")
        except Exception as cleanup_error:
            print("Cleanup warning:", cleanup_error)

        client.close()


if __name__ == "__main__":
    asyncio.run(main())