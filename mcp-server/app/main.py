from __future__ import annotations

import logging
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware

from .factcheck import get_recent_fact_checks
from .gov import get_government_bulletins
from .news import get_latest_news
from .social import get_social_samples

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
logger = logging.getLogger("mcp-server")

app = FastAPI(title="RAMA MCP Server", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("%s %s", request.method, request.url.path)
    response = await call_next(request)
    logger.info("Completed %s with status %s", request.url.path, response.status_code)
    return response


@app.get("/tools/news.get_latest")
async def read_latest_news(
    topic: Optional[str] = Query(default=None, description="Optional topic keyword"),
    limit: int = Query(default=50, ge=1, le=200),
):
    try:
        items = get_latest_news(topic=topic, limit=limit)
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Failed to fetch latest news")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"items": items}


@app.get("/tools/gov.get_bulletins")
async def read_government_bulletins(limit: int = Query(default=50, ge=1, le=200)):
    try:
        items = get_government_bulletins(limit=limit)
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Failed to fetch government bulletins")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"items": items}


@app.get("/tools/factcheck.get_recent")
async def read_recent_fact_checks(limit: int = Query(default=25, ge=1, le=200)):
    try:
        items = get_recent_fact_checks(limit=limit)
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Failed to fetch fact checks")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"items": items}


@app.get("/tools/social.get_samples")
async def read_social_samples(limit: int = Query(default=25, ge=1, le=200)):
    try:
        items = get_social_samples(limit=limit)
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Failed to fetch social samples")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"items": items}


@app.get(
    "/health",
    tags=["Health"],
    summary="Health check for MCP server",
)
async def health_check():
    """Simple health endpoint for quick availability checks."""
    return {"status": "ok"}


if __name__ == "__main__":  # pragma: no cover - convenience entry point
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=3333, reload=True)
