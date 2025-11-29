from __future__ import annotations

import hashlib
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

import requests

logger = logging.getLogger("mcp-server.factcheck")

FACT_CHECK_ENDPOINT = "https://factchecktools.googleapis.com/v1alpha1/claims:search"


def _hash_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _isoformat(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.isoformat() + "Z"
    return dt.isoformat()


def _normalize_claim(claim: Dict) -> Dict:
    reviews = claim.get("claimReview") or []
    primary_review = reviews[0] if reviews else {}

    review_url = primary_review.get("url") or ""
    claim_text = claim.get("text") or ""
    identifier = primary_review.get("url") or claim.get("claimant") or _hash_id(claim_text)
    claim_date = _parse_datetime(claim.get("claimDate"))

    return {
        "id": identifier,
        "claim": claim_text.strip(),
        "claimant": (claim.get("claimant") or "").strip(),
        "claim_date": _isoformat(claim_date),
        "review_url": review_url,
        "review_title": primary_review.get("title"),
        "review_publisher": (primary_review.get("publisher", {}) or {}).get("name"),
        "review_rating": primary_review.get("textualRating"),
        "language_code": claim.get("languageCode"),
    }


def get_recent_fact_checks(limit: int = 25) -> List[Dict]:
    """Fetch recent fact checks from Google Fact Check Tools API.

    Example request:
        https://factchecktools.googleapis.com/v1alpha1/claims:search?languageCode=en&key=YOUR_API_KEY
    """

    api_key = os.getenv("FACT_CHECK_API_KEY")
    if not api_key:
        logger.warning("FACT_CHECK_API_KEY not set; skipping Fact Check Tools fetch")
        return []

    params = {
        "key": api_key,
        "languageCode": "en",
        "pageSize": min(limit, 200),
        "maxAgeDays": 30,
    }

    try:
        response = requests.get(FACT_CHECK_ENDPOINT, params=params, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Fact Check Tools request failed: %s", exc)
        return []

    payload = response.json()
    claims = payload.get("claims", [])

    normalized = [_normalize_claim(claim) for claim in claims]
    normalized.sort(key=lambda item: item.get("claim_date") or "", reverse=True)
    return normalized[:limit]
