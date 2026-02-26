from fastapi import APIRouter, Depends, Response, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from app.db.db import get_db
from app.schemas.v1.response.token import JWTResponse
from app.services.refresh import refresh_token


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/refresh", response_model=JWTResponse)
async def refresh_tokens(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    raw_token = request.cookies.get("refresh_token")
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token provided"
        )

    result = await refresh_token(raw_token, db)

    response.set_cookie(
        key="refresh_token",
        value=result.rt_raw_token,
        httponly=True,
        secure=True,
        samesite="strict",
    )

    return result.jwt_response
