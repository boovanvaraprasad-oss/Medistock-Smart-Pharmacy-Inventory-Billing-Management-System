from datetime import datetime, timedelta, timezone
from typing import List, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.database import db
from app.core.dependencies import get_current_user
from app.core.permissions import COMPLIANCE_OFFICER, OWNER, STORE_MANAGER
from app.schemas.inquiry import InquiryCreate, InquiryResponse, InquiryStatusUpdate
from app.services.mailer import (
    send_inquiry_admin_notification,
    send_inquiry_customer_acknowledgment,
)

router = APIRouter(
    prefix="/inquiries",
    tags=["Inquiries & Contact"],
)

INDIA_TIMEZONE = timezone(timedelta(hours=5, minutes=30))
ALLOWED_STAFF_ROLES = {OWNER, STORE_MANAGER, COMPLIANCE_OFFICER}


@router.post("", status_code=status.HTTP_201_CREATED)
async def submit_inquiry(payload: InquiryCreate):
    """
    Public contact form endpoint:
    1. Validates customer information.
    2. Saves the inquiry to MongoDB.
    3. Dispatches SMTP notifications to staff and the customer.
    """
    now_utc = datetime.now(timezone.utc)
    now_ist = datetime.now(INDIA_TIMEZONE)
    display_time = now_ist.strftime("%d %b %Y, %I:%M %p IST")

    doc = {
        "name": payload.name.strip(),
        "email": str(payload.email).lower().strip(),
        "pharmacy": payload.pharmacy.strip(),
        "phone": payload.phone.strip() if payload.phone else None,
        "subject": payload.subject.strip(),
        "message": payload.message.strip(),
        "status": "new",
        "created_at": now_utc,
        "created_at_display": display_time,
        "email_sent": False,
        "admin_notified": False,
        "customer_notified": False,
    }

    insert_result = await db.inquiries.insert_one(doc)
    doc["_id"] = insert_result.inserted_id

    # Send notifications via SMTP mailer
    admin_notified = await send_inquiry_admin_notification(doc)
    customer_notified = await send_inquiry_customer_acknowledgment(doc)
    email_delivered = admin_notified or customer_notified

    await db.inquiries.update_one(
        {"_id": doc["_id"]},
        {
            "$set": {
                "email_sent": email_delivered,
                "admin_notified": admin_notified,
                "customer_notified": customer_notified,
            }
        },
    )

    return {
        "success": True,
        "message": f"Thank you, {payload.name}! Your message has been received. Our pharmacy support specialist will contact you within 24 hours.",
        "inquiry_id": str(doc["_id"]),
        "email_sent": email_delivered,
    }


@router.get("", response_model=List[InquiryResponse])
async def list_inquiries(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    current_user=Depends(get_current_user),
):
    """Staff endpoint to review pharmacy inquiries."""
    user_id = current_user.get("sub")
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user or user.get("role") not in ALLOWED_STAFF_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view customer inquiries",
        )

    query = {}
    if status_filter:
        query["status"] = status_filter

    cursor = db.inquiries.find(query).sort("created_at", -1).skip(skip).limit(limit)
    items = []
    async for item in cursor:
        created_val = item.get("created_at_display")
        if not created_val:
            raw_date = item.get("created_at")
            created_val = raw_date.isoformat() if hasattr(raw_date, "isoformat") else str(raw_date or "")
        items.append(
            InquiryResponse(
                id=str(item["_id"]),
                name=item.get("name", ""),
                email=item.get("email", ""),
                pharmacy=item.get("pharmacy", ""),
                phone=item.get("phone"),
                subject=item.get("subject", ""),
                message=item.get("message", ""),
                status=item.get("status", "new"),
                email_sent=bool(item.get("email_sent", False)),
                created_at=created_val,
                notes=item.get("notes"),
            )
        )
    return items


@router.patch("/{inquiry_id}/status")
async def update_inquiry_status(
    inquiry_id: str,
    update: InquiryStatusUpdate,
    current_user=Depends(get_current_user),
):
    """Staff endpoint to update an inquiry's progress or resolution."""
    user_id = current_user.get("sub")
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user or user.get("role") not in ALLOWED_STAFF_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update customer inquiries",
        )

    try:
        oid = ObjectId(inquiry_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid inquiry ID format",
        )

    inquiry = await db.inquiries.find_one({"_id": oid})
    if not inquiry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inquiry not found",
        )

    update_fields = {
        "status": update.status,
        "updated_at": datetime.now(timezone.utc),
        "updated_by": user.get("email"),
    }
    if update.notes is not None:
        update_fields["notes"] = update.notes

    await db.inquiries.update_one({"_id": oid}, {"$set": update_fields})
    return {"success": True, "status": update.status}
