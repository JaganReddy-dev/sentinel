from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.db import get_db
from app.schemas.v1.request.login import LoginRequest
from app.schemas.v1.response.token import JWTResponse
from app.services.login import login_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=JWTResponse)
async def login(
    payload: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    result = await login_user(payload, db)

    response.set_cookie(
        key="refresh_token",
        value=result.rt_raw_token,
        httponly=True,
        secure=True,
        samesite="strict",
    )

    return result.jwt_response
