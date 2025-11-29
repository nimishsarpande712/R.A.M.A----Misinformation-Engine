"""MongoDB-backed logging helpers for claim results."""

import logging
import os
from datetime import datetime
from threading import Lock, Thread
from typing import Any, Dict, Optional

from pymongo import MongoClient, errors
from pymongo.collection import Collection

logger = logging.getLogger(__name__)

_CLIENT: Optional[MongoClient] = None
_DATABASE = None
_LOCK = Lock()
_MISSING_ENV_LOGGED = False
_COLLECTION_NAME = "claim_logs"


def _reset_client(locked: bool = False) -> None:
    """Reset the cached MongoDB client so the next call reconnects."""
    global _CLIENT, _DATABASE
    if locked:
        if _CLIENT is not None:
            try:
                _CLIENT.close()
            except Exception:  # pragma: no cover - best effort cleanup
                pass
        _CLIENT = None
        _DATABASE = None
        return

    with _LOCK:
        if _CLIENT is not None:
            try:
                _CLIENT.close()
            except Exception:  # pragma: no cover - best effort cleanup
                pass
        _CLIENT = None
        _DATABASE = None


def _get_collection() -> Optional[Collection]:
    """Return the MongoDB collection, creating the client lazily."""
    global _CLIENT, _DATABASE, _MISSING_ENV_LOGGED

    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB")

    if not uri or not db_name:
        if not _MISSING_ENV_LOGGED:
            logger.warning(
                "MongoDB logging disabled because MONGODB_URI or MONGODB_DB is not set."
            )
            _MISSING_ENV_LOGGED = True
        return None

    with _LOCK:
        if _CLIENT is None:
            try:
                _CLIENT = MongoClient(
                    uri,
                    serverSelectionTimeoutMS=3000,
                    connect=False,
                )
                _DATABASE = _CLIENT[db_name]
            except errors.PyMongoError as exc:
                logger.error("Failed to initialize MongoDB client: %s", exc)
                _reset_client(locked=True)
                return None

        if _DATABASE is None:
            try:
                _DATABASE = _CLIENT[db_name]
            except errors.PyMongoError as exc:
                logger.error("Failed to select MongoDB database: %s", exc)
                _reset_client(locked=True)
                return None

        return _DATABASE[_COLLECTION_NAME]


def _insert_document(document: Dict[str, Any]) -> None:
    """Insert a document, resetting the client on failure."""
    collection = _get_collection()
    if collection is None:
        return

    try:
        collection.insert_one(document)
    except errors.PyMongoError as exc:
        logger.warning("MongoDB logging failed, will retry on next call: %s", exc)
        _reset_client()


def log_claim_result(claim_text: str, language: str, result: Dict[str, Any]) -> None:
    """Queue a best-effort insert of the claim result into MongoDB."""
    document = {
        "claim_text": claim_text,
        "language": language,
        "mode": result.get("mode"),
        "verdict": result.get("verdict"),
        "timestamp": datetime.utcnow(),
        "raw_result": result,
    }

    Thread(target=_insert_document, args=(document,), daemon=True).start()
