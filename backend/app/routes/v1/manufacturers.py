from fastapi import APIRouter, Depends, status

from app.core.dependencies import require_permission
from app.core.permissions import MEDICINE_READ, MEDICINE_WRITE
from app.schemas.manufacturer import (
    CreateManufacturerRequest,
    ManufacturerResponse,
    UpdateManufacturerRequest,
)
from app.services.manufacturers import (
    create_manufacturer,
    get_all_manufacturers,
    update_manufacturer,
)


router = APIRouter(
    prefix="/manufacturers",
    tags=["Manufacturers"],
)


@router.post(
    "",
    response_model=ManufacturerResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_manufacturer(
    data: CreateManufacturerRequest,
    current_user=Depends(require_permission(MEDICINE_WRITE)),
):
    return await create_manufacturer(
        name=data.name,
    )


@router.get(
    "",
    response_model=list[ManufacturerResponse],
)
async def get_manufacturers(
    current_user=Depends(require_permission(MEDICINE_READ)),
):
    return await get_all_manufacturers()


@router.patch(
    "/{manufacturer_id}",
    response_model=ManufacturerResponse,
)
async def edit_manufacturer(
    manufacturer_id: str,
    data: UpdateManufacturerRequest,
    current_user=Depends(require_permission(MEDICINE_WRITE)),
):
    return await update_manufacturer(
        manufacturer_id=manufacturer_id,
        name=data.name,
        is_active=data.is_active,
    )