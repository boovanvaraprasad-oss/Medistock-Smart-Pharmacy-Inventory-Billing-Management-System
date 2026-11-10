from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.dependencies import require_permission
from app.core.permissions import REPORT_VIEW
from app.services.dashboard import get_dashboard_summary


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get("/summary")
async def get_summary(
    selected_date: date | None = Query(default=None, alias="date"),
    selected_month: str | None = Query(default=None, alias="month"),
    current_user=Depends(
        require_permission(REPORT_VIEW)
    ),
):
    if selected_month:
        try:
            datetime.strptime(selected_month, "%Y-%m")
        except ValueError as error:
            raise HTTPException(status_code=422, detail="Month must use YYYY-MM format.") from error
    return await get_dashboard_summary(selected_date, selected_month)
