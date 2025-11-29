"""
Module for ingesting news data from various sources.
"""

import json
import logging
import os
from typing import Dict, List, Optional, Any

from . import mcp_client
from .vector_store import upsert_documents
from .google_factcheck_ingestion import ingest_multiple_queries_from_google

logger = logging.getLogger(__name__)


def ingest_fact_checks_from_json(path: str = "data/fact_checks.json") -> int:
    """
    Load fact checks from local JSON file and upsert to verified_claims collection.
    
    Args:
        path: Path to the JSON file containing fact check data
        
    Returns:
        int: Number of fact checks successfully ingested
        
    Raises:
        FileNotFoundError: If the JSON file doesn't exist
        json.JSONDecodeError: If the JSON file is malformed
        Exception: If ingestion error occurs
    """
    logger.info(f"Ingesting fact checks from {path}...")
    
    try:
        if not os.path.exists(path):
            logger.warning(f"Fact check file not found at {path}, skipping...")
            return 0
            
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Ensure data is a list
        if isinstance(data, dict) and 'items' in data:
            fact_checks = data['items']
        elif isinstance(data, list):
            fact_checks = data
        else:
            raise ValueError("JSON file should contain a list or dict with 'items' key")
        
        # Transform to document format for vector store
        documents = []
        for i, fact_check in enumerate(fact_checks):
            if not isinstance(fact_check, dict):
                logger.warning(f"Skipping invalid fact check at index {i}")
                continue
                
            # Generate ID if not present
            doc_id = fact_check.get('id', f"fact_check_{i}")
            
            # Create text content from available fields
            text_parts = []
            if 'claim' in fact_check:
                text_parts.append(f"Claim: {fact_check['claim']}")
            if 'verdict' in fact_check:
                text_parts.append(f"Verdict: {fact_check['verdict']}")
            if 'explanation' in fact_check:
                text_parts.append(f"Explanation: {fact_check['explanation']}")
            
            text = ' '.join(text_parts) if text_parts else str(fact_check)
            
            # Prepare metadata, convert lists to comma-separated strings
            metadata = {}
            for k, v in fact_check.items():
                if k in ['id', 'text']:
                    continue
                if isinstance(v, list):
                    metadata[k] = ', '.join(str(item) for item in v)
                else:
                    metadata[k] = v
            metadata['source'] = 'local_json'
            metadata['type'] = 'fact_check'
            
            documents.append({
                'id': doc_id,
                'text': text,
                'metadata': metadata
            })
        
        if documents:
            upsert_documents('verified_claims', documents)
            logger.info(f"Successfully ingested {len(documents)} fact checks from JSON")
        else:
            logger.warning("No valid fact checks found in JSON file")
            
        return len(documents)
        
    except Exception as e:
        logger.error(f"Error ingesting fact checks from JSON: {str(e)}")
        raise


def ingest_factchecks_from_mcp(limit: int = 100) -> int:
    """
    Fetch fact checks from MCP server and upsert to verified_claims collection.
    
    Args:
        limit: Maximum number of fact checks to fetch
        
    Returns:
        int: Number of fact checks successfully ingested
    """
    logger.info(f"Ingesting fact checks from MCP server (limit: {limit})...")
    
    try:
        fact_checks = mcp_client.fetch_factchecks(limit=limit)
        
        # Transform to document format for vector store
        documents = []
        for fact_check in fact_checks:
            if not isinstance(fact_check, dict):
                logger.warning(f"Skipping invalid fact check: {fact_check}")
                continue
                
            # Generate ID if not present
            doc_id = fact_check.get('id', f"mcp_fact_check_{len(documents)}")
            
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
            metadata['source'] = 'mcp'
            metadata['type'] = 'fact_check'
            
            documents.append({
                'id': doc_id,
                'text': text,
                'metadata': metadata
            })
        
        if documents:
            upsert_documents('verified_claims', documents)
            logger.info(f"Successfully ingested {len(documents)} fact checks from MCP")
        else:
            logger.warning("No valid fact checks received from MCP")
            
        return len(documents)
        
    except Exception as e:
        logger.warning(f"Error ingesting fact checks from MCP (continuing with other sources): {str(e)}")
        return 0


