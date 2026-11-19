from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.dependencies import require_permission
from app.core.permissions import STOCK_READ
from app.services.notifications import (
    build_notifications,
    set_all_notifications_read,
    set_notification_read,
)


router = APIRouter(prefix="/notifications", tags=["Notifications"])


class NotificationReadRequest(BaseModel):
    notification_id: str = Field(min_length=1, max_length=100)


@router.get("")
async def list_notifications(
    current_user=Depends(require_permission(STOCK_READ)),
):
    return await build_notifications(current_user)


@router.post("/read")
async def mark_notification_read(
    data: NotificationReadRequest,
    current_user=Depends(require_permission(STOCK_READ)),
):
    return await set_notification_read(current_user, data.notification_id)


@router.patch("/{notification_id}/read")
async def mark_notification_read_by_id(
    notification_id: str,
    current_user=Depends(require_permission(STOCK_READ)),
):
    return await set_notification_read(current_user, notification_id)


@router.post("/read-all")
async def mark_all_notifications_read(
    current_user=Depends(require_permission(STOCK_READ)),
):
    return await set_all_notifications_read(current_user)
