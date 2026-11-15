"""
StoryForge AI - Application Lifecycle Events

Startup and shutdown event handlers for the FastAPI application.
"""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.database.init_db import init_db
from app.database.session import engine

logger = logging.getLogger(__name__)


def _create_storage_directories() -> None:
    """Create all required storage directories at startup."""
    for directory in settings.get_all_storage_dirs():
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug("Ensured directory exists: %s", directory)
    logger.info("All storage directories ready.")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """FastAPI lifespan context manager handling startup and shutdown."""
    # ── Startup ──────────────────────────────────────────────────────
    setup_logging()
    logger.info("Starting %s v%s", settings.APP_NAME, settings.VERSION)

    _create_storage_directories()
    await init_db(engine)

    logger.info("%s is ready to serve requests.", settings.APP_NAME)

    yield

    # ── Shutdown ─────────────────────────────────────────────────────
    logger.info("Shutting down %s...", settings.APP_NAME)
    await engine.dispose()
    logger.info("Database connections closed. Goodbye.")
