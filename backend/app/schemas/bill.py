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

    tax_percentage: float = Field(
        default=0.0,
        ge=0,
        le=100,
    )


class BillResponse(BaseModel):
    id: str
    invoice_number: str
    customer_name: str
    customer_phone: str
    subtotal: float
    tax_percentage: float
    tax_amount: float
    total_amount: float
    payment_status: str
    status: str
    is_active: bool
