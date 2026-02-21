from pydantic import Field, field_validator, model_validator
import re
from app.schemas.v1.internal.user_base import UserBase


class UserSignUpRequest(UserBase):
    """Schema for user signup request validation"""

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User password (8-128 characters)",
        examples=["SecurePass123!"],
    )
    terms_accepted: bool = Field(
        ..., description="User must accept terms and conditions", examples=[True]
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Password must contain at least one special character")
        return v

    @field_validator("terms_accepted")
    @classmethod
    def validate_terms(cls, v: bool) -> bool:
        if v is not True:
            raise ValueError("You must accept the terms and conditions")
        return v

    @model_validator(mode="after")
    def validate_phone_country_dependency(self):
        if bool(self.phone_number) != bool(self.country_code):
            raise ValueError("phone_number and country_code must be provided together")
        return self
