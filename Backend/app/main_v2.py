"""
RAMA FastAPI Application - Complete Implementation per SRS.

Endpoints:
- POST /verify: Verify a claim
- POST /admin/ingest: Trigger ingestion
- GET /health: Health check
- POST /feedback: Submit user feedback
- GET /admin/logs: View recent claim logs
"""

from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import os
import hashlib

from app.engine_v2 import check_claim
from app.ingestion_v2 import ingest_all_sources
from app.model_gateway_v2 import check_model_availability, get_current_mode
from app.mongodb import (
    mongo_client,
    insert_feedback,
    get_recent_claim_logs,
    get_last_ingestion_time,
    insert_user_query_history,
    get_user_query_history
)
from app.supabase_db import (
    SupabasePostgresConnection,
    create_user_history_table,
    create_news_data_table,
    insert_user_query_history as insert_supabase_history,
    get_user_history as get_supabase_history
)

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load configuration
ADMIN_TOKEN = os.getenv("X_ADMIN_TOKEN", "dev_admin_token_change_in_production")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:5174,http://localhost:3000").split(",")


# ========================================
# PYDANTIC MODELS (SRS API CONTRACTS)
# ========================================

class ClaimRequest(BaseModel):
    """Request model for POST /verify"""
    text: str = Field(..., min_length=10, description="The claim text to verify")
    language: str = Field("en", description="ISO 639-1 language code")
    category: Optional[str] = Field(None, description="Category: health, election, disaster, other")


class Source(BaseModel):
    """Source model per SRS"""
    type: str = Field(..., description="Source type: news, factcheck, gov, social")
    source: str = Field(..., description="Source name (e.g., PIB, AltNews)")
    url: str = Field(..., description="Source URL")
    snippet: str = Field(..., description="Relevant text snippet")


class VerifyResponse(BaseModel):
    """Response model for POST /verify per SRS 7.1"""
    mode: str = Field(..., description="existing_fact_check or reasoned")
    verdict: str = Field(..., description="true, false, unverified, or misleading")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    contradiction_score: float = Field(..., ge=0.0, le=1.0, description="Contradiction score")
    explanation: str = Field(..., description="Short 1-3 line explanation")
    raw_answer: str = Field(..., description="Full model response text")
    sources_used: List[Source] = Field(..., description="List of sources used")
    timestamp: str = Field(..., description="ISO 8601 timestamp")


class IngestRequest(BaseModel):
    """Request model for POST /admin/ingest"""
    force: bool = Field(False, description="Force re-ingestion")


class IngestResponse(BaseModel):
    """Response model for POST /admin/ingest per SRS 7.2"""
    status: str = Field(..., description="ok or error")
    ingested: Dict[str, int] = Field(..., description="Counts by source")
    last_synced: str = Field(..., description="ISO 8601 timestamp")
    errors: List[str] = Field(default_factory=list, description="Error messages")


class HealthResponse(BaseModel):
    """Response model for GET /health per SRS 7.3"""
    status: str = Field(..., description="ok or degraded")
    mode: str = Field(..., description="online or offline")
    last_ingest: Optional[str] = Field(None, description="ISO 8601 timestamp")
    models: Dict[str, str] = Field(..., description="Model availability status")


class FeedbackRequest(BaseModel):
    """Request model for POST /feedback"""
    claim_text: str = Field(..., description="The original claim")
    verdict_returned: str = Field(..., description="The verdict that was returned")
    comment: str = Field(..., description="User feedback comment")
    screenshot_url: Optional[str] = Field(None, description="Optional screenshot URL")


class FeedbackResponse(BaseModel):
    """Response model for POST /feedback"""
    status: str
    message: str


# ========================================
# DEPENDENCY INJECTION
# ========================================

async def verify_admin_token(x_admin_token: str = Header(None)):
    """Verify admin token from header."""
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid admin token")
    return x_admin_token


# ========================================
# LIFESPAN EVENTS
# ========================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("=" * 60)
    logger.info("R.A.M.A. Backend Starting...")
    logger.info("=" * 60)
    
    # Test MongoDB connection
    try:
        if mongo_client.is_connected():
            logger.info("✓ MongoDB connected")
        else:
            logger.warning("✗ MongoDB connection failed")
    except Exception as e:
        logger.error(f"✗ MongoDB error: {e}")
    
    # Check model availability
    models = check_model_availability()
    logger.info(f"Model Status: {models}")
    
    # Log current mode
    mode = get_current_mode()
    logger.info(f"Operating Mode: {mode.upper()}")
    
    logger.info("=" * 60)
    logger.info("R.A.M.A. Backend Ready")
    logger.info("=" * 60)
    
    yield
    
    logger.info("R.A.M.A. Backend Shutting Down...")


