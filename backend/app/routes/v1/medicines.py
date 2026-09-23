from fastapi import APIRouter, Depends, status

from app.core.dependencies import require_permission
from app.core.permissions import MEDICINE_READ, MEDICINE_WRITE
from app.schemas.medicine import (
    CreateMedicineRequest,
    MedicineResponse,
    UpdateMedicineRequest,
)
from app.services.medicines import (
    create_medicine,
    get_all_medicines,
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
async def add_medicine(
    data: CreateMedicineRequest,
    current_user=Depends(
        require_permission(MEDICINE_WRITE)
    ),
):
    return await create_medicine(
        name=data.name,
        category_id=data.category_id,
        manufacturer_id=data.manufacturer_id,
        unit_id=data.unit_id,
        supplier_id=data.supplier_id,
    )


@router.get(
    "",
    response_model=list[MedicineResponse],
)
async def get_medicines(
    current_user=Depends(
        require_permission(MEDICINE_READ)
    ),
):
    return await get_all_medicines()


@router.patch(
    "/{medicine_id}",
    response_model=MedicineResponse,
)
async def edit_medicine(
    medicine_id: str,
    data: UpdateMedicineRequest,
    current_user=Depends(
        require_permission(MEDICINE_WRITE)
    ),
):
    return await update_medicine(
        medicine_id=medicine_id,
        name=data.name,
        category_id=data.category_id,
        manufacturer_id=data.manufacturer_id,
        unit_id=data.unit_id,
        supplier_id=data.supplier_id,
        is_active=data.is_active,
    )