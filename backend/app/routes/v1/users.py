from fastapi import APIRouter, Depends, status

from app.core.dependencies import require_permission
from app.core.permissions import USER_READ, USER_WRITE
from app.schemas.staff import (
    CreateStaffRequest,
    StaffResponse,
    UpdateStaffRequest,
)
from app.services.users import (
    create_staff_user,
    get_all_staff_users,
    update_staff_user,
)


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post(
    "",
    response_model=StaffResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_staff(
    data: CreateStaffRequest,
    current_user=Depends(require_permission(USER_WRITE)),
):
    return await create_staff_user(
        email=data.email,
        password=data.password,
        role=data.role,
    )


@router.get(
    "",
    response_model=list[StaffResponse],
)
async def get_staff_users(
    current_user=Depends(require_permission(USER_READ)),
):
    return await get_all_staff_users()

@router.patch(
    "/{user_id}",
    response_model=StaffResponse,
)
async def update_staff(
    user_id: str,
    data: UpdateStaffRequest,
    current_user=Depends(require_permission(USER_WRITE)),
):
    return await update_staff_user(
        user_id=user_id,
        role=data.role,
        is_active=data.is_active,
    )