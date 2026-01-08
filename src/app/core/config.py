import os
from enum import Enum

from pydantic import SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    APP_NAME: str = "FastAPI app"
    APP_DESCRIPTION: str | None = None
    APP_VERSION: str | None = None
    LICENSE_NAME: str | None = None
    CONTACT_NAME: str | None = None
    CONTACT_EMAIL: str | None = None


class CryptSettings(BaseSettings):
    SECRET_KEY: SecretStr = SecretStr("secret-key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7


class DatabaseSettings(BaseSettings):
    pass


class SQLiteSettings(DatabaseSettings):
    SQLITE_URI: str = "./sql_app.db"
    SQLITE_SYNC_PREFIX: str = "sqlite:///"
    SQLITE_ASYNC_PREFIX: str = "sqlite+aiosqlite:///"


class MySQLSettings(DatabaseSettings):
    MYSQL_USER: str = "username"
    MYSQL_PASSWORD: str = "password"
    MYSQL_SERVER: str = "localhost"
    MYSQL_PORT: int = 5432
    MYSQL_DB: str = "dbname"
    MYSQL_SYNC_PREFIX: str = "mysql://"
    MYSQL_ASYNC_PREFIX: str = "mysql+aiomysql://"
    MYSQL_URL: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def MYSQL_URI(self) -> str:
        credentials = f"{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
        location = f"{self.MYSQL_SERVER}:{self.MYSQL_PORT}/{self.MYSQL_DB}"
        return f"{credentials}@{location}"


class PostgresSettings(DatabaseSettings):
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "postgres"
    POSTGRES_SYNC_PREFIX: str = "postgresql://"
    POSTGRES_ASYNC_PREFIX: str = "postgresql+asyncpg://"
    POSTGRES_URL: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def POSTGRES_URI(self) -> str:
        credentials = f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
        location = f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        return f"{credentials}@{location}"


class FirstUserSettings(BaseSettings):
    ADMIN_NAME: str = "admin"
    ADMIN_EMAIL: str = "admin@admin.com"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "!Ch4ng3Th1sP4ssW0rd!"


class TestSettings(BaseSettings):
    ...


class RedisCacheSettings(BaseSettings):
    REDIS_CACHE_HOST: str = "localhost"
    REDIS_CACHE_PORT: int = 6379

    @computed_field  # type: ignore[prop-decorator]
    @property
    def REDIS_CACHE_URL(self) -> str:
        return f"redis://{self.REDIS_CACHE_HOST}:{self.REDIS_CACHE_PORT}"


class ClientSideCacheSettings(BaseSettings):
    CLIENT_CACHE_MAX_AGE: int = 60


class EnvironmentOption(str, Enum):
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"


class EnvironmentSettings(BaseSettings):
    ENVIRONMENT: EnvironmentOption = EnvironmentOption.LOCAL


class CORSSettings(BaseSettings):
    CORS_ORIGINS: list[str] = ["*"]
    CORS_METHODS: list[str] = ["*"]
    CORS_HEADERS: list[str] = ["*"]


class OAuth2Settings(BaseSettings):
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: SecretStr = SecretStr("")
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/callback"
    OAUTH2_SCOPES: list[str] = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/calendar.readonly",
        "https://www.googleapis.com/auth/calendar.events",
    ]
    TOKEN_ENCRYPTION_KEY: SecretStr = SecretStr("")


class AISettings(BaseSettings):
    AI_PROVIDER: str = "claude"  # "claude" or "openai"
    CLAUDE_API_KEY: SecretStr = SecretStr("")
    OPENAI_API_KEY: SecretStr = SecretStr("")
    AI_MODEL_CLASSIFICATION: str = "claude-3-haiku-20240307"
    AI_MODEL_REPLY: str = "claude-3-5-sonnet-20241022"
    AI_MODEL_CALENDAR: str = "claude-3-5-sonnet-20241022"
    AI_AUTO_REPLY_ENABLED: bool = False
    AI_CONFIDENCE_THRESHOLD: float = 0.8


class PubSubSettings(BaseSettings):
    GOOGLE_CLOUD_PROJECT: str = ""
    PUBSUB_TOPIC_NAME: str = "gmail-notifications"
    PUBSUB_SUBSCRIPTION_NAME: str = "gmail-notifications-sub"


class PushNotificationSettings(BaseSettings):
    VAPID_PUBLIC_KEY: str = ""
    VAPID_PRIVATE_KEY: SecretStr = SecretStr("")
    VAPID_CONTACT_EMAIL: str = "admin@example.com"


class CelerySettings(BaseSettings):
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"


class FeatureSettings(BaseSettings):
    AUTO_CREATE_CALENDAR_EVENTS: bool = True
    REQUIRE_EVENT_CONFIRMATION: bool = False
    DEFAULT_NOTIFICATION_ADVANCE_MINUTES: int = 15
    EMAIL_PROCESSING_ENABLED: bool = True


class Settings(
    AppSettings,
    SQLiteSettings,
    PostgresSettings,
    CryptSettings,
    FirstUserSettings,
    TestSettings,
    RedisCacheSettings,
    ClientSideCacheSettings,
    EnvironmentSettings,
    CORSSettings,
    OAuth2Settings,
    AISettings,
    PubSubSettings,
    PushNotificationSettings,
    CelerySettings,
    FeatureSettings,
):
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
