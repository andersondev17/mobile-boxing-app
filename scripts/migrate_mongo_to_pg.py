"""
One-time migration: copy Training documents from MongoDB to PostgreSQL.

Run this AFTER the Alembic migration 0004 has been applied.

Usage:
    python scripts/migrate_mongo_to_pg.py

Environment:
    Requires MONGO_URI, MONGO_DB, and ASYNC_POSTGRES_URI to be set
    (loaded automatically from app.schemas.env).
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Must be run from project root so these imports resolve
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

from app.schemas.env import settings
from models.postgres import Training

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


async def migrate() -> None:
    # ── MongoDB ─────────────────────────────────────────────
    mongo_client = AsyncIOMotorClient(settings.MONGO_URI)
    mongo_db = mongo_client[settings.MONGO_DB]
    mongo_trainings = mongo_db["trainings"]

    # ── PostgreSQL ──────────────────────────────────────────
    pg_engine = create_async_engine(
        settings.ASYNC_POSTGRES_URI,
        echo=False,
        pool_pre_ping=True,
    )
    AsyncSessionLocal = async_sessionmaker(pg_engine, expire_on_commit=False, class_=AsyncSession)

    migrated = 0
    skipped = 0
    errors = 0

    async with AsyncSessionLocal() as pg_session:
        async for doc in mongo_trainings.find():
            try:
                user_id_str = doc.get("user_id")
                if not user_id_str:
                    logger.warning("Skipping doc without user_id: %s", doc.get("_id"))
                    skipped += 1
                    continue

                user_uuid = uuid.UUID(user_id_str)
                title = doc.get("title", "Untitled")
                status = bool(doc.get("status", False))
                started_at = doc.get("started_at", datetime.now(timezone.utc))
                ended_at = doc.get("ended_at")

                # Idempotency check: same user + title + started_at
                stmt = select(Training).where(
                    Training.user_id == user_uuid,
                    Training.title == title,
                    Training.started_at == started_at,
                )
                result = await pg_session.execute(stmt)
                if result.scalar_one_or_none():
                    logger.debug("Skipping duplicate: user=%s title=%s", user_uuid, title)
                    skipped += 1
                    continue

                pg_training = Training(
                    user_id=user_uuid,
                    title=title,
                    status=status,
                    started_at=started_at,
                    ended_at=ended_at,
                )
                pg_session.add(pg_training)
                migrated += 1

                # Commit in batches of 50 to avoid huge transactions
                if migrated % 50 == 0:
                    await pg_session.commit()
                    logger.info("Committed batch: %d migrated so far", migrated)

            except Exception as exc:
                logger.error("Error migrating doc %s: %s", doc.get("_id"), exc)
                errors += 1

        # Final commit
        await pg_session.commit()

    await pg_engine.dispose()
    mongo_client.close()

    logger.info("Migration complete: %d migrated, %d skipped, %d errors", migrated, skipped, errors)


if __name__ == "__main__":
    asyncio.run(migrate())
