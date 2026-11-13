from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class InquiryCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    pharmacy: str = Field(..., min_length=2, max_length=150)
    phone: Optional[str] = Field(None, max_length=30)
    subject: str = Field(..., min_length=2, max_length=50)
    message: str = Field(..., min_length=10, max_length=3000)


class InquiryStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(new|in_progress|resolved|archived)$")
    notes: Optional[str] = Field(None, max_length=1000)


class InquiryResponse(BaseModel):
    id: str
    name: str
    email: str
    pharmacy: str
    phone: Optional[str] = None
    subject: str
    message: str
    status: str
    email_sent: bool
    created_at: str
    notes: Optional[str] = None

