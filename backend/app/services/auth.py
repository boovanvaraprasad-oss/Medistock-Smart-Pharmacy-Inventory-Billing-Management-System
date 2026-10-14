from datetime import datetime, timezone

from bson import ObjectId
from fastapi import HTTPException, status

from app.core.database import db
from app.core.security import (
    verify_password,
    hash_password,
)


async def log_login_attempt(
    email: str,
    success: bool,
):
    await db.login_attempts.insert_one(
        {
            "email": email,
            "success": success,
            "timestamp": datetime.now(timezone.utc),
        }
    )


async def authenticate_user(
    email: str,
    password: str,
):
    user = await db.users.find_one(
        {"email": email}
    )

    if not user:
        await log_login_attempt(
            email,
            False,
        )
        return None

    if not verify_password(
        password,
        user["password_hash"],
    ):
        await log_login_attempt(
            email,
            False,
        )
        return None

    if not user.get("is_active", True):
        await log_login_attempt(
            email,
            False,
        )
        return None

    await log_login_attempt(
        email,
        True,
    )

    return user


async def register_user(
    email: str,
    password: str,
):
    # Public signup is only allowed for the very first account.
    # After that, the owner creates staff through /users.
    any_user = await db.users.find_one({}, {"_id": 1})

    if any_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Signup is closed. "
                "Ask the owner to create your staff account."
            ),
        )

    user = {
        "email": email,
        "password_hash": hash_password(password),
        "is_active": True,
        "role": "owner",
    }

    result = await db.users.insert_one(user)

    user["_id"] = result.inserted_id

    return user


async def revoke_token(
    jti: str,
    exp: int,
):
    # Saves the token identifier in the revoked_tokens collection.
    # upsert=True means revoking the same token twice never
    # creates a duplicate record.
    await db.revoked_tokens.update_one(
        {"jti": jti},
        {
            "$set": {
                "expires_at": datetime.fromtimestamp(
                    exp,
                    tz=timezone.utc,
                )
            }
        },
        upsert=True,
    )


async def change_user_password(
    user_id: str,
    current_password: str,
    new_password: str,
):
    user = await db.users.find_one(
        {"_id": ObjectId(user_id)}
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # The person must prove they know the current password
    if not verify_password(
        current_password,
        user["password_hash"],
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # The new password must really be new
    if verify_password(
        new_password,
        user["password_hash"],
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from the current one",
        )

    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "password_hash": hash_password(new_password)
            }
        },
    )