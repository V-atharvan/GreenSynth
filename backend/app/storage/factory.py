"""
GreenSynth Analytics — Storage Backend Factory

Provides a unified factory function to instantiate the configured FileStorageBackend.
Supports local filesystem storage and S3-compatible cloud object storage.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from app.core.config import Settings, get_settings
from app.storage.base import FileStorageBackend
from app.storage.local import LocalFileStorage
from app.storage.s3 import S3FileStorage

logger = logging.getLogger(__name__)


def create_storage_backend(settings: Settings | None = None) -> FileStorageBackend:
    """
    Instantiate and return a FileStorageBackend based on application configuration.

    Fails closed if STORAGE_BACKEND='s3' is configured but required parameters are missing.
    """
    cfg = settings or get_settings()
    cfg.validate_storage_settings()

    if cfg.storage_backend == "s3":
        logger.info("Initializing S3-compatible cloud object storage backend (%s)", cfg.s3_bucket)
        return S3FileStorage(
            bucket=cfg.s3_bucket,
            region=cfg.s3_region,
            endpoint_url=cfg.s3_endpoint_url,
            access_key_id=cfg.s3_access_key_id,
            secret_access_key=cfg.s3_secret_access_key,
            public_base_url=cfg.s3_public_base_url,
            use_ssl=cfg.s3_use_ssl,
            signature_version=cfg.s3_signature_version,
            presigned_expiry_seconds=cfg.s3_presigned_url_expiry_seconds,
            settings=cfg,
        )

    logger.info("Initializing Local filesystem storage backend (%s)", cfg.raw_data_dir)
    return LocalFileStorage(base_dir=cfg.raw_data_dir)


@lru_cache
def get_storage_backend() -> FileStorageBackend:
    """
    FastAPI dependency and application singleton for FileStorageBackend.
    """
    return create_storage_backend()
