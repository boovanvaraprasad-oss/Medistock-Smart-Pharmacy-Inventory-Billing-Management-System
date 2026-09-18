from fastapi import APIRouter, Depends, status

from app.core.dependencies import require_permission
from app.core.permissions import MEDICINE_WRITE, MEDICINE_READ
from app.schemas.category import (
    CreateCategoryRequest,
    CategoryResponse,
    UpdateCategoryRequest,
)
from app.services.categories import (
    create_category,
    get_all_categories,
    update_category,
)


router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
)


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_category(
    data: CreateCategoryRequest,
    current_user=Depends(require_permission(MEDICINE_WRITE)),
):
    return await create_category(
        name=data.name,
    )

@router.get(
    "",
    response_model=list[CategoryResponse],
)
async def get_categories(
    current_user=Depends(require_permission(MEDICINE_READ)),
):
    return await get_all_categories()

@router.patch(
    "/{category_id}",
    response_model=CategoryResponse,
)
async def edit_category(
    category_id: str,
    data: UpdateCategoryRequest,
    current_user=Depends(require_permission(MEDICINE_WRITE)),
):
    return await update_category(
        category_id=category_id,
        name=data.name,
        is_active=data.is_active,
    )