from __future__ import annotations

import hashlib
import logging
from email.utils import parsedate_to_datetime
from typing import Dict, List, Optional

import feedparser

logger = logging.getLogger("mcp-server.gov")

PIB_FEED_URL = "https://pib.gov.in/PressReleaseSite/rss/eng_release_0.xml"
WHO_FEED_URL = "https://www.who.int/rss-feeds/news-english.xml"


def _hash_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _isoformat(dt: Optional[object]) -> Optional[str]:
    if dt is None:
        return None
    try:
        if getattr(dt, "tzinfo", None) is None:
            return dt.isoformat() + "Z"
        return dt.isoformat()
    except AttributeError:
        return None


def _normalize(entry: Dict, source: str) -> Dict:
    published_at = entry.get("published")
    published_dt = None
    if published_at:
        try:
            published_dt = parsedate_to_datetime(published_at)
        except (TypeError, ValueError):
            published_dt = None

    identifier = entry.get("id") or entry.get("guid") or _hash_id(entry.get("link", ""))

    return {
        "id": identifier,
        "title": (entry.get("title") or "").strip(),
        "summary": (entry.get("summary") or entry.get("description") or "").strip(),
        "url": entry.get("link") or "",
        "source": source,
        "published_at": _isoformat(published_dt),
    }


def _fetch_feed(url: str, source: str) -> List[Dict]:
    try:
        feed = feedparser.parse(url)
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Failed to parse %s feed: %s", source, exc)
        return []

    return [_normalize(entry, source) for entry in feed.entries]


def get_government_bulletins(limit: int = 50) -> List[Dict]:
    """Return recent bulletins from PIB India and WHO feeds."""
    limit = max(1, limit)
    items: List[Dict] = []
    items.extend(_fetch_feed(PIB_FEED_URL, "Press Information Bureau"))
    items.extend(_fetch_feed(WHO_FEED_URL, "World Health Organization"))

    items.sort(key=lambda entry: entry.get("published_at") or "", reverse=True)
    return items[:limit]
