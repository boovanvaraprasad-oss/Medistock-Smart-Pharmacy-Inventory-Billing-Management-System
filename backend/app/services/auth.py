from app.core.database import db
from app.core.security import verify_password


async def authenticate_user(email: str, password: str):
    user = await db.users.find_one({"email": email})

    if not user:
        return None

    if not verify_password(password, user["password_hash"]):
        return None

    return user