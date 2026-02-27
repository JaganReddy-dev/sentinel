from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.schemas.v1.internal.email_verification_db_model import (
    EmailVerificationDBModel,
    MAX_OTP_ATTEMPTS,
)
from app.models.email_verification import EmailVerificationModel
from app.core.security.otp.otp import generate_otp, hash_otp, verify_otp
from app.core.email.resend import send_verification_email
from app.utils.utc_now import utc_now
from app.models.user import UserModel


async def send_otp(user_id: str, email: str, db: AsyncSession) -> tuple[bool, str]:
    now = int(utc_now().timestamp())
    raw_otp = generate_otp()
    otp_hash = hash_otp(raw_otp)
    verification = EmailVerificationDBModel.from_signup(user_id, otp_hash, now)

    try:
        db.add(EmailVerificationModel(**verification.model_dump()))
        await db.commit()
    except Exception:
        await db.rollback()
        return False, "Failed to save verification record"

    try:
        sent = send_verification_email(email, raw_otp)
        if not sent:
            return False, "Failed to send verification email"
        return True, "OTP sent successfully"
    except Exception:
        return False, "Catch all: Failed to send verification email"


async def verify_email(
    user_id: str, raw_otp: str, db: AsyncSession
) -> tuple[bool, str]:
    """Verify OTP and mark email as verified"""
    now = int(utc_now().timestamp())

    # step 1 - get user by user_id
    user_result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = user_result.scalar_one_or_none()

    if user is None:
        return False, "User not found"

    if user.email_verified:
        return False, "Email already verified"

    # step 2 - get latest verification record
    result = await db.execute(
        select(EmailVerificationModel)
        .where(EmailVerificationModel.user_id == user.id)
        .order_by(EmailVerificationModel.created_at.desc())
        .limit(1)
    )
    record = result.scalar_one_or_none()

    if record is None:
        return False, "No verification record found"

    verification = EmailVerificationDBModel(**record.__dict__)

    if verification.is_expired(now):
        return False, "OTP expired, please request a new one"

    if verification.is_max_attempts():
        return False, "Maximum attempts reached, please request a new one"

    if not verify_otp(raw_otp, verification.otp_hash):
        await db.execute(
            update(EmailVerificationModel)
            .where(EmailVerificationModel.id == record.id)
            .values(attempts=record.attempts + 1)
        )
        await db.commit()
        remaining = MAX_OTP_ATTEMPTS - (record.attempts + 1)
        return False, f"Invalid OTP, {remaining} attempts remaining"

    # mark verification record and user as verified in one transaction
    await db.execute(
        update(EmailVerificationModel)
        .where(EmailVerificationModel.id == record.id)
        .values(verified_at=now)
    )
    await db.execute(
        update(UserModel).where(UserModel.id == user.id).values(email_verified=True)
    )
    await db.commit()

    return True, "Email verified successfully"


async def resend_otp(user_id: str, db: AsyncSession) -> tuple[bool, str]:
    """Resend OTP if cooldown has passed"""
    now = int(utc_now().timestamp())
    print(f"user_id received: {repr(user_id)}")
    user_result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = user_result.scalar_one_or_none()

    if user is None:
        return False, "User not found"

    if user.email_verified:
        return False, "Email already verified"

    # step 2 - get latest verification record
    result = await db.execute(
        select(EmailVerificationModel)
        .where(EmailVerificationModel.user_id == user.id)
        .order_by(EmailVerificationModel.created_at.desc())
        .limit(1)
    )
    record = result.scalar_one_or_none()

    if record is None:
        return False, "No verification record found"

    verification = EmailVerificationDBModel(**record.__dict__)

    if not verification.can_resend(now):
        remaining = (verification.created_at + 60) - now
        return False, f"Please wait {remaining} seconds before requesting a new OTP"

    # generate new OTP and store
    raw_otp = generate_otp()
    otp_hash = hash_otp(raw_otp)
    new_verification = EmailVerificationDBModel.from_signup(user.id, otp_hash, now)

    try:
        db.add(EmailVerificationModel(**new_verification.model_dump()))
        await db.commit()
    except Exception:
        await db.rollback()
        return False, "Failed to save verification record"

    try:
        sent = send_verification_email(user.email, raw_otp)
        if not sent:
            return False, "Failed to send email, please try again"
        return True, "OTP sent successfully"
    except Exception:
        return False, "Failed to send email, please try again"
