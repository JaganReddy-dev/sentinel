from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from app.db.db import get_db
from app.services.reset_password import reset_password
from app.schemas.v1.request.reset_password import ResetPasswordRequest
from app.schemas.v1.response.reset_password import ResetPasswordResponse


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid, expired, or used token"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Failed to reset password"
        },
    },
)
async def reset_password_handler(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    message = await reset_password(payload.token, payload.new_password, db)
    return ResetPasswordResponse(message=message)
