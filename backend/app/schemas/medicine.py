from pydantic import BaseModel, Field


class CreateMedicineRequest(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=150,
    )
    category_id: str
    manufacturer_id: str
    unit_id: str
    supplier_id: str


class MedicineResponse(BaseModel):
    id: str
    name: str
    category_id: str
    manufacturer_id: str
    unit_id: str
    supplier_id: str
    is_active: bool


class UpdateMedicineRequest(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )
    category_id: str | None = None
    manufacturer_id: str | None = None
    unit_id: str | None = None
    supplier_id: str | None = None
    is_active: bool | None = None