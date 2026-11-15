"""
StoryForge AI - Database Initialization

Creates all tables from the ORM metadata.
"""

import logging

from sqlalchemy.ext.asyncio import AsyncEngine

from app.database.base import Base

# Import all models so they register with Base.metadata
from app.models.project import Project, Scene, Character, VideoRender  # noqa: F401
from app.models.analytics import VideoAnalytics, GenerationHistory  # noqa: F401

logger = logging.getLogger(__name__)


async def init_db(engine: AsyncEngine) -> None:
    """Create all database tables if they don't exist."""
    logger.info("Initializing database — creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialization complete.")


async def drop_db(engine: AsyncEngine) -> None:
    """Drop all database tables. USE WITH CAUTION."""
    logger.warning("Dropping all database tables!")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.info("All tables dropped.")
