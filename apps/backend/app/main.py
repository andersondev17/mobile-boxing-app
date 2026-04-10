"""
Boxing Training API — FastAPI Application Entry Point.

Initializes MongoDB (Beanie), seeds default data, and mounts
all route modules. Uses the modern lifespan handler instead
of deprecated on_event("startup").
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import init_db, close_db, run_all_seeds
from routes import (
    boxing_router,
    kafka_router,
    training_router,
    user_router,
    exercise_router,
    consent_router,
)
from auth import auth_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown hooks.

    Startup:
      1. Initialize MongoDB connection + Beanie ODM
      2. Seed default roles, categories, and exercises

    Shutdown:
      1. Close MongoDB connection pool
    """
    # ── Startup ──────────────────────────────────────────────
    logger.info("🚀 Starting Boxing API...")
    await init_db()
    try:
        await run_all_seeds()
        logger.info("✅ Startup seeding completed.")
    except Exception as exc:
        logger.warning("⚠️ Seed failed (non-fatal): %s", exc)

    yield

    # ── Shutdown ─────────────────────────────────────────────
    logger.info("🛑 Shutting down Boxing API...")
    await close_db()


app = FastAPI(
    title="Boxing Training API",
    description="Real-time boxing technique analysis with ML",
    version="0.2.0",
    lifespan=lifespan,
)

# ── Routes ───────────────────────────────────────────────────
app.include_router(user_router)
app.include_router(training_router)
app.include_router(auth_router)
app.include_router(boxing_router)
app.include_router(kafka_router)
app.include_router(exercise_router)
app.include_router(consent_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "capacitor://localhost",
        "http://localhost",
        "http://localhost:8080",
        "http://localhost:8081",
        "http://localhost:3000",
        "boxing-app://auth",
    ],
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
    expose_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Boxing Training API v0.2.0", "status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
