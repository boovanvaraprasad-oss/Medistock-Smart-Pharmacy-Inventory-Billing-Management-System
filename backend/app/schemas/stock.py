from pydantic import BaseModel, Field


class StockAdjustmentRequest(BaseModel):
    medicine_id: str
    quantity: int = Field(gt=0)