from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timezone
from typing import Any

from pymongo import ASCENDING
from pymongo.database import Database

from .csv_importer import normalize_text

PBKDF2_ITERATIONS = 120_000


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_auth_indexes(db: Database) -> None:
    db.user_accounts.create_index([("usernameNormalized", ASCENDING)], unique=True)


def _normalize_username(username: str) -> str:
    normalized = normalize_text(username).replace(" ", "_")
    return normalized[:40]


def _hash_password(password: str, salt_hex: str | None = None) -> tuple[str, str]:
    salt = bytes.fromhex(salt_hex) if salt_hex else secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return salt.hex(), digest.hex()


def _verify_password(password: str, salt_hex: str, password_hash: str) -> bool:
    _, candidate_hash = _hash_password(password, salt_hex)
    return hmac.compare_digest(candidate_hash, password_hash)


def _public_user(account: dict[str, Any]) -> dict[str, str]:
    return {
        "userId": str(account["_id"]),
        "username": account["username"],
    }


def register_user(db: Database, username: str, password: str) -> dict[str, str]:
    _ensure_auth_indexes(db)
    username = username.strip()
    username_normalized = _normalize_username(username)
    password = password.strip()

    if len(username_normalized) < 3:
        raise ValueError("USERNAME_TOO_SHORT")
    if len(password) < 6:
        raise ValueError("PASSWORD_TOO_SHORT")
    if db.user_accounts.find_one({"usernameNormalized": username_normalized}):
        raise ValueError("USERNAME_EXISTS")

    salt_hex, password_hash = _hash_password(password)
    account = {
        "username": username,
        "usernameNormalized": username_normalized,
        "passwordSalt": salt_hex,
        "passwordHash": password_hash,
        "createdAt": _now(),
        "updatedAt": _now(),
    }
    result = db.user_accounts.insert_one(account)
    account["_id"] = result.inserted_id
    return _public_user(account)


def login_user(db: Database, username: str, password: str) -> dict[str, str]:
    _ensure_auth_indexes(db)
    username_normalized = _normalize_username(username)
    account = db.user_accounts.find_one({"usernameNormalized": username_normalized})
    if not account:
        raise ValueError("INVALID_LOGIN")
    if not _verify_password(password.strip(), account["passwordSalt"], account["passwordHash"]):
        raise ValueError("INVALID_LOGIN")

    db.user_accounts.update_one(
        {"_id": account["_id"]},
        {"$set": {"lastLoginAt": _now(), "updatedAt": _now()}},
    )
    return _public_user(account)
