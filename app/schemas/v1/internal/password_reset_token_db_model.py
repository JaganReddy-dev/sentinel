from pydantic import BaseModel, Field
from uuid import uuid4
from app.utils.get_secret import get_required_secret


reset_token_expiry_seconds = int(get_required_secret("RESET_TOKEN_EXPIRY_SECONDS"))
reset_token_cooldown_seconds = int(get_required_secret("RESET_TOKEN_COOLDOWN_SECONDS"))


class PasswordResetTokenDBModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    token_hash: str
    expires_at: int
    used_at: int | None = None
    created_at: int

    @classmethod
    def from_request(
        cls, user_id: str, token_hash: str, now: int
    ) -> "PasswordResetTokenDBModel":
        return cls(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=now + reset_token_expiry_seconds,
            created_at=now,
        )

    def is_expired(self, now: int) -> bool:
        return now > self.expires_at

    def is_used(self) -> bool:
        return self.used_at is not None

    def is_valid(self, now: int) -> bool:
        return not self.is_expired(now) and not self.is_used()

    def can_request_new(self, now: int) -> bool:
        return now >= self.created_at + reset_token_cooldown_seconds
