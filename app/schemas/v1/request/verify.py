from pydantic import BaseModel


class VerifyEmailRequest(BaseModel):
    user_id: str
    otp: str
