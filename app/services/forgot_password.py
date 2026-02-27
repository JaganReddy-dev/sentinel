from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from fastapi import status
from app.models.user import UserModel
from app.models.password_reset_token import PasswordResetTokenModel
from app.schemas.v1.internal.password_reset_token_db_model import (
    PasswordResetTokenDBModel,
)
from app.core.security.tokens.reset.reset_token import (
    generate_reset_token,
    hash_reset_token,
)
from app.core.email.resend import send_password_reset_email
from app.utils.utc_now import utc_now
from app.utils.email import is_email


GENERIC_MESSAGE = (
    "If an account exists with that username/email, a reset link has been sent"
)


async def forgot_password(identifier: str, db: AsyncSession) -> str:
    now = int(utc_now().timestamp())

    # 1. fetch user by email or username
    if is_email(identifier):
        result = await db.execute(
            select(UserModel).where(UserModel.email == identifier)
        )
    else:
        result = await db.execute(
            select(UserModel).where(UserModel.username == identifier)
        )

    user = result.scalar_one_or_none()

    print(f"user: {user}")
    print(f"email_verified: {user.email_verified if user else None}")
    print(f"is_active: {user.is_active if user else None}")

    # always return generic message — never reveal if user exists
    if user is None or not user.email_verified or not user.is_active:
        print("hit early return")
        return GENERIC_MESSAGE

    print("past early return")

    # 2. check cooldown — fetch latest reset token for this user
    latest_result = await db.execute(
        select(PasswordResetTokenModel)
        .where(PasswordResetTokenModel.user_id == user.id)
        .order_by(PasswordResetTokenModel.created_at.desc())
        .limit(1)
    )
    latest = latest_result.scalar_one_or_none()

    if latest is not None:
        latest_db_model = PasswordResetTokenDBModel(**latest.__dict__)
        if not latest_db_model.can_request_new(now):
            remaining = (latest_db_model.created_at + 300) - now
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Please wait {remaining} seconds before requesting another reset link",
            )

    raw_token = generate_reset_token()
    token_hash = hash_reset_token(raw_token)
    reset_token = PasswordResetTokenDBModel.from_request(user.id, token_hash, now)

    try:
        db.add(PasswordResetTokenModel(**reset_token.model_dump()))
        await db.commit()
    except Exception:
        await db.rollback()
        return GENERIC_MESSAGE

    # 4. send reset email
    reset_link = f"http://localhost:8000/api/v1/auth/reset-password?token={raw_token}"
    send_password_reset_email(user.email, reset_link)

    return GENERIC_MESSAGE
