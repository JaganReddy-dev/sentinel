from fastapi import APIRouter, Depends, Response, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.db import get_db
from app.schemas.v1.request.verify import VerifyEmailRequest
from app.schemas.v1.response.token import JWTResponse
from app.schemas.v1.response.error import ErrorResponse
from app.services.email import verify_email, VerifyEmailError
from app.services.tokens import create_jwt_token, create_refresh_token
from app.schemas.v1.request.tokens import JWTGenRequest
from app.schemas.v1.internal.rt_db_model import RefreshTokenDBModel
from app.models.refresh_token import RefreshTokenModel
from app.utils.utc_now import utc_now


router = APIRouter(prefix="/auth", tags=["auth"])


VERIFY_ERROR_STATUS_MAP = {
    VerifyEmailError.USER_NOT_FOUND: status.HTTP_404_NOT_FOUND,
    VerifyEmailError.FETCH_USER_FAILED: status.HTTP_500_INTERNAL_SERVER_ERROR,
    VerifyEmailError.FETCH_RECORD_FAILED: status.HTTP_500_INTERNAL_SERVER_ERROR,
    VerifyEmailError.UPDATE_ATTEMPTS_FAILED: status.HTTP_500_INTERNAL_SERVER_ERROR,
    VerifyEmailError.VERIFY_FAILED: status.HTTP_500_INTERNAL_SERVER_ERROR,
    VerifyEmailError.ALREADY_VERIFIED: status.HTTP_400_BAD_REQUEST,
    VerifyEmailError.NO_RECORD: status.HTTP_400_BAD_REQUEST,
    VerifyEmailError.OTP_EXPIRED: status.HTTP_400_BAD_REQUEST,
    VerifyEmailError.MAX_ATTEMPTS: status.HTTP_400_BAD_REQUEST,
    VerifyEmailError.INVALID_OTP: status.HTTP_400_BAD_REQUEST,
}


@router.post(
    "/verify-email",
    response_model=JWTResponse,
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
                        "otp_expired": {
                            "summary": "OTP expired",
                            "value": {
                                "detail": "OTP expired, please request a new one"
                            },
                        },
                        "max_attempts": {
                            "summary": "Max attempts reached",
                            "value": {
                                "detail": "Maximum attempts reached, please request a new one"
                            },
                        },
                        "invalid_otp": {
                            "summary": "Invalid OTP",
                            "value": {"detail": "Invalid OTP, 2 attempts remaining"},
                        },
                        "no_record": {
                            "summary": "No verification record",
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
                            "summary": "Failed to fetch record",
                            "value": {"detail": "Failed to fetch verification record"},
                        },
                        "update_attempts_failed": {
                            "summary": "Failed to update attempts",
                            "value": {"detail": "Failed to update attempts"},
                        },
                        "verify_failed": {
                            "summary": "Failed to verify email",
                            "value": {"detail": "Failed to verify email"},
                        },
                        "session_failed": {
                            "summary": "Failed to create session",
                            "value": {"detail": "Failed to create session"},
                        },
                    }
                }
            },
        },
    },
)
async def verify_email_id(
    payload: VerifyEmailRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    success, message, error = await verify_email(payload.user_id, payload.otp, db)

    if not success and error is not None:
        status_code = VERIFY_ERROR_STATUS_MAP.get(error, status.HTTP_400_BAD_REQUEST)
        raise HTTPException(status_code=status_code, detail=message)

    now = int(utc_now().timestamp())

    try:
        jwt = create_jwt_token(JWTGenRequest(sub=payload.user_id, now=now))
        rt = create_refresh_token(payload.user_id, now)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session",
        )

    rt_in_db = RefreshTokenDBModel.from_token_doc(rt)

    try:
        db.add(RefreshTokenModel(**rt_in_db.model_dump()))
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session",
        )

    response.set_cookie(
        key="refresh_token",
        value=rt["raw_token"],
        httponly=True,
        secure=False,  # set True in production
        samesite="strict",
    )

    return JWTResponse(token=jwt["token"], iat=jwt["iat"], exp=jwt["exp"])
