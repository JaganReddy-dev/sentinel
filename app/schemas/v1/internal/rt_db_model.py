from pydantic import BaseModel


class RefreshTokenDBModel(BaseModel):
    """Stored in DB - raw_token excluded"""

    id: str
    user_id: str
    token: str
    created_at: int
    expiry: int
    revoked: bool

    @classmethod
    def from_token_doc(cls, doc: dict) -> "RefreshTokenDBModel":
        return cls(**{k: v for k, v in doc.items() if k != "raw_token"})
