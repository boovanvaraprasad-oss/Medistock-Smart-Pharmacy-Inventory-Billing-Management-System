from datetime import datetime, timezone

from bson import ObjectId
from fastapi import HTTPException, status

from app.core.database import client, db
from app.core.permissions import OWNER, ROLES
from app.core.security import hash_password


def to_object_id(user_id: str) -> ObjectId:
    # Turns the text ID from the URL into a MongoDB ID,
    # or answers 400 if the text is not a valid ID.
    try:
        return ObjectId(user_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID",
        )


def to_staff_response(user: dict) -> dict:
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "role": user["role"],
        "is_active": user.get("is_active", True),
    }


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
        users.append(to_staff_response(user))

    return users


async def get_staff_user(user_id: str):
    object_id = to_object_id(user_id)

    user = await db.users.find_one(
        {"_id": object_id},
        {"password_hash": 0},
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return to_staff_response(user)


async def update_staff_user(
    user_id: str,
    acting_user_id: str,
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
    object_id = to_object_id(user_id)

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

    changing_role = (
        role is not None and role != user.get("role")
    )
    deactivating = is_active is False

    # Protection 1: nobody can lock themselves out
    if str(user["_id"]) == acting_user_id and (
        changing_role or deactivating
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "You cannot change your own role "
                "or deactivate your own account"
            ),
        )

    # Protection 2: the system must always keep an active owner
    if (
        user.get("role") == OWNER
        and user.get("is_active", True)
        and (changing_role or deactivating)
    ):
        other_active_owners = await db.users.count_documents(
            {
                "role": OWNER,
                "is_active": {"$ne": False},
                "_id": {"$ne": object_id},
            }
        )

        if other_active_owners == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one active owner is required",
            )

    await db.users.update_one(
        {"_id": object_id},
        {"$set": update_data},
    )

    updated_user = await db.users.find_one(
        {"_id": object_id},
        {"password_hash": 0},
    )

    return to_staff_response(updated_user)


async def delete_staff_user(
    user_id: str,
    acting_user_id: str,
    acting_user_role: str,
) -> dict:
    """Permanently delete an inactive non-owner account with no audit history."""

    object_id = to_object_id(user_id)
    acting_object_id = to_object_id(acting_user_id)

    if object_id == acting_object_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot permanently delete your own account",
        )

    async def transaction_work(session):
        user = await db.users.find_one(
            {"_id": object_id},
            session=session,
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if user.get("role") == OWNER:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Owner accounts cannot be permanently deleted",
            )

        if user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Deactivate the user before permanently deleting the account",
            )

        existing_audit = await db.audit_logs.find_one(
            {
                "$or": [
                    {"actor_user_id": object_id},
                    {"target_user_id": object_id},
                ]
            },
            {"_id": 1},
            session=session,
        )

        if existing_audit:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "User is referenced by audit history and cannot be "
                    "permanently deleted; keep the account deactivated"
                ),
            )

        result = await db.users.delete_one(
            {"_id": object_id, "is_active": False},
            session=session,
        )

        if result.deleted_count != 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User changed while deletion was in progress; retry",
            )

        await db.audit_logs.insert_one(
            {
                "action": "USER_DELETE",
                "entity_type": "users",
                "entity_id": str(object_id),
                "entity_label": user.get("email", str(object_id)),
                "actor_user_id": acting_object_id,
                "actor_role": acting_user_role,
                "created_at": datetime.now(timezone.utc),
            },
            session=session,
        )

        return {
            "id": str(object_id),
            "message": "Inactive staff account permanently deleted",
        }

    async with await client.start_session() as session:
        return await session.with_transaction(transaction_work)
