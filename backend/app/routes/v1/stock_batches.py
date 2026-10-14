from fastapi import APIRouter, Depends, Query

from app.core.dependencies import require_permission
from app.core.permissions import STOCK_READ, STOCK_WRITE

from app.schemas.stock_batch import CreateStockBatchRequest

from app.services.stock_batch_intake import (
    create_stock_batch_and_update_total,
)
from app.services.stock_batches import (
    get_expiring_stock_batches,
    get_stock_batches,
)


router = APIRouter(
    prefix="/stock-batches",
    tags=["Stock Batches"],
)


@router.post("")
async def create_batch(
    data: CreateStockBatchRequest,
    current_user=Depends(
        require_permission(STOCK_WRITE)
    ),
):
    return await create_stock_batch_and_update_total(
        medicine_id=data.medicine_id,
        batch_number=data.batch_number,
        quantity=data.quantity,
        purchase_price=data.purchase_price,
        manufacturing_date=data.manufacturing_date,
        expiry_date=data.expiry_date,
    )


@router.get("")
async def get_batches(
    medicine_id: str | None = None,
    current_user=Depends(
        require_permission(STOCK_READ)
    ),
):
    return await get_stock_batches(
        medicine_id=medicine_id,
    )


@router.get("/expiring")
async def get_expiring_batches(
    days: int = Query(
        default=30,
        ge=0,
        le=365,
        description="Include batches expiring within this many days",
    ),
    medicine_id: str | None = None,
    current_user=Depends(
        require_permission(STOCK_READ)
    ),
):
    return await get_expiring_stock_batches(
        days=days,
        medicine_id=medicine_id,
    )