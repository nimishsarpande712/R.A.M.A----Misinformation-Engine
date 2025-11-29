"""
FastAPI application for R.A.M.A News Engine.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
from typing import Optional
import logging

from app.ingestion import ingest_all_sources
from app.engine import check_claim
from app.logging_store import log_claim_result

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Pydantic Models
class ClaimRequest(BaseModel):
    """Request model for claim checking endpoint."""
    text: str = Field(..., description="The claim text to check")
    language: Optional[str] = Field(None, description="ISO 639-1 language code (e.g., 'en', 'es')")


class IngestResponse(BaseModel):
    """Response model for ingestion endpoint."""
    status: str
    results: dict
    total_ingested: int


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str


class ErrorResponse(BaseModel):
    """Response model for error responses."""
    detail: str
    status_code: int


# Startup and Shutdown Event Handlers
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup event
    logger.info("Application startup - initializing resources...")
    # Add your startup logic here (e.g., initialize connections, load models, etc.)
    
    yield
    
    # Shutdown event
    logger.info("Application shutdown - cleaning up resources...")
    # Add your shutdown logic here (e.g., close connections, save state, etc.)


# Create FastAPI app instance
app = FastAPI(
    title="R.A.M.A News Engine API",
    description="API for checking claims in news articles",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health Check Endpoint
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health check endpoint"
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint to verify the API is running.
    
    Returns:
        HealthResponse: JSON object with status "ok"
    """
    return HealthResponse(status="ok")


# Ingestion Endpoint
@app.post(
    "/admin/ingest",
    response_model=IngestResponse,
    tags=["Admin"],
    summary="Ingest all news sources"
)
async def ingest() -> IngestResponse:
    """
    Ingests data from all configured news sources.
    
    Returns:
        IngestResponse: JSON object with status and detailed count breakdown
        
    Raises:
        HTTPException: 500 error if ingestion fails
    """
    try:
        logger.info("Starting ingestion process...")
        results = ingest_all_sources()
        total_ingested = results.get('total', 0)
        logger.info(f"Ingestion completed successfully. Total ingested: {total_ingested} items.")
        return IngestResponse(
            status="ok", 
            results=results,
            total_ingested=total_ingested
        )
    except Exception as e:
        logger.error(f"Ingestion failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {str(e)}"
        )


# Claim Checking Endpoint
@app.post(
    "/check-claim",
    tags=["Claims"],
    summary="Check a claim for veracity"
)
async def check_claim_endpoint(claim_request: ClaimRequest) -> dict:
    """
    Checks a claim for veracity using the R.A.M.A engine.
    
    Args:
        claim_request: ClaimRequest object containing the text and optional language
        
    Returns:
        dict: Result from engine.check_claim with claim verification details
        
    Raises:
        HTTPException: 500 error if claim checking fails
    """
    try:
        logger.info(f"Processing claim check request: {claim_request.text[:100]}...")
        result = check_claim(
            claim_text=claim_request.text,
            language=claim_request.language or "en"
        )
        log_claim_result(
            claim_text=claim_request.text,
            language=claim_request.language or "en",
            result=result
        )
        logger.info(f"Claim check completed successfully.")
        return result
    except Exception as e:
        logger.error(f"Claim checking failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Claim checking failed: {str(e)}"
        )


# Global exception handler for 500 errors
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """
    Custom handler for HTTP exceptions.
    """
    logger.error(f"HTTP Exception: {exc.detail}", exc_info=True)
    return {
        "detail": exc.detail,
        "status_code": exc.status_code
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """
    Global exception handler for unhandled exceptions.
    """
    logger.error(f"Unhandled Exception: {str(exc)}", exc_info=True)
    raise HTTPException(
        status_code=500,
        detail="Internal server error"
    )
