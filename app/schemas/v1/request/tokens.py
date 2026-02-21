from uuid import UUID
from pydantic import BaseModel, Field


class RefreshToken(BaseModel):
    id: UUID
    user_id: str
    raw_token: str
    token: str
    iat: int
    exp: int
    revoked: bool = Field(default=False)


class JWTGenRequest(BaseModel):
    sub: str
    now: int


class VerifyTokenRequest(BaseModel):
    token: str
