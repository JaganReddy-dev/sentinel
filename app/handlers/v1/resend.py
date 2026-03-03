from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.db import get_db
from app.services.email import resend_otp
from app.schemas.v1.request.resend import ResendVerificationRequest
from app.schemas.v1.response.resend import ResendVerificationResponse
from app.schemas.v1.response.error import ErrorResponse
from app.schemas.v1.errors.resend_errors import ResendError


ERROR_STATUS_MAP = {
    ResendError.USER_NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ResendError.FETCH_USER_FAILED: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ResendError.FETCH_RECORD_FAILED: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ResendError.SAVE_FAILED: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ResendError.ALREADY_VERIFIED: status.HTTP_400_BAD_REQUEST,
    ResendError.NO_RECORD: status.HTTP_400_BAD_REQUEST,
    ResendError.COOLDOWN: status.HTTP_429_TOO_MANY_REQUESTS,
    ResendError.SEND_FAILED: status.HTTP_502_BAD_GATEWAY,
}


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/resend-verification",
    response_model=ResendVerificationResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "examples": {
                        "already_verified": {
                            "summary": "Email already verified",
                            "value": {"detail": "Email already verified"},
                        },
                        "no_record": {
                            "summary": "No verification record found",
                            "value": {"detail": "No verification record found"},
                        },
                    }
                }
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "content": {"application/json": {"example": {"detail": "User not found"}}},
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Please wait 45 seconds before requesting a new OTP"
                    }
                }
            },
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "examples": {
                        "fetch_user_failed": {
                            "summary": "Failed to fetch user",
                            "value": {"detail": "Failed to fetch user"},
                        },
                        "fetch_record_failed": {
                            "summary": "Failed to fetch verification record",
                            "value": {"detail": "Failed to fetch verification record"},
                        },
                        "save_failed": {
                            "summary": "Failed to save verification record",
                            "value": {"detail": "Failed to save verification record"},
                        },
                    }
                }
            },
        },
        status.HTTP_502_BAD_GATEWAY: {
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to send verification email"}
                }
            },
        },
    },
)
async def resend_verification(
    payload: ResendVerificationRequest,
    db: AsyncSession = Depends(get_db),
):
    success, message, error = await resend_otp(payload.user_id, db)

    if not success and error is not None:
        status_code = ERROR_STATUS_MAP.get(error, status.HTTP_400_BAD_REQUEST)
        raise HTTPException(status_code=status_code, detail=message)

    return ResendVerificationResponse(message=message)
