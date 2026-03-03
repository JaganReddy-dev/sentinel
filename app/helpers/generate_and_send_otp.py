from sqlalchemy.ext.asyncio import AsyncSession
from app.core.email.resend import send_verification_email
from app.core.security.otp.otp import generate_otp, hash_otp
from app.models.email_verification import EmailVerificationModel
from app.schemas.v1.internal.email_verification_db_model import EmailVerificationDBModel
from app.utils.utc_now import utc_now


async def _generate_and_send_otp(
    user_id: str, email: str, db: AsyncSession
) -> tuple[bool, str]:
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
        return False, "Failed to send verification email"
