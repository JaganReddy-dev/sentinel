from fastapi import APIRouter, Body, HTTPException, status
from app.services.tokens import (
    create_refresh_token,
    create_jwt_token,
    revoke_refresh_token,
    verify_jwt_token,
    verify_refresh_token,
)
from app.schemas.v1.request.tokens import JWTGenRequest
from app.schemas.v1.request.tokens import RefreshToken, VerifyTokenRequest
from app.schemas.v1.response.verify_token import VerifyTokenResponse
from app.schemas.v1.response.error import ErrorResponse


router = APIRouter(
    prefix="/tokens",
    tags=["Tokens"],
)


@router.post(
    "/create",
    summary="Create new JWT, Refresh tokens",
    responses={400: {"model": ErrorResponse}},
)
async def create_token(user: JWTGenRequest) -> dict:
    try:
        jwt = create_jwt_token(user)
        refresh = create_refresh_token(user.sub)
        return {"jwt_token": jwt, "refresh_token": refresh}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/verify",
    summary="Verify JWT token",
    response_model=VerifyTokenResponse,
    responses={
        401: {
            "model": ErrorResponse,
            "description": "Unauthorized - invalid or missing token",
        },
        422: {"description": "Validation error - bad request data"},
    },
)
async def verify_token(token: VerifyTokenRequest = Body(...)) -> dict:
    try:
        data = verify_jwt_token(token)
        return data
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post(
    "/refresh",
    summary="Refresh JWT and RT",
    responses={400: {"model": ErrorResponse}},
)
async def refresh_token(old_rt: RefreshToken = Body(...)) -> dict:
    try:
        verify_refresh_token(old_rt)
        revoked_rt = revoke_refresh_token(old_rt)
        new_jwt = create_jwt_token(JWTGenRequest(sub=old_rt.user_id))
        new_rt = create_refresh_token(old_rt.user_id)
        return {"revoked_rt": revoked_rt, "jwt_token": new_jwt, "refresh_token": new_rt}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.delete(
    "/revoke",
    summary="Revoke Refresh Token",
    responses={400: {"model": ErrorResponse}},
)
async def revoke_token(old_rt: RefreshToken = Body(...)) -> dict:
    try:
        verify_refresh_token(old_rt)
        revoked_rt = revoke_refresh_token(old_rt)
        return revoked_rt.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
