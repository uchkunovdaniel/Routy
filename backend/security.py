from functools import cache

from pwdlib import PasswordHash

_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _hasher.verify(password, password_hash)


@cache
def demo_password_hash() -> str:
    """Seed users share the demo password; hash it once per process."""
    return hash_password("demo1234")
