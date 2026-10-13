from bson import ObjectId
from fastapi import HTTPException, status

from app.core.database import db


async def recalculate_bill_subtotal(
    bill_object_id: ObjectId,
):
    """
    Recalculate the bill subtotal from all bill items.

    Tax and final total are calculated separately
    by the billing service.
    """

    bill_items = db.bill_items.find(
        {
            "bill_id": bill_object_id,
        }
    )

    subtotal = 0.0

    async for item in bill_items:
        subtotal += float(
            item.get(
                "total_price",
                0,
            )
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

    tax_percentage = float(
        bill.get(
            "tax_percentage",
            0.0,
        )
    )

    tax_amount = round(
        subtotal * tax_percentage / 100,
        2,
    )

    total_amount = round(
        subtotal + tax_amount,
        2,
    )

    await db.bills.update_one(
        {
            "_id": bill_object_id,
        },
        {
            "$set": {
                "subtotal": subtotal,
                "tax_amount": tax_amount,
                "total_amount": total_amount,
            }
        },
    )

    return {
        "subtotal": subtotal,
        "tax_percentage": tax_percentage,
        "tax_amount": tax_amount,
        "total_amount": total_amount,
    }


async def create_bill_item(
    bill_id: str,
    medicine_id: str,
    quantity: int,
):
    # Validate bill ID
    try:
        bill_object_id = ObjectId(bill_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid bill ID",
        )

    if quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity must be greater than zero",
        )

    # Check whether bill exists
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

    # Only draft bills can receive new items
    if bill.get("status") != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft bills can be modified",
        )

    # Validate medicine ID
    try:
        medicine_object_id = ObjectId(medicine_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid medicine ID",
        )

    # Check whether medicine exists
    medicine = await db.medicines.find_one(
        {
            "_id": medicine_object_id,
            "is_active": True,
        }
    )

    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine not found or inactive",
        )

    # Get medicine price
    unit_price = medicine.get(
        "price",
        0,
    )

    if unit_price <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Medicine price is not set",
        )

    # Check available stock
    current_stock = medicine.get(
        "stock",
        0,
    )

    if quantity > current_stock:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient stock",
        )

    # Calculate item total
    total_price = quantity * unit_price

    # Create bill item
    bill_item = {
        "bill_id": bill_object_id,
        "medicine_id": medicine_object_id,
        "quantity": quantity,
        "unit_price": unit_price,
        "total_price": total_price,
    }

    result = await db.bill_items.insert_one(
        bill_item
    )

    # Recalculate subtotal and tax
    totals = await recalculate_bill_subtotal(
        bill_object_id
    )

    return {
        "id": str(result.inserted_id),
        "bill_id": bill_id,
        "medicine_id": medicine_id,
        "medicine_name": medicine["name"],
        "quantity": quantity,
        "unit_price": unit_price,
        "total_price": total_price,
        "subtotal": totals["subtotal"],
        "tax_percentage": totals[
            "tax_percentage"
        ],
        "tax_amount": totals["tax_amount"],
        "total_amount": totals[
            "total_amount"
        ],
    }


async def update_bill_item(
    bill_item_id: str,
    quantity: int,
):
    # Validate bill item ID
    try:
        bill_item_object_id = ObjectId(
            bill_item_id
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid bill item ID",
        )

    if quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity must be greater than zero",
        )

    # Find bill item
    bill_item = await db.bill_items.find_one(
        {
            "_id": bill_item_object_id,
        }
    )

    if not bill_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bill item not found",
        )

    bill_object_id = bill_item["bill_id"]

    # Find the bill
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

    # Only draft bills can be changed
    if bill.get("status") != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft bills can be modified",
        )

    # Find medicine
    medicine = await db.medicines.find_one(
        {
            "_id": bill_item["medicine_id"],
            "is_active": True,
        }
    )

    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine not found or inactive",
        )

    # Check stock
    current_stock = medicine.get(
        "stock",
        0,
    )

    if quantity > current_stock:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient stock",
        )

    # Get current medicine price
    unit_price = medicine.get(
        "price",
        0,
    )

    if unit_price <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Medicine price is not set",
        )

    # Calculate new item total
    total_price = quantity * unit_price

    # Update bill item
    await db.bill_items.update_one(
        {
            "_id": bill_item_object_id,
        },
        {
            "$set": {
                "quantity": quantity,
                "unit_price": unit_price,
                "total_price": total_price,
            }
        },
    )

    # Recalculate subtotal and tax
    totals = await recalculate_bill_subtotal(
        bill_object_id
    )

    return {
        "id": bill_item_id,
        "bill_id": str(bill_object_id),
        "medicine_id": str(
            bill_item["medicine_id"]
        ),
        "medicine_name": medicine["name"],
        "quantity": quantity,
        "unit_price": unit_price,
        "total_price": total_price,
        "subtotal": totals["subtotal"],
        "tax_percentage": totals[
            "tax_percentage"
        ],
        "tax_amount": totals["tax_amount"],
        "total_amount": totals[
            "total_amount"
        ],
    }


async def delete_bill_item(
    bill_item_id: str,
):
    # Validate bill item ID
    try:
        bill_item_object_id = ObjectId(
            bill_item_id
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid bill item ID",
        )

    # Find bill item
    bill_item = await db.bill_items.find_one(
        {
            "_id": bill_item_object_id,
        }
    )

    if not bill_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bill item not found",
        )

    bill_object_id = bill_item["bill_id"]

    # Find the bill
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

    # Only draft bills can be changed
    if bill.get("status") != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft bills can be modified",
        )

    # Delete the bill item
    await db.bill_items.delete_one(
        {
            "_id": bill_item_object_id,
        }
    )

    # Recalculate subtotal and tax
    totals = await recalculate_bill_subtotal(
        bill_object_id
    )

    return {
        "message": "Bill item deleted successfully",
        "bill_item_id": bill_item_id,
        "bill_id": str(bill_object_id),
        "subtotal": totals["subtotal"],
        "tax_percentage": totals[
            "tax_percentage"
        ],
        "tax_amount": totals["tax_amount"],
        "total_amount": totals[
            "total_amount"
        ],
    }