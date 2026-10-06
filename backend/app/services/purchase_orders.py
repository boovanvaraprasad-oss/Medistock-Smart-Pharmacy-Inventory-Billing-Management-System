from bson import ObjectId
from fastapi import HTTPException, status

from app.core.database import db
from app.services.stock_batches import create_stock_batch
from app.services.stock_transactions import (
    create_stock_transaction,
)


async def create_purchase_order(
    supplier_id: str,
    status_value: str = "draft",
    notes: str | None = None,
):
    try:
        supplier_object_id = ObjectId(supplier_id)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid supplier ID",
        )

    supplier = await db.suppliers.find_one(
        {
            "_id": supplier_object_id,
            "is_active": True,
        }
    )

    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Supplier not found or inactive",
        )

    purchase_order = {
        "supplier_id": supplier_object_id,
        "status": status_value,
        "notes": notes,
        "is_active": True,
    }

    result = await db.purchase_orders.insert_one(
        purchase_order
    )

    return {
        "id": str(result.inserted_id),
        "supplier_id": supplier_id,
        "status": status_value,
        "notes": notes,
        "is_active": True,
    }


async def get_all_purchase_orders():
    purchase_orders = []

    cursor = db.purchase_orders.find({})

    async for purchase_order in cursor:
        purchase_orders.append(
            {
                "id": str(purchase_order["_id"]),
                "supplier_id": str(
                    purchase_order["supplier_id"]
                ),
                "status": purchase_order["status"],
                "notes": purchase_order.get("notes"),
                "is_active": purchase_order.get(
                    "is_active",
                    True,
                ),
            }
        )

    return purchase_orders


async def update_purchase_order(
    purchase_order_id: str,
    status_value: str | None = None,
    notes: str | None = None,
    is_active: bool | None = None,
):
    try:
        object_id = ObjectId(purchase_order_id)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid purchase order ID",
        )

    purchase_order = await db.purchase_orders.find_one(
        {
            "_id": object_id
        }
    )

    if not purchase_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found",
        )

    update_data = {}

    if status_value is not None:
        update_data["status"] = status_value

    if notes is not None:
        update_data["notes"] = notes

    if is_active is not None:
        update_data["is_active"] = is_active

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    await db.purchase_orders.update_one(
        {
            "_id": object_id
        },
        {
            "$set": update_data
        },
    )

    updated_purchase_order = await db.purchase_orders.find_one(
        {
            "_id": object_id
        }
    )

    return {
        "id": str(updated_purchase_order["_id"]),
        "supplier_id": str(
            updated_purchase_order["supplier_id"]
        ),
        "status": updated_purchase_order["status"],
        "notes": updated_purchase_order.get("notes"),
        "is_active": updated_purchase_order.get(
            "is_active",
            True,
        ),
    }


async def receive_purchase_order(
    purchase_order_id: str,
):
    # Validate purchase order ID
    try:
        object_id = ObjectId(purchase_order_id)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid purchase order ID",
        )

    # Find purchase order
    purchase_order = await db.purchase_orders.find_one(
        {
            "_id": object_id
        }
    )

    if not purchase_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found",
        )

    # Make sure the order has not already been received
    if purchase_order.get("status") == "received":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Purchase order has already been received",
        )

    # Get all items belonging to this purchase order
    purchase_items = []

    cursor = db.purchase_items.find(
        {
            "purchase_order_id": object_id
        }
    )

    async for purchase_item in cursor:
        purchase_items.append(purchase_item)

    if not purchase_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Purchase order has no items",
        )

    # Validate all items before changing stock
    for purchase_item in purchase_items:
        medicine_id = purchase_item["medicine_id"]

        medicine = await db.medicines.find_one(
            {
                "_id": medicine_id,
                "is_active": True,
            }
        )

        if not medicine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medicine not found or inactive",
            )

        # Batch information is required for receiving stock
        if not purchase_item.get("batch_number"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Purchase item is missing batch number"
                ),
            )

        if not purchase_item.get("expiry_date"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Purchase item is missing expiry date"
                ),
            )

    # Process each purchase item
    for purchase_item in purchase_items:
        medicine_id = purchase_item["medicine_id"]
        quantity = purchase_item["quantity"]

        # Get current medicine stock
        medicine = await db.medicines.find_one(
            {
                "_id": medicine_id,
                "is_active": True,
            }
        )

        current_stock = medicine.get(
            "stock",
            0,
        )

        new_stock = current_stock + quantity

        # Create stock batch
        await create_stock_batch(
            medicine_id=str(medicine_id),
            batch_number=purchase_item[
                "batch_number"
            ],
            quantity=quantity,
            purchase_price=purchase_item[
                "unit_price"
            ],
            manufacturing_date=purchase_item.get(
                "manufacturing_date"
            ),
            expiry_date=purchase_item[
                "expiry_date"
            ],
        )

        # Increase medicine stock
        await db.medicines.update_one(
            {
                "_id": medicine_id
            },
            {
                "$set": {
                    "stock": new_stock
                }
            },
        )

        # Create STOCK_IN transaction
        await create_stock_transaction(
            medicine_id=str(medicine_id),
            transaction_type="STOCK_IN",
            quantity=quantity,
            previous_stock=current_stock,
            new_stock=new_stock,
            reason="Purchase order received",
        )

    # Change purchase order status
    await db.purchase_orders.update_one(
        {
            "_id": object_id
        },
        {
            "$set": {
                "status": "received"
            }
        },
    )

    updated_purchase_order = await db.purchase_orders.find_one(
        {
            "_id": object_id
        }
    )

    return {
        "id": str(updated_purchase_order["_id"]),
        "supplier_id": str(
            updated_purchase_order["supplier_id"]
        ),
        "status": updated_purchase_order["status"],
        "notes": updated_purchase_order.get("notes"),
        "is_active": updated_purchase_order.get(
            "is_active",
            True,
        ),
    }