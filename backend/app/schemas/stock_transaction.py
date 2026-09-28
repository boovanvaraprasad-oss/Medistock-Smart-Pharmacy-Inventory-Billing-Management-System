from datetime import datetime

from pydantic import BaseModel


class StockTransactionResponse(BaseModel):
    id: str
    medicine_id: str
    medicine_name: str
    transaction_type: str
    quantity: int
    previous_stock: int
    new_stock: int
    reason: str
    created_at: datetime