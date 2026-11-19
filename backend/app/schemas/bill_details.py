from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BillItemDetails(BaseModel):
    id: str
    medicine_id: str
    medicine_name: str
    quantity: int
    unit_price: float
    total_price: float
    is_controlled_substance: bool = False


class BillPrescriptionDetails(BaseModel):
    file_name: str
    file_path: str
    content_type: str
    file_size: int
    doctor_name: Optional[str] = None
    doctor_reg_no: Optional[str] = None
    patient_notes: Optional[str] = None
    uploaded_at: datetime
    uploaded_by_user_id: Optional[str] = None
    uploaded_by_role: Optional[str] = None


class BillBatchAllocationDetails(BaseModel):
    medicine_id: str
    batch_id: str
    batch_number: str
    expiry_date: datetime
    quantity_sold: int
    quantity_returned: int = 0


class BillDetailsResponse(BaseModel):
    id: str
    invoice_number: str
    customer_name: str
    customer_phone: str
    customer_email: Optional[str] = None
    items: list[BillItemDetails]
    batch_allocations: list[BillBatchAllocationDetails] = Field(
        default_factory=list
    )
    subtotal: float
    tax_percentage: float
    tax_amount: float
    total_amount: float
    payment_status: str
    payment_method: Optional[str] = None
    amount_received: float = 0.0
    change_due: float = 0.0
    status: str
    is_active: bool
    prescription: Optional[BillPrescriptionDetails] = None
    requires_prescription: bool = False
    controlled_medicines: list[str] = Field(default_factory=list)
    receipt_email_sent: bool = False
    receipt_email_sent_at: Optional[datetime] = None