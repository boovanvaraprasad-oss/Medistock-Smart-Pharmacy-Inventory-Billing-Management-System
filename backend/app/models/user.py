from pydantic import BaseModel, EmailStr

from app.core.permissions import ROLES


class User(BaseModel):
    id: str | None = None
    email: EmailStr
    password_hash: str
    is_active: bool = True
    role: str = ROLES[0]