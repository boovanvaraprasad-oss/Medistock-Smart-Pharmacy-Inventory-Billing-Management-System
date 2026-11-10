import calendar
from datetime import date, datetime, time, timedelta, timezone
from collections import defaultdict

from app.core.database import db


INDIA_TIMEZONE = timezone(timedelta(hours=5, minutes=30))


async def get_dashboard_summary(selected_date: date | None = None, selected_month: str | None = None):
    """Return current inventory and all-time business summary values."""

    now = datetime.now(INDIA_TIMEZONE)
    selected_date = selected_date or now.date()
    try:
        selected_month_date = datetime.strptime(selected_month, "%Y-%m").date() if selected_month else now.date().replace(day=1)
    except ValueError:
        selected_month_date = now.date().replace(day=1)
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
            "name": 1,
            "sku": 1,
        },
    )

    active_medicine_count = 0
    low_stock_count = 0
    out_of_stock_count = 0
    low_stock_medicines = []

    async for medicine in medicines:
        active_medicine_count += 1

        stock = medicine.get("stock", 0)
        reorder_threshold = medicine.get("reorder_threshold", 10)

        if stock <= 0:
            out_of_stock_count += 1

        if stock <= reorder_threshold:
            low_stock_count += 1
            low_stock_medicines.append(
                {
                    "id": str(medicine["_id"]),
                    "name": medicine.get("name", "Unknown medicine"),
                    "sku": medicine.get("sku"),
                    "stock": stock,
                    "threshold": reorder_threshold,
                    "status": "out_of_stock" if stock <= 0 else "low_stock",
                }
            )

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
    purchases_by_year = defaultdict(float)
    purchases_by_hour_today = defaultdict(float)
    purchases_by_day_current_month = defaultdict(float)
    sales_by_hour_selected_date = defaultdict(float)
    purchases_by_hour_selected_date = defaultdict(float)
    sales_by_day_selected_month = defaultdict(float)
    purchases_by_day_selected_month = defaultdict(float)
    selected_date_sales_total = 0.0
    selected_month_sales_total = 0.0
    completed_bill_count_today = 0
    yesterday_sales_total = 0.0
    received_purchase_total_all_time = 0.0

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
            completed_bill_count_today += 1
            sales_by_hour_today[local_sale_date.hour] += amount
        elif local_sale_date.date() == now.date() - timedelta(days=1):
            yesterday_sales_total += amount

        if local_sale_date.date() == selected_date:
            selected_date_sales_total += amount
            sales_by_hour_selected_date[local_sale_date.hour] += amount

        if (
            local_sale_date.year == now.year
            and local_sale_date.month == now.month
        ):
            sales_by_day_current_month[local_sale_date.day] += amount
        if (
            local_sale_date.year == selected_month_date.year
            and local_sale_date.month == selected_month_date.month
        ):
            selected_month_sales_total += amount
            sales_by_day_selected_month[local_sale_date.day] += amount

    # Measure purchases when stock is received. Older orders use their ObjectId
    # creation time because they predate the received_at timestamp.
    received_orders = await db.purchase_orders.find(
        {
            "status": "received",
            "is_active": {"$ne": False},
        },
        {"received_at": 1},
    ).to_list(length=None)
    if received_orders:
        order_ids = [order["_id"] for order in received_orders]
        order_totals = defaultdict(float)
        async for item in db.purchase_items.find(
            {"purchase_order_id": {"$in": order_ids}},
            {"purchase_order_id": 1, "total_price": 1, "quantity": 1, "unit_price": 1},
        ):
            order_totals[item["purchase_order_id"]] += float(
                item.get("total_price", item.get("quantity", 0) * item.get("unit_price", 0))
            )

        for order in received_orders:
            amount = order_totals[order["_id"]]
            received_purchase_total_all_time += amount
            received_at = order.get("received_at")
            if not isinstance(received_at, datetime):
                received_at = order["_id"].generation_time
            elif received_at.tzinfo is None:
                received_at = received_at.replace(tzinfo=timezone.utc)
            local_received_date = received_at.astimezone(INDIA_TIMEZONE)
            purchases_by_year[local_received_date.year] += amount
            if local_received_date.date() == now.date():
                purchases_by_hour_today[local_received_date.hour] += amount
            if local_received_date.date() == selected_date:
                purchases_by_hour_selected_date[local_received_date.hour] += amount
            if (
                local_received_date.year == now.year
                and local_received_date.month == now.month
            ):
                purchases_by_day_current_month[local_received_date.day] += amount
            if (
                local_received_date.year == selected_month_date.year
                and local_received_date.month == selected_month_date.month
            ):
                purchases_by_day_selected_month[local_received_date.day] += amount

    open_purchase_order_count = await db.purchase_orders.count_documents(
        {
            "is_active": {"$ne": False},
            "status": {"$in": ["draft", "ordered"]},
        }
    )

    top_selling_medicines = await db.bill_items.aggregate(
        [
            {
                "$lookup": {
                    "from": "bills",
                    "localField": "bill_id",
                    "foreignField": "_id",
                    "as": "bill",
                }
            },
            {"$unwind": "$bill"},
            {
                "$match": {
                    "bill.status": "completed",
                    "bill.is_active": {"$ne": False},
                }
            },
            {
                "$addFields": {
                    "returned_quantity": {
                        "$sum": {
                            "$map": {
                                "input": {
                                    "$filter": {
                                        "input": {
                                            "$ifNull": [
                                                "$bill.batch_allocations",
                                                [],
                                            ]
                                        },
                                        "as": "allocation",
                                        "cond": {
                                            "$eq": [
                                                "$$allocation.medicine_id",
                                                {"$toString": "$medicine_id"},
                                            ]
                                        },
                                    }
                                },
                                "as": "allocation",
                                "in": {
                                    "$ifNull": [
                                        "$$allocation.quantity_returned",
                                        0,
                                    ]
                                },
                            }
                        }
                    }
                }
            },
            {
                "$addFields": {
                    "net_quantity_sold": {
                        "$cond": [
                            {
                                "$gt": [
                                    {
                                        "$subtract": [
                                            "$quantity",
                                            "$returned_quantity",
                                        ]
                                    },
                                    0,
                                ]
                            },
                            {
                                "$subtract": [
                                    "$quantity",
                                    "$returned_quantity",
                                ]
                            },
                            0,
                        ]
                    }
                }
            },
            {
                "$group": {
                    "_id": "$medicine_id",
                    "units_sold": {"$sum": "$net_quantity_sold"},
                    "revenue": {"$sum": "$total_price"},
                }
            },
            {
                "$lookup": {
                    "from": "medicines",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "medicine",
                }
            },
            {"$unwind": {"path": "$medicine", "preserveNullAndEmptyArrays": True}},
            {
                "$project": {
                    "_id": 0,
                    "medicine_id": {"$toString": "$_id"},
                    "medicine_name": {
                        "$ifNull": ["$medicine.name", "Unknown medicine"]
                    },
                    "units_sold": 1,
                    "revenue": {"$round": ["$revenue", 2]},
                }
            },
            {"$sort": {"units_sold": -1, "revenue": -1}},
            {"$limit": 5},
        ]
    ).to_list(length=5)

    category_values = await db.stock_batches.aggregate(
        [
            {
                "$match": {
                    "is_active": True,
                    "quantity": {"$gt": 0},
                }
            },
            {
                "$lookup": {
                    "from": "medicines",
                    "localField": "medicine_id",
                    "foreignField": "_id",
                    "as": "medicine",
                }
            },
            {"$unwind": {"path": "$medicine", "preserveNullAndEmptyArrays": True}},
            {
                "$group": {
                    "_id": "$medicine.category_id",
                    "stock_value": {
                        "$sum": {
                            "$multiply": ["$quantity", "$purchase_price"]
                        }
                    },
                }
            },
            {
                "$lookup": {
                    "from": "categories",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "category",
                }
            },
            {"$unwind": {"path": "$category", "preserveNullAndEmptyArrays": True}},
            {
                "$project": {
                    "_id": 0,
                    "category_name": {
                        "$ifNull": ["$category.name", "Uncategorized"]
                    },
                    "stock_value": {"$round": ["$stock_value", 2]},
                }
            },
            {"$sort": {"stock_value": -1}},
        ]
    ).to_list(length=None)

    total_category_stock_value = sum(
        float(category.get("stock_value", 0)) for category in category_values
    )
    if len(category_values) > 5:
        top_categories = category_values[:4]
        other_value = sum(
            float(category.get("stock_value", 0)) for category in category_values[4:]
        )
        top_categories.append(
            {"category_name": "Others", "stock_value": round(other_value, 2)}
        )
    else:
        top_categories = category_values

    category_distribution = [
        {
            **category,
            "percentage": round(
                float(category.get("stock_value", 0))
                / total_category_stock_value
                * 100,
                1,
            ) if total_category_stock_value else 0,
        }
        for category in top_categories
    ]

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
            "current_date": now.date().isoformat(),
            "selected_date": selected_date.isoformat(),
            "selected_date_sales_total": round(selected_date_sales_total, 2),
            "selected_date_hourly_totals": [
                {
                    "hour": hour,
                    "total_amount": round(sales_by_hour_selected_date[hour], 2),
                    "purchase_amount": round(purchases_by_hour_selected_date[hour], 2),
                }
                for hour in range(now.hour + 1 if selected_date == now.date() else 24)
            ],
            "daily_sales_total": round(
                sum(sales_by_hour_today.values()),
                2,
            ),
            "daily_completed_bill_count": completed_bill_count_today,
            "daily_sales_change_percentage": (
                round(
                    (sum(sales_by_hour_today.values()) - yesterday_sales_total)
                    / yesterday_sales_total
                    * 100,
                    1,
                )
                if yesterday_sales_total > 0
                else None
            ),
            "yesterday_sales_total": round(yesterday_sales_total, 2),
            "daily_hourly_totals": [
                {
                    "hour": hour,
                    "total_amount": round(
                        sales_by_hour_today[hour],
                        2,
                    ),
                    "purchase_amount": round(purchases_by_hour_today[hour], 2),
                }
                for hour in range(now.hour + 1)
            ],
            "current_month": now.strftime("%B %Y"),
            "selected_month": selected_month_date.strftime("%B %Y"),
            "selected_month_sales_total": round(selected_month_sales_total, 2),
            "selected_month_daily_totals": [
                {
                    "day": day,
                    "total_amount": round(sales_by_day_selected_month[day], 2),
                    "purchase_amount": round(purchases_by_day_selected_month[day], 2),
                }
                for day in range(
                    1,
                    now.day + 1
                    if selected_month_date.year == now.year and selected_month_date.month == now.month
                    else calendar.monthrange(selected_month_date.year, selected_month_date.month)[1] + 1,
                )
            ],
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
                    "purchase_amount": round(purchases_by_day_current_month[day], 2),
                }
                for day in range(1, now.day + 1)
            ],
            "yearly_totals": [
                {
                    "year": year,
                    "total_amount": round(sales_by_year[year], 2),
                    "purchase_amount": round(purchases_by_year[year], 2),
                }
                for year in sorted(set(sales_by_year) | set(purchases_by_year))
            ],
            "daily_purchase_total": round(sum(purchases_by_hour_today.values()), 2),
            "monthly_purchase_total": round(sum(purchases_by_day_current_month.values()), 2),
        },
        "purchasing": {
            "open_purchase_order_count": open_purchase_order_count,
            "received_purchase_total_all_time": round(received_purchase_total_all_time, 2),
        },
        "top_selling_medicines": top_selling_medicines,
        "category_distribution": category_distribution,
        "alerts": {
            "low_stock_medicines": sorted(
                low_stock_medicines,
                key=lambda medicine: (medicine["stock"], medicine["name"].lower()),
            )
        },
    }
