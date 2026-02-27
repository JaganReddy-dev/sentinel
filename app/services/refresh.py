from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException
from fastapi import status
from app.models.refresh_token import RefreshTokenModel
from app.schemas.v1.internal.rt_db_model import RefreshTokenDBModel
from app.schemas.v1.response.login import LoginServiceResult
from app.schemas.v1.response.token import JWTResponse
from app.schemas.v1.request.tokens import JWTGenRequest
from app.services.tokens import create_jwt_token, create_refresh_token
from app.core.security.tokens.refresh_token.refresh_token_hash import (
    create_refresh_token_hash,
)
from app.utils.utc_now import utc_now


async def refresh_token(raw_token: str, db: AsyncSession) -> LoginServiceResult:
    now = int(utc_now().timestamp())

    # 1. hash the raw token and find in DB
    hashed = create_refresh_token_hash(raw_token)
    result = await db.execute(
        select(RefreshTokenModel).where(RefreshTokenModel.token == hashed)
    )
    record = result.scalar_one_or_none()

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    # 2. reuse detection - if already revoked, revoke all user tokens
    if record.revoked:
        await db.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.user_id == record.user_id)
            .values(revoked=True)
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token reuse detected, all sessions revoked",
        )

    # 3. check expiry
    if now > record.expiry:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired, please login again",
        )

    # 4. revoke old RT
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke old refresh token",
        )

    # 5. issue new JWT + RT
    jwt = create_jwt_token(JWTGenRequest(sub=record.user_id, now=now))
    rt = create_refresh_token(record.user_id, now)
    rt_in_db = RefreshTokenDBModel.from_token_doc(rt)

    try:
        db.add(RefreshTokenModel(**rt_in_db.model_dump()))
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create new session",
        )

    return LoginServiceResult(
        jwt_response=JWTResponse(token=jwt["token"], iat=jwt["iat"], exp=jwt["exp"]),
        rt_raw_token=rt["raw_token"],
    )
