from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status
from app.schemas.v1.request.login import LoginRequest
from app.models.user import UserModel
from app.models.password import PasswordModel
from app.models.refresh_token import RefreshTokenModel
from app.schemas.v1.internal.rt_db_model import RefreshTokenDBModel
from app.schemas.v1.response.token import JWTResponse
from app.core.security.password.hash_password import verify_password
from app.services.tokens import create_jwt_token, create_refresh_token
from app.schemas.v1.request.tokens import JWTGenRequest
from app.utils.utc_now import utc_now
from app.schemas.v1.response.login import LoginServiceResult
from app.utils.email import is_email


FAILED_LOGIN_LIMIT = 5
LOCKOUT_DURATION = 15 * 60  # 15 minutes in seconds


async def login_user(request: LoginRequest, db: AsyncSession) -> LoginServiceResult:
    now = int(utc_now().timestamp())

    # 1. fetch user by email or username
    try:
        if is_email(request.identifier):
            result = await db.execute(
                select(UserModel).where(UserModel.email == request.identifier)
            )
        else:
            result = await db.execute(
                select(UserModel).where(UserModel.username == request.identifier)
            )
        user = result.scalar_one_or_none()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user",
        )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # 2. check account state
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    if user.is_locked:
        if user.locked_until is not None and now < user.locked_until:
            remaining = user.locked_until - now
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Account locked. Try again in {remaining} seconds",
            )
        # lock expired — unlock account
        try:
            await db.execute(
                update(UserModel)
                .where(UserModel.id == user.id)
                .values(is_locked=False, locked_until=None, failed_login_count=0)
            )
            await db.commit()
        except Exception:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to unlock account",
            )

    # 3. fetch password record
    try:
        password_result = await db.execute(
            select(PasswordModel).where(PasswordModel.user_id == user.id)
        )
        password = password_result.scalar_one_or_none()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch password record",
        )

    if password is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password record not found",
        )

    # 4. verify password
    if not verify_password(request.password, password.hashed_password):
        new_count = user.failed_login_count + 1
        values = {"failed_login_count": new_count}

        if new_count >= FAILED_LOGIN_LIMIT:
            values["is_locked"] = True
            values["locked_until"] = now + LOCKOUT_DURATION

        try:
            await db.execute(
                update(UserModel).where(UserModel.id == user.id).values(**values)
            )
            await db.commit()
        except Exception:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update login attempt",
            )

        remaining_attempts = FAILED_LOGIN_LIMIT - new_count
        if remaining_attempts > 0:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid credentials, {remaining_attempts} attempts remaining",
            )
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account locked for {LOCKOUT_DURATION // 60} minutes due to too many failed attempts",
        )

    # 5. reset failed login count and update last_login_at
    try:
        await db.execute(
            update(UserModel)
            .where(UserModel.id == user.id)
            .values(failed_login_count=0, last_login_at=now)
        )
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update login record",
        )

    # 6. issue JWT + RT
    try:
        jwt = create_jwt_token(JWTGenRequest(sub=user.id, now=now))
        rt = create_refresh_token(user.id, now)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate tokens",
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

    return LoginServiceResult(
        jwt_response=JWTResponse(token=jwt["token"], iat=jwt["iat"], exp=jwt["exp"]),
        rt_raw_token=rt["raw_token"],
    )
