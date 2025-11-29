"""
MongoDB integration for RAMA system.

Manages collections:
- verified_claims: Fact-checked claims
- news_items: Ingested news articles with chunks
- claim_logs: Request/response logs for /verify
- ingest_logs: Ingestion operation logs
- feedback: User feedback on verdicts
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import PyMongoError
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "rama_db")


class MongoDBClient:
    """MongoDB client singleton for RAMA system."""
    
    _instance: Optional['MongoDBClient'] = None
    _client: Optional[MongoClient] = None
    _db: Any = None  # Database object with dynamic collection attributes
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize MongoDB connection and collections."""
        try:
            client = MongoClient(MONGODB_URI)
            self._client = client
            self._db = client[MONGODB_DATABASE]
            
            # Test connection
            client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {MONGODB_DATABASE}")
            
            # Create indexes
            self._create_indexes()
            
        except PyMongoError as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def _create_indexes(self):
        """Create indexes for efficient querying."""
        try:
            # verified_claims indexes
            self._db.verified_claims.create_index([("claim", ASCENDING)])
            self._db.verified_claims.create_index([("language", ASCENDING)])
            self._db.verified_claims.create_index([("created_at", DESCENDING)])
            self._db.verified_claims.create_index([("tags", ASCENDING)])
            
            # news_items indexes
            self._db.news_items.create_index([("url", ASCENDING)], unique=True)
            self._db.news_items.create_index([("source", ASCENDING)])
            self._db.news_items.create_index([("published_at", DESCENDING)])
            self._db.news_items.create_index([("language", ASCENDING)])
            
            # claim_logs indexes
            self._db.claim_logs.create_index([("timestamp", DESCENDING)])
            self._db.claim_logs.create_index([("model_used", ASCENDING)])
            self._db.claim_logs.create_index([("user_hash", ASCENDING)])
            
            # ingest_logs indexes
            self._db.ingest_logs.create_index([("timestamp", DESCENDING)])
            self._db.ingest_logs.create_index([("source", ASCENDING)])
            
            # feedback indexes
            self._db.feedback.create_index([("timestamp", DESCENDING)])
            
            logger.info("MongoDB indexes created successfully")
            
        except PyMongoError as e:
            logger.warning(f"Failed to create indexes: {e}")
    
    @property
    def db(self):
        """Get database instance."""
        return self._db
    
    def is_connected(self) -> bool:
        """Check if MongoDB is connected."""
        try:
            if self._client:
                self._client.admin.command('ping')
                return True
            return False
        except:
            return False


# Singleton instance
mongo_client = MongoDBClient()


# ========================================
# VERIFIED CLAIMS OPERATIONS
# ========================================

def insert_verified_claim(claim: str, verdict: str, explanation: str, 
                          source: str, url: str, tags: Optional[List[str]] = None,
                          language: str = "en") -> Optional[str]:
    """
    Insert a verified claim into the database.
    
    Args:
        claim: The claim text
        verdict: Verdict (true, false, misleading, unverified)
        explanation: Explanation of the verdict
        source: Source of the fact-check (e.g., AltNews, PIB)
        url: URL to the fact-check article
        tags: Optional list of tags
        language: ISO 639-1 language code
        
    Returns:
        str: Inserted document ID or None if failed
    """
    try:
        doc = {
            "claim": claim,
            "verdict": verdict.lower(),
            "explanation": explanation,
            "source": source,
            "url": url,
            "tags": tags or [],
            "language": language,
            "created_at": datetime.utcnow()
        }
        result = mongo_client.db.verified_claims.insert_one(doc)
        logger.info(f"Inserted verified claim: {result.inserted_id}")
        return str(result.inserted_id)
    except PyMongoError as e:
        logger.error(f"Failed to insert verified claim: {e}")
        return None


