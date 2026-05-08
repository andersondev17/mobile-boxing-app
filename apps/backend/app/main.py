"""

Boxing Training API — FastAPI Application Entry Point.



Initializes MongoDB (Beanie), PostgreSQL (SQLAlchemy), seeds default data,

and mounts all route modules. Uses the modern lifespan handler instead

of deprecated on_event("startup").

"""



import sys



# ── Python version gate (hard fail) ──────────────────────────

if not (sys.version_info.major == 3 and sys.version_info.minor in [10, 11]):

    print(

        f"❌ ERROR: Incompatible Python version {sys.version}. "

        "System requires 3.10 or 3.11 ONLY."

    )

    sys.exit(1)



import json

import logging

import logging.config

from contextlib import asynccontextmanager



from fastapi import FastAPI, Request

from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import JSONResponse



from config import init_db, close_db, run_all_seeds

from routes import (

    boxing_router,

    kafka_router,

    training_router,

    user_router,

    exercise_router,

    consent_router,

    hybrid_analysis_router,

    gamification_router,

    monitoring_router,

)

from auth import auth_router

from schemas.env import settings





# ── Structured JSON Logging ───────────────────────────────────

class JsonFormatter(logging.Formatter):

    """Emit log records as single-line JSON — required for log aggregators."""



    def format(self, record: logging.LogRecord) -> str:

        doc = {

            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),

            "level": record.levelname,

            "logger": record.name,

            "msg": record.getMessage(),

            "env": settings.ENV_MODE,

        }

        if record.exc_info:

            doc["exc"] = self.formatException(record.exc_info)

        return json.dumps(doc, ensure_ascii=False)





def _configure_logging() -> None:

    handler = logging.StreamHandler(sys.stdout)

    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()

    root.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    root.handlers = [handler]





_configure_logging()

logger = logging.getLogger(__name__)





# ── Sentry (optional — only when DSN is set) ──────────────────

def _init_sentry() -> None:

    if not settings.SENTRY_DSN:

        logger.info("Sentry DSN not configured — skipping Sentry init.")

        return

    try:

        import sentry_sdk

        from sentry_sdk.integrations.fastapi import FastApiIntegration

        from sentry_sdk.integrations.starlette import StarletteIntegration



        sentry_sdk.init(

            dsn=settings.SENTRY_DSN,

            traces_sample_rate=1.0,

            profile_session_sample_rate=1.0,

            profile_lifecycle="trace",

            send_default_pii=True,

            enable_logs=True,

            integrations=[StarletteIntegration(), FastApiIntegration()],

            environment=settings.ENV_MODE,

        )

        logger.info("Sentry initialized (env=%s)", settings.ENV_MODE)

    except Exception as exc:

        logger.warning("Sentry init failed (non-fatal): %s", exc)





_init_sentry()





# ── Application Lifespan ──────────────────────────────────────

@asynccontextmanager

async def lifespan(app: FastAPI):

    """Startup and shutdown hooks.



    Startup order:

      1. Initialize MongoDB (Beanie) + PostgreSQL (SQLAlchemy)

      2. Seed default roles, categories, and exercises



    Shutdown:

      1. Close DB connection pools

    """

    logger.info(

        "🚀 Starting Boxing API",

        extra={"env_mode": settings.ENV_MODE, "kafka_enabled": settings.kafka_enabled},

    )

    await init_db()



    try:

        await run_all_seeds()

        logger.info("✅ Startup seeding completed.")

    except Exception as exc:

        logger.warning("⚠️ Seed failed (non-fatal): %s", exc)



    logger.info(

        "🟢 Boxing API ready",

        extra={

            "env_mode": settings.ENV_MODE,

            "kafka": settings.kafka_enabled,

            "sentry": bool(settings.SENTRY_DSN),

        },

    )



    yield



    logger.info("🛑 Shutting down Boxing API…")

    await close_db()





# ── FastAPI App ───────────────────────────────────────────────

app = FastAPI(

    title="Boxing Training API",

    description="Real-time boxing technique analysis with ML",

    version="0.3.0",

    lifespan=lifespan,

    docs_url="/docs",

    redoc_url="/redoc",

)



# ── Routers ───────────────────────────────────────────────────

app.include_router(user_router)

app.include_router(training_router)

app.include_router(auth_router)

app.include_router(boxing_router)

app.include_router(exercise_router)

app.include_router(consent_router)

app.include_router(hybrid_analysis_router)

app.include_router(gamification_router)

app.include_router(monitoring_router)



# Kafka router only when Kafka is enabled

if settings.kafka_enabled:

    app.include_router(kafka_router)

    logger.info("Kafka router mounted (ENV_MODE=%s)", settings.ENV_MODE)

else:

    logger.info(

        "Kafka router SKIPPED (ENV_MODE=%s). Set ENV_MODE=full to enable.",

        settings.ENV_MODE,

    )



# ── CORS ──────────────────────────────────────────────────────

app.add_middleware(

    CORSMiddleware,

    allow_origins=[

        "capacitor://localhost",

        "http://localhost",

        "http://localhost:8080",

        "http://localhost:8081",

        "http://localhost:3000",

        "http://localhost:5173",

        "http://localhost:5174",

        "boxing-app://auth",

    ],

    allow_credentials=True,

    allow_headers=["*"],

    allow_methods=["*"],

    expose_headers=["*"],

)





# ── Global error handler ──────────────────────────────────────

@app.exception_handler(Exception)

async def _unhandled_exception_handler(request: Request, exc: Exception):

    logger.exception("Unhandled exception: %s %s", request.method, request.url.path)

    return JSONResponse(status_code=500, content={"detail": "Internal server error"})





# ── Health check ──────────────────────────────────────────────

@app.get("/", tags=["health"])

async def root():

    return {

        "service": "Boxing Training API",

        "version": "0.3.0",

        "env_mode": settings.ENV_MODE,

        "kafka_enabled": settings.kafka_enabled,

        "status": "ok",

    }





@app.get("/health", tags=["health"])

async def health():

    """Liveness probe — returns 200 when app is running."""

    return {"status": "ok"}





if __name__ == "__main__":

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=None)

