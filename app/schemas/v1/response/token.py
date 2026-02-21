from pydantic import BaseModel


class JWTResponse(BaseModel):
    """JWT fields to include in response"""

    token: str
    iat: int
    exp: int


class RefreshTokenResponse(BaseModel):
    token: str
