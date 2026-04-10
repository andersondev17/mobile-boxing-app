"""
Environment settings for the boxing backend.

Uses pydantic-settings to load from .env file and environment variables.
MongoDB connection, Kafka topics, JWT config, and Google OAuth.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Application Modes ────────────────────────────────────
    # Modes: "dev_mock" or "local_real"
    ENV_MODE: str = "local_real"

    # ── MongoDB ──────────────────────────────────────────────
    MONGO_URI: str = "mongodb://admin:admin123@localhost:27017/boxing_app?authSource=admin"
    MONGO_DB: str = "boxing_app"

    # ── Redis ────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    SMARTWATCH_BUFFER_SIZE: int = 500

    # ── Kafka ────────────────────────────────────────────────
    KAFKA_BROKERS: str = "localhost:19092"
    KAFKA_TOPIC_HEALTH: str = "health-metrics"
    KAFKA_TOPIC_TECHNIQUE: str = "technical-metrics"
    KAFKA_TOPIC_ROUNDS: str = "round-events"
    GROUP_ID: str = "boxing-consumer-group"
    CLIENT_ID: str = "boxing-app"
    SESSION_TIMEOUT: int = 30000
    AUTO_OFFSET_RESET: str = "earliest"

    # ── JWT / Auth ───────────────────────────────────────────
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Google OAuth ─────────────────────────────────────────
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/callback"
    GOOGLE_IOS_CLIENT_ID: str = ""
    GOOGLE_IOS_REDIRECT_URI: str = ""
    GOOGLE_AUTH_ENDPOINT: str = "https://accounts.google.com/o/oauth2/v2/auth"
    GOOGLE_TOKEN_ENDPOINT: str = "https://oauth2.googleapis.com/token"
    GOOGLE_USERINFO_ENDPOINT: str = "https://www.googleapis.com/oauth2/v3/userinfo"

    # ── Application ──────────────────────────────────────────
    FRONTEND_URL: str = "http://localhost:3000"
    MOBILE_DEEP_LINK_SCHEME: str = "gymshock://"

    class Config:
        env_file = "../.env"


settings = Settings()
