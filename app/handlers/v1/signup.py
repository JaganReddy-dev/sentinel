from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.db import get_db
from app.schemas.v1.request.signup import UserSignUpRequest
from app.services.signup import signup_user
from app.schemas.v1.response.signup import SignUpResponse
from app.schemas.v1.response.error import ErrorResponse


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/signup",
    response_model=SignUpResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {"detail": "Email or username already exists"}
                }
            },
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "examples": {
                        "check_failed": {
                            "summary": "DB check failed",
                            "value": {"detail": "Failed to check existing user"},
                        },
                        "create_failed": {
                            "summary": "User creation failed",
                            "value": {"detail": "Failed to create user"},
                        },
                    }
                }
            },
        },
    },
)
async def user_signup(
    payload: UserSignUpRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await signup_user(payload, db)

    return SignUpResponse(
        user_id=result.user_id,
        message=result.message,
    )
