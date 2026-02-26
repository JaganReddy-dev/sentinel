from pydantic.dataclasses import dataclass
from app.schemas.v1.response.token import JWTResponse


@dataclass
class LoginServiceResult:
    jwt_response: JWTResponse
    rt_raw_token: str
