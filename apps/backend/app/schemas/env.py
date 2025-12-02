from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    JWT_SECRET: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str
    # Google OAuth - iOS Client
    GOOGLE_IOS_CLIENT_ID: str
    GOOGLE_IOS_REDIRECT_URI: str
    GOOGLE_AUTH_ENDPOINT: str
    GOOGLE_TOKEN_ENDPOINT: str
    GOOGLE_USERINFO_ENDPOINT: str
    # Application URLs
    FRONTEND_URL: str
    MOBILE_DEEP_LINK_SCHEME: str
    POSTGRES_DRIVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    # Kafka configuration
    KAFKA_TOPIC: str
    KAFKA_BROKERS: str
    GROUP_ID: str
    CLIENT_ID: str
    SESSION_TIMEOUT: int
    AUTO_OFFSET_RESET: str
    REDIS_URL: str
    SMARTWATCH_BUFFER_SIZE: int = 500

    class Config:
        env_file = "../.env"

settings = Settings()
