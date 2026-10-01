from bson import ObjectId
from fastapi import HTTPException, status

from app.core.database import db
from app.services.stock_transactions import (
    create_stock_transaction,
)


async def create_bill(
    customer_name: str,
    customer_phone: str,
):
    bill = {
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "total_amount": 0.0,
        "payment_status": "pending",
        "status": "draft",
        "is_active": True,
    }

    result = await db.bills.insert_one(
        bill
    )

    return {
        "id": str(result.inserted_id),
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "total_amount": 0.0,
        "payment_status": "pending",
        "status": "draft",
        "is_active": True,
    }


async def complete_bill(
    bill_id: str,
):
    try:
        bill_object_id = ObjectId(bill_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid bill ID",
        )

    bill = await db.bills.find_one(
        {
            "_id": bill_object_id,
            "is_active": True,
        }
    )

    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bill not found or inactive",
        )

    if bill.get("status") == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bill has already been completed",
        )

    bill_items = []

    cursor = db.bill_items.find(
        {
            "bill_id": bill_object_id,
        }
    )

    async for item in cursor:
        bill_items.append(item)

    if not bill_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bill has no items",
        )

    for item in bill_items:
        medicine = await db.medicines.find_one(
            {
                "_id": item["medicine_id"],
                "is_active": True,
            }
        )

        if not medicine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medicine not found or inactive",
            )

        current_stock = medicine.get(
            "stock",
            0,
        )

        quantity = item["quantity"]

        if quantity > current_stock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Insufficient stock for "
                    f"{medicine['name']}"
                ),
            )

    for item in bill_items:
        medicine = await db.medicines.find_one(
            {
                "_id": item["medicine_id"],
                "is_active": True,
            }
        )

        current_stock = medicine.get(
            "stock",
            0,
        )

        quantity = item["quantity"]

        new_stock = current_stock - quantity

        await db.medicines.update_one(
            {
                "_id": item["medicine_id"],
            },
            {
                "$set": {
                    "stock": new_stock
                }
            },
        )

        await create_stock_transaction(
            medicine_id=str(
                item["medicine_id"]
            ),
            transaction_type="STOCK_OUT",
            quantity=quantity,
            previous_stock=current_stock,
            new_stock=new_stock,
            reason="Bill completed",
        )

    await db.bills.update_one(
        {
            "_id": bill_object_id,
        },
        {
            "$set": {
                "status": "completed",
                "payment_status": "paid",
            }
        },
    )

    updated_bill = await db.bills.find_one(
        {
            "_id": bill_object_id,
        }
    )

    return {
        "id": str(updated_bill["_id"]),
        "customer_name": updated_bill[
            "customer_name"
        ],
        "customer_phone": updated_bill[
            "customer_phone"
        ],
        "total_amount": updated_bill[
            "total_amount"
        ],
        "payment_status": updated_bill[
            "payment_status"
        ],
        "status": updated_bill["status"],
        "is_active": updated_bill.get(
            "is_active",
            True,
        ),
    }


async def get_bill_details(
    bill_id: str,
):
    try:
        bill_object_id = ObjectId(bill_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid bill ID",
        )

    bill = await db.bills.find_one(
        {
            "_id": bill_object_id,
            "is_active": True,
        }
    )

    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bill not found or inactive",
        )

    items = []

    cursor = db.bill_items.find(
        {
            "bill_id": bill_object_id,
        }
    )

    async for item in cursor:
        medicine = await db.medicines.find_one(
            {
                "_id": item["medicine_id"],
            }
        )

        medicine_name = "Unknown Medicine"

        if medicine:
            medicine_name = medicine["name"]

        items.append(
            {
                "medicine_id": str(
                    item["medicine_id"]
                ),
                "medicine_name": medicine_name,
                "quantity": item["quantity"],
                "unit_price": item["unit_price"],
                "total_price": item["total_price"],
            }
        )

    return {
        "id": str(bill["_id"]),
        "customer_name": bill["customer_name"],
        "customer_phone": bill["customer_phone"],
        "items": items,
        "total_amount": bill.get(
            "total_amount",
            0,
        ),
        "payment_status": bill.get(
            "payment_status",
            "pending",
        ),
        "status": bill.get(
            "status",
            "draft",
        ),
        "is_active": bill.get(
            "is_active",
            True,
        ),
    }


async def get_all_bills():
    bills = []

    cursor = db.bills.find({}).sort(
        "_id",
        -1,
    )

    async for bill in cursor:
        bills.append(
            {
                "id": str(
                    bill["_id"]
                ),
                "customer_name": bill[
                    "customer_name"
                ],
                "customer_phone": bill[
                    "customer_phone"
                ],
                "total_amount": bill.get(
                    "total_amount",
                    0,
                ),
                "payment_status": bill.get(
                    "payment_status",
                    "pending",
                ),
                "status": bill.get(
                    "status",
                    "draft",
                ),
                "is_active": bill.get(
                    "is_active",
                    True,
                ),
            }
        )

    return bills