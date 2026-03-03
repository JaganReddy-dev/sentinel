import jwt
import dotenv
from app.utils.get_secret import get_required_secret

dotenv.load_dotenv()

secret = get_required_secret("SECRET")
algorithm = get_required_secret("ALGORITHM")


def encoded_jwt(payload):
    required_fields = {
        "payload": payload,
    }
    missing = [name for name, value in required_fields.items() if not value]
    if missing:
        raise ValueError(f"Missing required field(s): {', '.join(missing)}")

    return jwt.encode(payload, secret, algorithm)


def decoded_jwt(token, aud):
    required_fields = {
        "token": token,
        "algorithm": algorithm,
        "audience": aud,
    }
    missing = [name for name, value in required_fields.items() if not value]
    if missing:
        raise ValueError(f"Missing required field(s): {', '.join(missing)}")
    return jwt.decode(token, secret, algorithm, audience=aud)
