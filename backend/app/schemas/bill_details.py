from datetime import datetime

from pydantic import BaseModel, Field


class BillItemDetails(BaseModel):
    id: str
    medicine_id: str
    medicine_name: str
    quantity: int
    unit_price: float
    total_price: float


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
    items: list[BillItemDetails]
    batch_allocations: list[BillBatchAllocationDetails] = Field(
        default_factory=list
    )
    subtotal: float
    tax_percentage: float
    tax_amount: float
    total_amount: float
    payment_status: str
    status: str
    is_active: bool
