from app.core.database import db


async def create_indexes():
    # Each index is created separately, so if one fails
    # (for example, duplicate emails already exist),
    # the others are still created and the server still starts.

    # 1. Two users can never share the same email,
    #    even if two signups arrive at the same moment.
    try:
        await db.users.create_index(
            "email",
            unique=True,
        )
        print("[indexes] users.email (unique) ready")
    except Exception as error:
        print(f"[indexes] users.email FAILED: {error}")

    # 2. Fast lookup when checking whether a token was revoked.
    try:
        await db.revoked_tokens.create_index("jti")
        print("[indexes] revoked_tokens.jti ready")
    except Exception as error:
        print(f"[indexes] revoked_tokens.jti FAILED: {error}")

    # 3. Self-cleaning: MongoDB deletes each revoked token
    #    automatically once its expires_at time has passed.
    #    (expireAfterSeconds=0 means "delete right at expires_at")
    try:
        await db.revoked_tokens.create_index(
            "expires_at",
            expireAfterSeconds=0,
        )
        print("[indexes] revoked_tokens.expires_at (auto-delete) ready")
    except Exception as error:
        print(f"[indexes] revoked_tokens.expires_at FAILED: {error}")