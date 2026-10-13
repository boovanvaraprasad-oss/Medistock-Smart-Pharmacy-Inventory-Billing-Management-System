import asyncio
from bson import ObjectId
from app.core.database import db


async def main():
    order_id = "6accb2f71157370f4e1b599d"

    order = await db.purchase_orders.find_one({
        "_id": ObjectId(order_id)
    })

    if order:
        print("Order found in MongoDB")
        print("ID:", str(order["_id"]))
        print("Status:", order.get("status"))
        print("Active:", order.get("is_active"))
    else:
        print("Order not found in MongoDB")


asyncio.run(main())