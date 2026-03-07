"""
Core configuration menggunakan Pydantic v2 Settings.

Pydantic v2 Features yang dipakai:
- model_config (pengganti class Config)
- @field_validator dengan mode='before'/'after'
- @model_validator untuk cross-field validation
- computed_field
"""
from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, PostgresDsn, computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Pydantic v2: model_config menggantikan class Config ──────────────────
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",          # abaikan env var yang tidak dikenal
    )

    # ── App ──────────────────────────────────────────────────────────────────
    APP_NAME: str = "Task Manager SaaS"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False

    # ── Sentry ──────────────────────────────────────────────────────────────────
    SENTRY_DSN: str | None = None

    # ── API ──────────────────────────────────────────────────────────────────
    API_V1_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: list[AnyHttpUrl] = []
    ALLOWED_HOSTS: list[str] = ["*"]

    # ── Database ─────────────────────────────────────────────────────────────
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "taskmanager"
    DB_POOL_SIZE: int = Field(default=5, ge=1, le=20)
    DB_MAX_OVERFLOW: int = Field(default=10, ge=0, le=50)

    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Auth / JWT ────────────────────────────────────────────────────────────
    SECRET_KEY: str = "changeme-in-production-use-openssl-rand-hex-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, ge=5)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, ge=1)

    # ── Multi-tenant ─────────────────────────────────────────────────────────
    MAX_TENANTS: int = Field(default=100, ge=1)
    DEFAULT_TENANT_PLAN: Literal["free", "pro", "enterprise"] = "free"

    # ── Railway override ─────────────────────────────────────────────────────
    DATABASE_URL_OVERRIDE: str | None = Field(default=None, alias="DATABASE_URL")

    # ── Pydantic v2: @field_validator ─────────────────────────────────────────
    @field_validator("SECRET_KEY", mode="after")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY harus minimal 32 karakter!")
        return v

    @field_validator("POSTGRES_PORT", mode="before")
    @classmethod
    def validate_port(cls, v: int | str) -> int:
        port = int(v)
        if not (1 <= port <= 65535):
            raise ValueError(f"Port tidak valid: {port}")
        return port

    # ── Pydantic v2: @model_validator (cross-field validation) ───────────────
    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """Pastikan production environment aman."""
        if self.ENVIRONMENT == "production":
            if self.DEBUG:
                raise ValueError("DEBUG tidak boleh True di production!")
            if self.SECRET_KEY == "changeme-in-production-use-openssl-rand-hex-32":
                raise ValueError("Ganti SECRET_KEY di production!")
        return self

    # ── Pydantic v2: @computed_field (properti yang ter-include di serialisasi) ─
    @computed_field  # type: ignore[misc]
    @property
    def DATABASE_URL(self) -> str:
        """Async database URL untuk SQLAlchemy + asyncpg."""
        if self.DATABASE_URL_OVERRIDE:
            # Railway inject postgresql://, kita butuh postgresql+asyncpg://
            return self.DATABASE_URL_OVERRIDE.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            ).replace("postgres://", "postgresql+asyncpg://", 1)
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @computed_field  # type: ignore[misc]
    @property
    def DATABASE_URL_SYNC(self) -> str:
        """Sync database URL untuk Alembic migrations."""
        if self.DATABASE_URL_OVERRIDE:
            return self.DATABASE_URL_OVERRIDE.replace(
                "postgresql+asyncpg://", "postgresql+psycopg2://", 1
            ).replace("postgresql://", "postgresql+psycopg2://", 1
            ).replace("postgres://", "postgresql+psycopg2://", 1)
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @computed_field  # type: ignore[misc]
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


# ── Singleton pattern dengan lru_cache ───────────────────────────────────────
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Cached settings instance.
    Di test, kita bisa override dengan: get_settings.cache_clear()
    """
    return Settings()


settings = get_settings()


# ── Redis ─────────────────────────────────────────────────────────────────────
# (ditambahkan di Phase 3)

# ── Sentry ────────────────────────────────────────────────────────────────────
# (ditambahkan di Phase 5)
