from __future__ import annotations

import hashlib
import logging
import os
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Dict, List, Optional

import feedparser
import requests

logger = logging.getLogger("mcp-server.news")

NEWS_API_BASE = "https://newsapi.org/v2"
NEWS_TOP_ENDPOINT = f"{NEWS_API_BASE}/top-headlines"
NEWS_EVERYTHING_ENDPOINT = f"{NEWS_API_BASE}/everything"
RSS_FEEDS = {
    "NDTV": "https://feeds.feedburner.com/ndtvnews-top-stories",
    "Indian Express": "https://indianexpress.com/section/india/feed/",
}


def _hash_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _safe_parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return parsedate_to_datetime(value)
    except (TypeError, ValueError):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None


def _isoformat(value: Optional[datetime]) -> Optional[str]:
    if not value:
        return None
    if value.tzinfo is None:
        return value.isoformat() + "Z"
    return value.isoformat()


def _normalize_article(raw: Dict, source: str, fallback_lang: str = "en") -> Dict:
    published_at = raw.get("publishedAt") or raw.get("published") or raw.get("pubDate")
    published_dt = _safe_parse_date(published_at)
    text = raw.get("content") or raw.get("summary") or raw.get("description") or ""
    url = raw.get("url") or raw.get("link") or ""
    identifier = raw.get("id") or _hash_id(url or raw.get("title", ""))

    return {
        "id": identifier,
        "title": raw.get("title", "").strip(),
        "text": text.strip(),
        "url": url,
        "source": source,
        "language": raw.get("language") or fallback_lang,
        "published_at": _isoformat(published_dt),
    }


def _fetch_news_api(topic: Optional[str], limit: int) -> List[Dict]:
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        logger.warning("NEWS_API_KEY not set; skipping NewsAPI.org fetch")
        return []

    endpoint = NEWS_EVERYTHING_ENDPOINT if topic else NEWS_TOP_ENDPOINT
    params = {
        "pageSize": min(limit, 100),
        "language": "en",
    }

    if topic:
        params.update({"q": topic, "sortBy": "publishedAt"})
    else:
        params["country"] = "in"

    headers = {"X-Api-Key": api_key}

    try:
        response = requests.get(endpoint, params=params, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error("NewsAPI request failed: %s", exc)
        return []

    payload = response.json()
    articles = payload.get("articles", [])
    results = []
    for article in articles:
        normalized = _normalize_article(article, source=article.get("source", {}).get("name", "NewsAPI"))
        results.append(normalized)
    return results


def _fetch_rss_feeds(limit: int) -> List[Dict]:
    articles: List[Dict] = []
    for source_name, feed_url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(feed_url)
        except Exception as exc:  # pragma: no cover - safety
            logger.error("Failed to parse RSS feed %s: %s", feed_url, exc)
            continue

        for entry in feed.entries[:limit]:
            raw = {
                "title": entry.get("title"),
                "description": entry.get("summary"),
                "url": entry.get("link"),
                "id": entry.get("id"),
                "published": entry.get("published"),
            }
            articles.append(_normalize_article(raw, source=source_name))
    return articles


def get_latest_news(topic: Optional[str] = None, limit: int = 50) -> List[Dict]:
    """Return consolidated news items sorted by publish date."""
    limit = max(1, limit)
    items = _fetch_news_api(topic, limit)
    if not topic:
        items.extend(_fetch_rss_feeds(limit))

    # De-duplicate by id while keeping the most recent entry when duplicates exist.
    deduped: Dict[str, Dict] = {}
    for item in items:
        identifier = item["id"]
        existing = deduped.get(identifier)
        if existing is None:
            deduped[identifier] = item
            continue
        existing_date = existing.get("published_at") or ""
        incoming_date = item.get("published_at") or ""
        if incoming_date > existing_date:
            deduped[identifier] = item

    sorted_items = sorted(
        deduped.values(),
        key=lambda entry: entry.get("published_at") or "",
        reverse=True,
    )

    return sorted_items[:limit]
