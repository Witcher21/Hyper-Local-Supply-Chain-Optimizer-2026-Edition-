"""
Hyper-Local Supply Chain Optimizer — FastAPI Application
=========================================================
Phase 1: Backend Foundation & WebSocket Live Tracking
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from database import engine, Base
from routers.tracking import router as tracking_router
from routers.crud import router as crud_router
from routers.inventory import router as inventory_router
from routers.settings import router as settings_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan: DB table creation on startup
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up — creating database tables (if not exists)...")
    async with engine.begin() as conn:
        # Creates all tables if they don't exist yet
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database ready.")
    yield
    logger.info("Shutting down — disposing database engine.")
    await engine.dispose()


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

CORS_ORIGINS = ["*"]

app = FastAPI(
    title="Hyper-Local Supply Chain Optimizer API",
    description=(
        "AI-first, usage-based SaaS backend for local distributors. "
        "Provides real-time fleet tracking via WebSockets."
    ),
    version="2026.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(tracking_router)
app.include_router(crud_router)
app.include_router(inventory_router)
app.include_router(settings_router)

# ---------------------------------------------------------------------------
# Health & Meta
# ---------------------------------------------------------------------------


@app.get("/health", tags=["Meta"], summary="Health check")
async def health_check():
    return {"status": "operational", "version": "2026.1.0", "environment": os.getenv("ENVIRONMENT", "development")}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# ---------------------------------------------------------------------------
# Entry point (python main.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("ENVIRONMENT") == "development",
        log_level="info",
    )
