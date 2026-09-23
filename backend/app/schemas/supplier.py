from pydantic import BaseModel, EmailStr, Field


class CreateSupplierRequest(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
    )
    phone: str = Field(
        min_length=10,
        max_length=15,
    )
    email: EmailStr | None = None
    address: str | None = Field(
        default=None,
        max_length=250,
    )


class SupplierResponse(BaseModel):
    id: str
    name: str
    phone: str
    email: EmailStr | None
    address: str | None
    is_active: bool


class UpdateSupplierRequest(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )
    phone: str | None = Field(
        default=None,
        min_length=10,
        max_length=15,
    )
    email: EmailStr | None = None
    address: str | None = Field(
        default=None,
        max_length=250,
    )
    is_active: bool | None = None