def get_verified_claims(limit: int = 100, language: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve verified claims from database.
    
    Args:
        limit: Maximum number of claims to retrieve
        language: Optional language filter
        
    Returns:
        List of verified claim documents
    """
    try:
        query = {}
        if language:
            query["language"] = language
            
        claims = list(mongo_client.db.verified_claims.find(
            query,
            limit=limit
        ).sort("created_at", DESCENDING))
        
        # Convert ObjectId to string
        for claim in claims:
            claim["_id"] = str(claim["_id"])
            
        return claims
    except PyMongoError as e:
        logger.error(f"Failed to retrieve verified claims: {e}")
        return []


# ========================================
# USER QUERY HISTORY OPERATIONS
# ========================================

def insert_user_query_history(
    user_id: str,
    query_text: str,
    verdict: str,
    confidence: float,
    sources_used: List[Dict[str, Any]],
    category: Optional[str] = None,
    language: str = "en",
    raw_response: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """
    Insert user query into history for tracking.
    
    Args:
        user_id: User identifier (session ID or hashed IP)
        query_text: The claim/query text
        verdict: Returned verdict
        confidence: Confidence score
        sources_used: List of sources used
        category: Query category
        language: Query language
        raw_response: Full response object
        
    Returns:
        str: Inserted document ID or None if failed
    """
    try:
        doc = {
            "user_id": user_id,
            "query_text": query_text,
            "verdict": verdict,
            "confidence": confidence,
            "sources_used": sources_used,
            "sources_count": len(sources_used),
            "category": category,
            "language": language,
            "raw_response": raw_response,
            "timestamp": datetime.utcnow()
        }
        result = mongo_client.db.user_query_history.insert_one(doc)
        logger.info(f"Inserted user query history: {result.inserted_id}")
        return str(result.inserted_id)
    except PyMongoError as e:
        logger.error(f"Failed to insert user query history: {e}")
        return None


def get_user_query_history(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Retrieve user's query history.
    
    Args:
        user_id: User identifier
        limit: Maximum number of queries to retrieve
        
    Returns:
        List of query history documents
    """
    try:
        queries = list(mongo_client.db.user_query_history.find(
            {"user_id": user_id},
            limit=limit
        ).sort("timestamp", DESCENDING))
        
        for query in queries:
            query["_id"] = str(query["_id"])
            
        return queries
    except PyMongoError as e:
        logger.error(f"Failed to retrieve user query history: {e}")
        return []


# ========================================
# NEWS ITEMS OPERATIONS
# ========================================

def insert_news_item(title: str, url: str, body: str, source: str,
                     published_at: Optional[str] = None, chunks: Optional[List[Dict]] = None,
                     language: str = "en") -> Optional[str]:
    """
    Insert a news item into the database.
    
    Args:
        title: Article title
        url: Article URL (must be unique)
        body: Full article text
        source: News source
        published_at: ISO timestamp
        chunks: List of text chunks with IDs
        language: ISO 639-1 language code
        
    Returns:
        str: Inserted document ID or None if failed
    """
    try:
        doc = {
            "title": title,
            "url": url,
            "body": body,
            "source": source,
            "published_at": published_at or datetime.utcnow().isoformat(),
            "chunks": chunks or [],
            "language": language,
            "ingested_at": datetime.utcnow()
        }
        result = mongo_client.db.news_items.insert_one(doc)
        logger.info(f"Inserted news item: {result.inserted_id}")
        return str(result.inserted_id)
    except PyMongoError as e:
        if "duplicate key" in str(e):
            logger.warning(f"News item already exists: {url}")
        else:
            logger.error(f"Failed to insert news item: {e}")
        return None


def news_item_exists(url: str) -> bool:
    """Check if a news item already exists."""
    try:
        return mongo_client.db.news_items.find_one({"url": url}) is not None
    except PyMongoError as e:
        logger.error(f"Failed to check news item existence: {e}")
        return False


def get_news_items(limit: int = 100, source: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve news items from database.
    
    Args:
        limit: Maximum number of items to retrieve
        source: Optional source filter
        
    Returns:
        List of news item documents
    """
    try:
        query = {}
        if source:
            query["source"] = source
            
        items = list(mongo_client.db.news_items.find(
            query,
            limit=limit
        ).sort("published_at", DESCENDING))
        
        # Convert ObjectId to string
        for item in items:
            item["_id"] = str(item["_id"])
            
        return items
    except PyMongoError as e:
        logger.error(f"Failed to retrieve news items: {e}")
        return []


# ========================================
# CLAIM LOGS OPERATIONS
# ========================================

def log_claim_verification(request: Dict[str, Any], response: Dict[str, Any],
                           model_used: str, latency_ms: float,
                           user_hash: Optional[str] = None) -> Optional[str]:
    """
    Log a claim verification request and response.
    
    Args:
        request: Request payload
        response: Response payload
        model_used: Model name (gemini, ollama, etc.)
        latency_ms: Request latency in milliseconds
        user_hash: Optional hashed user identifier
        
    Returns:
        str: Inserted document ID or None if failed
    """
    try:
        doc = {
            "request": request,
            "response": response,
            "model_used": model_used,
            "latency_ms": latency_ms,
            "user_hash": user_hash,
            "timestamp": datetime.utcnow()
        }
        result = mongo_client.db.claim_logs.insert_one(doc)
        return str(result.inserted_id)
    except PyMongoError as e:
        logger.error(f"Failed to log claim verification: {e}")
        return None


def get_recent_claim_logs(limit: int = 20) -> List[Dict[str, Any]]:
    """
    Retrieve recent claim logs.
    
    Args:
        limit: Maximum number of logs to retrieve
        
    Returns:
        List of claim log documents
    """
    try:
        logs = list(mongo_client.db.claim_logs.find(
            {},
            limit=limit
        ).sort("timestamp", DESCENDING))
        
        # Convert ObjectId to string
        for log in logs:
            log["_id"] = str(log["_id"])
            
        return logs
    except PyMongoError as e:
        logger.error(f"Failed to retrieve claim logs: {e}")
        return []


# ========================================
# INGEST LOGS OPERATIONS
# ========================================

def log_ingestion(source: str, count: int, errors: Optional[List[str]] = None) -> Optional[str]:
    """
    Log an ingestion operation.
    
    Args:
        source: Source name (news, gov, factcheck, social)
        count: Number of items ingested
        errors: List of error messages
        
    Returns:
        str: Inserted document ID or None if failed
    """
    try:
        doc = {
            "source": source,
            "count": count,
            "errors": errors or [],
            "timestamp": datetime.utcnow()
        }
        result = mongo_client.db.ingest_logs.insert_one(doc)
        return str(result.inserted_id)
    except PyMongoError as e:
        logger.error(f"Failed to log ingestion: {e}")
        return None


def get_last_ingestion_time() -> Optional[datetime]:
    """Get the timestamp of the last successful ingestion."""
    try:
        log = mongo_client.db.ingest_logs.find_one(
            {},
            sort=[("timestamp", DESCENDING)]
        )
        return log["timestamp"] if log else None
    except PyMongoError as e:
        logger.error(f"Failed to get last ingestion time: {e}")
        return None


# ========================================
# FEEDBACK OPERATIONS
# ========================================

def insert_feedback(claim_text: str, verdict_returned: str, comment: str,
                    screenshot_url: Optional[str] = None) -> Optional[str]:
    """
    Insert user feedback about a verdict.
    
    Args:
        claim_text: The original claim text
        verdict_returned: The verdict that was returned
        comment: User's feedback comment
        screenshot_url: Optional screenshot URL
        
    Returns:
        str: Inserted document ID or None if failed
    """
    try:
        doc = {
            "claim_text": claim_text,
            "verdict_returned": verdict_returned,
            "comment": comment,
            "screenshot_url": screenshot_url,
            "timestamp": datetime.utcnow()
        }
        result = mongo_client.db.feedback.insert_one(doc)
        logger.info(f"Inserted feedback: {result.inserted_id}")
        return str(result.inserted_id)
    except PyMongoError as e:
        logger.error(f"Failed to insert feedback: {e}")
        return None


def get_feedback(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Retrieve user feedback.
    
    Args:
        limit: Maximum number of feedback items to retrieve
        
    Returns:
        List of feedback documents
    """
    try:
        feedback = list(mongo_client.db.feedback.find(
            {},
            limit=limit
        ).sort("timestamp", DESCENDING))
        
        # Convert ObjectId to string
        for item in feedback:
            item["_id"] = str(item["_id"])
            
        return feedback
    except PyMongoError as e:
        logger.error(f"Failed to retrieve feedback: {e}")
        return []
