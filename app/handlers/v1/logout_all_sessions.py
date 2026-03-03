from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.db import get_db
from app.core.security.get_user_id_from_auth_bearer import get_user_id
from app.schemas.v1.response.logout_all_sesions import LogoutAllResponse
from app.services.logout_all import revoke_all_tokens


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/logout-all", response_model=LogoutAllResponse)
async def logout_all(
    response: Response,
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    await revoke_all_tokens(user_id, db)

    response.delete_cookie("refresh_token")

    return LogoutAllResponse(message="Logged out of all devices")
