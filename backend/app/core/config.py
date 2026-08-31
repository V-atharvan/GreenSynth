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

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_async_database_url(cls, v: str | None) -> str:
        if not v:
            return "postgresql+asyncpg://greensynth:changeme@localhost:5432/greensynth_db"
        val = str(v).strip()
        # Convert standard Render/Heroku/Supabase/Neon postgresql URL formats to asyncpg
        if val.startswith("postgres://"):
            val = "postgresql+asyncpg://" + val[len("postgres://"):]
        elif val.startswith("postgresql://"):
            val = "postgresql+asyncpg://" + val[len("postgresql://"):]
        elif val.startswith("sqlite://") and not val.startswith("sqlite+aiosqlite://"):
            val = "sqlite+aiosqlite://" + val[len("sqlite://"):]

        # For asyncpg, sslmode=require should be ssl=require and channel_binding stripped
        if "postgresql+asyncpg://" in val:
            val = val.replace("sslmode=require", "ssl=require")
            val = val.replace("&channel_binding=require", "").replace("?channel_binding=require&", "?").replace("?channel_binding=require", "")
        return val

    @field_validator("database_url_sync", mode="before")
    @classmethod
    def normalize_sync_database_url(cls, v: str | None) -> str:
        if not v:
            return "postgresql+psycopg2://greensynth:changeme@localhost:5432/greensynth_db"
        val = str(v).strip()
        if val.startswith("postgres://"):
            val = "postgresql+psycopg2://" + val[len("postgres://"):]
        elif val.startswith("postgresql+asyncpg://"):
            val = "postgresql+psycopg2://" + val[len("postgresql+asyncpg://"):]
        elif val.startswith("postgresql://") and not val.startswith("postgresql+psycopg2://"):
            val = "postgresql+psycopg2://" + val[len("postgresql://"):]
        return val

    # ── Security ──────────────────────────────────────────
    secret_key: str = Field(
        default="dev-secret-key-CHANGE-IN-PRODUCTION",
        description="JWT signing secret — must be changed in production",
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm",
    )
    access_token_expire_minutes: int = Field(
        default=60,
        description="Access token expiration duration in minutes",
    )

    # ── CORS ──────────────────────────────────────────────
    cors_origins: str = Field(
        default="*,http://localhost:5173,http://localhost:3000,https://green-synth.vercel.app",
        description="Comma-separated list of allowed CORS origins",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Return CORS origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    # ── Group & Invitation ────────────────────────────────
    max_group_members: int = Field(
        default=4,
        description="Maximum total group members including leader",
    )
    invitation_expiry_hours: int = Field(
        default=72,
        description="Invitation expiration lifetime in hours",
    )
    frontend_base_url: str = Field(
        default="http://localhost:5173",
        description="Frontend base URL for generating invitation links",
    )

    # ── Email & SMTP Service (Phase 16) ───────────────────
    email_mode: Literal["console", "smtp"] = Field(
        default="console",
        description="Email delivery mode: 'console' for dev/testing, 'smtp' for production",
    )
    email_enabled: bool = Field(
        default=True,
        description="Master switch to enable/disable email sending",
    )
    smtp_host: str = Field(
        default="smtp.gmail.com",
        description="SMTP server host (e.g. smtp.gmail.com)",
    )
    smtp_port: int = Field(
        default=587,
        description="SMTP port (587 for STARTTLS, 465 for SSL, 1025 for local dev)",
    )
    smtp_username: str = Field(
        default="",
        description="SMTP username (e.g. v.atharvan@gmail.com)",
    )
    smtp_password: str = Field(
        default="",
        description="SMTP password or Gmail App Password",
    )
    smtp_from_email: str = Field(
        default="v.atharvan@gmail.com",
        description="Sender email address",
    )
    smtp_from_name: str = Field(
        default="GreenSynth Analytics",
        description="Sender display name",
    )
    smtp_use_tls: bool = Field(
        default=True,
        description="Use STARTTLS encryption (port 587)",
    )
    smtp_use_ssl: bool = Field(
        default=False,
        description="Use SSL encryption (port 465)",
    )
    smtp_timeout: int = Field(
        default=30,
        description="SMTP socket connection & command timeout in seconds",
    )
    email_from: str = Field(
        default="v.atharvan@gmail.com",
        description="Legacy fallback sender email address",
    )

    @field_validator("smtp_use_ssl")
    @classmethod
    def validate_smtp_ssl_tls(cls, v: bool, info) -> bool:
        use_tls = info.data.get("smtp_use_tls")
        if v and use_tls:
            raise ValueError("Cannot enable both SMTP_USE_TLS and SMTP_USE_SSL simultaneously.")
        return v

    def validate_smtp_settings(self) -> None:
        """
        Validate that required SMTP settings are present when SMTP delivery mode is active.
        Ensures clear, safe configuration error messages without credential leakage.
        """
        if self.email_enabled and self.email_mode == "smtp":
            if not self.smtp_host or not self.smtp_host.strip():
                raise ValueError("SMTP configuration error: SMTP_HOST must be specified.")
            if not self.smtp_from_email or not self.smtp_from_email.strip():
                raise ValueError("SMTP configuration error: SMTP_FROM_EMAIL must be specified.")
            if not self.smtp_username or not self.smtp_password:
                raise ValueError("SMTP configuration error: SMTP authentication credentials (SMTP_USERNAME / SMTP_PASSWORD) are missing or incomplete.")

    # ── Storage (Phase 9) ─────────────────────────────────
    storage_backend: Literal["local", "s3"] = Field(
        default="local",
        description="Storage provider backend: 'local' for filesystem, 's3' for cloud object storage",
    )
    storage_path: str = Field(
        default="./data",
        description="Root path for file storage",
    )
    raw_data_dir: str = Field(
        default="./data/raw",
        description="Local root directory for raw files",
    )
    s3_endpoint_url: str | None = Field(
        default=None,
        description="Custom S3 endpoint URL (e.g. MinIO or Cloudflare R2)",
    )
    s3_region: str = Field(
        default="us-east-1",
        description="S3 region name",
    )
    s3_bucket: str = Field(
        default="greensynth-raw-files",
        description="S3 bucket name for raw laboratory files",
    )
    s3_access_key_id: str | None = Field(
        default=None,
        description="S3 access key ID",
    )
    s3_secret_access_key: str | None = Field(
        default=None,
        description="S3 secret access key",
    )
    s3_public_base_url: str | None = Field(
        default=None,
        description="Optional public CDN/base URL for object downloads",
    )
    s3_use_ssl: bool = Field(
        default=True,
        description="Use SSL for S3 connections",
    )
    s3_signature_version: str = Field(
        default="s3v4",
        description="S3 signature version",
    )
    s3_presigned_url_expiry_seconds: int = Field(
        default=3600,
        description="Pre-signed download URL validity lifetime in seconds",
    )

    def validate_storage_settings(self) -> None:
        """
        Validate storage configuration.
        Ensures fail-closed behavior if S3 is selected but credentials or bucket are missing.
        """
        if self.storage_backend == "s3":
            if not self.s3_bucket or not self.s3_bucket.strip():
                raise ValueError("STORAGE_BACKEND='s3' requires S3_BUCKET to be configured.")
            # For non-IAM / explicit credential setups:
            if not self.s3_access_key_id or not self.s3_secret_access_key:
                raise ValueError(
                    "STORAGE_BACKEND='s3' requires S3_ACCESS_KEY_ID and S3_SECRET_ACCESS_KEY. "
                    "Cannot silently fall back to ephemeral local storage in production."
                )


@lru_cache
def get_settings() -> Settings:
    """
    Return the cached application settings singleton.

    Using @lru_cache means settings are only read from the environment once.
    Call get_settings.cache_clear() in tests to reload settings.
    """
    return Settings()
