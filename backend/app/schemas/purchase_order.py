from pydantic import BaseModel, Field


class CreatePurchaseOrderRequest(BaseModel):
    supplier_id: str
    status: str = Field(
        default="draft",
        pattern="^(draft|ordered|received|cancelled)$"
    )
    notes: str | None = Field(
        default=None,
        max_length=500
    )


class PurchaseOrderResponse(BaseModel):
    id: str
    supplier_id: str
    status: str
    notes: str | None
    is_active: bool


class UpdatePurchaseOrderRequest(BaseModel):
    status: str | None = Field(
        default=None,
        pattern="^(draft|ordered|received|cancelled)$"
    )
    notes: str | None = Field(
        default=None,
        max_length=500
    )
    is_active: bool | None = None