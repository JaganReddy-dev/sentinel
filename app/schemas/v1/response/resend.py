from pydantic import BaseModel


class ResendVerificationResponse(BaseModel):
    message: str
