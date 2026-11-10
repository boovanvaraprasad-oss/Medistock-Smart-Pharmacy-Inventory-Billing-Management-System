from datetime import datetime, time, timedelta, timezone

from bson import ObjectId
from fastapi import HTTPException, status
from pymongo import ReturnDocument

from app.core.database import client, db
from app.services.audit_log import create_audit_log
from app.services.stock_transactions import create_stock_transaction


# India Standard Time (UTC+05:30)
INDIA_TIMEZONE = timezone(timedelta(hours=5, minutes=30))


async def generate_invoice_number(prefix: str = "INV") -> str:
    """Generate a unique sequential invoice number."""
    counter = await db.counters.find_one_and_update(
        {"_id": "invoice_number"},
        {"$inc": {"sequence": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return f"{prefix}-{counter['sequence']:06d}"


async def create_bill(
    customer_name: str,
    customer_phone: str,
    tax_percentage: float = 0.0,
    invoice_prefix: str = "INV",
):
    """Create a new draft bill."""
    if not 0 <= tax_percentage <= 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tax percentage must be between 0 and 100",
        )

    invoice_number = await generate_invoice_number(invoice_prefix)

    bill = {
        "invoice_number": invoice_number,
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "subtotal": 0.0,
        "tax_percentage": tax_percentage,
        "tax_amount": 0.0,
        "total_amount": 0.0,
        "payment_status": "pending",
        "payment_method": None,
        "amount_received": 0.0,
        "change_due": 0.0,
        "status": "draft",
        "is_active": True,
    }

    result = await db.bills.insert_one(bill)

    return {
        "id": str(result.inserted_id),
        **bill,
    }


async def deduct_stock_fefo(
    medicine_id: ObjectId,
    quantity: int,
    session=None,
):
    """Deduct stock from earliest-expiring eligible batches."""
    if quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity must be greater than zero",
        )

    today_start = datetime.combine(
        datetime.now(INDIA_TIMEZONE).date(),
        time.min,
    )
    remaining = quantity
    batches_used = []

    cursor = (
        db.stock_batches.find(
            {
                "medicine_id": medicine_id,
                "is_active": True,
                "quantity": {"$gt": 0},
                "expiry_date": {"$gte": today_start},
            },
            session=session,
        )
        .sort("expiry_date", 1)
    )

    batches = await cursor.to_list(length=None)

    if sum(batch.get("quantity", 0) for batch in batches) < quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient non-expired batch stock",
        )

    for batch in batches:
        if remaining <= 0:
            break

        available = batch.get("quantity", 0)
        deduct = min(available, remaining)
        new_quantity = available - deduct

        result = await db.stock_batches.update_one(
            {
                "_id": batch["_id"],
                "quantity": available,
                "is_active": True,
            },
            {
                "$set": {
                    "quantity": new_quantity,
                    "is_active": new_quantity > 0,
                }
            },
            session=session,
        )

        if result.modified_count != 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Batch stock changed. Please try again.",
            )

        batches_used.append(
            {
                "batch_id": str(batch["_id"]),
                "batch_number": batch.get("batch_number", ""),
                "expiry_date": batch["expiry_date"],
                "quantity_deducted": deduct,
            }
        )

        remaining -= deduct

    if remaining:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to deduct the required batch stock",
        )

    return batches_used


async def calculate_bill_totals(
    bill_object_id: ObjectId,
    session=None,
):
    """Calculate and save bill subtotal, tax, and total."""
    cursor = db.bill_items.find(
        {"bill_id": bill_object_id},
        session=session,
    )

    subtotal = 0.0
    async for item in cursor:
        subtotal += float(item.get("total_price", 0))

    bill = await db.bills.find_one(
        {
            "_id": bill_object_id,
            "is_active": True,
        },
        session=session,
    )

    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bill not found or inactive",
        )

    tax_percentage = float(bill.get("tax_percentage", 0.0))
    tax_amount = round(subtotal * tax_percentage / 100, 2)
    total_amount = round(subtotal + tax_amount, 2)

    await db.bills.update_one(
        {"_id": bill_object_id},
        {
            "$set": {
                "subtotal": subtotal,
                "tax_percentage": tax_percentage,
                "tax_amount": tax_amount,
                "total_amount": total_amount,
            }
        },
        session=session,
    )

    return {
        "subtotal": subtotal,
        "tax_percentage": tax_percentage,
        "tax_amount": tax_amount,
        "total_amount": total_amount,
    }


