from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from fastapi import HTTPException
from fastapi import status
from app.models.refresh_token import RefreshTokenModel


async def revoke_all_tokens(user_id: str, db: AsyncSession) -> None:
    try:
        await db.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.user_id == user_id)
            .values(revoked=True)
        )
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke all sessions",
        )
