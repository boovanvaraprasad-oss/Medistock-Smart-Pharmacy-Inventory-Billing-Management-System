from datetime import datetime, time, timedelta, timezone

from bson import ObjectId
from fastapi import HTTPException, status

from app.core.database import db
from app.core.permissions import ROLE_PERMISSIONS


INDIA_TIMEZONE = timezone(timedelta(hours=5, minutes=30))


async def build_notifications(user):
    """Build current inventory and purchasing alerts for one signed-in user."""
    today = datetime.now(INDIA_TIMEZONE).date()
    cutoff = datetime.combine(today + timedelta(days=31), time.min)
    alerts = []

    async for medicine in db.medicines.find(
        {"is_active": {"$ne": False}},
        {"name": 1, "sku": 1, "stock": 1, "reorder_threshold": 1},
    ):
        stock = int(medicine.get("stock", 0) or 0)
        threshold = int(medicine.get("reorder_threshold", 10) or 0)
        if stock <= threshold:
            is_empty = stock <= 0
            alerts.append({
                "id": f"low-stock:{medicine['_id']}",
                "type": "out_of_stock" if is_empty else "low_stock",
                "priority": "critical" if is_empty else "warning",
                "title": "Out of stock" if is_empty else "Low stock",
                "message": f"{medicine.get('name', 'Medicine')} has {stock} units remaining; minimum level is {threshold}.",
                "medicine_name": medicine.get("name", "Medicine"),
                "sku": medicine.get("sku"),
                "current_stock": stock,
                "minimum_stock": threshold,
                "href": "medicines.html",
            })

    batch_alerts = await db.stock_batches.find(
        {
            "is_active": True,
            "quantity": {"$gt": 0},
            "expiry_date": {"$lt": cutoff},
        },
        {"medicine_id": 1, "batch_number": 1, "quantity": 1, "expiry_date": 1},
    ).sort("expiry_date", 1).to_list(length=None)
    medicine_ids = list({batch["medicine_id"] for batch in batch_alerts})
    medicine_names = {}
    if medicine_ids:
        async for medicine in db.medicines.find(
            {"_id": {"$in": medicine_ids}},
            {"name": 1},
        ):
            medicine_names[medicine["_id"]] = medicine.get("name", "Medicine")

    for batch in batch_alerts:
        expiry = batch.get("expiry_date")
        if not isinstance(expiry, datetime):
            continue
        expiry_date = expiry.date()
        days_left = (expiry_date - today).days
        expired = days_left < 0
        medicine_name = medicine_names.get(batch["medicine_id"], "Medicine")
        alerts.append({
            "id": f"batch-expiry:{batch['_id']}",
            "type": "expired_batch" if expired else "expiring_batch",
            "priority": "critical" if expired else "warning",
            "title": "Expired batch" if expired else "Batch expiring soon",
            "message": (
                f"{medicine_name}, batch {batch.get('batch_number', '—')}, "
                f"has {batch.get('quantity', 0)} units and "
                f"{'expired' if expired else f'expires in {days_left} days'}."
            ),
            "medicine_name": medicine_name,
            "batch_number": batch.get("batch_number"),
            "quantity": batch.get("quantity", 0),
            "expiry_date": expiry_date.isoformat(),
            "days_until_expiry": days_left,
            "href": "batches.html",
        })

    role_permissions = ROLE_PERMISSIONS.get(user.get("role"), [])
    if "purchase:read" in role_permissions:
        open_orders = await db.purchase_orders.find(
            {
                "is_active": {"$ne": False},
                "status": {"$in": ["draft", "ordered"]},
            },
            {"supplier_id": 1, "status": 1},
        ).to_list(length=None)
        supplier_ids = list({order["supplier_id"] for order in open_orders if order.get("supplier_id")})
        supplier_names = {}
        if supplier_ids:
            async for supplier in db.suppliers.find(
                {"_id": {"$in": supplier_ids}},
                {"name": 1},
            ):
                supplier_names[supplier["_id"]] = supplier.get("name", "Supplier")
        for order in open_orders:
            supplier = supplier_names.get(order.get("supplier_id"), "Supplier")
            status_label = order.get("status", "draft").replace("_", " ").title()
            alerts.append({
                "id": f"purchase-order:{order['_id']}",
                "type": "open_purchase_order",
                "priority": "info",
                "title": "Purchase order needs attention",
                "message": f"{supplier} · {status_label}",
                "supplier_name": supplier,
                "status": order.get("status"),
                "href": "purchase_orders.html",
            })

    user_id = user["_id"]
    read_docs = await db.notification_reads.find(
        {"user_id": user_id},
        {"notification_id": 1},
    ).to_list(length=None)
    read_ids = {record["notification_id"] for record in read_docs}

    priority_order = {"critical": 0, "warning": 1, "info": 2}
    alerts.sort(key=lambda alert: (priority_order.get(alert["priority"], 3), alert["title"].lower()))
    for alert in alerts:
        alert["is_read"] = alert["id"] in read_ids

    return {
        "unread_count": sum(not alert["is_read"] for alert in alerts),
        "total_count": len(alerts),
        "items": alerts,
    }


async def set_notification_read(user, notification_id: str, read: bool = True):
    state = await build_notifications(user)
    if notification_id not in {item["id"] for item in state["items"]}:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification is no longer active",
        )

    query = {"user_id": user["_id"], "notification_id": notification_id}
    if read:
        await db.notification_reads.update_one(
            query,
            {"$set": {"read_at": datetime.now(timezone.utc)}},
            upsert=True,
        )
    else:
        await db.notification_reads.delete_one(query)
    return await build_notifications(user)


async def set_all_notifications_read(user):
    state = await build_notifications(user)
    now = datetime.now(timezone.utc)
    for item in state["items"]:
        await db.notification_reads.update_one(
            {"user_id": user["_id"], "notification_id": item["id"]},
            {"$set": {"read_at": now}},
            upsert=True,
        )
    return await build_notifications(user)
