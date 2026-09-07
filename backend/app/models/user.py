from pydantic import BaseModel, EmailStr

class User(BaseModel):
    id: str | none =None
    email: EmailStr
    password_hash: str
    is_ active: bool = True
    