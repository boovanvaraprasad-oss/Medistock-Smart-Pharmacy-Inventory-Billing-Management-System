from pydantic import BaseModel


class BillItemDetails(BaseModel):
    medicine_id: str
    medicine_name: str
    quantity: int
    unit_price: float
    total_price: float


class BillDetailsResponse(BaseModel):
    id: str
    customer_name: str
    customer_phone: str
    items: list[BillItemDetails]
    total_amount: float
    payment_status: str
    status: str
    is_active: bool