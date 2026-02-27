from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status
from app.db.db import get_db
from app.services.email_verification import resend_otp
from app.schemas.v1.request.resend import ResendVerificationRequest
from app.schemas.v1.response.resend import ResendVerificationResponse


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/resend-verification",
    response_model=ResendVerificationResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Already verified or cooldown not passed"
        },
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
    },
)
async def resend_verification(
    payload: ResendVerificationRequest,
    db: AsyncSession = Depends(get_db),
):
    success, message = await resend_otp(payload.user_id, db)

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return ResendVerificationResponse(message=message)
