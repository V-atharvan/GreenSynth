"""
GreenSynth Analytics — Application Configuration

All configuration is read from environment variables (or a .env file).
No secrets are hard-coded here.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve to the project root .env (two levels up from this file: backend/app/core/ -> root)
_ENV_FILE = str(Path(__file__).resolve().parent.parent.parent.parent / ".env")


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    In development, create a .env file at the backend/ directory
    (or at the project root with docker-compose) and fill in values
    from .env.example.
    """

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────
    app_name: str = "GreenSynth Analytics"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # ── Database ──────────────────────────────────────────
    # Async URL for FastAPI application runtime
    database_url: str = Field(
        default="postgresql+asyncpg://greensynth:changeme@localhost:5432/greensynth_db",
        description="PostgreSQL async connection URL (asyncpg driver)",
    )
    # Sync URL for Alembic migrations
    database_url_sync: str = Field(
        default="postgresql+psycopg2://greensynth:changeme@localhost:5432/greensynth_db",
        description="PostgreSQL sync connection URL (psycopg2 driver, for Alembic)",
    )

    # ── Security ──────────────────────────────────────────
    secret_key: str = Field(
        default="dev-secret-key-CHANGE-IN-PRODUCTION",
        description="JWT signing secret — must be changed in production",
    )

    # ── CORS ──────────────────────────────────────────────
    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        description="Comma-separated list of allowed CORS origins",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Return CORS origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    # ── Storage ───────────────────────────────────────────
    storage_path: str = Field(
        default="./data",
        description="Root path for file storage",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Return the cached application settings singleton.

    Using @lru_cache means settings are only read from the environment once.
    Call get_settings.cache_clear() in tests to reload settings.
    """
    return Settings()
