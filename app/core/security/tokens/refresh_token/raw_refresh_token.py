import secrets


def create_raw_refresh_token() -> str:
    try:
        return secrets.token_urlsafe(64)
    except Exception:
        raise ValueError("Error creating raw refresh token")
