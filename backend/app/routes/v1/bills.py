import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
import uuid

logger = logging.getLogger(__name__)

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)

from app.core.dependencies import require_permission
from app.core.permissions import (
    BILL_CREATE,
    BILL_COMPLETE,
    BILL_READ,
)
from app.schemas.bill import (
    CreateBillRequest,
    CompleteBillRequest,
    SendReceiptRequest,
    BillResponse,
)
from app.schemas.bill_details import (
    BillDetailsResponse,
)
from app.schemas.bill_item import (
    CreateBillItemRequest,
    BillItemResponse,
    UpdateBillItemRequest,
)
from app.schemas.bill_return import (
    CreateBillReturnRequest,
)
from app.services.bill_items import (
    create_bill_item,
    update_bill_item,
    delete_bill_item,
)
from app.services.bill_returns import (
    return_bill_batch_stock,
)
from app.services.bills import (
    attach_bill_prescription,
    complete_bill,
    create_bill,
    delete_bill_prescription,
    dispatch_bill_receipt,
    get_all_bills,
    get_bill_details,
)
from app.core.database import db


router = APIRouter(
    prefix="/bills",
    tags=["Billing"],
)

ALLOWED_PRESCRIPTION_MIME_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "application/pdf",
}
ALLOWED_PRESCRIPTION_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}
MAX_PRESCRIPTION_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


