from pydantic import BaseModel


class ForgotPasswordRequest(BaseModel):
    identifier: str
