from typing import Literal, Optional

from pydantic import BaseModel, Field


class CreateBillRequest(BaseModel):
    customer_name: str = Field(
        min_length=2,
        max_length=100,
    )

    customer_phone: str = Field(
        min_length=10,
        max_length=15,
    )

    customer_email: Optional[str] = Field(
        default=None,
        max_length=150,
    )

    tax_percentage: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )


class CompleteBillRequest(BaseModel):
    payment_method: Literal["cash", "card", "upi"]
    amount_received: Optional[float] = Field(
        default=None,
        description="Amount received from the customer when completing the bill.",
    )
    tender_amount: Optional[float] = Field(
        default=None,
        description="Alias for amount_received.",
    )
    customer_email: Optional[str] = Field(
        default=None,
        max_length=150,
    )
    send_email_receipt: bool = False


class SendReceiptRequest(BaseModel):
    email: Optional[str] = Field(
        default=None,
        max_length=150,
    )


class BillResponse(BaseModel):
    id: str
    invoice_number: str
    customer_name: str
    customer_phone: str
    customer_email: Optional[str] = None
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
    has_prescription: bool = False
    requires_prescription: bool = False
    receipt_email_sent: bool = False
