from pydantic import BaseModel


class ResendVerificationRequest(BaseModel):
    user_id: str
