"""Password hashing and JWT token utilities."""

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import os

import jwt

from app.core.config import get_settings


PBKDF2_ITERATIONS = 210_000


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 and a random salt."""

    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against the stored hash."""

    try:
        algorithm, iterations, salt_hex, digest_hex = hashed_password.split("$", 3)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations)
    )
    return hmac.compare_digest(digest.hex(), digest_hex)


def create_access_token(subject: str) -> str:
    """Create a signed JWT access token for a user id."""

    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": subject, "exp": expires_at}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token."""

    settings = get_settings()
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
