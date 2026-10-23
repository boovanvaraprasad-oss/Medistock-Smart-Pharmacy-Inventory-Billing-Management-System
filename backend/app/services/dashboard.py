from datetime import datetime, time, timedelta, timezone
from collections import defaultdict

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

    # Track completed sales by year for the all-time dashboard graph. Older
    # bills predate completed_at, so their ObjectId creation time is used.
    completed_bills = db.bills.find(
        {
            "status": "completed",
            "is_active": {"$ne": False},
        },
        {"total_amount": 1, "completed_at": 1},
    )

    completed_bill_count = 0
    completed_sales_total = 0.0
    sales_by_year = defaultdict(float)
    sales_by_hour_today = defaultdict(float)
    sales_by_day_current_month = defaultdict(float)

    async for bill in completed_bills:
        completed_bill_count += 1
        amount = float(bill.get("total_amount", 0))
        completed_sales_total += amount

        sale_date = bill.get("completed_at")
        if not isinstance(sale_date, datetime):
            sale_date = bill["_id"].generation_time
        elif sale_date.tzinfo is None:
            sale_date = sale_date.replace(tzinfo=timezone.utc)

        local_sale_date = sale_date.astimezone(INDIA_TIMEZONE)
        sales_by_year[local_sale_date.year] += amount

        if local_sale_date.date() == now.date():
            sales_by_hour_today[local_sale_date.hour] += amount

        if (
            local_sale_date.year == now.year
            and local_sale_date.month == now.month
        ):
            sales_by_day_current_month[local_sale_date.day] += amount

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
            "yearly_totals": [
                {
                    "year": year,
                    "total_amount": round(amount, 2),
                }
                for year, amount in sorted(sales_by_year.items())
            ],
            "current_date": now.date().isoformat(),
            "daily_sales_total": round(
                sum(sales_by_hour_today.values()),
                2,
            ),
            "daily_hourly_totals": [
                {
                    "hour": hour,
                    "total_amount": round(
                        sales_by_hour_today[hour],
                        2,
                    ),
                }
                for hour in range(now.hour + 1)
            ],
            "current_month": now.strftime("%B %Y"),
            "monthly_sales_total": round(
                sum(sales_by_day_current_month.values()),
                2,
            ),
            "monthly_daily_totals": [
                {
                    "day": day,
                    "total_amount": round(
                        sales_by_day_current_month[day],
                        2,
                    ),
                }
                for day in range(1, now.day + 1)
            ],
        },
        "purchasing": {
            "open_purchase_order_count": open_purchase_order_count,
        },
    }
