from datetime import datetime, timezone
import re

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from app.core.database import db
from app.core.dependencies import get_current_user, require_permission
from app.core.permissions import BILL_CREATE


router = APIRouter(prefix="/settings", tags=["Settings"])
SETTINGS_ID = "pharmacy_settings"


class BillingSettingsRequest(BaseModel):
    default_tax_percentage: float = Field(ge=0, le=100)
    invoice_prefix: str = Field(min_length=1, max_length=12)

    @field_validator("invoice_prefix")
    @classmethod
    def normalize_invoice_prefix(cls, value: str) -> str:
        value = value.strip().upper()
        if not re.fullmatch(r"[A-Z0-9-]+", value):
            raise ValueError("Use only letters, numbers, and hyphens for the invoice prefix")
        return value


class BillingSettingsResponse(BaseModel):
    default_tax_percentage: float
    invoice_prefix: str


async def require_owner(current_user=Depends(get_current_user)):
    try:
        user = await db.users.find_one({"_id": ObjectId(current_user["sub"])})
    except (KeyError, TypeError, ValueError):
        user = None

    if not user or user.get("role") != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner can manage billing settings",
        )
    return user


@router.get("", response_model=BillingSettingsResponse)
async def get_billing_settings(
    current_user=Depends(require_permission(BILL_CREATE)),
):
    settings = await db.settings.find_one({"_id": SETTINGS_ID}) or {}
    return BillingSettingsResponse(
        default_tax_percentage=settings.get("default_tax_percentage", 0.0),
        invoice_prefix=settings.get("invoice_prefix", "INV"),
    )


@router.put("", response_model=BillingSettingsResponse)
async def update_billing_settings(
    data: BillingSettingsRequest,
    current_user=Depends(require_owner),
):
    await db.settings.update_one(
        {"_id": SETTINGS_ID},
        {
            "$set": {
                "default_tax_percentage": data.default_tax_percentage,
                "invoice_prefix": data.invoice_prefix,
                "updated_at": datetime.now(timezone.utc),
                "updated_by": str(current_user["_id"]),
            }
        },
        upsert=True,
    )
    return BillingSettingsResponse(**data.model_dump())
