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


class BillResponse(BaseModel):
    id: str
    customer_name: str
    customer_phone: str
    total_amount: float
    payment_status: str
    status: str
    is_active: bool
    