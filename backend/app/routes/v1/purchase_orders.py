from fastapi import APIRouter, Depends, status

from app.core.dependencies import require_permission
from app.core.permissions import PURCHASE_READ, PURCHASE_WRITE
from app.schemas.purchase_order import (
    CreatePurchaseOrderRequest,
    PurchaseOrderResponse,
    UpdatePurchaseOrderRequest,
)
from app.services.purchase_orders import (
    auto_generate_purchase_orders_for_low_stock,
    create_purchase_order,
    get_all_purchase_orders,
    preview_low_stock_for_po,
    receive_purchase_order,
    update_purchase_order,
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
        require_permission(PURCHASE_WRITE)
    ),
):
    return await create_purchase_order(
        supplier_id=data.supplier_id,
        status_value=data.status,
        notes=data.notes,
        actor_user_id=str(current_user["_id"]),
        actor_role=current_user["role"],
    )


@router.get(
    "",
    response_model=list[PurchaseOrderResponse],
)
async def get_purchase_orders(
    current_user=Depends(
        require_permission(PURCHASE_READ)
    ),
):
    return await get_all_purchase_orders()


@router.get(
    "/low-stock-preview",
)
async def preview_low_stock(
    current_user=Depends(
        require_permission(PURCHASE_READ)
    ),
):
    """Preview low-stock medicines that require purchase orders grouped by supplier."""
    return await preview_low_stock_for_po()


@router.post(
    "/generate-from-low-stock",
    status_code=status.HTTP_200_OK,
)
async def generate_po_from_low_stock(
    current_user=Depends(
        require_permission(PURCHASE_WRITE)
    ),
):
    """Automatically create draft purchase orders and line items for low-stock medicines."""
    return await auto_generate_purchase_orders_for_low_stock(
        actor_user_id=str(current_user["_id"]),
        actor_role=current_user["role"],
    )


@router.patch(
    "/{purchase_order_id}",
    response_model=PurchaseOrderResponse,
)
async def edit_purchase_order(
    purchase_order_id: str,
    data: UpdatePurchaseOrderRequest,
    current_user=Depends(
        require_permission(PURCHASE_WRITE)
    ),
):
    return await update_purchase_order(
        purchase_order_id=purchase_order_id,
        status_value=data.status,
        notes=data.notes,
        is_active=data.is_active,
        actor_user_id=str(current_user["_id"]),
        actor_role=current_user["role"],
    )

@router.patch(
    "/{purchase_order_id}/receive",
    response_model=PurchaseOrderResponse,
)
async def receive_order(
    purchase_order_id: str,
    current_user=Depends(
        require_permission(PURCHASE_WRITE)
    ),
):
    return await receive_purchase_order(
        purchase_order_id=purchase_order_id,
        actor_user_id=str(current_user["_id"]),
        actor_role=current_user["role"],
    )
