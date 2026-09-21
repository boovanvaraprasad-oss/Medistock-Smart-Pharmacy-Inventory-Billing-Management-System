from bson import ObjectId

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    RefreshTokenRequest,
    LogoutRequest,
)
from app.services.auth import authenticate_user, register_user
from app.core.database import db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
)
from app.core.dependencies import (
    get_current_user,
    require_permission,
)
from app.core.permissions import MEDICINE_WRITE


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

bearer_scheme = HTTPBearer()


# Login

@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(data: LoginRequest):
    user = await authenticate_user(
        data.email,
        data.password,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(
        str(user["_id"])
    )

    refresh_token = create_refresh_token(
        str(user["_id"])
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


# Refresh access token

@router.post(
    "/refresh",
    response_model=TokenResponse,
)
async def refresh_access_token(
    data: RefreshTokenRequest,
):
    payload = decode_refresh_token(
        data.refresh_token
    )

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Check refresh token identifier

    refresh_jti = payload.get("jti")

    if not refresh_jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has no identifier",
        )

    # Check whether refresh token was revoked

    revoked_token = await db.revoked_tokens.find_one(
        {"jti": refresh_jti}
    )

    if revoked_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
        )

    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Check whether the user still exists

    try:
        user = await db.users.find_one(
            {"_id": ObjectId(user_id)}
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID",
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Check whether the user is still active

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
        )

    # Create a new access token

    new_access_token = create_access_token(
        user_id
    )

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=data.refresh_token,
        token_type="bearer",
    )


# Sign up

@router.post("/register")
async def register(data: RegisterRequest):
    user = await register_user(
        data.email,
        data.password,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    return {
        "message": "User registered successfully",
        "email": user["email"],
    }


# Protected user endpoint

@router.get("/me")
async def get_me(
    current_user=Depends(get_current_user),
):
    return {
        "message": "You are authenticated",
        "user": current_user,
    }


# RBAC permission test

@router.get("/test-medicine-write")
async def test_medicine_write(
    current_user=Depends(
        require_permission(MEDICINE_WRITE)
    ),
):
    return {
        "message": "You have medicine:write permission",
        "email": current_user["email"],
        "role": current_user["role"],
    }


# Logout

@router.post("/logout")
async def logout(
    data: LogoutRequest,
    credentials: HTTPAuthorizationCredentials = Depends(
        bearer_scheme
    ),
):
    # Get access token

    access_token = credentials.credentials

    # Decode access token

    access_payload = decode_access_token(
        access_token
    )

    if not access_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )

    access_jti = access_payload.get("jti")

    if not access_jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has no identifier",
        )

    # Decode refresh token

    refresh_payload = decode_refresh_token(
        data.refresh_token
    )

    if not refresh_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    refresh_jti = refresh_payload.get("jti")

    if not refresh_jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has no identifier",
        )

    # Revoke access token

    await db.revoked_tokens.insert_one(
        {
            "jti": access_jti,
            "expires_at": access_payload.get("exp"),
        }
    )

    # Revoke refresh token

    await db.revoked_tokens.insert_one(
        {
            "jti": refresh_jti,
            "expires_at": refresh_payload.get("exp"),
        }
    )

    return {
        "message": "Successfully logged out",
    }