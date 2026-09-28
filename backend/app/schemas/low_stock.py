from pydantic import BaseModel


class LowStockResponse(BaseModel):
    id: str
    name: str
    stock: int
    threshold: int
    