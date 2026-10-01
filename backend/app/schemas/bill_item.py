from pydantic import BaseModel, Field


class CreateBillItemRequest(BaseModel):
    bill_id: str
    medicine_id: str
    quantity: int = Field(
        gt=0
    )


class BillItemResponse(BaseModel):
    id: str
    bill_id: str
    medicine_id: str
    medicine_name: str
    quantity: int
    unit_price: float
    total_price: float


class UpdateBillItemRequest(BaseModel):
    quantity: int = Field(
        gt=0
    )