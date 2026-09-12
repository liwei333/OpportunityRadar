"""OpportunityRadar Agent — FastAPI application entry point."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import health, research
from .core.config import get_settings
from .core.logging import setup_logging

settings = get_settings()
setup_logging(level="DEBUG" if settings.debug else "INFO")

logger = logging.getLogger(__name__)

app = FastAPI(
    title="OpportunityRadar Agent",
    description="AI Research Agent — market research, candidate discovery, buyer scoring",
    version="0.1.0",
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router, prefix="/api")
app.include_router(research.router, prefix="/api")


@app.on_event("startup")
async def on_startup() -> None:
    """Initialize database on startup."""
    from .infrastructure.database import init_db

    await init_db()
    logger.info("OpportunityRadar Agent started (env=%s)", settings.app_env)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    """Cleanup on shutdown."""
    from .infrastructure.database import async_engine

    await async_engine.dispose()
    logger.info("OpportunityRadar Agent stopped")
