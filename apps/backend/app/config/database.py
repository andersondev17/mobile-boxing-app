"""
MongoDB connection and Beanie ODM initialization.

Uses motor (async MongoDB driver) with Beanie ODM for
Pydantic-native document models. Initializes all document
classes on application startup.
"""

import logging
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from schemas.env import settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None


async def init_db() -> None:
    """Initialize MongoDB connection and Beanie ODM.

    Called once during application startup via the lifespan handler.
    Registers all Beanie Document subclasses for the configured database.
    """
    global _client

    from models import (
        User,
        Role,
        Training,
        Exercise,
        Category,
        Difficulty,
        BoxingSession,
        Consent,
        AuthCode,
    )

    _client = AsyncIOMotorClient(settings.MONGO_URI)
    db = _client[settings.MONGO_DB]

    await init_beanie(
        database=db,
        document_models=[
            User,
            Role,
            Training,
            Exercise,
            Category,
            Difficulty,
            BoxingSession,
            Consent,
            AuthCode,
        ],
    )
    logger.info("MongoDB connected: %s / %s", settings.MONGO_URI.split("@")[-1], settings.MONGO_DB)


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