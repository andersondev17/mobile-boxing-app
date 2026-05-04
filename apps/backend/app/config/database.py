"""
Database initialization - PostgreSQL and MongoDB/Beanie.
"""

import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.schemas.env import settings
from models import User, Training, Exercise, Role, AuthCode, Category, Difficulty, BoxingSession, Consent

logger = logging.getLogger(__name__)

_pg_engine = None
_AsyncSessionLocal = None


async def init_db() -> None:
    """Initialize PostgreSQL and MongoDB/Beanie connections.
    
    Called once during application startup via the lifespan handler.
    """
    global _pg_engine, _AsyncSessionLocal
    
    # Beanie/MongoDB Initialization
    try:
        client = AsyncIOMotorClient(settings.MONGO_URI)
        await init_beanie(
            database=client.get_default_database(),
            document_models=[
                User,
                Training,
                Exercise,
                Role,
                AuthCode,
                Category,
                Difficulty,
                BoxingSession,
                Consent
            ],
        )
        logger.info("Beanie (MongoDB) initialized successfully.")
    except Exception as exc:
        logger.error("❌ MongoDB connection failed: %s", exc)

    # Postgres Initialization 
    try:
        _pg_engine = create_async_engine(
            settings.ASYNC_POSTGRES_URI,
            echo=False,
            pool_pre_ping=True,  # detect stale connections
            pool_size=20,  # Connection pool size
            max_overflow=30,  # Max overflow connections
            pool_recycle=3600,  # Recycle connections after 1 hour
        )
        _AsyncSessionLocal = async_sessionmaker(
            _pg_engine, expire_on_commit=False, class_=AsyncSession
        )
        # Schema is managed by Alembic do NOT call create_all here.
        logger.info("Postgres engine initialized (schema via Alembic).")
    except Exception as exc:
        logger.warning("⚠️ Postgres connection failed (dev_mock): %s", exc)


async def close_db() -> None:
    """Close database connections."""
    global _pg_engine
    if _pg_engine:
        await _pg_engine.dispose()
        _pg_engine = None
        logger.info("Postgres connection closed.")


def get_db():
    """Mock database function - returns None."""
    return None


async def get_pg_session():
    """Async generator for Postgres sessions (FastAPI dependency)."""
    if _AsyncSessionLocal is None:
        raise RuntimeError("Postgres not initialized. Call init_db() first.")
    async with _AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()