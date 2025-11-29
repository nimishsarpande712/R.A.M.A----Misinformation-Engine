"""
MCP Client for fetching data from the MCP server.

This module provides functions to interact with the MCP server endpoints
for fetching news, government bulletins, fact-checks, and social media samples.
"""

import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional


# Configuration
MCP_BASE_URL = os.getenv("MCP_BASE_URL", "http://localhost:3333")
# Timeout for MCP requests (seconds). Lowered to fail fast on local dev when MCP is down.
DEFAULT_TIMEOUT = int(os.getenv("MCP_TIMEOUT", "5"))


def _get_session() -> requests.Session:
    """
    Create a requests session with retry logic.
    
    Returns:
        requests.Session: Configured session with retry strategy
    """
    session = requests.Session()
    
    # Configure retry strategy
    # Keep retries low for local development so failures surface quickly
    retry_strategy = Retry(
        total=1,  # fewer retries to avoid long hangs when MCP is down
        backoff_factor=0.5,  # short backoff
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session


def fetch_news(topic: Optional[str] = None, limit: int = 50) -> list[dict]:
    """
    Fetch news articles from the MCP server.
    
    Args:
        topic: Optional topic filter for news articles
        limit: Maximum number of articles to fetch (default: 50)
    
    Returns:
        list[dict]: List of news article dictionaries
    
    Raises:
        ValueError: If the response is malformed or missing expected data
        requests.RequestException: If the request fails
    """
    session = _get_session()
    url = f"{MCP_BASE_URL}/tools/news.get_latest"
    
    params = {"limit": limit}
    if topic:
        params["topic"] = topic
    
    try:
        response = session.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        
        if not isinstance(data, dict):
            raise ValueError(f"Expected dict response, got {type(data).__name__}")
        
        if "items" not in data:
            raise ValueError("Response missing 'items' field")
        
        if not isinstance(data["items"], list):
            raise ValueError(f"Expected 'items' to be list, got {type(data['items']).__name__}")
        
        return data["items"]
    
    except requests.RequestException as e:
        raise requests.RequestException(f"Failed to fetch news: {str(e)}") from e


def fetch_gov_bulletins(limit: int = 50) -> list[dict]:
    """
    Fetch government bulletins from the MCP server.
    
    Args:
        limit: Maximum number of bulletins to fetch (default: 50)
    
    Returns:
        list[dict]: List of government bulletin dictionaries
    
    Raises:
        ValueError: If the response is malformed or missing expected data
        requests.RequestException: If the request fails
    """
    session = _get_session()
    url = f"{MCP_BASE_URL}/tools/gov.get_bulletins"
    
    params = {"limit": limit}
    
    try:
        response = session.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        
        if not isinstance(data, dict):
            raise ValueError(f"Expected dict response, got {type(data).__name__}")
        
        if "items" not in data:
            raise ValueError("Response missing 'items' field")
        
        if not isinstance(data["items"], list):
            raise ValueError(f"Expected 'items' to be list, got {type(data['items']).__name__}")
        
        return data["items"]
    
    except requests.RequestException as e:
        raise requests.RequestException(f"Failed to fetch government bulletins: {str(e)}") from e


def fetch_factchecks(limit: int = 50) -> list[dict]:
    """
    Fetch fact-checks from the MCP server.
    
    Args:
        limit: Maximum number of fact-checks to fetch (default: 50)
    
    Returns:
        list[dict]: List of fact-check dictionaries
    
    Raises:
        ValueError: If the response is malformed or missing expected data
        requests.RequestException: If the request fails
    """
    session = _get_session()
    url = f"{MCP_BASE_URL}/tools/factcheck.get_recent"
    
    params = {"limit": limit}
    
    try:
        response = session.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        
        if not isinstance(data, dict):
            raise ValueError(f"Expected dict response, got {type(data).__name__}")
        
        if "items" not in data:
            raise ValueError("Response missing 'items' field")
        
        if not isinstance(data["items"], list):
            raise ValueError(f"Expected 'items' to be list, got {type(data['items']).__name__}")
        
        return data["items"]
    
    except requests.RequestException as e:
        raise requests.RequestException(f"Failed to fetch fact-checks: {str(e)}") from e


def fetch_social_samples(limit: int = 50) -> list[dict]:
    """
    Fetch social media samples from the MCP server.
    
    Args:
        limit: Maximum number of samples to fetch (default: 50)
    
    Returns:
        list[dict]: List of social media sample dictionaries
    
    Raises:
        ValueError: If the response is malformed or missing expected data
        requests.RequestException: If the request fails
    """
    session = _get_session()
    url = f"{MCP_BASE_URL}/tools/social.get_samples"
    
    params = {"limit": limit}
    
    try:
        response = session.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        
        if not isinstance(data, dict):
            raise ValueError(f"Expected dict response, got {type(data).__name__}")
        
        if "items" not in data:
            raise ValueError("Response missing 'items' field")
        
        if not isinstance(data["items"], list):
            raise ValueError(f"Expected 'items' to be list, got {type(data['items']).__name__}")
        
        return data["items"]
    
    except requests.RequestException as e:
        raise requests.RequestException(f"Failed to fetch social samples: {str(e)}") from e


# Test function for quick verification
if __name__ == "__main__":
    """Quick test of MCP client functions."""
    print(f"Testing MCP client with base URL: {MCP_BASE_URL}")
    
    try:
        print("\n1. Fetching news...")
        news = fetch_news(limit=5)
        print(f"   ✓ Fetched {len(news)} news articles")
        if news:
            print(f"   Sample: {news[0].get('title', 'N/A')[:80]}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    try:
        print("\n2. Fetching government bulletins...")
        bulletins = fetch_gov_bulletins(limit=5)
        print(f"   ✓ Fetched {len(bulletins)} bulletins")
        if bulletins:
            print(f"   Sample: {bulletins[0].get('title', 'N/A')[:80]}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    try:
        print("\n3. Fetching fact-checks...")
        factchecks = fetch_factchecks(limit=5)
        print(f"   ✓ Fetched {len(factchecks)} fact-checks")
        if factchecks:
            print(f"   Sample: {factchecks[0].get('title', 'N/A')[:80]}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    try:
        print("\n4. Fetching social samples...")
        social = fetch_social_samples(limit=5)
        print(f"   ✓ Fetched {len(social)} social samples")
        if social:
            print(f"   Sample: {social[0].get('text', 'N/A')[:80]}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n✓ MCP client test complete")
