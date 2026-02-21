from pydantic import BaseModel
from app.schemas.v1.response.token import JWTResponse
from app.schemas.v1.response.user import UserResponse


class SignUpResponse(BaseModel):
    user: UserResponse
    jwt: JWTResponse
