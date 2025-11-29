"""
Enhanced Ingestion Module for RAMA System.
Orchestrates data ingestion from MCP server and processes for vector storage.
"""

import os
import logging
import hashlib
import requests
from typing import Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv

from app.embeddings_v2 import get_embedding, EmbeddingException
from app.vector_store import upsert_documents
from app.mongodb import (
    insert_verified_claim,
    insert_news_item,
    news_item_exists,
    log_ingestion
)
from app.supabase_db import (
    SupabasePostgresConnection,
    create_news_data_table,
    insert_news_data
)

load_dotenv()

logger = logging.getLogger(__name__)

# Configuration
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8001")
NEWS_FETCH_LIMIT = int(os.getenv("NEWS_FETCH_LIMIT", "50"))
GOV_FETCH_LIMIT = int(os.getenv("GOV_FETCH_LIMIT", "30"))
FACTCHECK_FETCH_LIMIT = int(os.getenv("FACTCHECK_FETCH_LIMIT", "20"))
SOCIAL_FETCH_LIMIT = int(os.getenv("SOCIAL_FETCH_LIMIT", "10"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
ENABLE_DEDUPLICATION = os.getenv("ENABLE_DEDUPLICATION", "1") == "1"
HTTP_REQUEST_TIMEOUT = int(os.getenv("HTTP_REQUEST_TIMEOUT", "10"))


def _generate_content_hash(text: str) -> str:
    """Generate SHA256 hash of normalized text for deduplication."""
    normalized = text.strip().lower().replace("\n", " ").replace("\r", " ")
    return hashlib.sha256(normalized.encode()).hexdigest()


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[Dict[str, Any]]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: Text to chunk
        chunk_size: Target chunk size in characters
        overlap: Overlap size in characters
        
    Returns:
        List of chunk dictionaries with chunk_id and text
    """
    chunks = []
    text = text.strip()
    
    if len(text) <= chunk_size:
        return [{"chunk_id": 0, "text": text}]
    
    start = 0
    chunk_id = 0
    
    while start < len(text):
        end = min(start + chunk_size, len(text))
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for period, question mark, or exclamation point
            last_period = text.rfind(".", start, end)
            last_question = text.rfind("?", start, end)
            last_exclaim = text.rfind("!", start, end)
            
            boundary = max(last_period, last_question, last_exclaim)
            if boundary > start + chunk_size // 2:  # Only if boundary is not too early
                end = boundary + 1
        
        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append({
                "chunk_id": chunk_id,
                "text": chunk_text
            })
            chunk_id += 1
        
        # Move start forward with overlap
        start = end - overlap if end < len(text) else end
    
    return chunks


def ingest_news(force: bool = False) -> Dict[str, Any]:
    """
    Ingest news articles from MCP server.
    
    Args:
        force: Force re-ingestion even if exists
        
    Returns:
        Dict with count and errors
    """
    logger.info("Ingesting news articles...")
    
    errors = []
    ingested_count = 0
    skipped_count = 0
    
    try:
        # Fetch from MCP server
        url = f"{MCP_SERVER_URL}/tools/news.get_latest"
        params = {"limit": NEWS_FETCH_LIMIT}
        
        response = requests.get(url, params=params, timeout=HTTP_REQUEST_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        items = data.get("items", [])
        
        logger.info(f"Fetched {len(items)} news articles from MCP")
        
        # Process each item
        for item in items:
            try:
                url = item.get("url", "")
                
                # Check for duplicates
                if not force and ENABLE_DEDUPLICATION:
                    if news_item_exists(url):
                        skipped_count += 1
                        continue
                
                # Chunk the article
                body = item.get("text", "")
                chunks = _chunk_text(body)
                
                # Insert into MongoDB
                mongo_id = insert_news_item(
                    title=item.get("title", ""),
                    url=url,
                    body=body,
                    source=item.get("source", "Unknown"),
                    published_at=item.get("published_at"),
                    chunks=chunks,
                    language=item.get("language", "en")
                )
                
                if not mongo_id:
                    continue
                
                # Also insert into Supabase for redundancy
                try:
                    with SupabasePostgresConnection() as db:
                        create_news_data_table(db)
                        insert_news_data(
                            db_connection=db,
                            title=item.get("title", ""),
                            url=url,
                            source=item.get("source", "Unknown"),
                            body=body,
                            published_at=item.get("published_at"),
                            language=item.get("language", "en"),
                            category=item.get("category"),
                            metadata=item
                        )
                except Exception as e:
                    logger.warning(f"Failed to insert to Supabase: {e}")
                
                # Prepare documents for vector store
                docs = []
                for chunk in chunks:
                    doc_id = f"{mongo_id}_{chunk['chunk_id']}"
                    docs.append({
                        "id": doc_id,
                        "text": chunk["text"],
                        "metadata": {
                            "source": item.get("source", "Unknown"),
                            "url": url,
                            "published_at": item.get("published_at", ""),
                            "language": item.get("language", "en"),
                            "chunk_id": chunk["chunk_id"],
                            "mongo_id": mongo_id
                        }
                    })
                
                # Upsert to vector store
                if docs:
                    upsert_documents("news_articles", docs)
                    ingested_count += 1
                
            except Exception as e:
                error_msg = f"Failed to process news item {item.get('url', 'unknown')}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        logger.info(f"News ingestion complete: {ingested_count} ingested, {skipped_count} skipped")
        log_ingestion("news", ingested_count, errors)
        
        return {
            "count": ingested_count,
            "skipped": skipped_count,
            "errors": errors
        }
        
    except Exception as e:
        error_msg = f"News ingestion failed: {e}"
        logger.error(error_msg)
        log_ingestion("news", 0, [error_msg])
        return {"count": 0, "skipped": 0, "errors": [error_msg]}


def ingest_gov_bulletins(force: bool = False) -> Dict[str, Any]:
    """
    Ingest government bulletins from MCP server.
    
    Args:
        force: Force re-ingestion
        
    Returns:
        Dict with count and errors
    """
    logger.info("Ingesting government bulletins...")
    
    errors = []
    ingested_count = 0
    
    try:
        url = f"{MCP_SERVER_URL}/tools/gov.get_bulletins"
        params = {"limit": GOV_FETCH_LIMIT}
        
        response = requests.get(url, params=params, timeout=HTTP_REQUEST_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        items = data.get("items", [])
        
        logger.info(f"Fetched {len(items)} government bulletins from MCP")
        
        docs = []
        for item in items:
            try:
                docs.append({
                    "id": item.get("id", _generate_content_hash(item.get("text", ""))),
                    "text": item.get("text", ""),
                    "metadata": {
                        "source": item.get("source", "Government"),
                        "url": item.get("url", ""),
                        "published_at": item.get("published_at", ""),
                        "language": item.get("language", "en")
                    }
                })
            except Exception as e:
                error_msg = f"Failed to process gov bulletin: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        if docs:
            upsert_documents("gov_bulletins", docs)
            ingested_count = len(docs)
        
        logger.info(f"Gov bulletins ingestion complete: {ingested_count} ingested")
        log_ingestion("gov", ingested_count, errors)
        
        return {"count": ingested_count, "errors": errors}
        
    except Exception as e:
        error_msg = f"Gov bulletins ingestion failed: {e}"
        logger.error(error_msg)
        log_ingestion("gov", 0, [error_msg])
        return {"count": 0, "errors": [error_msg]}


def ingest_fact_checks(force: bool = False) -> Dict[str, Any]:
    """
    Ingest fact-checks from MCP server.
    
    Args:
        force: Force re-ingestion
        
    Returns:
        Dict with count and errors
    """
    logger.info("Ingesting fact-checks...")
    
    errors = []
    ingested_count = 0
    
    try:
        url = f"{MCP_SERVER_URL}/tools/factcheck.get_recent"
        params = {"limit": FACTCHECK_FETCH_LIMIT}
        
        response = requests.get(url, params=params, timeout=HTTP_REQUEST_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        items = data.get("items", [])
        
        logger.info(f"Fetched {len(items)} fact-checks from MCP")
        
        docs = []
        for item in items:
            try:
                # Insert into MongoDB
                mongo_id = insert_verified_claim(
                    claim=item.get("claim", ""),
                    verdict=item.get("verdict", "unverified"),
                    explanation=item.get("explanation", ""),
                    source=item.get("source", "FactCheck"),
                    url=item.get("url", ""),
                    tags=item.get("tags", []),
                    language=item.get("language", "en")
                )
                
                # Add to vector store
                docs.append({
                    "id": mongo_id or _generate_content_hash(item.get("claim", "")),
                    "text": item.get("claim", ""),
                    "metadata": {
                        "verdict": item.get("verdict", "unverified"),
                        "explanation": item.get("explanation", ""),
                        "source": item.get("source", "FactCheck"),
                        "url": item.get("url", ""),
                        "language": item.get("language", "en")
                    }
                })
            except Exception as e:
                error_msg = f"Failed to process fact-check: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        if docs:
            upsert_documents("verified_claims", docs)
            ingested_count = len(docs)
        
        logger.info(f"Fact-checks ingestion complete: {ingested_count} ingested")
        log_ingestion("factcheck", ingested_count, errors)
        
        return {"count": ingested_count, "errors": errors}
        
    except Exception as e:
        error_msg = f"Fact-checks ingestion failed: {e}"
        logger.error(error_msg)
        log_ingestion("factcheck", 0, [error_msg])
        return {"count": 0, "errors": [error_msg]}


def ingest_social(force: bool = False) -> Dict[str, Any]:
    """
    Ingest social media posts from MCP server.
    
    Args:
        force: Force re-ingestion
        
    Returns:
        Dict with count and errors
    """
    logger.info("Ingesting social media posts...")
    
    errors = []
    ingested_count = 0
    
    try:
        url = f"{MCP_SERVER_URL}/tools/social.get_samples"
        params = {"limit": SOCIAL_FETCH_LIMIT}
        
        response = requests.get(url, params=params, timeout=HTTP_REQUEST_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        items = data.get("items", [])
        
        logger.info(f"Fetched {len(items)} social posts from MCP")
        
        docs = []
        for item in items:
            try:
                docs.append({
                    "id": item.get("id", _generate_content_hash(item.get("text", ""))),
                    "text": item.get("text", ""),
                    "metadata": {
                        "source": item.get("source", "Social"),
                        "url": item.get("url", ""),
                        "published_at": item.get("published_at", ""),
                        "language": item.get("language", "en")
                    }
                })
            except Exception as e:
                error_msg = f"Failed to process social post: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        if docs:
            upsert_documents("social_posts", docs)
            ingested_count = len(docs)
        
        logger.info(f"Social posts ingestion complete: {ingested_count} ingested")
        log_ingestion("social", ingested_count, errors)
        
        return {"count": ingested_count, "errors": errors}
        
    except Exception as e:
        error_msg = f"Social posts ingestion failed: {e}"
        logger.error(error_msg)
        log_ingestion("social", 0, [error_msg])
        return {"count": 0, "errors": [error_msg]}


def ingest_all_sources(force: bool = False) -> Dict[str, Any]:
    """
    Ingest from all sources.
    
    Args:
        force: Force re-ingestion
        
    Returns:
        Dict with aggregated counts and errors
    """
    logger.info("=" * 60)
    logger.info("Starting full ingestion from all sources...")
    logger.info("=" * 60)
    
    results = {
        "ingested": {},
        "errors": []
    }
    
    # Ingest news
    news_result = ingest_news(force=force)
    results["ingested"]["news"] = news_result["count"]
    results["errors"].extend(news_result.get("errors", []))
    
    # Ingest gov bulletins
    gov_result = ingest_gov_bulletins(force=force)
    results["ingested"]["gov"] = gov_result["count"]
    results["errors"].extend(gov_result.get("errors", []))
    
    # Ingest fact-checks
    factcheck_result = ingest_fact_checks(force=force)
    results["ingested"]["factchecks"] = factcheck_result["count"]
    results["errors"].extend(factcheck_result.get("errors", []))
    
    # Ingest social
    social_result = ingest_social(force=force)
    results["ingested"]["social"] = social_result["count"]
    results["errors"].extend(social_result.get("errors", []))
    
    total = sum(results["ingested"].values())
    
    logger.info("=" * 60)
    logger.info(f"Ingestion complete. Total: {total} items")
    logger.info(f"Breakdown: {results['ingested']}")
    logger.info(f"Errors: {len(results['errors'])}")
    logger.info("=" * 60)
    
    return results
