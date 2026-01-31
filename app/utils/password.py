"""Password hashing utilities."""

import bcrypt


def hash_password(plain: str) -> str:
    """
    Hash a plain-text password using bcrypt.

    Args:
        plain: Plain-text password

    Returns:
        Hashed password string (UTF-8 decoded for storage)
    """
    password_bytes = plain.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")
