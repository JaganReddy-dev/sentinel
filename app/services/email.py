from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.schemas.v1.internal.email_verification_db_model import (
    EmailVerificationDBModel,
    MAX_OTP_ATTEMPTS,
)
from app.models.email_verification import EmailVerificationModel
from app.core.security.otp.otp import verify_otp
from app.utils.utc_now import utc_now
from app.models.user import UserModel
from app.helpers.generate_and_send_otp import _generate_and_send_otp
from app.schemas.v1.errors.resend_errors import ResendError
from app.schemas.v1.errors.verify_email_errors import VerifyEmailError


async def send_otp(user_id: str, email: str, db: AsyncSession) -> tuple[bool, str]:
    return await _generate_and_send_otp(user_id, email, db)


async def verify_email(
    user_id: str, raw_otp: str, db: AsyncSession
) -> tuple[bool, str, VerifyEmailError | None]:
    now = int(utc_now().timestamp())

    try:
        user_result = await db.execute(select(UserModel).where(UserModel.id == user_id))
        user = user_result.scalar_one_or_none()
    except Exception:
        return False, "Failed to fetch user", VerifyEmailError.FETCH_USER_FAILED

    if user is None:
        return False, "User not found", VerifyEmailError.USER_NOT_FOUND

    if user.email_verified:
        return False, "Email already verified", VerifyEmailError.ALREADY_VERIFIED

    try:
        result = await db.execute(
            select(EmailVerificationModel)
            .where(EmailVerificationModel.user_id == user.id)
            .order_by(EmailVerificationModel.created_at.desc())
            .limit(1)
        )
        record = result.scalar_one_or_none()
    except Exception:
        return (
            False,
            "Failed to fetch verification record",
            VerifyEmailError.FETCH_RECORD_FAILED,
        )

    if record is None:
        return False, "No verification record found", VerifyEmailError.NO_RECORD

    verification = EmailVerificationDBModel(**record.__dict__)

    if verification.is_expired(now):
        return (
            False,
            "OTP expired, please request a new one",
            VerifyEmailError.OTP_EXPIRED,
        )

    if verification.is_max_attempts():
        return (
            False,
            "Maximum attempts reached, please request a new one",
            VerifyEmailError.MAX_ATTEMPTS,
        )

    if not verify_otp(raw_otp, verification.otp_hash):
        try:
            await db.execute(
                update(EmailVerificationModel)
                .where(EmailVerificationModel.id == record.id)
                .values(attempts=record.attempts + 1)
            )
            await db.commit()
        except Exception:
            await db.rollback()
            return (
                False,
                "Failed to update attempts",
                VerifyEmailError.UPDATE_ATTEMPTS_FAILED,
            )

        remaining = MAX_OTP_ATTEMPTS - (record.attempts + 1)
        return (
            False,
            f"Invalid OTP, {remaining} attempts remaining",
            VerifyEmailError.INVALID_OTP,
        )

    try:
        await db.execute(
            update(EmailVerificationModel)
            .where(EmailVerificationModel.id == record.id)
            .values(verified_at=now)
        )
        await db.execute(
            update(UserModel).where(UserModel.id == user.id).values(email_verified=True)
        )
        await db.commit()
    except Exception:
        await db.rollback()
        return False, "Failed to verify email", VerifyEmailError.VERIFY_FAILED

    return True, "Email verified successfully", None


async def resend_otp(
    user_id: str, db: AsyncSession
) -> tuple[bool, str, ResendError | None]:
    try:
        user_result = await db.execute(select(UserModel).where(UserModel.id == user_id))
        user = user_result.scalar_one_or_none()
    except Exception:
        return False, "Failed to fetch user", ResendError.FETCH_USER_FAILED

    if user is None:
        return False, "User not found", ResendError.USER_NOT_FOUND

    if user.email_verified:
        return False, "Email already verified", ResendError.ALREADY_VERIFIED

    try:
        result = await db.execute(
            select(EmailVerificationModel)
            .where(EmailVerificationModel.user_id == user.id)
            .order_by(EmailVerificationModel.created_at.desc())
            .limit(1)
        )
        record = result.scalar_one_or_none()
    except Exception:
        return (
            False,
            "Failed to fetch verification record",
            ResendError.FETCH_RECORD_FAILED,
        )

    if record is None:
        return False, "No verification record found", ResendError.NO_RECORD

    now = int(utc_now().timestamp())
    verification = EmailVerificationDBModel(**record.__dict__)

    if not verification.can_resend(now):
        remaining = (verification.created_at + 60) - now
        return (
            False,
            f"Please wait {remaining} seconds before requesting a new OTP",
            ResendError.COOLDOWN,
        )

    success, message = await _generate_and_send_otp(user.id, user.email, db)
    if not success:
        return False, message, ResendError.SAVE_FAILED
    return True, message, None
