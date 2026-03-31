# TASK: Project 1, 2 & 3 (AURA Lite - FastAPI Entrypoint)
"""
main.py
-------
FastAPI entrypoint for AURA Lite.
- POST /predict       → Project 1: Text summarization (Gemini)
- POST /crop-suggest  → Project 2: Weather-based crop recommendation (MCP Hybrid)
- POST /query         → Project 3: AI-powered database query (AlloyDB + Gemini)
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request

from app.schemas.request import PredictRequest, CropRequest, QueryRequest
from app.schemas.response import PredictResponse, CropResponse, QueryResponse
from app.services.inference_service import InferenceService
from app.db.query_engine import run_query
from app.utils.logger import get_logger
from app.utils.error_handler import handle_exception

logger = get_logger(__name__)


# ── STARTUP / SHUTDOWN LIFECYCLE ───────────────────────────────────────────────
@asynccontextmanager
async def lifespan(application: FastAPI):
    """Initialize database on startup if DB env vars are configured."""
    if os.getenv("DB_HOST"):
        try:
            from app.db.db_connect import init_db
            from app.db.seed import seed_crops
            logger.info("[Startup] Initializing database...")
            init_db()
            seed_crops()
            logger.info("[Startup] Database ready.")
        except Exception as e:
            logger.warning(f"[Startup] DB init skipped or failed: {e}")
    else:
        logger.info("[Startup] DB_HOST not set — skipping database initialization.")
    yield


from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AURA Lite",
    description="Production-grade AI agent featuring ADK, MCP, and AlloyDB architecture",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

inference_service = InferenceService()


from fastapi.responses import FileResponse

@app.get("/")
async def serve_frontend():
    """Serves the pure HTML frontend directly through the backend port."""
    return FileResponse("frontend.html")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "AURA Lite", "version": "3.0.0"}


# ── PROJECT 1: TEXT SUMMARIZATION ──────────────────────────────────────────────
@app.post("/predict", response_model=PredictResponse)
async def predict(payload: PredictRequest, request: Request):
    logger.info(f"[POST /predict] Request from {request.client.host}")
    try:
        summary = await inference_service.summarize(payload.text)
        return PredictResponse(summary=summary, status="success")
    except Exception as e:
        handle_exception(logger, e)
        return PredictResponse(
            summary="Service temporarily unavailable.",
            status="error",
        )


# ── PROJECT 2: CROP RECOMMENDATION (MCP HYBRID) ──────────────────────────────
@app.post("/crop-suggest", response_model=CropResponse)
async def crop_suggest(payload: CropRequest, request: Request):
    logger.info(f"[POST /crop-suggest] Request for {payload.location} from {request.client.host}")
    try:
        result = await inference_service.suggest_crop(payload.location)
        logger.info(f"[POST /crop-suggest] Success. Source: {result.get('source')}")
        return CropResponse(**result)
    except Exception as e:
        handle_exception(logger, e)
        return CropResponse(
            location=payload.location,
            recommended_crops=[],
            source="error",
            reason="Service temporarily unavailable. Please try again.",
            status="error",
        )


# ── PROJECT 3: AI-POWERED DATABASE QUERY (ALLOYDB) ───────────────────────────
@app.post("/query", response_model=QueryResponse)
async def query_database(payload: QueryRequest, request: Request):
    """
    Accepts a natural language question, converts it to SQL via Gemini,
    executes on AlloyDB, and returns structured results.
    Use case: Querying crop recommendations and profitability based on weather conditions.
    """
    logger.info(f"[POST /query] Question: '{payload.question}' from {request.client.host}")
    try:
        result = await run_query(payload.question)
        return QueryResponse(**result)
    except Exception as e:
        handle_exception(logger, e)
        return QueryResponse(
            query=None,
            results=[],
            total_results=0,
            status="error",
            error=f"Query processing failed: {str(e)}",
        )
