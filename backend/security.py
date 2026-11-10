import os
from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _hasher.verify(password, password_hash)


# --- tokens ---------------------------------------------------------------

_DEV_SECRET = "routy-dev-only-secret-change-me-in-production"  # never used outside local dev
TOKEN_TTL = timedelta(days=7)


def _secret() -> str:
    return os.environ.get("ROUTY_JWT_SECRET", _DEV_SECRET)


def create_token(user_id: str) -> str:
    now = datetime.now(UTC)
    return jwt.encode({"sub": user_id, "iat": now, "exp": now + TOKEN_TTL}, _secret(), algorithm="HS256")


def read_token(token: str) -> str | None:
    """Return the user id, or None if the token is invalid or expired."""
    try:
        payload = jwt.decode(token, _secret(), algorithms=["HS256"], options={"require": ["sub", "exp"]})
    except jwt.PyJWTError:
        return None
    sub = payload.get("sub")
    return sub if isinstance(sub, str) else None