def ingest_news_from_mcp(limit: int = 200, topic: Optional[str] = None) -> int:
    """
    Fetch news articles from MCP server and upsert to news_articles collection.
    
    Args:
        limit: Maximum number of articles to fetch
        topic: Optional topic filter for news articles
        
    Returns:
        int: Number of news articles successfully ingested
    """
    logger.info(f"Ingesting news from MCP server (limit: {limit}, topic: {topic})...")
    
    try:
        news_articles = mcp_client.fetch_news(topic=topic, limit=limit)
        
        # Transform to document format for vector store
        documents = []
        for article in news_articles:
            if not isinstance(article, dict):
                logger.warning(f"Skipping invalid article: {article}")
                continue
                
            # Generate ID if not present
            doc_id = article.get('id', f"mcp_news_{len(documents)}")
            
            # Create text content from available fields
            text_parts = []
            if 'title' in article:
                text_parts.append(f"Title: {article['title']}")
            if 'content' in article:
                text_parts.append(f"Content: {article['content']}")
            if 'summary' in article:
                text_parts.append(f"Summary: {article['summary']}")
            if 'description' in article:
                text_parts.append(f"Description: {article['description']}")
            
            text = ' '.join(text_parts) if text_parts else str(article)
            
            # Prepare metadata
            metadata = {k: v for k, v in article.items() if k not in ['id', 'text']}
            metadata['source'] = 'mcp'
            metadata['type'] = 'news_article'
            if topic:
                metadata['topic'] = topic
            
            documents.append({
                'id': doc_id,
                'text': text,
                'metadata': metadata
            })
        
        if documents:
            upsert_documents('news_articles', documents)
            logger.info(f"Successfully ingested {len(documents)} news articles from MCP")
        else:
            logger.warning("No valid news articles received from MCP")
            
        return len(documents)
        
    except Exception as e:
        logger.warning(f"Error ingesting news from MCP (continuing with other sources): {str(e)}")
        return 0


def ingest_gov_from_mcp(limit: int = 100) -> int:
    """
    Fetch government bulletins from MCP server and upsert to gov_bulletins collection.
    
    Args:
        limit: Maximum number of bulletins to fetch
        
    Returns:
        int: Number of government bulletins successfully ingested
    """
    logger.info(f"Ingesting government bulletins from MCP server (limit: {limit})...")
    
    try:
        gov_bulletins = mcp_client.fetch_gov_bulletins(limit=limit)
        
        # Transform to document format for vector store
        documents = []
        for bulletin in gov_bulletins:
            if not isinstance(bulletin, dict):
                logger.warning(f"Skipping invalid bulletin: {bulletin}")
                continue
                
            # Generate ID if not present
            doc_id = bulletin.get('id', f"mcp_gov_{len(documents)}")
            
            # Create text content from available fields
            text_parts = []
            if 'title' in bulletin:
                text_parts.append(f"Title: {bulletin['title']}")
            if 'content' in bulletin:
                text_parts.append(f"Content: {bulletin['content']}")
            if 'summary' in bulletin:
                text_parts.append(f"Summary: {bulletin['summary']}")
            if 'description' in bulletin:
                text_parts.append(f"Description: {bulletin['description']}")
            
            text = ' '.join(text_parts) if text_parts else str(bulletin)
            
            # Prepare metadata
            metadata = {k: v for k, v in bulletin.items() if k not in ['id', 'text']}
            metadata['source'] = 'mcp'
            metadata['type'] = 'gov_bulletin'
            
            documents.append({
                'id': doc_id,
                'text': text,
                'metadata': metadata
            })
        
        if documents:
            upsert_documents('gov_bulletins', documents)
            logger.info(f"Successfully ingested {len(documents)} government bulletins from MCP")
        else:
            logger.warning("No valid government bulletins received from MCP")
            
        return len(documents)
        
    except Exception as e:
        logger.warning(f"Error ingesting government bulletins from MCP (continuing with other sources): {str(e)}")
        return 0


def ingest_social_from_mcp(limit: int = 100) -> int:
    """
    Fetch social media samples from MCP server and upsert to social_posts collection.
    
    Args:
        limit: Maximum number of social posts to fetch
        
    Returns:
        int: Number of social posts successfully ingested
        
    Raises:
        Exception: If MCP fetch or ingestion error occurs
    """
    logger.info(f"Ingesting social media samples from MCP server (limit: {limit})...")
    
    try:
        social_posts = mcp_client.fetch_social_samples(limit=limit)
        # Transform to document format for vector store
        documents = []
        for post in social_posts:
            if not isinstance(post, dict):
                logger.warning(f"Skipping invalid social post: {post}")
                continue
            # Generate ID if not present
            doc_id = post.get('id', f"mcp_social_{len(documents)}")
            # Create text content from available fields
            text_parts = []
            if 'content' in post:
                text_parts.append(f"Content: {post['content']}")
            if 'text' in post:
                text_parts.append(f"Text: {post['text']}")
            if 'caption' in post:
                text_parts.append(f"Caption: {post['caption']}")
            if 'description' in post:
                text_parts.append(f"Description: {post['description']}")
            text = ' '.join(text_parts) if text_parts else str(post)
            # Prepare metadata
            metadata = {k: v for k, v in post.items() if k not in ['id', 'text']}
            metadata['source'] = 'mcp'
            metadata['type'] = 'social_post'
            documents.append({
                'id': doc_id,
                'text': text,
                'metadata': metadata
            })
        if documents:
            upsert_documents('social_posts', documents)
            logger.info(f"Successfully ingested {len(documents)} social posts from MCP")
        else:
            logger.warning("No valid social posts received from MCP")
        return len(documents)
    except Exception as e:
        logger.warning(f"Error ingesting social posts from MCP (continuing with other sources): {str(e)}")
        return 0


