from datetime import timedelta
from app.schemas.v1.request.signup import UserSignUpRequest
from app.schemas.v1.request.tokens import JWTGenRequest
from app.utils.utc_now import utc_now
from app.core.security.password.hash_password import hash_password
from app.services.tokens import (
    create_refresh_token,
    create_jwt_token,
    get_refresh_token_expiry,
)
import uuid
from pprint import pprint


def signup_user(data: UserSignUpRequest):
    user_id = str(uuid.uuid4())
    now = utc_now()
    timestamp = int(now.timestamp())
    data.password = hash_password(data.password)
    jwt = create_jwt_token(JWTGenRequest(sub=user_id))
    refresh_token = create_refresh_token(user_id)

    new_user = {
        "id": user_id,
        "email": data.email.lower(),
        "first_name": data.first_name.lower(),
        "last_name": data.last_name.lower(),
        "username": data.username.lower(),
        "email_verified": False,
        "phone": data.phone_number,
        "country_code": data.country_code,
        "is_active": True,
        "is_locked": False,
        "locked_until": None,
        "failed_login_count": 0,
        "last_login_at": None,
        "created_at": timestamp,
        "updated_at": timestamp,
    }

    password = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "hashed_password": data.password,
        "previous_passwords": [],
        "created_at": timestamp,
        "password_changed_at": timestamp,
    }

    refresh_token_data = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "hashed_token": refresh_token,
        "revoked": False,
        "revoked_at": None,
        "last_used_at": None,
        "created_at": timestamp,
        "expires_at": int(
            (now + timedelta(days=get_refresh_token_expiry())).timestamp()
        ),
    }

    return {
        "user": new_user,
        "password": password,
        "refresh_token": refresh_token_data,
        "jwt": jwt,
    }


res = signup_user(
    UserSignUpRequest(
        email="H0OoI@example.com",
        password="SecurePass123!",
        username="johndoe",
        first_name="John",
        last_name="Doe",
        phone_number="1234567890",
        country_code="+1",
        terms_accepted=True,
    )
)
pprint(res)
