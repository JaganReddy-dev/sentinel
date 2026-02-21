from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional
import re


class UserBase(BaseModel):
    """Shared user fields across request, DB, and response schemas"""

    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr = Field(
        ..., description="User's email address", examples=["user@example.com"]
    )
    username: str = Field(
        ...,
        min_length=3,
        max_length=30,
        description="Unique username (3-30 characters, alphanumeric and underscore only)",
        examples=["john_doe"],
    )
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="User's first name",
        examples=["John"],
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="User's last name",
        examples=["Doe"],
    )
    phone_number: Optional[str] = Field(
        None, description="Optional phone number", examples=["+1234567890"]
    )
    country_code: Optional[str] = Field(
        None, description="Optional country code (ISO 3166-1 alpha-2)", examples=["US"]
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError(
                "Username can only contain letters, numbers, and underscores"
            )
        if v[0].isdigit():
            raise ValueError("Username cannot start with a number")
        return v.lower()

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        cleaned = re.sub(r"[\s\-\(\)]", "", v)
        if not re.match(r"^\+?\d{10,15}$", cleaned):
            raise ValueError(
                "Invalid phone number format. Use international format (+1234567890)"
            )
        return cleaned

    @field_validator("first_name", "last_name", "email", mode="before")
    @classmethod
    def normalize_strings(cls, v: str) -> str:
        return v.strip().lower()
