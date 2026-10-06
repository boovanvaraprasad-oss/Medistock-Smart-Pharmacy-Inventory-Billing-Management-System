from fastapi import APIRouter, Depends

from app.core.dependencies import require_permission
from app.core.permissions import STOCK_READ, STOCK_WRITE

from app.schemas.stock import StockAdjustmentRequest

from app.services.stock import reduce_stock

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


@router.get("/transactions")
async def get_transactions(
    medicine_id: str | None = None,
    transaction_type: str | None = None,
    current_user=Depends(
        require_permission(STOCK_READ)
    ),
):
    return await get_stock_transactions(
        medicine_id=medicine_id,
        transaction_type=transaction_type,
    )


@router.get("/low-stock")
async def get_low_stock(
    current_user=Depends(
        require_permission(STOCK_READ)
    ),
):
    return await get_low_stock_medicines()