# ========================================
# FASTAPI APP
# ========================================

app = FastAPI(
    title="R.A.M.A. API",
    description="Reliable Agent for Misinformation Analysis - Backend API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========================================
# API ENDPOINTS
# ========================================

@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Health check endpoint (SRS 7.3)"
)
async def health_check() -> HealthResponse:
    """
    System health check per SRS 7.3.
    
    Returns status, mode, last ingest time, and model availability.
    """
    try:
        models = check_model_availability()
        mode = get_current_mode()
        last_ingest = get_last_ingestion_time()
        
        # Determine overall status
        status = "ok" if any(v == "ok" for v in models.values()) else "degraded"
        
        return HealthResponse(
            status=status,
            mode=mode,
            last_ingest=last_ingest.isoformat() + "Z" if last_ingest else None,
            models=models
        )
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return HealthResponse(
            status="degraded",
            mode="offline",
            last_ingest=None,
            models={"gemini": "down", "openrouter": "down", "ollama": "down"}
        )


@app.post(
    "/verify",
    response_model=VerifyResponse,
    tags=["Verification"],
    summary="Verify a claim (SRS 7.1)",
    responses={
        200: {"description": "Verification successful"},
        400: {"description": "Bad request - invalid input"},
        503: {"description": "Service unavailable - all models down"},
        500: {"description": "Internal server error"}
    }
)
async def verify_claim(
    req: ClaimRequest, 
    request: Request,
    x_user_id: Optional[str] = Header(None, description="Optional User ID from Supabase Auth")
) -> VerifyResponse:
    """
    Verify a claim per SRS 7.1.
    
    Returns verdict, explanation, confidence, and sources.
    Also saves user query history to both Supabase and MongoDB.
    """
    try:
        logger.info(f"POST /verify - Claim: {req.text[:100]}...")
        
        # Determine user_id: Use header if provided (logged in), else hash IP (guest)
        if x_user_id:
            user_id = x_user_id
            logger.info(f"Using authenticated User ID: {user_id}")
        else:
            client_ip = request.client.host if request.client else "unknown"
            user_id = hashlib.sha256(f"{client_ip}".encode()).hexdigest()[:16]
            logger.info(f"Using guest IP hash: {user_id}")
        
        result = check_claim(
            claim_text=req.text,
            language=req.language,
            category=req.category
        )
        
        # Convert to response model
        response = VerifyResponse(
            mode=result["mode"],
            verdict=result["verdict"],
            confidence=result["confidence"],
            contradiction_score=result["contradiction_score"],
            explanation=result["explanation"],
            raw_answer=result["raw_answer"],
            sources_used=[Source(**s) for s in result["sources_used"]],
            timestamp=result["timestamp"]
        )
        
        # Save to MongoDB user history
        try:
            insert_user_query_history(
                user_id=user_id,
                query_text=req.text,
                verdict=result["verdict"],
                confidence=result["confidence"],
                sources_used=result["sources_used"],
                category=req.category or "other",
                language=req.language,
                raw_response=result
            )
            logger.info(f"Saved query to MongoDB for user: {user_id}")
        except Exception as e:
            logger.warning(f"Failed to save to MongoDB history: {e}")
        
        # Save to Supabase user history
        try:
            with SupabasePostgresConnection() as db:
                # Ensure tables exist
                create_user_history_table(db)
                
                insert_supabase_history(
                    db_connection=db,
                    user_id=user_id,
                    query_text=req.text,
                    verdict=result["verdict"],
                    confidence=result["confidence"],
                    sources_count=len(result["sources_used"]),
                    category=req.category or "other",
                    language=req.language,
                    raw_response=result
                )
                logger.info(f"Saved query to Supabase for user: {user_id}")
        except Exception as e:
            logger.warning(f"Failed to save to Supabase history: {e}")
        
        logger.info(f"Verification complete: {response.verdict} (confidence={response.confidence})")
        return response
        
    except Exception as e:
        logger.error(f"Verification error: {e}", exc_info=True)
        
        # Check if all models are down
        models = check_model_availability()
        if all(status == "down" for status in models.values()):
            raise HTTPException(
                status_code=503,
                detail="Service temporarily unavailable. All models are down."
            )
        
        raise HTTPException(
            status_code=500,
            detail=f"Verification failed: {str(e)}"
        )


