from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.db import get_db
from app.core.security.get_user_id_from_auth_bearer import get_user_id
from app.services.get_user import get_user_details


router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/user")
async def user_details(
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_details(user_id, db)
    return user
