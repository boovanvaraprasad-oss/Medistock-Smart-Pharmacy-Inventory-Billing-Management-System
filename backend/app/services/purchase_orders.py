from datetime import datetime, timedelta, timezone

from bson import ObjectId
from fastapi import HTTPException, status

from app.core.database import client, db
from app.services.audit_log import create_audit_log
from app.services.stock_batches import create_stock_batch
from app.services.stock_transactions import (
    create_stock_transaction,
)


async def create_purchase_order(
    supplier_id: str,
    actor_user_id: str,
    actor_role: str,
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

    if status_value != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Purchase orders must be created as draft",
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
        "status": "draft",
        "notes": notes,
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
    }

    async def transaction_work(session):
        result = await db.purchase_orders.insert_one(
            purchase_order,
            session=session,
        )
        await create_audit_log(
            action="PURCHASE_ORDER_CREATE",
            entity_type="purchase_orders",
            entity_id=str(result.inserted_id),
            entity_label=str(result.inserted_id),
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            details={"supplier_name": supplier.get("name", "Unknown supplier")},
            session=session,
        )
        return result

    async with await client.start_session() as session:
        result = await session.with_transaction(transaction_work)

    return {
        "id": str(result.inserted_id),
        "supplier_id": supplier_id,
        "status": "draft",
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
                    "is_active", True
                ),
            }
        )

    return purchase_orders


async def update_purchase_order(
    purchase_order_id: str,
    actor_user_id: str,
    actor_role: str,
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
        {"_id": object_id}
    )

    if not purchase_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found",
        )

    if purchase_order.get("status") == "received":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Received purchase orders cannot be edited",
        )

    if status_value is not None and status_value == "received":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use the receive endpoint to receive stock",
        )

    update_data = {}

    if status_value is not None:
        if status_value not in {"draft", "ordered", "cancelled"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid purchase order status",
            )
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

    changed_fields = [
        field
        for field, value in update_data.items()
        if purchase_order.get(field, True if field == "is_active" else None) != value
    ]
    audit_details = {"changed_fields": changed_fields}
    if "status" in changed_fields:
        audit_details["previous_status"] = purchase_order.get("status")
        audit_details["status"] = update_data["status"]
    if "is_active" in changed_fields:
        audit_details["previous_is_active"] = purchase_order.get("is_active", True)
        audit_details["is_active"] = update_data["is_active"]

    async def transaction_work(session):
        if changed_fields:
            order_filter = {"_id": object_id}
            for field in ("status", "is_active"):
                if field in purchase_order:
                    order_filter[field] = purchase_order[field]
                elif field == "is_active":
                    order_filter[field] = {"$exists": False}
            result = await db.purchase_orders.update_one(
                order_filter,
                {"$set": {field: update_data[field] for field in changed_fields}},
                session=session,
            )
            if result.modified_count != 1:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Purchase order changed while the update was in progress; retry",
                )
            await create_audit_log(
                action="PURCHASE_ORDER_UPDATE",
                entity_type="purchase_orders",
                entity_id=str(object_id),
                entity_label=str(purchase_order.get("order_number", object_id)),
                actor_user_id=actor_user_id,
                actor_role=actor_role,
                details=audit_details,
                session=session,
            )
        return await db.purchase_orders.find_one(
            {"_id": object_id},
            session=session,
        )

    async with await client.start_session() as session:
        updated = await session.with_transaction(transaction_work)

    return {
        "id": str(updated["_id"]),
        "supplier_id": str(updated["supplier_id"]),
        "status": updated["status"],
        "notes": updated.get("notes"),
        "is_active": updated.get("is_active", True),
    }