@router.post(
    "",
    response_model=BillResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_new_bill(
    data: CreateBillRequest,
    current_user=Depends(
        require_permission(BILL_CREATE)
    ),
):
    settings = await db.settings.find_one({"_id": "pharmacy_settings"}) or {}
    tax_percentage = (
        data.tax_percentage
        if data.tax_percentage is not None
        else settings.get("default_tax_percentage", 0.0)
    )
    invoice_prefix = settings.get("invoice_prefix", "INV")

    return await create_bill(
        customer_name=data.customer_name,
        customer_phone=data.customer_phone,
        customer_email=data.customer_email,
        tax_percentage=tax_percentage,
        invoice_prefix=invoice_prefix,
    )


@router.post(
    "/items",
    response_model=BillItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_bill_item(
    data: CreateBillItemRequest,
    current_user=Depends(
        require_permission(BILL_CREATE)
    ),
):
    return await create_bill_item(
        bill_id=data.bill_id,
        medicine_id=data.medicine_id,
        quantity=data.quantity,
    )


@router.patch(
    "/items/{bill_item_id}",
    response_model=BillItemResponse,
)
async def update_existing_bill_item(
    bill_item_id: str,
    data: UpdateBillItemRequest,
    current_user=Depends(
        require_permission(BILL_CREATE)
    ),
):
    return await update_bill_item(
        bill_item_id=bill_item_id,
        quantity=data.quantity,
    )


@router.delete(
    "/items/{bill_item_id}",
)
async def delete_existing_bill_item(
    bill_item_id: str,
    current_user=Depends(
        require_permission(BILL_CREATE)
    ),
):
    return await delete_bill_item(
        bill_item_id=bill_item_id,
    )


@router.patch(
    "/{bill_id}/complete",
    response_model=BillResponse,
)
async def complete_existing_bill(
    bill_id: str,
    data: CompleteBillRequest,
    current_user=Depends(
        require_permission(BILL_COMPLETE)
    ),
):
    received = data.amount_received if data.amount_received is not None else data.tender_amount
    if received is None or received <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="amount_received must be greater than zero",
        )

    res = await complete_bill(
        bill_id=bill_id,
        payment_method=data.payment_method,
        amount_received=received,
        customer_email=data.customer_email,
        actor_user_id=str(current_user["_id"]),
        actor_role=current_user["role"],
    )

    if data.send_email_receipt:
        target_email = (data.customer_email or res.get("customer_email") or "").strip()
        if target_email:
            try:
                await dispatch_bill_receipt(
                    bill_id=bill_id,
                    target_email=target_email,
                    actor_user_id=str(current_user["_id"]),
                    actor_role=current_user["role"],
                )
                res["receipt_email_sent"] = True
            except Exception as exc:
                logger.warning("Could not auto-deliver receipt email: %s", exc)

    return res


@router.post(
    "/{bill_id}/send-receipt",
)
async def send_digital_receipt(
    bill_id: str,
    data: Optional[SendReceiptRequest] = None,
    current_user=Depends(
        require_permission(BILL_READ)
    ),
):
    """Deliver a digital invoice receipt to the customer's email."""
    target_email = data.email.strip() if data and data.email else None
    return await dispatch_bill_receipt(
        bill_id=bill_id,
        target_email=target_email,
        actor_user_id=str(current_user["_id"]),
        actor_role=current_user["role"],
    )


@router.post(
    "/{bill_id}/returns",
    status_code=status.HTTP_201_CREATED,
)
async def create_bill_return(
    bill_id: str,
    data: CreateBillReturnRequest,
    current_user=Depends(
        require_permission(BILL_CREATE)
    ),
):
    return await return_bill_batch_stock(
        bill_id=bill_id,
        batch_id=data.batch_id,
        quantity=data.quantity,
        reason=data.reason,
        actor_user_id=str(current_user["_id"]),
        actor_role=current_user["role"],
    )


@router.get(
    "/{bill_id}",
    response_model=BillDetailsResponse,
)
async def get_existing_bill(
    bill_id: str,
    current_user=Depends(
        require_permission(BILL_READ)
    ),
):
    return await get_bill_details(
        bill_id=bill_id,
    )


@router.post(
    "/{bill_id}/prescription",
    response_model=BillDetailsResponse,
)
async def upload_prescription_file(
    bill_id: str,
    file: UploadFile = File(...),
    doctor_name: Optional[str] = Form(None),
    doctor_reg_no: Optional[str] = Form(None),
    patient_notes: Optional[str] = Form(None),
    current_user=Depends(
        require_permission(BILL_CREATE)
    ),
):
    """Attach a doctor prescription (image or PDF) to a draft bill."""
    filename = file.filename or "prescription"
    ext = Path(filename).suffix.lower()

    if ext not in ALLOWED_PRESCRIPTION_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file extension. Allowed formats: JPG, PNG, WEBP, and PDF.",
        )

    content_type = (file.content_type or "").lower()
    if content_type and content_type not in ALLOWED_PRESCRIPTION_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{content_type}'. Allowed types: JPEG, PNG, WEBP, and PDF.",
        )

    contents = await file.read()
    if len(contents) > MAX_PRESCRIPTION_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prescription file exceeds the 5 MB limit.",
        )
    if len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    safe_name = f"rx_{bill_id}_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:6]}{ext}"
    uploads_dir = Path(__file__).resolve().parents[3] / "uploads" / "prescriptions"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    destination = uploads_dir / safe_name
    destination.write_bytes(contents)

    return await attach_bill_prescription(
        bill_id=bill_id,
        file_name=filename,
        file_path=f"/uploads/prescriptions/{safe_name}",
        content_type=content_type or "application/octet-stream",
        file_size=len(contents),
        doctor_name=doctor_name,
        doctor_reg_no=doctor_reg_no,
        patient_notes=patient_notes,
        actor_user_id=str(current_user["_id"]),
        actor_role=current_user["role"],
    )


@router.delete(
    "/{bill_id}/prescription",
    response_model=BillDetailsResponse,
)
async def remove_prescription_file(
    bill_id: str,
    current_user=Depends(
        require_permission(BILL_CREATE)
    ),
):
    """Remove attached prescription from a draft bill."""
    return await delete_bill_prescription(
        bill_id=bill_id,
        actor_user_id=str(current_user["_id"]),
        actor_role=current_user["role"],
    )


@router.get(
    "",
    response_model=list[BillResponse],
)
async def get_bills(
    current_user=Depends(
        require_permission(BILL_READ)
    ),
):
    return await get_all_bills()