async def complete_bill(
    bill_id: str,
    payment_method: str,
    amount_received: float,
    actor_user_id: str,
    actor_role: str,
):
    """
    Complete a draft bill atomically.

    Payment validation, batch deductions, medicine stock changes,
    stock transaction records, and bill completion commit together.
    """
    try:
        bill_object_id = ObjectId(bill_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid bill ID",
        )

    payment_method = payment_method.lower().strip()
    if payment_method not in {"cash", "card", "upi"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment method must be cash, card, or upi",
        )

    try:
        received = round(float(amount_received), 2)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount received must be a valid number",
        )

    if received <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount received must be greater than zero",
        )

    async def transaction_work(session):
        bill = await db.bills.find_one(
            {
                "_id": bill_object_id,
                "is_active": True,
                "status": "draft",
            },
            session=session,
        )

        if not bill:
            existing = await db.bills.find_one(
                {"_id": bill_object_id},
                session=session,
            )

            if not existing or not existing.get("is_active", False):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Bill not found or inactive",
                )

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Bill is not a draft or has already been completed",
            )

        items_cursor = db.bill_items.find(
            {"bill_id": bill_object_id},
            session=session,
        )
        items = await items_cursor.to_list(length=None)

        if not items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bill has no items",
            )

        # Aggregate duplicate lines for the same medicine.
        quantities = {}
        for item in items:
            quantity = item.get("quantity", 0)

            if (
                not isinstance(quantity, int)
                or isinstance(quantity, bool)
                or quantity <= 0
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Bill item quantities must be positive integers",
                )

            medicine_id = item["medicine_id"]
            key = str(medicine_id)

            if key not in quantities:
                quantities[key] = {
                    "medicine_id": medicine_id,
                    "quantity": 0,
                }

            quantities[key]["quantity"] += quantity

        totals = await calculate_bill_totals(
            bill_object_id,
            session=session,
        )

        total_amount = round(totals["total_amount"], 2)

        if received < total_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Amount received (₹{received:.2f}) is less than "
                    f"the bill total (₹{total_amount:.2f})"
                ),
            )

        if payment_method in {"card", "upi"} and received != total_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"For {payment_method.upper()} payments, the amount "
                    f"received must equal the bill total "
                    f"(₹{total_amount:.2f})"
                ),
            )

        change_due = round(received - total_amount, 2)

        today_start = datetime.combine(
            datetime.now(INDIA_TIMEZONE).date(),
            time.min,
        )

        bill_batch_allocations = []

        for entry in quantities.values():
            medicine_id = entry["medicine_id"]
            quantity = entry["quantity"]

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
                    detail="A medicine on this bill was not found or is inactive",
                )

            previous_stock = medicine.get("stock", 0)

            if quantity > previous_stock:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock for {medicine['name']}",
                )

            batch_cursor = db.stock_batches.find(
                {
                    "medicine_id": medicine_id,
                    "is_active": True,
                    "quantity": {"$gt": 0},
                    "expiry_date": {"$gte": today_start},
                },
                session=session,
            )

            batch_stock = 0
            async for batch in batch_cursor:
                batch_stock += batch.get("quantity", 0)

            if quantity > batch_stock:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Insufficient non-expired batch stock "
                        f"for {medicine['name']}"
                    ),
                )

            batches_used = await deduct_stock_fefo(
                medicine_id=medicine_id,
                quantity=quantity,
                session=session,
            )

            for batch in batches_used:
                bill_batch_allocations.append(
                    {
                        "medicine_id": str(medicine_id),
                        "batch_id": batch["batch_id"],
                        "batch_number": batch["batch_number"],
                        "expiry_date": batch["expiry_date"],
                        "quantity_sold": batch["quantity_deducted"],
                        "quantity_returned": 0,
                    }
                )

            new_stock = previous_stock - quantity

            medicine_update = await db.medicines.update_one(
                {
                    "_id": medicine_id,
                    "stock": previous_stock,
                    "is_active": True,
                },
                {"$set": {"stock": new_stock}},
                session=session,
            )

            if medicine_update.modified_count != 1:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "Medicine stock changed while completing "
                        "the bill. Please try again."
                    ),
                )

            await create_stock_transaction(
                medicine_id=str(medicine_id),
                transaction_type="STOCK_OUT",
                quantity=quantity,
                previous_stock=previous_stock,
                new_stock=new_stock,
                reason="Bill completed",
                session=session,
            )

        bill_update = await db.bills.update_one(
            {
                "_id": bill_object_id,
                "is_active": True,
                "status": "draft",
            },
            {
                "$set": {
                    "status": "completed",
                    "payment_status": "paid",
                    "payment_method": payment_method,
                    "amount_received": received,
                    "change_due": change_due,
                    "completed_at": datetime.now(timezone.utc),
                    "batch_allocations": bill_batch_allocations,
                }
            },
            session=session,
        )

        if bill_update.modified_count != 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Bill status changed. Please try again.",
            )

        await create_audit_log(
            action="BILL_COMPLETE",
            entity_type="bills",
            entity_id=str(bill_object_id),
            entity_label=bill.get("invoice_number", str(bill_object_id)),
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            details={
                "total_amount": total_amount,
                "payment_method": payment_method,
            },
            session=session,
        )

        updated_bill = await db.bills.find_one(
            {"_id": bill_object_id},
            session=session,
        )

        return {
            "id": str(updated_bill["_id"]),
            "invoice_number": updated_bill.get("invoice_number", ""),
            "customer_name": updated_bill["customer_name"],
            "customer_phone": updated_bill["customer_phone"],
            "subtotal": totals["subtotal"],
            "tax_percentage": totals["tax_percentage"],
            "tax_amount": totals["tax_amount"],
            "total_amount": totals["total_amount"],
            "payment_status": updated_bill["payment_status"],
            "payment_method": updated_bill["payment_method"],
            "amount_received": updated_bill["amount_received"],
            "change_due": updated_bill["change_due"],
            "status": updated_bill["status"],
            "is_active": updated_bill.get("is_active", True),
        }

    async with await client.start_session() as session:
        return await session.with_transaction(transaction_work)