async def receive_purchase_order(
    purchase_order_id: str,
    actor_user_id: str,
    actor_role: str,
):
    try:
        object_id = ObjectId(purchase_order_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid purchase order ID",
        )

    async def transaction_work(session):
        purchase_order = await db.purchase_orders.find_one(
            {
                "_id": object_id,
                "is_active": True,
                "status": {"$in": ["draft", "ordered"]},
            },
            session=session,
        )

        if not purchase_order:
            existing = await db.purchase_orders.find_one(
                {"_id": object_id},
                session=session,
            )

            if not existing or not existing.get("is_active", True):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Purchase order not found or inactive",
                )

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Purchase order is not eligible for receiving",
            )

        items_cursor = db.purchase_items.find(
            {"purchase_order_id": object_id},
            session=session,
        )
        purchase_items = await items_cursor.to_list(length=None)

        if not purchase_items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Purchase order has no items",
            )

        # Validate all items before changing any stock.
        for item in purchase_items:
            medicine_id = item.get("medicine_id")
            quantity = item.get("quantity", 0)
            batch_number = item.get("batch_number")
            expiry_date = item.get("expiry_date")

            if not isinstance(medicine_id, ObjectId):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid medicine reference in purchase item",
                )

            if (
                not isinstance(quantity, int)
                or isinstance(quantity, bool)
                or quantity <= 0
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Purchase quantity must be a positive integer",
                )

            if not batch_number or expiry_date is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Purchase item requires batch number and expiry date",
                )

            medicine = await db.medicines.find_one(
                {
                    "_id": medicine_id,
                    "is_active": True,
                },
                session=session,
            )

            if not medicine:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Medicine not found or inactive",
                )

        # Receive each item inside the same transaction.
        for item in purchase_items:
            medicine_id = item["medicine_id"]
            quantity = item["quantity"]

            medicine = await db.medicines.find_one(
                {
                    "_id": medicine_id,
                    "is_active": True,
                },
                session=session,
            )

            current_stock = medicine.get("stock", 0)
            new_stock = current_stock + quantity

            await create_stock_batch(
                medicine_id=str(medicine_id),
                batch_number=item["batch_number"],
                quantity=quantity,
                purchase_price=item["unit_price"],
                manufacturing_date=item.get("manufacturing_date"),
                expiry_date=item["expiry_date"],
                session=session,
            )

            stock_update = await db.medicines.update_one(
                {
                    "_id": medicine_id,
                    "is_active": True,
                    "stock": current_stock,
                },
                {"$set": {"stock": new_stock}},
                session=session,
            )

            if stock_update.modified_count != 1:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Medicine stock changed. Please try again.",
                )

            await create_stock_transaction(
                medicine_id=str(medicine_id),
                transaction_type="STOCK_IN",
                quantity=quantity,
                previous_stock=current_stock,
                new_stock=new_stock,
                reason="Purchase order received",
                session=session,
            )

        order_update = await db.purchase_orders.update_one(
            {
                "_id": object_id,
                "is_active": True,
                "status": {"$in": ["draft", "ordered"]},
            },
            {
                "$set": {
                    "status": "received",
                    "received_at": datetime.now(timezone.utc),
                }
            },
            session=session,
        )

        if order_update.modified_count != 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Purchase order status changed. Please retry.",
            )

        await create_audit_log(
            action="PURCHASE_ORDER_RECEIVE",
            entity_type="purchase_orders",
            entity_id=str(object_id),
            entity_label=str(purchase_order.get("order_number", object_id)),
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            details={
                "item_count": len(purchase_items),
                "total_units_received": sum(item["quantity"] for item in purchase_items),
            },
            session=session,
        )

        updated = await db.purchase_orders.find_one(
            {"_id": object_id},
            session=session,
        )

        return {
            "id": str(updated["_id"]),
            "supplier_id": str(updated["supplier_id"]),
            "status": updated["status"],
            "notes": updated.get("notes"),
            "is_active": updated.get("is_active", True),
        }

    async with await client.start_session() as session:
        return await session.with_transaction(transaction_work)


async def preview_low_stock_for_po():
    """Identify all active medicines at or below reorder threshold grouped by supplier."""
    low_stock_medicines = await db.medicines.find(
        {
            "is_active": True,
            "$expr": {"$lte": ["$stock", "$reorder_threshold"]},
        }
    ).to_list(length=None)

    if not low_stock_medicines:
        return {
            "total_low_stock_medicines": 0,
            "total_suppliers_affected": 0,
            "suppliers": [],
        }

    supplier_ids = list({m["supplier_id"] for m in low_stock_medicines if "supplier_id" in m})
    suppliers_cursor = db.suppliers.find({"_id": {"$in": supplier_ids}})
    supplier_map = {}
    async for s in suppliers_cursor:
        supplier_map[s["_id"]] = s

    grouped: dict[str, dict] = {}
    for med in low_stock_medicines:
        s_id = med.get("supplier_id")
        s_id_str = str(s_id) if s_id else "unassigned"
        supplier = supplier_map.get(s_id)

        if s_id_str not in grouped:
            grouped[s_id_str] = {
                "supplier_id": s_id_str,
                "supplier_name": supplier.get("name", "Unknown Supplier") if supplier else "Unassigned Supplier",
                "supplier_email": supplier.get("email") if supplier else None,
                "supplier_phone": supplier.get("phone") if supplier else None,
                "items": [],
            }

        curr_stock = int(med.get("stock", 0))
        threshold = int(med.get("reorder_threshold", 10))
        suggested_qty = max((threshold * 2) - curr_stock, 10)
        unit_price = float(med.get("price", 0.0))

        grouped[s_id_str]["items"].append({
            "medicine_id": str(med["_id"]),
            "medicine_name": med.get("name", "Unknown Medicine"),
            "sku": med.get("sku", ""),
            "current_stock": curr_stock,
            "reorder_threshold": threshold,
            "suggested_quantity": suggested_qty,
            "estimated_unit_price": unit_price,
            "estimated_total": round(suggested_qty * unit_price, 2),
        })

    suppliers_list = list(grouped.values())
    return {
        "total_low_stock_medicines": len(low_stock_medicines),
        "total_suppliers_affected": len(suppliers_list),
        "suppliers": suppliers_list,
    }


