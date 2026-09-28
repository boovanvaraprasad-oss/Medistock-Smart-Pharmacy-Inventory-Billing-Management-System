from pydantic import BaseModel, Field


class CreatePurchaseItemRequest(BaseModel):
    purchase_order_id: str
    medicine_id: str
    quantity: int = Field(
        gt=0
    )
    unit_price: float = Field(
        gt=0
    )


class PurchaseItemResponse(BaseModel):
    id: str
    purchase_order_id: str
    medicine_id: str
    quantity: int
    unit_price: float
    total_price: float

class UpdatePurchaseItemRequest(BaseModel):
    quantity: int | None = Field(
        default=None,
        gt=0
    )
    unit_price: float | None = Field(
        default=None,
        gt=0
    )