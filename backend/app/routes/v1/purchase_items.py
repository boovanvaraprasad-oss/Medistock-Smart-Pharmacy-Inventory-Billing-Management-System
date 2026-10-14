from fastapi import APIRouter, Depends, status

from app.core.dependencies import require_permission
from app.core.permissions import (
    PURCHASE_READ,
    PURCHASE_WRITE,
)
from app.schemas.purchase_items import (
    CreatePurchaseItemRequest,
    PurchaseItemResponse,
    UpdatePurchaseItemRequest,
)
from app.services.purchase_items import (
    create_purchase_item,
    get_all_purchase_items,
    update_purchase_item,
)


router = APIRouter(
    prefix="/purchase-items",
    tags=["Purchase Items"],
)


@router.post(
    "",
    response_model=PurchaseItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_purchase_item(
    data: CreatePurchaseItemRequest,
    current_user=Depends(
        require_permission(PURCHASE_WRITE)
    ),
):
    return await create_purchase_item(
        purchase_order_id=data.purchase_order_id,
        medicine_id=data.medicine_id,
        quantity=data.quantity,
        unit_price=data.unit_price,
        batch_number=data.batch_number,
        manufacturing_date=data.manufacturing_date,
        expiry_date=data.expiry_date,
    )


@router.get(
    "",
    response_model=list[PurchaseItemResponse],
)
async def get_purchase_items(
    current_user=Depends(
        require_permission(PURCHASE_READ)
    ),
):
    return await get_all_purchase_items()


@router.patch(
    "/{purchase_item_id}",
    response_model=PurchaseItemResponse,
)
async def edit_purchase_item(
    purchase_item_id: str,
    data: UpdatePurchaseItemRequest,
    current_user=Depends(
        require_permission(PURCHASE_WRITE)
    ),
):
    return await update_purchase_item(
        purchase_item_id=purchase_item_id,
        quantity=data.quantity,
        unit_price=data.unit_price,
        batch_number=data.batch_number,
        manufacturing_date=data.manufacturing_date,
        expiry_date=data.expiry_date,
    )