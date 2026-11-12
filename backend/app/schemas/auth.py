from pydantic import BaseModel, EmailStr, field_validator

from app.core.password_rules import validate_password_strength
from app.core.email_rules import validate_medistock_email


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def check_email_domain(cls, value: EmailStr) -> EmailStr:
        return validate_medistock_email(value)

    @field_validator("password")
    @classmethod
    def check_password(cls, value: str) -> str:
        return validate_password_strength(value)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str | None = None
    access_token: str | None = None


class MeResponse(BaseModel):
    id: str
    email: EmailStr
    role: str
    is_active: bool
    permissions: list[str]
    full_name: str = ""
    phone: str = ""


class UpdateProfileRequest(BaseModel):
    full_name: str = ""
    phone: str = ""

    @field_validator("full_name")
    @classmethod
    def clean_full_name(cls, value: str) -> str:
        value = value.strip()
        if len(value) > 120:
            raise ValueError("Name must be 120 characters or fewer")
        return value

    @field_validator("phone")
    @classmethod
    def clean_phone(cls, value: str) -> str:
        value = value.strip()
        if len(value) > 30:
            raise ValueError("Phone must be 30 characters or fewer")
        return value


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def check_new_password(cls, value: str) -> str:
        return validate_password_strength(value)
