from pydantic import ConfigDict
from app.schemas.v1.internal.user_base import UserBase
from app.schemas.v1.internal.user_db_model import UserDBModel


class UserResponse(UserBase):
    """Response model for user creation"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    email_verified: bool
    is_active: bool
    created_at: int

    @classmethod
    def from_db(cls, user: "UserDBModel") -> "UserResponse":
        return cls(
            **user.model_dump(
                include={
                    "id",
                    "email",
                    "username",
                    "first_name",
                    "last_name",
                    "email_verified",
                    "is_active",
                    "created_at",
                }
            )
        )
