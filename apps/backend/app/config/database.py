"""
MongoDB connection and Beanie ODM initialization.

Uses motor (async MongoDB driver) with Beanie ODM for
Pydantic-native document models. Initializes all document
classes on application startup.
"""

import logging
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from schemas.env import settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
_pg_engine = None
_AsyncSessionLocal = None


async def init_db() -> None:
    """Initialize MongoDB connection and Beanie ODM.

    Called once during application startup via the lifespan handler.
    Registers all Beanie Document subclasses for the configured database.
    """
    global _client, _pg_engine, _AsyncSessionLocal
    
    # ── MongoDB Initialization ───────────────────────────────
    from models.model import (
        Role,
        Training,
        Exercise,
        Category,
        Difficulty,
        AuthCode,
    )
    from models.boxing import BoxingSession, Consent

    allow_mock = (settings.ENV_MODE == "dev_mock")
    
    try:
        _client = AsyncIOMotorClient(settings.MONGO_URI, serverSelectionTimeoutMS=2000)
        # Verify connection
        await _client.admin.command('ping')
        db = _client[settings.MONGO_DB]
        logger.info("MongoDB connected: %s / %s", settings.MONGO_URI.split("@")[-1], settings.MONGO_DB)
    except Exception as exc:
        if allow_mock:
            logger.warning("⚠️ MongoDB connection failed, using in-memory mock: %s", exc)
            from mongomock_motor import AsyncMongoMockClient as MockClient
            _client = MockClient()
            db = _client[settings.MONGO_DB]
        else:
            logger.error("❌ CRITICAL: MongoDB connection failed and ENV_MODE='local_real'. Exiting.")
            raise exc

    await init_beanie(
        database=db,
        document_models=[
            Role,
            Training,
            Exercise,
            Category,
            Difficulty,
            AuthCode,
            BoxingSession,
            Consent,
        ],
    )

    # ── Postgres Initialization ──────────────────────────────
    try:
        _pg_engine = create_async_engine(
            settings.ASYNC_POSTGRES_URI,
            echo=False,
            pool_pre_ping=True,  # detect stale connections
        )
        _AsyncSessionLocal = async_sessionmaker(
            _pg_engine, expire_on_commit=False, class_=AsyncSession
        )
        # ⚠️ Schema is managed by Alembic — do NOT call create_all here.
        # Run: alembic upgrade head (before first startup)
        logger.info("Postgres engine initialized (schema via Alembic).")
    except Exception as exc:
        if allow_mock:
            logger.warning("⚠️ Postgres connection failed (dev_mock): %s", exc)
        else:
            logger.error("❌ CRITICAL: Postgres connection failed: %s", exc)
            raise exc



async def close_db() -> None:
    """Close the MongoDB connection pool.

    Called during application shutdown via the lifespan handler.
    """
    global _client
    if _client:
        _client.close()
        _client = None
        logger.info("MongoDB connection closed.")


def get_db():
    """Return the active motor database instance.

    Use this for raw motor operations outside of Beanie.
    Beanie documents use their own internal connection.
    """
    if _client is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _client[settings.MONGO_DB]


async def get_pg_session():
    """Async generator for Postgres sessions (FastAPI dependency)."""
    if _AsyncSessionLocal is None:
        raise RuntimeError("Postgres not initialized. Call init_db() first.")
    async with _AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()