"""
Module for ingesting fact checks from Google Fact Check Tools API.

Integrates with Google's Fact Check Tools API to fetch and normalize fact check data.
Reference: https://developers.google.com/fact-check/tools/api/reference/rest/v1alpha1/claims/search
"""

import logging
import os
from typing import Dict, List, Optional, Any
import requests

from .vector_store import upsert_documents

logger = logging.getLogger(__name__)

# Google Fact Check Tools API endpoint
GOOGLE_FACTCHECK_API_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"


def get_google_factcheck_api_key() -> Optional[str]:
    """
    Get Google Fact Check Tools API key from environment.
    
    Returns:
        Optional[str]: API key if available, None otherwise
    """
    return os.getenv("GOOGLE_FACTCHECK_API_KEY")


def normalize_google_response(
    claim_reviews: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Normalize Google Fact Check Tools API response into fact-checks format.
    
    Transforms claimReview objects from Google API into the standard fact-check format:
    {
        id: unique identifier
        claim: claim text (title from API)
        verdict: normalized verdict
        explanation: summary from claimReview
        source: publisher name
        url: claim review URL
        language: language code
        date: claim date
        tags: extracted tags
    }
    
    Args:
        claim_reviews: List of claimReview objects from Google API response
        
    Returns:
        List[Dict[str, Any]]: Normalized fact checks
    """
    normalized = []
    
    for idx, review in enumerate(claim_reviews):
        try:
            # Extract basic fields
            claim_text = review.get("claimText", "")
            claim_date = review.get("claimDate", "")
            url = review.get("claimReview", {}).get("url", "") if isinstance(review.get("claimReview"), dict) else ""
            
            # Handle claimReview as list (API can return multiple reviews per claim)
            claim_reviews_list = review.get("claimReview", [])
            if isinstance(claim_reviews_list, dict):
                claim_reviews_list = [claim_reviews_list]
            
            if not claim_reviews_list:
                logger.warning(f"Skipping claim without reviews: {claim_text}")
                continue
            
            # Process first claim review
            first_review = claim_reviews_list[0]
            publisher_name = first_review.get("publisher", {}).get("name", "Unknown")
            summary = first_review.get("textualRating", "")
            verdict_rating = first_review.get("reviewRating", {})
            
            # Normalize verdict
            verdict = normalize_verdict(verdict_rating)
            
            # Extract explanation (use title if available, otherwise rating name)
            explanation = first_review.get("title", "")
            if not explanation:
                explanation = verdict_rating.get("name", "")
            
            # Get source URL (publisher site)
            source_url = first_review.get("publisher", {}).get("site", "")
            
            # Extract language (default to 'en')
            language = review.get("languageCode", "en")
            
            # Create ID
            doc_id = f"google_factcheck_{idx}_{claim_text[:20].replace(' ', '_')}"
            
            # Extract tags from claim text and verdict
            tags = extract_tags(claim_text, verdict)
            
            normalized_item = {
                "id": doc_id,
                "claim": claim_text,
                "verdict": verdict,
                "explanation": explanation,
                "source": publisher_name,
                "url": url or source_url,
                "language": language,
                "date": claim_date,
                "tags": tags,
                "provider": "google_factcheck",
                "original_data": {
                    "textual_rating": summary,
                    "rating_value": verdict_rating.get("ratingValue"),
                    "best_rating": verdict_rating.get("bestRating"),
                    "worst_rating": verdict_rating.get("worstRating"),
                }
            }
            
            normalized.append(normalized_item)
            logger.debug(f"Normalized claim: {claim_text[:50]}... -> verdict: {verdict}")
            
        except Exception as e:
            logger.warning(f"Error normalizing claim review at index {idx}: {str(e)}")
            continue
    
    return normalized


def normalize_verdict(rating: Dict[str, Any]) -> str:
    """
    Normalize rating object to standard verdict format.
    
    Converts rating values/names to "TRUE", "FALSE", or "MISLEADING".
    
    Args:
        rating: Rating object from API response
        
    Returns:
        str: Normalized verdict
    """
    # Common rating patterns
    name = str(rating.get("name", "")).lower()
    
    # TRUE/ACCURATE patterns
    if any(x in name for x in ["true", "accurate", "correct", "verified", "fact-checked", "correct fact"]):
        return "TRUE"
    
    # FALSE/INACCURATE patterns
    if any(x in name for x in ["false", "inaccurate", "incorrect", "fabricated", "false claim", "false information"]):
        return "FALSE"
    
    # MISLEADING patterns
    if any(x in name for x in ["misleading", "misleaded", "mixed", "partial", "out of context", "lacks context"]):
        return "MISLEADING"
    
    # Fallback to rating value if available
    rating_value = rating.get("ratingValue")
    if rating_value is not None:
        # If ratingValue > best_rating/2, consider it TRUE
        best = rating.get("bestRating", 1)
        if float(rating_value) > float(best) / 2:
            return "TRUE"
        else:
            return "FALSE"
    
    return "MISLEADING"  # Default


def extract_tags(claim_text: str, verdict: str) -> List[str]:
    """
    Extract tags from claim text and verdict for categorization.
    
    Args:
        claim_text: The claim text
        verdict: The verdict ("TRUE", "FALSE", "MISLEADING")
        
    Returns:
        List[str]: Extracted tags
    """
    tags = [verdict.lower()]
    
    # Add category tags based on claim content
    claim_lower = claim_text.lower()
    
    category_keywords = {
        "health": ["vaccine", "covid", "flu", "disease", "medicine", "health", "symptom", "treatment", "cancer", "autism"],
        "election": ["election", "vote", "voter", "ballot", "candidate", "poll", "voting"],
        "disaster": ["earthquake", "flood", "storm", "hurricane", "tornado", "tsunami", "disaster", "emergency"],
        "politics": ["politician", "senator", "congressman", "parliament", "president", "government"],
        "science": ["study", "research", "scientist", "climate", "physics", "chemistry"],
        "technology": ["tech", "ai", "algorithm", "software", "computer", "internet"],
        "economy": ["economy", "stock", "market", "business", "money", "price"],
        "immigration": ["immigrant", "immigration", "border", "refugee"],
    }
    
    for category, keywords in category_keywords.items():
        if any(kw in claim_lower for kw in keywords):
            tags.append(category)
            break  # Only add one category
    
    return tags


def fetch_factchecks_from_google(
    query: str,
    language_code: str = "en",
    max_claims: int = 10
) -> List[Dict[str, Any]]:
    """
    Fetch fact checks from Google Fact Check Tools API.
    
    Args:
        query: Search query (e.g., "vaccine", "election")
        language_code: Language code (default: "en")
        max_claims: Maximum number of claims to fetch
        
    Returns:
        List[Dict[str, Any]]: List of normalized fact checks
        
    Raises:
        ValueError: If API key is not configured
        requests.RequestException: If API request fails
    """
    api_key = get_google_factcheck_api_key()
    if not api_key:
        raise ValueError(
            "GOOGLE_FACTCHECK_API_KEY environment variable not set. "
            "Get one from: https://console.developers.google.com/"
        )
    
    logger.info(f"Fetching fact checks from Google API for query: '{query}' (language: {language_code})")
    
    params = {
        "key": api_key,
        "query": query,
        "languageCode": language_code,
        "maxClaims": max_claims
    }
    
    try:
        response = requests.get(GOOGLE_FACTCHECK_API_URL, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        claim_reviews = data.get("claims", [])
        
        logger.info(f"Retrieved {len(claim_reviews)} claims from Google API")
        
        # Normalize the response
        normalized = normalize_google_response(claim_reviews)
        
        logger.info(f"Successfully normalized {len(normalized)} fact checks")
        return normalized
        
    except requests.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error fetching from Google Fact Check API: {str(e)}")
        raise


def ingest_factchecks_from_google(
    query: str,
    language_code: str = "en",
    max_claims: int = 10
) -> int:
    """
    Fetch fact checks from Google API and upsert to verified_claims collection.
    
    Args:
        query: Search query
        language_code: Language code (default: "en")
        max_claims: Maximum number of claims to fetch
        
    Returns:
        int: Number of fact checks successfully ingested
        
    Raises:
        Exception: If fetch or ingestion error occurs
    """
    logger.info(f"Ingesting fact checks from Google API (query: '{query}')")
    
    try:
        # Fetch from Google API
        fact_checks = fetch_factchecks_from_google(
            query=query,
            language_code=language_code,
            max_claims=max_claims
        )
        
        # Transform to document format for vector store
        documents = []
        for fact_check in fact_checks:
            # Create text content from available fields
            text_parts = []
            if 'claim' in fact_check:
                text_parts.append(f"Claim: {fact_check['claim']}")
            if 'verdict' in fact_check:
                text_parts.append(f"Verdict: {fact_check['verdict']}")
            if 'explanation' in fact_check:
                text_parts.append(f"Explanation: {fact_check['explanation']}")
            
            text = ' '.join(text_parts) if text_parts else str(fact_check)
            
            # Prepare metadata
            metadata = {k: v for k, v in fact_check.items() if k not in ['id', 'text']}
            metadata['source'] = 'google_factcheck'
            metadata['type'] = 'fact_check'
            
            documents.append({
                'id': fact_check['id'],
                'text': text,
                'metadata': metadata
            })
        
        if documents:
            upsert_documents('verified_claims', documents)
            logger.info(f"Successfully ingested {len(documents)} fact checks from Google API")
        else:
            logger.warning("No valid fact checks retrieved from Google API")
        
        return len(documents)
        
    except Exception as e:
        logger.error(f"Error ingesting fact checks from Google API: {str(e)}")
        raise


def ingest_multiple_queries_from_google(
    queries: List[str],
    language_code: str = "en",
    max_claims_per_query: int = 10
) -> Dict[str, int]:
    """
    Fetch fact checks from Google API for multiple queries.
    
    Useful for bulk ingestion across multiple topics.
    
    Args:
        queries: List of search queries
        language_code: Language code
        max_claims_per_query: Max claims per query
        
    Returns:
        Dict[str, int]: Results per query
    """
    logger.info(f"Ingesting from Google API for {len(queries)} queries")
    
    results = {}
    total = 0
    
    for query in queries:
        try:
            count = ingest_factchecks_from_google(
                query=query,
                language_code=language_code,
                max_claims=max_claims_per_query
            )
            results[query] = count
            total += count
        except Exception as e:
            logger.error(f"Failed to ingest for query '{query}': {str(e)}")
            results[query] = 0
    
    logger.info(f"Ingestion completed. Total: {total} claims across {len(queries)} queries")
    return results
