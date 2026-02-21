from pydantic import BaseModel, Field
from uuid import uuid4


class PasswordDBModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    hashed_password: str
    previous_passwords: list[str] = []
    created_at: int
    password_changed_at: int

    @classmethod
    def from_signup(
        cls, user_id: str, hashed_password: str, now: int
    ) -> "PasswordDBModel":
        return cls(
            user_id=user_id,
            hashed_password=hashed_password,
            previous_passwords=[],
            created_at=now,
            password_changed_at=now,
        )
