from datetime import datetime, timezone

from app.core.database import db
from app.core.security import verify_password, hash_password
from app.core.permissions import ROLES


async def log_login_attempt(email: str, success: bool):
    await db.login_attempts.insert_one(
        {
            "email": email,
            "success": success,
            "timestamp": datetime.now(timezone.utc),
        }
    )


async def authenticate_user(email: str, password: str):
    user = await db.users.find_one({"email": email})

    if not user:
        await log_login_attempt(email, False)
        return None

    if not verify_password(password, user["password_hash"]):
        await log_login_attempt(email, False)
        return None

    if not user.get("is_active", True):
        await log_login_attempt(email, False)
        return None

    await log_login_attempt(email, True)
    return user

async def register_user(email: str, password: str):
    existing_user = await db.users.find_one({"email": email})

    if existing_user:
        return None

    user = {
        "email": email,
        "password_hash": hash_password(password),
        "is_active": True,
        "role": "owner",
    }

    result = await db.users.insert_one(user)
    user["_id"] = result.inserted_id
    return user


async def create_staff_user(email: str, password: str, role: str):
    
    if role not in ROLES:
        return None  # invalid role

    existing_user = await db.users.find_one({"email": email})

    if existing_user:
        return None  # email already taken

    user = {
        "email": email,
        "password_hash": hash_password(password),
        "is_active": True,
        "role": role,
    }

    result = await db.users.insert_one(user)
    user["_id"] = result.inserted_id
    return user