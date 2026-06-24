import base64
import hashlib
import hmac
import os
from typing import Tuple

# Preferência: Argon2id quando a dependência existir.
try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError, VerificationError
    _ARGON2 = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2, hash_len=32, salt_len=16)
except Exception:  # fallback sem dependência externa
    PasswordHasher = None
    VerifyMismatchError = Exception
    VerificationError = Exception
    _ARGON2 = None

PBKDF2_ITERATIONS = 600_000


def _pbkdf2_hash(password: str, salt: bytes | None = None) -> str:
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return "pbkdf2_sha256${}${}${}".format(
        PBKDF2_ITERATIONS,
        base64.urlsafe_b64encode(salt).decode("ascii"),
        base64.urlsafe_b64encode(dk).decode("ascii"),
    )


def _pbkdf2_verify(password: str, stored_hash: str) -> bool:
    try:
        alg, iter_s, salt_b64, hash_b64 = stored_hash.split("$", 3)
        if alg != "pbkdf2_sha256":
            return False
        iterations = int(iter_s)
        salt = base64.urlsafe_b64decode(salt_b64.encode("ascii"))
        expected = base64.urlsafe_b64decode(hash_b64.encode("ascii"))
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(expected, actual)
    except Exception:
        return False


def hash_password(password: str) -> str:
    if not password or len(password) < 8:
        raise ValueError("A senha deve ter pelo menos 8 caracteres.")
    if _ARGON2 is not None:
        return _ARGON2.hash(password)
    return _pbkdf2_hash(password)


def verify_password(password: str, stored_hash: str) -> bool:
    if not stored_hash:
        return False
    if stored_hash.startswith("$argon2") and _ARGON2 is not None:
        try:
            return _ARGON2.verify(stored_hash, password)
        except (VerifyMismatchError, VerificationError, Exception):
            return False
    if stored_hash.startswith("pbkdf2_sha256$"):
        return _pbkdf2_verify(password, stored_hash)
    return False


def needs_rehash(stored_hash: str) -> bool:
    if stored_hash.startswith("pbkdf2_sha256$") and _ARGON2 is not None:
        return True
    if stored_hash.startswith("$argon2") and _ARGON2 is not None:
        try:
            return _ARGON2.check_needs_rehash(stored_hash)
        except Exception:
            return False
    return False
