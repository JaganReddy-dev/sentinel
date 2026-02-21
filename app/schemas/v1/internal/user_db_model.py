from pydantic import Field, ConfigDict
from typing import Optional
from uuid import uuid4
from app.schemas.v1.internal.user_base import UserBase
from app.schemas.v1.request.signup import UserSignUpRequest


class UserDBModel(UserBase):
    """Pydantic model representing the users table"""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    email_verified: bool = False
    is_active: bool = True
    is_locked: bool = False
    locked_until: Optional[int] = None
    failed_login_count: int = 0
    last_login_at: Optional[int] = None
    created_at: int | None = None
    updated_at: int | None = None

    @classmethod
    def from_signup(cls, signup: "UserSignUpRequest", now: int) -> "UserDBModel":
        user = cls(**signup.model_dump(exclude={"password", "terms_accepted"}))
        user.created_at = now
        user.updated_at = now
        return user
