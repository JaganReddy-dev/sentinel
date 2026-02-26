import secrets


def gen_hex_secret(random_bytes: int = 32) -> str:
    """Generates a random hex secret string.
    Args:        random_bytes (int): The number of random bytes to generate. Default is 32. Use 64 for a 128 character hex string.
    Returns:        str: A random hex secret string.
    """
    return secrets.token_hex(random_bytes)
