from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.db import get_db
from app.schemas.v1.request.login import LoginRequest
from app.schemas.v1.response.token import JWTResponse
from app.services.login import login_user
from app.schemas.v1.response.error import ErrorResponse
from fastapi import status

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=JWTResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "User not found",
            "content": {"application/json": {"example": {"detail": "User not found"}}},
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": "Email not verified or account inactive",
            "content": {
                "application/json": {
                    "examples": {
                        "email_not_verified": {
                            "summary": "Email not verified",
                            "value": {"detail": "Email not verified"},
                        },
                        "account_inactive": {
                            "summary": "Account inactive",
                            "value": {"detail": "Account is inactive"},
                        },
                    }
                }
            },
        },
        status.HTTP_423_LOCKED: {
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {"detail": "Account locked. Try again in 900 seconds"}
                }
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid credentials, 4 attempts remaining"}
                }
            },
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "content": {
                "application/json": {"example": {"detail": "Internal server error"}}
            },
        },
    },
)
async def user_login(
    payload: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    result = await login_user(payload, db)

    response.set_cookie(
        key="refresh_token",
        value=result.rt_raw_token,
        httponly=True,
        secure=True,
        samesite="strict",
    )

    return result.jwt_response
