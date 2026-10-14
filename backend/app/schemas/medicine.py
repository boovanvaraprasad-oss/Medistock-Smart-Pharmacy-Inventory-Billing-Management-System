from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Letters, numbers, hyphen and underscore only, e.g. PARA-650
SKU_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9_-]*$"


class CreateMedicineRequest(BaseModel):
    # Unknown fields (for example "stock") are refused with a clear error
    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        min_length=2,
        max_length=150,
    )

    sku: str = Field(
        min_length=2,
        max_length=30,
        pattern=SKU_PATTERN,
        description="Internal stock code, for example PARA-650",
    )

    dosage_form: str = Field(
        min_length=2,
        max_length=50,
        description="Tablet, Syrup, Injection, and so on",
    )

    category_id: str
    manufacturer_id: str
    unit_id: str
    supplier_id: str

    price: float = Field(
        gt=0,
    )

    reorder_threshold: int = Field(
        default=10,
        ge=0,
        description="Low-stock alert starts at this quantity",
    )

    is_controlled_substance: bool = False

    @field_validator("sku", mode="before")
    @classmethod
    def clean_sku(cls, value):
        # Spaces removed and capitals used, so "para-650 " becomes "PARA-650"
        if isinstance(value, str):
            return value.strip().upper()
        return value

    @field_validator("dosage_form", mode="before")
    @classmethod
    def clean_dosage_form(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value


class MedicineResponse(BaseModel):
    id: str
    name: str
    sku: str | None = None
    dosage_form: str | None = None
    category_id: str
    manufacturer_id: str
    unit_id: str
    supplier_id: str
    stock: int
    price: float
    reorder_threshold: int = 10
    is_controlled_substance: bool = False
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None


class MedicineListResponse(BaseModel):
    items: list[MedicineResponse]
    total: int
    page: int
    limit: int


class UpdateMedicineRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    sku: str | None = Field(
        default=None,
        min_length=2,
        max_length=30,
        pattern=SKU_PATTERN,
    )

    dosage_form: str | None = Field(
        default=None,
        min_length=2,
        max_length=50,
    )

    category_id: str | None = None
    manufacturer_id: str | None = None
    unit_id: str | None = None
    supplier_id: str | None = None

    price: float | None = Field(
        default=None,
        gt=0,
    )

    reorder_threshold: int | None = Field(
        default=None,
        ge=0,
    )

    is_controlled_substance: bool | None = None

    is_active: bool | None = None

    @field_validator("sku", mode="before")
    @classmethod
    def clean_sku(cls, value):
        if isinstance(value, str):
            return value.strip().upper()
        return value

    @field_validator("dosage_form", mode="before")
    @classmethod
    def clean_dosage_form(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value