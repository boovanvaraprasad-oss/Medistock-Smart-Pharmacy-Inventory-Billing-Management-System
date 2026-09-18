from bson import ObjectId
from fastapi import HTTPException, status

from app.core.database import db
from app.core.permissions import ROLES
from app.core.security import hash_password


async def create_staff_user(
    email: str,
    password: str,
    role: str,
):
    if role not in ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role",
        )

    existing_user = await db.users.find_one(
        {"email": email}
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    user = {
        "email": email,
        "password_hash": hash_password(password),
        "role": role,
        "is_active": True,
    }

    result = await db.users.insert_one(user)

    return {
        "id": str(result.inserted_id),
        "email": email,
        "role": role,
        "is_active": True,
    }
async def get_all_staff_users():
    users = []

    cursor = db.users.find(
        {"role": {"$exists": True}},
        {
            "password_hash": 0,
        }
    )

    async for user in cursor:
        users.append({
            "id": str(user["_id"]),
            "email": user["email"],
            "role": user["role"],
            "is_active": user.get("is_active", True),
        })

    return users

async def update_staff_user(
    user_id: str,
    role: str | None = None,
    is_active: bool | None = None,
):
    # Validate role if a new role was provided
    if role is not None and role not in ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role",
        )

    # Check whether the user ID is valid
    try:
        object_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID",
        )

    # Find the user
    user = await db.users.find_one(
        {"_id": object_id}
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Build only the fields that need to be updated
    update_data = {}

    if role is not None:
        update_data["role"] = role

    if is_active is not None:
        update_data["is_active"] = is_active

    # Nothing was provided to update
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    await db.users.update_one(
        {"_id": object_id},
        {"$set": update_data},
    )

    updated_user = await db.users.find_one(
        {"_id": object_id},
        {"password_hash": 0},
    )

    return {
        "id": str(updated_user["_id"]),
        "email": updated_user["email"],
        "role": updated_user["role"],
        "is_active": updated_user.get("is_active", True),
    }