def ingest_factchecks_from_google(
    queries: Optional[List[str]] = None,
    language_code: str = "en",
    max_claims_per_query: int = 10
) -> Dict[str, int]:
    """
    Ingest fact checks from Google Fact Check Tools API for multiple queries.
    
    Requires GOOGLE_FACTCHECK_API_KEY environment variable to be set.
    Default queries cover health, election, and disaster topics.
    
    Args:
        queries: List of search queries. If None, uses default queries.
        language_code: Language code (default: "en")
        max_claims_per_query: Max claims per query
        
    Returns:
        Dict[str, int]: Number of fact checks ingested per query
        
    Raises:
        ValueError: If API key not configured
        Exception: If ingestion error occurs
    """
    if queries is None:
        # Default queries covering multiple topics
        queries = [
            "vaccine",
            "election",
            "climate change",
            "pandemic",
            "immigration",
            "economy"
        ]
    
    logger.info(f"Ingesting fact checks from Google API for {len(queries)} queries...")
    
    try:
        results = ingest_multiple_queries_from_google(
            queries=queries,
            language_code=language_code,
            max_claims_per_query=max_claims_per_query
        )
        
        total_ingested = sum(results.values())
        logger.info(f"Successfully ingested {total_ingested} fact checks from Google API")
        return results
        
    except ValueError as e:
        logger.warning(f"Google Fact Check API not configured: {str(e)}")
        return {query: 0 for query in queries}
    except Exception as e:
        logger.error(f"Error ingesting from Google Fact Check API: {str(e)}")
        raise


def ingest_all_sources() -> Dict[str, int]:
    """
    Ingest data from all configured sources in sequence.
    
    This function calls all ingestion functions in sequence and returns
    a summary of documents ingested per collection.
    
    Returns:
        Dict[str, int]: Dictionary with counts ingested per collection
        
    Raises:
        Exception: If critical ingestion error occurs
    """
    logger.info("Starting ingestion from all sources...")
    
    results = {
        'verified_claims_json': 0,
        'verified_claims_mcp': 0,
        'verified_claims_google': 0,
        'news_articles': 0,
        'gov_bulletins': 0,
        'social_posts': 0,
        'total': 0
    }
    
    try:
        # Ingest fact checks from local JSON
        try:
            results['verified_claims_json'] = ingest_fact_checks_from_json()
        except Exception as e:
            logger.error(f"Failed to ingest fact checks from JSON: {str(e)}")
            # Continue with other sources
        
        # Ingest fact checks from MCP
        try:
            results['verified_claims_mcp'] = ingest_factchecks_from_mcp()
        except Exception as e:
            logger.error(f"Failed to ingest fact checks from MCP: {str(e)}")
            # Continue with other sources
        
        # Ingest fact checks from Google Fact Check API
        try:
            google_results = ingest_factchecks_from_google()
            results['verified_claims_google'] = sum(google_results.values())
        except Exception as e:
            logger.error(f"Failed to ingest fact checks from Google API: {str(e)}")
            # Continue with other sources
        
        # Ingest news articles from MCP
        try:
            results['news_articles'] = ingest_news_from_mcp()
        except Exception as e:
            logger.error(f"Failed to ingest news from MCP: {str(e)}")
            # Continue with other sources
        
        # Ingest government bulletins from MCP
        try:
            results['gov_bulletins'] = ingest_gov_from_mcp()
        except Exception as e:
            logger.error(f"Failed to ingest government bulletins from MCP: {str(e)}")
            # Continue with other sources
        
        # Ingest social media samples from MCP
        try:
            results['social_posts'] = ingest_social_from_mcp()
        except Exception as e:
            logger.error(f"Failed to ingest social posts from MCP: {str(e)}")
            # Continue with other sources
        
        # Calculate total
        results['total'] = sum([
            results['verified_claims_json'],
            results['verified_claims_mcp'],
            results['verified_claims_google'],
            results['news_articles'],
            results['gov_bulletins'],
            results['social_posts']
        ])
        
        logger.info(f"Ingestion completed successfully. Total documents: {results['total']}")
        logger.info(f"Breakdown: {results}")
        
        return results
        
    except Exception as e:
        logger.error(f"Critical error during ingestion: {str(e)}")
        raise
