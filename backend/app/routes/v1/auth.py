from fastapi import APIRouter, HTTPException, status

from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth import authenticate_user
from app.core.security import create_access_token, create_refresh_token

router = APIRouter(prefix="/auth",tags=["Authentication"])

@router.post("/login",response_model=TokenResponse)
async def login(data:LoginRequest):
    user = await authenticate_user(data.email, data.password)

    if not user:
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail = "invalid email or password",
        )
    access_token = create_access_token(
        {"sub":str(user["_id"])}
    )
    refresh_token = create_refresh_token(
        {"sub": str(user["_id"])}
    )
    return TokenResponse(
        access_token= access_token,
        refresh_token= refresh_token,
        token_type="bearer",
    )