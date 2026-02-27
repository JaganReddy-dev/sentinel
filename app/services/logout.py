from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException
from fastapi import status
from app.models.refresh_token import RefreshTokenModel
from app.core.security.tokens.refresh_token.refresh_token_hash import (
    create_refresh_token_hash,
)


async def logout_user(raw_token: str, db: AsyncSession) -> None:
    hashed = create_refresh_token_hash(raw_token)
    result = await db.execute(
        select(RefreshTokenModel).where(RefreshTokenModel.token == hashed)
    )
    record = result.scalar_one_or_none()

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    if record.revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Session already ended"
        )

    try:
        await db.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.id == record.id)
            .values(revoked=True)
        )
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to logout"
        )
