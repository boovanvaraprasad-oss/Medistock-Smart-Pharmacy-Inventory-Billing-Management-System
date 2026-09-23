from fastapi import APIRouter, Depends, status

from app.core.dependencies import require_permission
from app.core.permissions import MEDICINE_READ, MEDICINE_WRITE
from app.schemas.supplier import (
    CreateSupplierRequest,
    SupplierResponse,
    UpdateSupplierRequest,
)
from app.services.suppliers import (
    create_supplier,
    get_all_suppliers,
    update_supplier,
)


router = APIRouter(
    prefix="/suppliers",
    tags=["Suppliers"],
)


@router.post(
    "",
    response_model=SupplierResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_supplier(
    data: CreateSupplierRequest,
    current_user=Depends(
        require_permission(MEDICINE_WRITE)
    ),
):
    return await create_supplier(
        name=data.name,
        phone=data.phone,
        email=data.email,
        address=data.address,
    )


@router.get(
    "",
    response_model=list[SupplierResponse],
)
async def get_suppliers(
    current_user=Depends(
        require_permission(MEDICINE_READ)
    ),
):
    return await get_all_suppliers()


@router.patch(
    "/{supplier_id}",
    response_model=SupplierResponse,
)
async def edit_supplier(
    supplier_id: str,
    data: UpdateSupplierRequest,
    current_user=Depends(
        require_permission(MEDICINE_WRITE)
    ),
):
    return await update_supplier(
        supplier_id=supplier_id,
        name=data.name,
        phone=data.phone,
        email=data.email,
        address=data.address,
        is_active=data.is_active,
    )