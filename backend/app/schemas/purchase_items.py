from datetime import date

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

    batch_number: str = Field(
        min_length=1,
        max_length=50
    )

    manufacturing_date: date | None = None

    expiry_date: date


class PurchaseItemResponse(BaseModel):
    id: str
    purchase_order_id: str
    medicine_id: str
    quantity: int
    unit_price: float
    total_price: float

    batch_number: str | None = None

    manufacturing_date: date | None = None

    expiry_date: date | None = None


class UpdatePurchaseItemRequest(BaseModel):
    quantity: int | None = Field(
        default=None,
        gt=0
    )

    unit_price: float | None = Field(
        default=None,
        gt=0
    )

    batch_number: str | None = Field(
        default=None,
        min_length=1,
        max_length=50
    )

    manufacturing_date: date | None = None

    expiry_date: date | None = None