from app.core.security.tokens.refresh_token.refresh_token_hash import (
    create_refresh_token_hash,
)
from app.core.security.tokens.refresh_token.raw_refresh_token import (
    create_raw_refresh_token,
)
from app.utils.get_secret import get_required_secret
import uuid
from app.core.security.tokens.jwt.jwt_token import encoded_jwt
from app.schemas.v1.request.tokens import JWTGenRequest
from app.schemas.v1.request.tokens import RefreshToken


REFRESH_TOKEN_EXPIRE_DAYS = int(get_required_secret("REFRESH_TOKEN_EXPIRE_DAYS"))


def create_refresh_token(user_id: str, now: int) -> dict:
    if not user_id:
        raise ValueError("User Id is required!")
    raw_token = create_raw_refresh_token()

    document = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "raw_token": raw_token,
        "token": create_refresh_token_hash(raw_token),
        "created_at": now,
        "expiry": int((now + (REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60))),
        "revoked": False,
    }
    RefreshToken(**document)

    return document


def create_jwt_token(payload: JWTGenRequest):
    if not payload.sub.strip():
        raise ValueError("Sub cannot be empty")
    document = {
        "sub": payload.sub,
        "iss": "localhost",
        "aud": "user",
    }
    try:
        jwt_token = encoded_jwt(document)
    except Exception as e:
        raise ValueError(f"Failed to encode JWT: {str(e)}")
    jwt_doc = {
        "token": jwt_token,
        "sub": payload.sub,
        "iss": document["iss"],
        "aud": document["aud"],
        "iat": payload.now,
        "exp": payload.now + (5 * 60),
    }

    return jwt_doc
