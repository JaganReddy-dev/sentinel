from pydantic import BaseModel, Field
from uuid import uuid4

OTP_EXPIRY_SECONDS = 15 * 60
RESEND_COOLDOWN_SECONDS = 60
MAX_OTP_ATTEMPTS = 3


class EmailVerificationDBModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    otp_hash: str
    expires_at: int
    verified_at: int | None = None
    attempts: int = 0
    created_at: int

    @classmethod
    def from_signup(
        cls, user_id: str, otp_hash: str, now: int
    ) -> "EmailVerificationDBModel":
        return cls(
            user_id=user_id,
            otp_hash=otp_hash,
            expires_at=now + OTP_EXPIRY_SECONDS,
            created_at=now,
        )

    def is_expired(self, now: int) -> bool:
        return now > self.expires_at

    def is_max_attempts(self) -> bool:
        return self.attempts >= MAX_OTP_ATTEMPTS

    def is_verified(self) -> bool:
        return self.verified_at is not None

    def is_valid(self, now: int) -> bool:
        return (
            not self.is_expired(now)
            and not self.is_max_attempts()
            and not self.is_verified()
        )

    def can_resend(self, now: int) -> bool:
        return now >= self.created_at + RESEND_COOLDOWN_SECONDS
