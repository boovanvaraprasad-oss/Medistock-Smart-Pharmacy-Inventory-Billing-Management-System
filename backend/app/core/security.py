import uuid

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import (
    JWT_SECRET_KEY,
    JWT_ACCESS_EXPIRY_MIN,
)


# ---------------------------------------------------------
# Password Hashing
# ---------------------------------------------------------

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(
    password: str,
    password_hash: str,
) -> bool:
    return pwd_context.verify(
        password,
        password_hash,
    )


# ---------------------------------------------------------
# JWT Configuration
# ---------------------------------------------------------

SECRET_KEY = JWT_SECRET_KEY
ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = JWT_ACCESS_EXPIRY_MIN
REFRESH_TOKEN_EXPIRE_DAYS = 3


# ---------------------------------------------------------
# Create Access Token
# ---------------------------------------------------------

def create_access_token(subject: str) -> str:
    expire = datetime.now(
        timezone.utc
    ) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": subject,
        "type": "access",
        "jti": str(uuid.uuid4()),
        "exp": expire,
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


# ---------------------------------------------------------
# Create Refresh Token
# ---------------------------------------------------------

def create_refresh_token(subject: str) -> str:
    expire = datetime.now(
        timezone.utc
    ) + timedelta(
        days=REFRESH_TOKEN_EXPIRE_DAYS
    )

    payload = {
        "sub": subject,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
        "exp": expire,
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


# ---------------------------------------------------------
# Decode and Verify Access Token
# ---------------------------------------------------------

def decode_access_token(token: str):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        # Make sure this is an access token

        if payload.get("type") != "access":
            return None

        return payload

    except JWTError:
        return None


# ---------------------------------------------------------
# Decode and Verify Refresh Token
# ---------------------------------------------------------

def decode_refresh_token(token: str):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        # Make sure this is a refresh token

        if payload.get("type") != "refresh":
            return None

        return payload

    except JWTError:
        return None