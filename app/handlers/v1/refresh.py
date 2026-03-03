from fastapi import APIRouter, Depends, Response, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.db import get_db
from app.schemas.v1.response.token import JWTResponse
from app.schemas.v1.response.error import ErrorResponse
from app.services.refresh import refresh_token


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/refresh",
    response_model=JWTResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "examples": {
                        "no_token": {
                            "summary": "No refresh token",
                            "value": {"detail": "No refresh token provided"},
                        },
                        "invalid_token": {
                            "summary": "Invalid refresh token",
                            "value": {"detail": "Invalid refresh token"},
                        },
                        "reuse_detected": {
                            "summary": "Token reuse detected",
                            "value": {
                                "detail": "Refresh token reuse detected, all sessions revoked"
                            },
                        },
                        "token_expired": {
                            "summary": "Token expired",
                            "value": {
                                "detail": "Refresh token expired, please login again"
                            },
                        },
                    }
                }
            },
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "examples": {
                        "fetch_failed": {
                            "summary": "Failed to fetch session",
                            "value": {"detail": "Failed to fetch session"},
                        },
                        "revoke_failed": {
                            "summary": "Failed to revoke old token",
                            "value": {"detail": "Failed to revoke old refresh token"},
                        },
                        "create_failed": {
                            "summary": "Failed to create session",
                            "value": {"detail": "Failed to create new session"},
                        },
                        "save_failed": {
                            "summary": "Failed to save session",
                            "value": {"detail": "Failed to save new session"},
                        },
                    }
                }
            },
        },
    },
)
async def refresh_tokens(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    raw_token = request.cookies.get("refresh_token")
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token provided"
        )

    result = await refresh_token(raw_token, db)

    response.set_cookie(
        key="refresh_token",
        value=result.rt_raw_token,
        httponly=True,
        secure=False,  # Set to True in production
        samesite="strict",
    )

    return result.jwt_response
