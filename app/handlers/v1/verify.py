from fastapi import APIRouter, Depends, Response, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.db import get_db
from app.schemas.v1.request.verify import VerifyEmailRequest
from app.schemas.v1.response.token import JWTResponse
from app.services.email_verification import verify_email
from app.services.tokens import create_jwt_token, create_refresh_token
from app.schemas.v1.request.tokens import JWTGenRequest
from app.schemas.v1.internal.rt_db_model import RefreshTokenDBModel
from app.models.refresh_token import RefreshTokenModel
from app.utils.utc_now import utc_now
from starlette import status
from app.schemas.v1.response.error import ErrorResponse


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/verify-email",
    response_model=JWTResponse,
    responses={
        400: {
            "model": ErrorResponse,
            "message": "Invalid OTP, OTP expired, or max attempts reached",
        },
    },
)
async def verify_email_handler(
    payload: VerifyEmailRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    success, message = await verify_email(payload.user_id, payload.otp, db)

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    now = int(utc_now().timestamp())
    jwt = create_jwt_token(JWTGenRequest(sub=payload.user_id, now=now))
    rt = create_refresh_token(payload.user_id, now)
    rt_in_db = RefreshTokenDBModel.from_token_doc(rt)

    async with db.begin():
        db.add(RefreshTokenModel(**rt_in_db.model_dump()))

    response.set_cookie(
        key="refresh_token",
        value=rt["raw_token"],
        httponly=True,
        secure=True,
        samesite="strict",
    )

    return JWTResponse(token=jwt["token"], iat=jwt["iat"], exp=jwt["exp"])
