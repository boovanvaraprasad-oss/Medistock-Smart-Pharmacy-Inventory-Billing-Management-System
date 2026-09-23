from fastapi import APIRouter, Depends, status

from app.core.dependencies import require_permission
from app.core.permissions import MEDICINE_READ, MEDICINE_WRITE
from app.schemas.unit import (
    CreateUnitRequest,
    UnitResponse,
    UpdateUnitRequest,
)
from app.services.units import (
    create_unit,
    get_all_units,
    update_unit,
)


router = APIRouter(
    prefix="/units",
    tags=["Units"],
)


@router.post(
    "",
    response_model=UnitResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_unit(
    data: CreateUnitRequest,
    current_user=Depends(
        require_permission(MEDICINE_WRITE)
    ),
):
    return await create_unit(
        name=data.name,
    )


@router.get(
    "",
    response_model=list[UnitResponse],
)
async def get_units(
    current_user=Depends(
        require_permission(MEDICINE_READ)
    ),
):
    return await get_all_units()


@router.patch(
    "/{unit_id}",
    response_model=UnitResponse,
)
async def edit_unit(
    unit_id: str,
    data: UpdateUnitRequest,
    current_user=Depends(
        require_permission(MEDICINE_WRITE)
    ),
):
    return await update_unit(
        unit_id=unit_id,
        name=data.name,
        is_active=data.is_active,
    )