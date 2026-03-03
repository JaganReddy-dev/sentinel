from pydantic import BaseModel


class LogoutAllResponse(BaseModel):
    message: str
