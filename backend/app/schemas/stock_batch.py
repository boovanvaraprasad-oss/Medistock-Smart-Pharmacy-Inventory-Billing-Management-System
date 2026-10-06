from datetime import date

from pydantic import BaseModel, Field


class CreateStockBatchRequest(BaseModel):
    batch_number: str = Field(
        min_length=1,
        max_length=50,
    )

    medicine_id: str

    quantity: int = Field(
        gt=0,
    )

    purchase_price: float = Field(
        gt=0,
    )

    manufacturing_date: date | None = None

    expiry_date: date