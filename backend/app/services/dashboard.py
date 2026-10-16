from datetime import datetime, time, timedelta, timezone

from app.core.database import db


INDIA_TIMEZONE = timezone(timedelta(hours=5, minutes=30))


async def get_dashboard_summary():
    """Return current inventory and all-time business summary values."""

    now = datetime.now(INDIA_TIMEZONE)
    today_start = datetime.combine(now.date(), time.min)
    expiring_cutoff = datetime.combine(
        now.date() + timedelta(days=31),
        time.min,
    )

    # Count active medicines and calculate low-stock totals.
    medicines = db.medicines.find(
        {"is_active": {"$ne": False}},
        {
            "stock": 1,
            "reorder_threshold": 1,
        },
    )

    active_medicine_count = 0
    low_stock_count = 0
    out_of_stock_count = 0

    async for medicine in medicines:
        active_medicine_count += 1

        stock = medicine.get("stock", 0)
        reorder_threshold = medicine.get("reorder_threshold", 10)

        if stock <= 0:
            out_of_stock_count += 1

        if stock <= reorder_threshold:
            low_stock_count += 1

    # Calculate current units and estimated purchase-cost value from batches.
    batches = db.stock_batches.find(
        {
            "is_active": True,
            "quantity": {"$gt": 0},
        },
        {
            "quantity": 1,
            "purchase_price": 1,
        },
    )

    total_stock_units = 0
    inventory_purchase_cost = 0.0

    async for batch in batches:
        quantity = batch.get("quantity", 0)
        purchase_price = batch.get("purchase_price", 0)

        total_stock_units += quantity
        inventory_purchase_cost += quantity * float(purchase_price)

    # Count active batches that are already expired or expiring within 30 days.
    expired_batch_count = await db.stock_batches.count_documents(
        {
            "is_active": True,
            "quantity": {"$gt": 0},
            "expiry_date": {"$lt": today_start},
        }
    )

    expiring_batch_count = await db.stock_batches.count_documents(
        {
            "is_active": True,
            "quantity": {"$gt": 0},
            "expiry_date": {
                "$gte": today_start,
                "$lt": expiring_cutoff,
            },
        }
    )

    # These are all-time totals because bills do not currently store
    # a completion timestamp.
    completed_bills = db.bills.find(
        {
            "status": "completed",
            "is_active": {"$ne": False},
        },
        {"total_amount": 1},
    )

    completed_bill_count = 0
    completed_sales_total = 0.0

    async for bill in completed_bills:
        completed_bill_count += 1
        completed_sales_total += float(
            bill.get("total_amount", 0)
        )

    open_purchase_order_count = await db.purchase_orders.count_documents(
        {
            "is_active": {"$ne": False},
            "status": {"$in": ["draft", "ordered"]},
        }
    )

    return {
        "generated_at": now.isoformat(),
        "medicines": {
            "active_count": active_medicine_count,
            "low_stock_count": low_stock_count,
            "out_of_stock_count": out_of_stock_count,
        },
        "inventory": {
            "total_units": total_stock_units,
            "purchase_cost_value": round(
                inventory_purchase_cost,
                2,
            ),
            "expired_batch_count": expired_batch_count,
            "expiring_within_30_days_count": expiring_batch_count,
        },
        "sales": {
            "completed_bill_count_all_time": completed_bill_count,
            "completed_sales_total_all_time": round(
                completed_sales_total,
                2,
            ),
        },
        "purchasing": {
            "open_purchase_order_count": open_purchase_order_count,
        },
    }