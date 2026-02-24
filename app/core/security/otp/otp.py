import random
import hashlib


def generate_otp() -> str:
    """Generate a 6 digit OTP"""
    return str(random.randint(100000, 999999))


def hash_otp(raw_otp: str) -> str:
    """Hash OTP using SHA-256"""
    return hashlib.sha256(raw_otp.encode()).hexdigest()


def verify_otp(raw_otp: str, otp_hash: str) -> bool:
    """Verify raw OTP against stored hash"""
    return hash_otp(raw_otp) == otp_hash
