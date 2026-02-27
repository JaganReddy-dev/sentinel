from pydantic import BaseModel, field_validator
from app.schemas.v1.request.signup import UserSignUpRequest


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        return UserSignUpRequest.validate_password_strength(v)
