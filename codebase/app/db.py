from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.database import Database

DEFAULT_DB_NAME = "demo"

_client: MongoClient | None = None


def load_environment() -> None:
    app_root = Path(__file__).resolve().parents[1]
    load_dotenv(app_root / ".env")
    load_dotenv(app_root.parent / ".env")
    load_dotenv()


@lru_cache
def get_mongo_url() -> str:
    load_environment()
    mongo_url = os.getenv("mongo_url") or os.getenv("MONGO_URL")
    if not mongo_url:
        raise RuntimeError("Missing mongo_url in .env")
    return mongo_url.strip()


@lru_cache
def get_db_name() -> str:
    load_environment()
    return (os.getenv("mongo_db_name") or os.getenv("MONGO_DB_NAME") or DEFAULT_DB_NAME).strip()


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(
            get_mongo_url(),
            serverSelectionTimeoutMS=15000,
            connectTimeoutMS=15000,
            socketTimeoutMS=15000,
        )
    return _client


def get_db() -> Database:
    return get_client()[get_db_name()]


def close_client() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
