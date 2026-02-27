from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException
from starlette import status
from app.models.password import PasswordModel
from app.models.refresh_token import RefreshTokenModel
from app.models.password_reset_token import PasswordResetTokenModel
from app.schemas.v1.internal.password_reset_token_db_model import (
    PasswordResetTokenDBModel,
)
from app.core.security.tokens.reset.reset_token import hash_reset_token
from app.core.security.password.hash_password import hash_password, verify_password
from app.utils.utc_now import utc_now


async def reset_password(raw_token: str, new_password: str, db: AsyncSession) -> str:
    now = int(utc_now().timestamp())

    token_hash = hash_reset_token(raw_token)
    result = await db.execute(
        select(PasswordResetTokenModel).where(
            PasswordResetTokenModel.token_hash == token_hash
        )
    )
    record = result.scalar_one_or_none()

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset token"
        )

    reset_token = PasswordResetTokenDBModel(**record.__dict__)

    if reset_token.is_used():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has already been used",
        )

    if reset_token.is_expired(now):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired, please request a new one",
        )

    password_result = await db.execute(
        select(PasswordModel).where(PasswordModel.user_id == record.user_id)
    )
    password_record = password_result.scalar_one_or_none()

    if password_record and verify_password(
        new_password, password_record.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as your current password",
        )

    new_hashed = hash_password(new_password)

    try:
        await db.execute(
            update(PasswordModel)
            .where(PasswordModel.user_id == record.user_id)
            .values(hashed_password=new_hashed, password_changed_at=now)
        )

        await db.execute(
            update(PasswordResetTokenModel)
            .where(PasswordResetTokenModel.id == record.id)
            .values(used_at=now)
        )

        await db.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.user_id == record.user_id)
            .values(revoked=True)
        )
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password",
        )

    return "Password reset successful, please login again"
