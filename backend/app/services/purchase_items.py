from bson import ObjectId

from fastapi import HTTPException, status

from app.core.database import db


async def create_purchase_item(
    purchase_order_id: str,
    medicine_id: str,
    quantity: int,
    unit_price: float,
):
    # Validate purchase order ID
    try:
        purchase_order_object_id = ObjectId(
            purchase_order_id
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid purchase order ID",
        )

    # Check purchase order exists
    purchase_order = await db.purchase_orders.find_one(
        {
            "_id": purchase_order_object_id,
            "is_active": True,
        }
    )

    if not purchase_order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Purchase order not found or inactive",
        )

    # Validate medicine ID
    try:
        medicine_object_id = ObjectId(medicine_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid medicine ID",
        )

    # Check medicine exists and is active
    medicine = await db.medicines.find_one(
        {
            "_id": medicine_object_id,
            "is_active": True,
        }
    )

    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Medicine not found or inactive",
        )

    # Calculate total price
    total_price = quantity * unit_price

    purchase_item = {
        "purchase_order_id": purchase_order_object_id,
        "medicine_id": medicine_object_id,
        "quantity": quantity,
        "unit_price": unit_price,
        "total_price": total_price,
    }

    result = await db.purchase_items.insert_one(
        purchase_item
    )

    return {
        "id": str(result.inserted_id),
        "purchase_order_id": purchase_order_id,
        "medicine_id": medicine_id,
        "quantity": quantity,
        "unit_price": unit_price,
        "total_price": total_price,
    }

async def get_all_purchase_items():
    purchase_items = []

    cursor = db.purchase_items.find({})

    async for purchase_item in cursor:
        purchase_items.append({
            "id": str(purchase_item["_id"]),
            "purchase_order_id": str(
                purchase_item["purchase_order_id"]
            ),
            "medicine_id": str(
                purchase_item["medicine_id"]
            ),
            "quantity": purchase_item["quantity"],
            "unit_price": purchase_item["unit_price"],
            "total_price": purchase_item["total_price"],
        })

    return purchase_items

async def update_purchase_item(
    purchase_item_id: str,
    quantity: int | None = None,
    unit_price: float | None = None,
):
    # Validate purchase item ID
    try:
        object_id = ObjectId(purchase_item_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid purchase item ID",
        )

    # Check purchase item exists
    purchase_item = await db.purchase_items.find_one(
        {"_id": object_id}
    )

    if not purchase_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase item not found",
        )

    # Make sure at least one field is provided
    if quantity is None and unit_price is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    # Use existing values when a field is not changed
    new_quantity = (
        quantity
        if quantity is not None
        else purchase_item["quantity"]
    )

    new_unit_price = (
        unit_price
        if unit_price is not None
        else purchase_item["unit_price"]
    )

    # Recalculate total price
    total_price = new_quantity * new_unit_price

    await db.purchase_items.update_one(
        {"_id": object_id},
        {
            "$set": {
                "quantity": new_quantity,
                "unit_price": new_unit_price,
                "total_price": total_price,
            }
        },
    )

    updated_purchase_item = await db.purchase_items.find_one(
        {"_id": object_id}
    )

    return {
        "id": str(updated_purchase_item["_id"]),
        "purchase_order_id": str(
            updated_purchase_item["purchase_order_id"]
        ),
        "medicine_id": str(
            updated_purchase_item["medicine_id"]
        ),
        "quantity": updated_purchase_item["quantity"],
        "unit_price": updated_purchase_item["unit_price"],
        "total_price": updated_purchase_item["total_price"],
    }