"""
Database initialization - restoring MongoDB/Beanie for production use.
"""

import logging
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.schemas.env import settings
from models.boxing import BoxingSession
from models.model import AuthCode

logger = logging.getLogger(__name__)

_pg_engine = None
_AsyncSessionLocal = None
_mongo_client = None

async def init_db() -> None:
    """Initialize both MongoDB (Beanie) and PostgreSQL connections."""
    global _pg_engine, _AsyncSessionLocal, _mongo_client

    # 1. MongoDB / Beanie Initialization (raw landmarks + temp auth codes only)
    try:
        _mongo_client = AsyncIOMotorClient(settings.MONGO_URI)
        # Verify connection
        await _mongo_client.admin.command('ping')
        
        db_name = settings.MONGO_DB
        await init_beanie(
            database=_mongo_client[db_name],
            document_models=[
                BoxingSession,
                AuthCode,
            ],
        )
        logger.info("Beanie (MongoDB) initialized successfully.")
    except Exception as exc:
        logger.error("❌ MongoDB initialization failed: %s", exc)
        # In dev_mock we might want to continue, but usually this is fatal
        if settings.ENV_MODE != "dev_mock":
            raise

    # 2. Postgres Initialization 
    try:
        _pg_engine = create_async_engine(
            settings.ASYNC_POSTGRES_URI,
            echo=False,
            pool_pre_ping=True,
            pool_size=20,
            max_overflow=30,
            pool_recycle=3600,
        )
        _AsyncSessionLocal = async_sessionmaker(
            _pg_engine, expire_on_commit=False, class_=AsyncSession
        )
        logger.info("Postgres engine initialized (schema via Alembic).")
    except Exception as exc:
        logger.warning("⚠️ Postgres connection failed: %s", exc)


async def close_db() -> None:
    """Close database connections."""
    global _pg_engine, _mongo_client
    if _pg_engine:
        await _pg_engine.dispose()
        _pg_engine = None
        logger.info("Postgres connection closed.")
    
    if _mongo_client:
        _mongo_client.close()
        _mongo_client = None
        logger.info("MongoDB connection closed.")


def get_db():
    """Returns the motor database instance (legacy helper)."""
    if _mongo_client is None:
        return None
    return _mongo_client[settings.MONGO_DB]


async def get_pg_session():
    """Async generator for Postgres sessions (FastAPI dependency)."""
    if _AsyncSessionLocal is None:
        raise RuntimeError("Postgres not initialized. Call init_db() first.")
    async with _AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def pg_session():
    """Return an async context manager for a Postgres session.

    For use outside FastAPI dependencies (e.g., WebSocket handlers).

    Usage::

        async with pg_session() as db:
            result = await db.execute(...)
    """
    if _AsyncSessionLocal is None:
        raise RuntimeError("Postgres not initialized. Call init_db() first.")
    return _AsyncSessionLocal()