@app.post(
    "/admin/ingest",
    response_model=IngestResponse,
    tags=["Admin"],
    summary="Trigger ingestion (SRS 7.2)",
    dependencies=[Depends(verify_admin_token)]
)
async def trigger_ingestion(request: IngestRequest = IngestRequest(force=False)) -> IngestResponse:
    """
    Trigger ingestion from all sources per SRS 7.2.
    
    Requires X-Admin-Token header for authentication.
    """
    try:
        logger.info(f"POST /admin/ingest - Force={request.force}")
        
        results = ingest_all_sources(force=request.force)
        
        return IngestResponse(
            status="ok",
            ingested=results["ingested"],
            last_synced=datetime.utcnow().isoformat() + "Z",
            errors=results.get("errors", [])
        )
        
    except Exception as e:
        logger.error(f"Ingestion error: {e}", exc_info=True)
        return IngestResponse(
            status="error",
            ingested={},
            last_synced=datetime.utcnow().isoformat() + "Z",
            errors=[str(e)]
        )


@app.post(
    "/feedback",
    response_model=FeedbackResponse,
    tags=["Feedback"],
    summary="Submit user feedback"
)
async def submit_feedback(request: FeedbackRequest) -> FeedbackResponse:
    """
    Submit user feedback about a verdict.
    """
    try:
        logger.info(f"POST /feedback - Verdict: {request.verdict_returned}")
        
        insert_feedback(
            claim_text=request.claim_text,
            verdict_returned=request.verdict_returned,
            comment=request.comment,
            screenshot_url=request.screenshot_url
        )
        
        return FeedbackResponse(
            status="ok",
            message="Feedback received. Thank you!"
        )
        
    except Exception as e:
        logger.error(f"Feedback submission error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit feedback: {str(e)}"
        )


@app.get(
    "/admin/logs",
    tags=["Admin"],
    summary="View recent claim logs",
    dependencies=[Depends(verify_admin_token)]
)
async def get_logs(limit: int = 20) -> Dict[str, Any]:
    """
    Retrieve recent claim verification logs.
    
    Requires X-Admin-Token header for authentication.
    """
    try:
        logs = get_recent_claim_logs(limit=limit)
        return {
            "status": "ok",
            "count": len(logs),
            "logs": logs
        }
    except Exception as e:
        logger.error(f"Failed to retrieve logs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve logs: {str(e)}"
        )


@app.get(
    "/user/history",
    tags=["User"],
    summary="Get user query history"
)
async def get_user_history_endpoint(
    request: Request, 
    limit: int = 50, 
    source: str = "mongodb",
    x_user_id: Optional[str] = Header(None, description="Optional User ID from Supabase Auth")
) -> Dict[str, Any]:
    """
    Retrieve user's query history from MongoDB or Supabase.
    
    Args:
        limit: Maximum number of queries to retrieve (default: 50)
        source: Database source - "mongodb" or "supabase" (default: "mongodb")
        x_user_id: User ID from header (if logged in)
    """
    try:
        # Determine user_id: Use header if provided (logged in), else hash IP (guest)
        if x_user_id:
            user_id = x_user_id
        else:
            client_ip = request.client.host if request.client else "unknown"
            user_id = hashlib.sha256(f"{client_ip}".encode()).hexdigest()[:16]
        
        if source.lower() == "supabase":
            # Retrieve from Supabase
            with SupabasePostgresConnection() as db:
                history = get_supabase_history(db, user_id, limit)
                return {
                    "status": "ok",
                    "user_id": user_id,
                    "count": len(history),
                    "source": "supabase",
                    "history": history
                }
        else:
            # Retrieve from MongoDB (default)
            history = get_user_query_history(user_id, limit)
            return {
                "status": "ok",
                "user_id": user_id,
                "count": len(history),
                "source": "mongodb",
                "history": history
            }
        
    except Exception as e:
        logger.error(f"Failed to retrieve user history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve user history: {str(e)}"
        )


@app.get(
    "/",
    tags=["System"],
    summary="Root endpoint"
)
async def root():
    """Root endpoint with API information."""
    return {
        "name": "R.A.M.A. API",
        "version": "1.0.0",
        "description": "Reliable Agent for Misinformation Analysis",
        "endpoints": {
            "health": "/health",
            "verify": "/verify",
            "user_history": "/user/history",
            "admin_ingest": "/admin/ingest",
            "feedback": "/feedback",
            "admin_logs": "/admin/logs"
        },
        "docs": "/docs",
        "status": "operational",
        "features": [
            "Comprehensive A-Z news retrieval",
            "Source credibility checking",
            "User history tracking (MongoDB + Supabase)",
            "Multi-source fact verification",
            "Real-time fact-checking engine"
        ]
    }


# ========================================
# ERROR HANDLERS
# ========================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    logger.error(f"HTTP {exc.status_code}: {exc.detail}")
    return {
        "detail": exc.detail,
        "status_code": exc.status_code
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    raise HTTPException(
        status_code=500,
        detail="Internal server error"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
