from fastapi import APIRouter, Depends

from app.core.dependencies import require_permission
from app.core.permissions import STOCK_READ, STOCK_WRITE

from app.schemas.stock import (
    AdjustBatchStockRequest,
    StockAdjustmentRequest,
)

from app.services.stock import reduce_stock
from app.services.stock_adjustments import adjust_batch_stock

from app.services.stock_transactions import (
    get_stock_transactions,
)

from app.services.low_stock import (
    get_low_stock_medicines,
)


router = APIRouter(
    prefix="/stock",
    tags=["Stock"],
)


@router.patch("/reduce")
async def reduce_medicine_stock(
    data: StockAdjustmentRequest,
    current_user=Depends(
        require_permission(STOCK_WRITE)
    ),
):
    return await reduce_stock(
        medicine_id=data.medicine_id,
        quantity=data.quantity,
    )


@router.post("/adjustments")
async def adjust_batch_quantity(
    data: AdjustBatchStockRequest,
    current_user=Depends(
        require_permission(STOCK_WRITE)
    ),
):
    return await adjust_batch_stock(
        medicine_id=data.medicine_id,
        batch_id=data.batch_id,
        quantity_change=data.quantity_change,
        reason=data.reason,
    )


@router.get("/transactions")
async def get_transactions(
    medicine_id: str | None = None,
    transaction_type: str | None = None,
    batch_id: str | None = None,
    current_user=Depends(
        require_permission(STOCK_READ)
    ),
):
    return await get_stock_transactions(
        medicine_id=medicine_id,
        transaction_type=transaction_type,
        batch_id=batch_id,
    )


@router.get("/low-stock")
async def get_low_stock(
    current_user=Depends(
        require_permission(STOCK_READ)
    ),
):
    return await get_low_stock_medicines()