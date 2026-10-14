from datetime import datetime, time, timedelta, timezone

from bson import ObjectId
from fastapi import HTTPException, status

from app.core.database import db


# The application uses India local dates for batch expiry.
INDIA_TIMEZONE = timezone(timedelta(hours=5, minutes=30))


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

    try:
        medicine_object_id = ObjectId(medicine_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid medicine ID",
        )

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

    manufacturing_datetime = date_to_datetime(
        manufacturing_date
    )

    expiry_datetime = date_to_datetime(
        expiry_date
    )

    stock_batch = {
        "medicine_id": medicine_object_id,
        "batch_number": batch_number,
        "quantity": quantity,
        "purchase_price": purchase_price,
        "manufacturing_date": manufacturing_datetime,
        "expiry_date": expiry_datetime,
        "is_active": True,
    }

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


async def get_expiring_stock_batches(
    days: int = 30,
    medicine_id: str | None = None,
):
    """
    Return batches with remaining stock that are already expired
    or will expire within the requested number of days.
    """

    if (
        not isinstance(days, int)
        or isinstance(days, bool)
        or days < 0
        or days > 365
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Days must be between 0 and 365",
        )

    today = datetime.now(
        INDIA_TIMEZONE
    ).date()

    # Include the whole final day in the requested date range.
    final_date = today + timedelta(days=days)
    cutoff_exclusive = datetime.combine(
        final_date + timedelta(days=1),
        time.min,
    )

    query = {
        "is_active": True,
        "quantity": {"$gt": 0},
        "expiry_date": {"$lt": cutoff_exclusive},
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

    alerts = []

    cursor = db.stock_batches.find(
        query
    ).sort(
        "expiry_date",
        1,
    )

    async for batch in cursor:
        expiry_datetime = batch.get("expiry_date")

        if expiry_datetime is None:
            continue

        expiry_date = expiry_datetime.date()
        days_until_expiry = (expiry_date - today).days

        medicine = await db.medicines.find_one(
            {"_id": batch["medicine_id"]},
            {"name": 1},
        )

        if days_until_expiry < 0:
            alert_status = "expired"
        else:
            alert_status = "expiring_soon"

        alerts.append(
            {
                "batch_id": str(batch["_id"]),
                "medicine_id": str(batch["medicine_id"]),
                "medicine_name": (
                    medicine.get("name", "Unknown Medicine")
                    if medicine
                    else "Unknown Medicine"
                ),
                "batch_number": batch.get("batch_number", ""),
                "quantity": batch.get("quantity", 0),
                "purchase_price": batch.get("purchase_price", 0),
                "expiry_date": expiry_date,
                "days_until_expiry": days_until_expiry,
                "alert_status": alert_status,
            }
        )

    return {
        "days_checked": days,
        "count": len(alerts),
        "items": alerts,
    }