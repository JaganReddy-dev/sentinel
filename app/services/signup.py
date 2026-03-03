from dataclasses import dataclass
from sqlalchemy import select
from fastapi import status, HTTPException
from app.schemas.v1.request.signup import UserSignUpRequest
from app.schemas.v1.internal.user_db_model import UserDBModel
from app.schemas.v1.internal.password_db_model import PasswordDBModel
from app.utils.utc_now import utc_now
from app.core.security.password.hash_password import hash_password
from app.models.user import UserModel
from app.models.password import PasswordModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.email import send_otp


@dataclass
class SignupServiceResult:
    user_id: str
    message: str


async def signup_user(user: UserSignUpRequest, db: AsyncSession) -> SignupServiceResult:
    now = int(utc_now().timestamp())

    # 1. check if email or username already exists
    try:
        existing_result = await db.execute(
            select(UserModel).where(
                (UserModel.email == user.email) | (UserModel.username == user.username)
            )
        )
        if existing_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email or username already exists",
            )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check existing user",
        )

    # 2. hash password
    hashed_password = hash_password(user.password)

    # 3. build pydantic DB models
    user_in_db = UserDBModel.from_signup(user, now)
    password_in_db = PasswordDBModel.from_signup(user_in_db.id, hashed_password, now)

    # 4. build ORM models and persist in a single transaction
    user_orm = UserModel(**user_in_db.model_dump())
    password_orm = PasswordModel(**password_in_db.model_dump())

    try:
        db.add(user_orm)
        await db.flush()
        db.add(password_orm)
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user",
        )

    # 5. send OTP after transaction — user creation should not fail if email fails
    sent, message = await send_otp(user_in_db.id, user.email, db)
    if not sent:
        return SignupServiceResult(
            user_id=user_in_db.id,
            message="Account created but failed to send verification email. Please use resend.",
        )

    return SignupServiceResult(
        user_id=user_in_db.id,
        message="Verification code sent to your email",
    )
