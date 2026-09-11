import asyncio

from app.core.database import db
from app.core.security import hash_password


async def main():
    email = "admin@example.com"
    password = "admin@123"

    existing_user = await db.users.find_one({"email": email})

    if existing_user:
        print("Test user already exists")
        return

    user = {
        "email": email,
        "password_hash": hash_password(password),
        "is_active": True,
        "role": "owner",
    }

    result = await db.users.insert_one(user)

    print("Test user created")
    print("Email:", email)
    print("Password:", password)
    print("ID:", result.inserted_id)


if __name__ == "__main__":
    asyncio.run(main())