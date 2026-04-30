"""
FastAPI application entry point.
Configures the app with CORS, lifespan handlers, and health endpoint.
"""

import warnings
from contextlib import asynccontextmanager
from datetime import datetime

# Suppress harmless guardrails event loop warning
warnings.filterwarnings("ignore", message="Could not obtain an event loop.*", category=UserWarning)

from dotenv import load_dotenv
from fastapi import FastAPI

# Load environment variables before any other imports that might depend on them
load_dotenv()
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.api.schemas import HealthResponse
from app.config import get_settings

from app.core.rate_limit import limiter

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.utils.logging import setup_logging, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger = get_logger(__name__)
    settings = get_settings()

    logger.info(
        "app_starting",
        app_name=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
    )

    yield

    logger.info("app_shutting_down")


# ── Create the FastAPI app ────────────────────────────────────
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description=(
        "A production-ready Kubernetes AI Agent powered by LangGraph, "
        "Google Gemini, and Guardrails AI. Provides a REST API to query "
        "and manage Kubernetes clusters using natural language."
    ),
    version=settings.app_version,
    lifespan=lifespan,
    root_path="/agent",
    openapi_url="/openapi.json",
    servers=[{"url": "/agent"}]
)

# ── Rate Limiting ─────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS Middleware ───────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount API routes ──────────────────────────────────────────
app.include_router(api_router)


# ── Health Check ──────────────────────────────────────────────
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Health check",
    description="Returns the health status of the application.",
)
async def health_check():
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.utcnow(),
        mcp_connected=True,
    )


# ── Root ──────────────────────────────────────────────────────
@app.get("/", tags=["System"], summary="Root endpoint")
async def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
    }
