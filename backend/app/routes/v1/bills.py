from fastapi import APIRouter, Depends, status

from app.core.dependencies import require_permission
from app.core.permissions import (
    BILL_CREATE,
    BILL_READ,
)

from app.schemas.bill import (
    CreateBillRequest,
    BillResponse,
)

from app.schemas.bill_item import (
    CreateBillItemRequest,
    BillItemResponse,
    UpdateBillItemRequest,
)

from app.schemas.bill_details import (
    BillDetailsResponse,
)

from app.services.bills import (
    create_bill,
    complete_bill,
    get_bill_details,
    get_all_bills,
)

from app.services.bill_items import (
    create_bill_item,
    update_bill_item,
    delete_bill_item,
)


router = APIRouter(
    prefix="/bills",
    tags=["Billing"],
)


@router.post(
    "",
    response_model=BillResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_new_bill(
    data: CreateBillRequest,
    current_user=Depends(
        require_permission(BILL_CREATE)
    ),
):
    return await create_bill(
        customer_name=data.customer_name,
        customer_phone=data.customer_phone,
    )


@router.post(
    "/items",
    response_model=BillItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_bill_item(
    data: CreateBillItemRequest,
    current_user=Depends(
        require_permission(BILL_CREATE)
    ),
):
    return await create_bill_item(
        bill_id=data.bill_id,
        medicine_id=data.medicine_id,
        quantity=data.quantity,
    )


@router.patch(
    "/items/{bill_item_id}",
    response_model=BillItemResponse,
)
async def update_existing_bill_item(
    bill_item_id: str,
    data: UpdateBillItemRequest,
    current_user=Depends(
        require_permission(BILL_CREATE)
    ),
):
    return await update_bill_item(
        bill_item_id=bill_item_id,
        quantity=data.quantity,
    )


@router.delete(
    "/items/{bill_item_id}",
)
async def delete_existing_bill_item(
    bill_item_id: str,
    current_user=Depends(
        require_permission(BILL_CREATE)
    ),
):
    return await delete_bill_item(
        bill_item_id=bill_item_id,
    )


@router.patch(
    "/{bill_id}/complete",
    response_model=BillResponse,
)
async def complete_existing_bill(
    bill_id: str,
    current_user=Depends(
        require_permission(BILL_CREATE)
    ),
):
    return await complete_bill(
        bill_id=bill_id,
    )


@router.get(
    "/{bill_id}",
    response_model=BillDetailsResponse,
)
async def get_existing_bill(
    bill_id: str,
    current_user=Depends(
        require_permission(BILL_READ)
    ),
):
    return await get_bill_details(
        bill_id=bill_id,
    )


@router.get(
    "",
    response_model=list[BillResponse],
)
async def get_bills(
    current_user=Depends(
        require_permission(BILL_READ)
    ),
):
    return await get_all_bills()