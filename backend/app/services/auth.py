from datetime import datetime, timezone

from app.core.database import db
from app.core.security import verify_password

async def log_login_attempt(email: str, success: bool):
    await db.login_attempts.insert_one(
        {
            "email":email,
            "success":success,
            "timestamp": datetime.now(timezone.utc),
        }
    )

async def authenticate_user(email: str, password: str):
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

    await log_login_attempt(
        email,
        True,
    )

    return user
