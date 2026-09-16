from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth import authenticate_user
from app.core.database import db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
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


# -------------------------
# Login
# -------------------------

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


# -------------------------
# Protected user endpoint
# -------------------------

@router.get("/me")
async def get_me(
    current_user=Depends(get_current_user),
):
    return {
        "message": "You are authenticated",
        "user": current_user,
    }


# -------------------------
# RBAC permission test
# -------------------------

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


# -------------------------
# Logout
# -------------------------

@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(
        bearer_scheme
    ),
):

    token = credentials.credentials

    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )

    jti = payload.get("jti")

    if not jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has no identifier",
        )

    await db.revoked_tokens.insert_one(
        {
            "jti": jti,
            "expires_at": payload.get("exp"),
        }
    )

    return {
        "message": "Successfully logged out",
    }