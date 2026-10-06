from fastapi import APIRouter, Depends

from app.core.dependencies import require_permission
from app.core.permissions import STOCK_READ, STOCK_WRITE

from app.schemas.stock_batch import CreateStockBatchRequest

from app.services.stock_batches import (
    create_stock_batch,
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
    return await create_stock_batch(
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