async def auto_generate_purchase_orders_for_low_stock(
    actor_user_id: str,
    actor_role: str,
):
    """Automatically generate draft Purchase Orders and line items for low-stock medicines."""
    preview = await preview_low_stock_for_po()
    if preview["total_low_stock_medicines"] == 0:
        return {
            "success": True,
            "message": "All medicine stocks are healthy and above their reorder thresholds. No purchase orders needed.",
            "created_orders_count": 0,
            "updated_orders_count": 0,
            "orders": [],
        }

    created_orders = []
    updated_orders = []
    total_items_added = 0

    now_utc = datetime.now(timezone.utc)
    expiry_placeholder = now_utc + timedelta(days=730)

    for supplier_group in preview["suppliers"]:
        s_id_str = supplier_group["supplier_id"]
        if s_id_str == "unassigned":
            continue

        try:
            s_oid = ObjectId(s_id_str)
        except Exception:
            continue

        # Check for open 'draft' purchase order for this supplier
        existing_draft = await db.purchase_orders.find_one(
            {
                "supplier_id": s_oid,
                "status": "draft",
                "is_active": True,
            }
        )

        if existing_draft:
            po_id = existing_draft["_id"]
            updated_orders.append(str(po_id))
        else:
            order_data = {
                "supplier_id": s_oid,
                "status": "draft",
                "notes": f"Automated replenishment generated on {now_utc.strftime('%d %b %Y, %I:%M %p')} for low stock medicines.",
                "is_active": True,
                "created_at": now_utc,
            }
            insert_res = await db.purchase_orders.insert_one(order_data)
            po_id = insert_res.inserted_id
            created_orders.append(str(po_id))

            await create_audit_log(
                action="PURCHASE_ORDER_CREATE",
                entity_type="purchase_orders",
                entity_id=str(po_id),
                entity_label=str(po_id),
                actor_user_id=actor_user_id,
                actor_role=actor_role,
                details={
                    "supplier_name": supplier_group["supplier_name"],
                    "auto_generated": True,
                },
            )

        existing_items = await db.purchase_items.find(
            {"purchase_order_id": po_id}
        ).to_list(length=None)
        existing_med_ids = {str(it["medicine_id"]): it for it in existing_items}

        for item in supplier_group["items"]:
            med_id = item["medicine_id"]
            med_oid = ObjectId(med_id)
            qty = item["suggested_quantity"]
            unit_price = item["estimated_unit_price"]

            if med_id not in existing_med_ids:
                batch_code = f"AUTO-{item['sku'] or 'BATCH'}-{now_utc.strftime('%y%m%d')}"
                item_doc = {
                    "purchase_order_id": po_id,
                    "medicine_id": med_oid,
                    "quantity": qty,
                    "unit_price": unit_price,
                    "total_price": round(qty * unit_price, 2),
                    "batch_number": batch_code,
                    "manufacturing_date": now_utc,
                    "expiry_date": expiry_placeholder,
                }
                await db.purchase_items.insert_one(item_doc)
                total_items_added += 1

    return {
        "success": True,
        "message": (
            f"Generated purchase orders for {preview['total_low_stock_medicines']} low-stock medicine(s). "
            f"Created {len(created_orders)} new order(s), updated {len(updated_orders)} draft order(s), and added {total_items_added} items."
        ),
        "created_orders_count": len(created_orders),
        "updated_orders_count": len(updated_orders),
        "total_items_added": total_items_added,
        "created_order_ids": created_orders,
        "updated_order_ids": updated_orders,
    }

