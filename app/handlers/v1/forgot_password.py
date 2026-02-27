from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.db import get_db
from app.services.forgot_password import forgot_password
from app.schemas.v1.request.forgot_password import ForgotPasswordRequest
from app.schemas.v1.response.forgot_password import ForgotPasswordResponse


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password_handler(
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    message = await forgot_password(payload.identifier, db)
    return ForgotPasswordResponse(message=message)
