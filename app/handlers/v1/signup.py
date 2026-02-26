from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.db import get_db
from app.schemas.v1.request.signup import UserSignUpRequest
from app.services.signup import signup_user
from app.schemas.v1.response.signup import SignUpResponse
# from app.schemas.v1.internal.rt_db_model import RefreshTokenDBModel
# from app.models.refresh_token import RefreshTokenModel
# from app.schemas.v1.response.token import JWTResponse


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=SignUpResponse)
async def user_signup(
    payload: UserSignUpRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    result = await signup_user(payload, db)

    return SignUpResponse(
        user_id=result.user_id,
        message=result.message,
    )
    # 1. service handles everything - building models, DB writes
    # result = await signup_user(payload, db)

    # # 2. set RT as httponly cookie
    # response.set_cookie(
    #     key="refresh_token",
    #     value=result.rt_raw_token,
    #     httponly=True,
    #     secure=True,
    #     samesite="strict",
    # )

    # # 3. return user + jwt in body
    # return SignUpResponse(user=result.user_response, jwt=result.jwt_response)
