from pydantic import BaseModel, EmailStr, field_validator

from app.core.password_rules import validate_password_strength
from app.core.permissions import ROLES


class CreateStaffRequest(BaseModel):
    email: EmailStr
    password: str
    role: str

    @field_validator("password")
    @classmethod
    def check_password(cls, value: str) -> str:
        return validate_password_strength(value)


class StaffResponse(BaseModel):
    id: str
    email: EmailStr
    role: str
    is_active: bool


class UpdateStaffRequest(BaseModel):
    role: str | None = None
    is_active: bool | None = None