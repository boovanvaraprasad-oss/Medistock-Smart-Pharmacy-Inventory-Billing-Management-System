from bson import ObjectId
from fastapi import HTTPException, status

from app.core.database import client, db
from app.services.stock_batches import create_stock_batch
from app.services.stock_transactions import (
    create_stock_transaction,
)


async def create_purchase_order(
    supplier_id: str,
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
    }

    result = await db.purchase_orders.insert_one(
        purchase_order
    )

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

    await db.purchase_orders.update_one(
        {"_id": object_id},
        {"$set": update_data},
    )

    updated = await db.purchase_orders.find_one(
        {"_id": object_id}
    )

    return {
        "id": str(updated["_id"]),
        "supplier_id": str(updated["supplier_id"]),
        "status": updated["status"],
        "notes": updated.get("notes"),
        "is_active": updated.get("is_active", True),
    }


async def receive_purchase_order(
    purchase_order_id: str,
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
            {"$set": {"status": "received"}},
            session=session,
        )

        if order_update.modified_count != 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Purchase order status changed. Please retry.",
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