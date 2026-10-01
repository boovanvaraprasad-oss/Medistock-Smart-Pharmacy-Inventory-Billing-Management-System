from bson import ObjectId

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.schemas.auth import (
    RegisterRequest,
    TokenResponse,
    RefreshTokenRequest,
    LogoutRequest,
    MeResponse,
    ChangePasswordRequest,
)

from app.services.auth import (
    authenticate_user,
    register_user,
    revoke_token,
    change_user_password,
)

from app.core.database import db

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
)

from app.core.dependencies import (
    get_current_user,
    oauth2_scheme,
)

from app.core.permissions import ROLE_PERMISSIONS


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# ---------------------------------------------------------
# OAuth2 Login
# ---------------------------------------------------------

@router.post(
    "/token",
    response_model=TokenResponse,
)
async def oauth2_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    user = await authenticate_user(
        form_data.username,
        form_data.password,
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


# ---------------------------------------------------------
# Refresh Access Token
# ---------------------------------------------------------

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

    # Check whether user still exists

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

    # Check whether user is still active

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
        )

    # Rotation: the old refresh token is revoked now,
    # so it can never be used a second time

    await revoke_token(
        refresh_jti,
        payload["exp"],
    )

    # Issue a brand new access token AND a brand new refresh token

    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
        token_type="bearer",
    )


# ---------------------------------------------------------
# Register
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# Protected User Endpoint
# ---------------------------------------------------------

@router.get(
    "/me",
    response_model=MeResponse,
)
async def get_me(
    current_user=Depends(get_current_user),
):
    # get_current_user already checked the token is valid.
    # Here we load the user to return who they are.
    user = await db.users.find_one(
        {"_id": ObjectId(current_user["sub"])}
    )

    role = user.get("role")

    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "role": role,
        "is_active": user.get("is_active", True),
        "permissions": ROLE_PERMISSIONS.get(role, []),
    }


# ---------------------------------------------------------
# Change My Password
# ---------------------------------------------------------

@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    current_user=Depends(get_current_user),
):
    await change_user_password(
        user_id=current_user["sub"],
        current_password=data.current_password,
        new_password=data.new_password,
    )

    # The token used for this request stops working,
    # so the person must log in again with the new password
    await revoke_token(
        current_user["jti"],
        current_user["exp"],
    )

    return {
        "message": "Password changed. Please log in again.",
    }


# ---------------------------------------------------------
# Logout
# ---------------------------------------------------------

@router.post("/logout")
async def logout(
    data: LogoutRequest,
    access_token: str = Depends(oauth2_scheme),
):
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

    await revoke_token(
        access_jti,
        access_payload["exp"],
    )

    # Revoke refresh token

    await revoke_token(
        refresh_jti,
        refresh_payload["exp"],
    )

    return {
        "message": "Successfully logged out",
    }