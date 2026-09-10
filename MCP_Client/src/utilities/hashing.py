from __future__ import annotations

import hashlib
import hmac

from settings import config


_HASH_ITERATIONS = 600_000


def hash_value(value: str) -> str:
    """Hash a password or token using the application's configured secret."""
    secret = config.jwt_secret.encode("utf-8")
    if not secret:
        raise ValueError("JWT_SECRET must be configured for hashing")
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        value.encode("utf-8"),
        secret,
        _HASH_ITERATIONS,
    )
    return digest.hex()


def verify_value(value: str, expected_hash: str | None) -> bool:
    if not expected_hash:
        return False
    return hmac.compare_digest(hash_value(value), expected_hash)