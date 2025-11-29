from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger("mcp-server.social")

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "social_samples.json"


def _parse_datetime(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.min.replace(tzinfo=None)


def get_social_samples(limit: int = 25) -> List[Dict]:
    """Return curated social media samples from the local dataset."""
    if not DATA_PATH.exists():
        logger.warning("Social samples file not found at %s", DATA_PATH)
        return []

    try:
        with DATA_PATH.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        logger.error("Failed to load social samples: %s", exc)
        return []

    items = list(payload)
    items.sort(key=lambda item: item.get("posted_at") or "", reverse=True)
    return items[: max(1, limit)]
