from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import require_permission
from app.core.permissions import (
    MEDICINE_READ,
    MEDICINE_WRITE,
)

from app.schemas.medicine import (
    CreateMedicineRequest,
    MedicineListResponse,
    MedicineResponse,
    UpdateMedicineRequest,
)

from app.services.medicines import (
    create_medicine,
    get_medicine,
    list_medicines,
    update_medicine,
)


router = APIRouter(
    prefix="/medicines",
    tags=["Medicines"],
)


@router.post(
    "",
    response_model=MedicineResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_new_medicine(
    data: CreateMedicineRequest,
    current_user=Depends(
        require_permission(MEDICINE_WRITE)
    ),
):
    return await create_medicine(
        name=data.name,
        sku=data.sku,
        dosage_form=data.dosage_form,
        category_id=data.category_id,
        manufacturer_id=data.manufacturer_id,
        unit_id=data.unit_id,
        supplier_id=data.supplier_id,
        price=data.price,
        reorder_threshold=data.reorder_threshold,
        is_controlled_substance=data.is_controlled_substance,
    )


@router.get(
    "",
    response_model=MedicineListResponse,
)
async def get_medicines(
    search: str | None = Query(
        default=None,
        max_length=100,
        description="Part of the medicine name",
    ),
    category_id: str | None = None,
    is_active: bool | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    current_user=Depends(
        require_permission(MEDICINE_READ)
    ),
):
    return await list_medicines(
        search=search,
        category_id=category_id,
        is_active=is_active,
        page=page,
        limit=limit,
    )


@router.get(
    "/{medicine_id}",
    response_model=MedicineResponse,
)
async def get_one_medicine(
    medicine_id: str,
    current_user=Depends(
        require_permission(MEDICINE_READ)
    ),
):
    return await get_medicine(medicine_id)


@router.patch(
    "/{medicine_id}",
    response_model=MedicineResponse,
)
async def update_existing_medicine(
    medicine_id: str,
    data: UpdateMedicineRequest,
    current_user=Depends(
        require_permission(MEDICINE_WRITE)
    ),
):
    return await update_medicine(
        medicine_id=medicine_id,
        name=data.name,
        sku=data.sku,
        dosage_form=data.dosage_form,
        category_id=data.category_id,
        manufacturer_id=data.manufacturer_id,
        unit_id=data.unit_id,
        supplier_id=data.supplier_id,
        price=data.price,
        reorder_threshold=data.reorder_threshold,
        is_controlled_substance=data.is_controlled_substance,
        is_active=data.is_active,
    )