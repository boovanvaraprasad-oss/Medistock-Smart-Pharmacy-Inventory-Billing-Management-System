from datetime import datetime, time

from bson import ObjectId
from fastapi import HTTPException, status

from app.core.database import db


def date_to_datetime(value):
    if value is None:
        return None

    return datetime.combine(
        value,
        time.min,
    )


async def create_stock_batch(
    medicine_id: str,
    batch_number: str,
    quantity: int,
    purchase_price: float,
    manufacturing_date,
    expiry_date,
    session=None,
):
    """
    Create a stock batch.

    When a MongoDB session is provided, all database
    operations participate in the caller's transaction.
    """

    # Validate medicine ID
    try:
        medicine_object_id = ObjectId(medicine_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid medicine ID",
        )

    # Validate quantity and purchase price
    if quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch quantity must be greater than zero",
        )

    if purchase_price < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Purchase price cannot be negative",
        )

    # Check medicine exists and is active
    medicine = await db.medicines.find_one(
        {
            "_id": medicine_object_id,
            "is_active": True,
        },
        session=session,
    )

    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine not found or inactive",
        )

    # Validate manufacturing and expiry dates
    if (
        manufacturing_date is not None
        and expiry_date is not None
        and expiry_date <= manufacturing_date
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expiry date must be after manufacturing date",
        )

    if expiry_date is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expiry date is required",
        )

    # Check duplicate batch number for this medicine
    existing_batch = await db.stock_batches.find_one(
        {
            "medicine_id": medicine_object_id,
            "batch_number": batch_number,
        },
        session=session,
    )

    if existing_batch:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch number already exists for this medicine",
        )

    # Convert date values to MongoDB datetime values
    manufacturing_datetime = date_to_datetime(
        manufacturing_date
    )

    expiry_datetime = date_to_datetime(
        expiry_date
    )

    # Prepare batch document
    stock_batch = {
        "medicine_id": medicine_object_id,
        "batch_number": batch_number,
        "quantity": quantity,
        "purchase_price": purchase_price,
        "manufacturing_date": manufacturing_datetime,
        "expiry_date": expiry_datetime,
        "is_active": True,
    }

    # Insert batch using the supplied session
    result = await db.stock_batches.insert_one(
        stock_batch,
        session=session,
    )

    return {
        "id": str(result.inserted_id),
        "medicine_id": medicine_id,
        "batch_number": batch_number,
        "quantity": quantity,
        "purchase_price": purchase_price,
        "manufacturing_date": manufacturing_date,
        "expiry_date": expiry_date,
        "is_active": True,
    }


async def get_stock_batches(
    medicine_id: str | None = None,
):
    """
    Return active stock batches, ordered by expiry date.
    This is a read-only operation.
    """

    query = {
        "is_active": True,
    }

    if medicine_id:
        try:
            medicine_object_id = ObjectId(medicine_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid medicine ID",
            )

        query["medicine_id"] = medicine_object_id

    batches = []

    cursor = db.stock_batches.find(
        query
    ).sort(
        "expiry_date",
        1,
    )

    async for batch in cursor:
        manufacturing_date = batch.get(
            "manufacturing_date"
        )

        expiry_date = batch.get(
            "expiry_date"
        )

        batches.append(
            {
                "id": str(batch["_id"]),
                "medicine_id": str(
                    batch["medicine_id"]
                ),
                "batch_number": batch["batch_number"],
                "quantity": batch["quantity"],
                "purchase_price": batch["purchase_price"],
                "manufacturing_date": (
                    manufacturing_date.date()
                    if manufacturing_date
                    else None
                ),
                "expiry_date": (
                    expiry_date.date()
                    if expiry_date
                    else None
                ),
                "is_active": batch.get(
                    "is_active",
                    True,
                ),
            }
        )

    return batches