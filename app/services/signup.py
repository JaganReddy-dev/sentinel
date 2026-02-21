from dataclasses import dataclass
from app.schemas.v1.request.signup import UserSignUpRequest
from app.schemas.v1.internal.user_db_model import UserDBModel
from app.schemas.v1.response.user import UserResponse
from app.schemas.v1.internal.rt_db_model import RefreshTokenDBModel
from app.schemas.v1.request.tokens import JWTGenRequest
from app.schemas.v1.internal.password_db_model import PasswordDBModel
from app.services.tokens import create_refresh_token, create_jwt_token
from app.schemas.v1.response.token import JWTResponse
from app.utils.utc_now import utc_now
from app.core.security.password.hash_password import hash_password
from app.models.user import UserModel
from app.models.password import PasswordModel
from app.models.refresh_token import RefreshTokenModel
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class SignupServiceResult:
    """What the service returns to the route handler"""

    user_response: UserResponse
    jwt_response: JWTResponse
    rt_raw_token: str


async def signup_user(user: UserSignUpRequest, db: AsyncSession) -> SignupServiceResult:
    now = int(utc_now().timestamp())

    # 1. hash password
    hashed_password = hash_password(user.password)

    # 2. build pydantic DB models
    user_in_db = UserDBModel.from_signup(user, now)
    password_in_db = PasswordDBModel.from_signup(user_in_db.id, hashed_password, now)

    # 3. generate tokens
    rt = create_refresh_token(user_in_db.id, now)
    jwt = create_jwt_token(JWTGenRequest(sub=user_in_db.id, now=now))

    # 4. build ORM models
    user_orm = UserModel(**user_in_db.model_dump())
    password_orm = PasswordModel(**password_in_db.model_dump())
    rt_in_db = RefreshTokenDBModel.from_token_doc(rt)
    rt_orm = RefreshTokenModel(**rt_in_db.model_dump())

    # 5. persist all in a single transaction
    async with db.begin():
        db.add(user_orm)
        await db.flush()
        db.add(password_orm)
        db.add(rt_orm)

    # 6. build response only after successful DB write
    user_response = UserResponse.from_db(user_in_db)
    jwt_response = JWTResponse(token=jwt["token"], iat=jwt["iat"], exp=jwt["exp"])

    return SignupServiceResult(
        user_response=user_response,
        jwt_response=jwt_response,
        rt_raw_token=rt["raw_token"],
    )
