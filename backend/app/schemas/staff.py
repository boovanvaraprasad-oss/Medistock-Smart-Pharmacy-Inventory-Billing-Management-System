from pydantic import BaseModel, EmailStr, Field

from app.core.permissions import ROLES


class CreateStaffRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    role: str


class StaffResponse(BaseModel):
    id: str
    email: EmailStr
    role: str
    is_active: bool


class UpdateStaffRequest(BaseModel):
    role: str | None = None
    is_active: bool | None = None