async def get_bill_details(bill_id: str):
    """Get one bill with its medicine details."""
    try:
        bill_object_id = ObjectId(bill_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid bill ID",
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

    items = []
    cursor = db.bill_items.find({"bill_id": bill_object_id})

    async for item in cursor:
        medicine = await db.medicines.find_one(
            {"_id": item["medicine_id"]}
        )

        items.append(
            {
                "id": str(item["_id"]),
                "medicine_id": str(item["medicine_id"]),
                "medicine_name": (
                    medicine["name"] if medicine else "Unknown Medicine"
                ),
                "quantity": item["quantity"],
                "unit_price": item["unit_price"],
                "total_price": item["total_price"],
            }
        )

    totals = await calculate_bill_totals(bill_object_id)

    return {
        "id": str(bill["_id"]),
        "invoice_number": bill.get("invoice_number", ""),
        "customer_name": bill["customer_name"],
        "customer_phone": bill["customer_phone"],
        "items": items,
        "batch_allocations": bill.get("batch_allocations", []),
        "subtotal": totals["subtotal"],
        "tax_percentage": totals["tax_percentage"],
        "tax_amount": totals["tax_amount"],
        "total_amount": totals["total_amount"],
        "payment_status": bill.get("payment_status", "pending"),
        "payment_method": bill.get("payment_method"),
        "amount_received": bill.get("amount_received", 0.0),
        "change_due": bill.get("change_due", 0.0),
        "status": bill.get("status", "draft"),
        "is_active": bill.get("is_active", True),
    }


async def get_all_bills():
    """Return bills in newest-first order."""
    bills = []
    cursor = db.bills.find({}).sort("_id", -1)

    async for bill in cursor:
        bill_id = bill["_id"]
        totals = await calculate_bill_totals(bill_id)

        bills.append(
            {
                "id": str(bill_id),
                "invoice_number": bill.get("invoice_number", ""),
                "customer_name": bill["customer_name"],
                "customer_phone": bill["customer_phone"],
                "subtotal": totals["subtotal"],
                "tax_percentage": totals["tax_percentage"],
                "tax_amount": totals["tax_amount"],
                "total_amount": totals["total_amount"],
                "payment_status": bill.get("payment_status", "pending"),
                "payment_method": bill.get("payment_method"),
                "amount_received": bill.get("amount_received", 0.0),
                "change_due": bill.get("change_due", 0.0),
                "status": bill.get("status", "draft"),
                "is_active": bill.get("is_active", True),
            }
        )

    return bills
