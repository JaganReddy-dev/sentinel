from app.core.security.tokens.refresh_token.refresh_token_hash import (
    create_refresh_token_hash,
)
from app.core.security.tokens.refresh_token.raw_refresh_token import (
    create_raw_refresh_token,
)
from app.utils.get_secret import get_required_secret
import uuid
from app.core.security.tokens.jwt.jw_token import encoded_jwt, decoded_jwt
from app.schemas.v1.request.tokens import JWTGenRequest
from app.utils.utc_now import utc_now
from app.schemas.v1.request.tokens import RefreshToken
from app.schemas.v1.request.tokens import VerifyTokenRequest
from jwt import exceptions as jwt_exceptions


def get_refresh_token_expiry() -> int:
    return int(get_required_secret("REFRESH_TOKEN_EXPIRE_DAYS"))


def get_jwt_secret() -> str:
    return get_required_secret("SECRET")


def get_algorithm() -> str:
    return get_required_secret("ALGORITHM")


def create_refresh_token(user_id: str, now: int) -> dict:
    if not user_id:
        raise ValueError({"detail": "User Id is required!"})
    raw_token = create_raw_refresh_token()
    refresh_token = create_refresh_token_hash(raw_token)
    id = str(uuid.uuid4())
    raw_token = raw_token
    created_at = now
    expiry = int((now + (get_refresh_token_expiry() * 24 * 60 * 60)))
    revoked = False

    document = {
        "id": id,
        "user_id": user_id,
        "raw_token": raw_token,
        "token": refresh_token,
        "created_at": created_at,
        "expiry": expiry,
        "revoked": revoked,
    }
    return document


def create_jwt_token(payload: JWTGenRequest):
    if not payload.sub.strip():
        raise ValueError({"detail": "Sub cannot be empty"})
    document = {
        "sub": payload.sub,
        "iss": "localhost",
        "aud": "user",
    }
    jwt_token = encoded_jwt(document, get_jwt_secret(), get_algorithm())
    jwtDoc = {
        "token": jwt_token,
        "sub": payload.sub,
        "iss": document["iss"],
        "aud": document["aud"],
        "iat": payload.now,
        "exp": payload.now + (5 * 60),
    }

    return jwtDoc


def verify_jwt_token(request: VerifyTokenRequest):
    if not request.token:
        raise ValueError({"detail": "Token is required"})
    try:
        decoded = decoded_jwt(
            request.token, get_jwt_secret(), get_algorithm(), aud="user"
        )
        return decoded
    except jwt_exceptions.DecodeError:
        raise ValueError("Invalid token format")
    except jwt_exceptions.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt_exceptions.InvalidAudienceError:
        raise ValueError("Token has invalid audience")
    except jwt_exceptions.PyJWTError as e:
        raise ValueError(f"JWT error: {str(e)}")


def revoke_refresh_token(token: RefreshToken):
    data = token.model_dump()
    data.update({"revoked": True, "exp": int(utc_now().timestamp())})
    return RefreshToken(**data)


def verify_refresh_token(token: RefreshToken):
    if not token.token or not token.raw_token:
        raise ValueError({"detail": "Token and Raw Token are required"})
    hashed_token = create_refresh_token_hash(token.raw_token)
    if hashed_token == token.token:
        return True
    else:
        raise ValueError("Invalid refresh token")
