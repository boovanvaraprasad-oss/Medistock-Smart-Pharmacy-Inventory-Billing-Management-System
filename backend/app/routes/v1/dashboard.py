from fastapi import APIRouter, Depends

from app.core.dependencies import require_permission
from app.core.permissions import REPORT_VIEW
from app.services.dashboard import get_dashboard_summary


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get("/summary")
async def get_summary(
    current_user=Depends(
        require_permission(REPORT_VIEW)
    ),
):
    return await get_dashboard_summary()
