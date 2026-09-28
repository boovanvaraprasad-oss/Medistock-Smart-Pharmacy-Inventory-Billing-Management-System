from bson import ObjectId

from fastapi import HTTPException, status

from app.core.database import db
from app.services.stock_transactions import (
    create_stock_transaction,
)


async def reduce_stock(
    medicine_id: str,
    quantity: int,
):
    # Check medicine ID

    try:
        object_id = ObjectId(medicine_id)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid medicine ID",
        )

    # Find medicine

    medicine = await db.medicines.find_one(
        {
            "_id": object_id,
            "is_active": True,
        }
    )

    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine not found or inactive",
        )

    # Get current stock

    current_stock = medicine.get(
        "stock",
        0,
    )

    # Check available stock

    if quantity > current_stock:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient stock",
        )

    # Calculate new stock

    new_stock = current_stock - quantity

    # Update medicine stock

    await db.medicines.update_one(
        {"_id": object_id},
        {
            "$set": {
                "stock": new_stock,
            }
        },
    )

    # Record stock transaction

    await create_stock_transaction(
        medicine_id=medicine_id,
        transaction_type="STOCK_OUT",
        quantity=quantity,
        previous_stock=current_stock,
        new_stock=new_stock,
        reason="Medicine issued",
    )

    return {
        "medicine_id": medicine_id,
        "previous_stock": current_stock,
        "quantity_reduced": quantity,
        "remaining_stock": new_stock,
    }