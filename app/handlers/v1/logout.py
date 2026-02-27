from fastapi import APIRouter, Depends, Response, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status
from app.db.db import get_db
from app.services.logout import logout_user
from app.schemas.v1.response.error import ErrorResponse


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Invalid refresh token",
            "content": {
                "application/json": {
                    "examples": {
                        "Invalid refresh token": {
                            "summary": "Invalid refresh token",
                            "value": {"detail": "Invalid refresh token"},
                        },
                        "Session already ended": {
                            "summary": "Session already ended",
                            "value": {"detail": "Session already ended"},
                        },
                        "No refresh token provided": {
                            "summary": "No refresh token provided",
                            "value": {"detail": "No refresh token provided"},
                        },
                    }
                }
            },
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "content": {
                "application/json": {"example": {"detail": "Failed to logout"}}
            },
        },
    },
)
async def user_logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    raw_token = request.cookies.get("refresh_token")
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token provided"
        )

    await logout_user(raw_token, db)

    response.delete_cookie("refresh_token")

    return {"message": "Logged out successfully"}
