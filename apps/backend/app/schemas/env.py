"""
Environment settings for the boxing backend.

Uses pydantic-settings to load from .env file and environment variables.
MongoDB connection, Kafka topics, JWT config, and Google OAuth.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Application Modes ────────────────────────────────────
    # Modes:
    #   dev_mock   → mocks for Mongo, Postgres, Redis (CI/CD, no infra needed)
    #   local_real → all real services required (Docker Compose)
    #   ml_only    → only ML pipeline active, no Kafka/Spark
    #   no_kafka   → real DBs but Kafka disabled
    #   full       → all services (production-equivalent)
    ENV_MODE: str = "local_real"

    # ── Observability ─────────────────────────────────────────
    SENTRY_DSN: str = ""
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR

    # ── MongoDB ──────────────────────────────────────────────
    MONGO_URI: str = "mongodb://admin:admin123@localhost:27017/boxing_app?authSource=admin"
    MONGO_DB: str = "boxing_app"

    # ── Postgres (Auth) ──────────────────────────────────────
    POSTGRES_USER: str = "admin"
    POSTGRES_PASSWORD: str = "admin123"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "boxing_auth"

    @property
    def ASYNC_POSTGRES_URI(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

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
    
    # Kafka Security (Confluent Cloud)
    KAFKA_SECURITY_PROTOCOL: str = "PLAINTEXT"
    KAFKA_SASL_MECHANISM: str = "PLAIN"
    KAFKA_SASL_USERNAME: str = ""
    KAFKA_SASL_PASSWORD: str = ""

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

    @property
    def kafka_enabled(self) -> bool:
        """Kafka is active only in full and local_real modes."""
        return self.ENV_MODE in ("full", "local_real")

    @property
    def mock_allowed(self) -> bool:
        return self.ENV_MODE == "dev_mock"

    class Config:
        env_file = "../.env"


settings = Settings()
