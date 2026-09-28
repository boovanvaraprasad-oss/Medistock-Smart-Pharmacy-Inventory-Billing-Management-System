from fastapi import APIRouter, Depends, status

from app.core.dependencies import require_permission
from app.core.permissions import STOCK_READ, STOCK_WRITE
from app.schemas.purchase_order import (
    CreatePurchaseOrderRequest,
    PurchaseOrderResponse,
    UpdatePurchaseOrderRequest,
)
from app.services.purchase_orders import (
    create_purchase_order,
    get_all_purchase_orders,
    update_purchase_order,
    receive_purchase_order,
)

router = APIRouter(
    prefix="/purchase-orders",
    tags=["Purchase Orders"],
)


@router.post(
    "",
    response_model=PurchaseOrderResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_purchase_order(
    data: CreatePurchaseOrderRequest,
    current_user=Depends(
        require_permission(STOCK_WRITE)
    ),
):
    return await create_purchase_order(
        supplier_id=data.supplier_id,
        status_value=data.status,
        notes=data.notes,
    )


@router.get(
    "",
    response_model=list[PurchaseOrderResponse],
)
async def get_purchase_orders(
    current_user=Depends(
        require_permission(STOCK_READ)
    ),
):
    return await get_all_purchase_orders()


@router.patch(
    "/{purchase_order_id}",
    response_model=PurchaseOrderResponse,
)
async def edit_purchase_order(
    purchase_order_id: str,
    data: UpdatePurchaseOrderRequest,
    current_user=Depends(
        require_permission(STOCK_WRITE)
    ),
):
    return await update_purchase_order(
        purchase_order_id=purchase_order_id,
        status_value=data.status,
        notes=data.notes,
        is_active=data.is_active,
    )

@router.patch(
    "/{purchase_order_id}/receive",
    response_model=PurchaseOrderResponse,
)
async def receive_order(
    purchase_order_id: str,
    current_user=Depends(
        require_permission(STOCK_WRITE)
    ),
):
    return await receive_purchase_order(
        purchase_order_id=purchase_order_id,
    )