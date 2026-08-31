"""
GreenSynth Analytics — S3-Compatible Cloud Object Storage Implementation

Concrete implementation of FileStorageBackend interface for AWS S3, Cloudflare R2,
MinIO, and other S3-compatible object storage providers.

Uses boto3 with non-blocking execution via asyncio.to_thread to prevent event-loop blocking.
Enforces SHA-256 checksum integrity, collision-resistant object keys, and immutability.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import mimetypes
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.config import Settings, get_settings
from app.storage.base import FileStorageBackend, StoredFile

logger = logging.getLogger(__name__)


class S3StorageError(Exception):
    """Base exception for S3 storage failures."""


class S3FileStorage(FileStorageBackend):
    """
    S3-compatible Object Storage implementation of FileStorageBackend.

    Compatible with:
      - Amazon S3
      - Cloudflare R2
      - MinIO
      - Ceph / Backblaze B2 / Supabase Storage S3 API
    """

    def __init__(
        self,
        bucket: str | None = None,
        region: str | None = None,
        endpoint_url: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        public_base_url: str | None = None,
        use_ssl: bool = True,
        signature_version: str = "s3v4",
        presigned_expiry_seconds: int = 3600,
        settings: Settings | None = None,
    ) -> None:
        cfg = settings or get_settings()

        self.bucket = bucket or cfg.s3_bucket
        self.region = region or cfg.s3_region
        self.endpoint_url = endpoint_url or cfg.s3_endpoint_url
        self.access_key_id = access_key_id or cfg.s3_access_key_id
        self.secret_access_key = secret_access_key or cfg.s3_secret_access_key
        self.public_base_url = public_base_url or cfg.s3_public_base_url
        self.use_ssl = use_ssl if use_ssl is not None else cfg.s3_use_ssl
        self.signature_version = signature_version or cfg.s3_signature_version
        self.presigned_expiry_seconds = presigned_expiry_seconds or cfg.s3_presigned_url_expiry_seconds

        if not self.bucket:
            raise ValueError("S3FileStorage requires a valid 'bucket' name.")

        # Initialize boto3 S3 client
        client_kwargs: dict[str, Any] = {
            "service_name": "s3",
            "region_name": self.region,
            "use_ssl": self.use_ssl,
            "config": Config(
                signature_version=self.signature_version,
                s3={"addressing_style": "auto"},
                retries={"max_attempts": 3, "mode": "standard"},
            ),
        }

        if self.endpoint_url:
            client_kwargs["endpoint_url"] = self.endpoint_url

        if self.access_key_id and self.secret_access_key:
            client_kwargs["aws_access_key_id"] = self.access_key_id
            client_kwargs["aws_secret_access_key"] = self.secret_access_key

        self._s3_client = boto3.client(**client_kwargs)

    @property
    def backend_name(self) -> str:
        return "s3"

    def _sanitize_key(self, object_key: str) -> str:
        """
        Normalize object key and prevent path traversal sequences.
        """
        clean_key = object_key.replace("\\", "/").strip("/")
        parts = [p for p in clean_key.split("/") if p and p != "."]
        if ".." in parts:
            raise ValueError(f"Path traversal detected in object key: {object_key}")
        return "/".join(parts)

    async def store(
        self,
        content: bytes,
        destination_path: str,
        original_filename: str,
        content_type: str | None = None,
    ) -> StoredFile:
        """
        Persist content to S3 bucket under destination_path (object key).

        Calculates SHA-256 checksum and uploads with metadata.
        Raises FileExistsError if object key already exists in S3.
        """
        key = self._sanitize_key(destination_path)

        # Check if object already exists
        if await self.exists(key):
            raise FileExistsError(
                f"Object already exists in S3 at '{key}'. Raw files are immutable and cannot be overwritten."
            )

        sha256_hash = hashlib.sha256(content).hexdigest()
        file_size = len(content)
        ext = Path(original_filename).suffix.lstrip(".").lower()
        mime = content_type or mimetypes.guess_type(original_filename)[0] or "application/octet-stream"

        def _upload() -> dict[str, Any]:
            return self._s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=content,
                ContentType=mime,
                Metadata={
                    "sha256": sha256_hash,
                    "original-filename": original_filename,
                    "uploaded-at": datetime.now(timezone.utc).isoformat(),
                },
            )

        try:
            resp = await asyncio.to_thread(_upload)
            etag = resp.get("ETag", "").strip('"')
        except ClientError as exc:
            logger.error("Failed to upload object to S3 (%s/%s): %s", self.bucket, key, exc)
            raise S3StorageError(f"S3 upload failed for '{key}': {exc}") from exc

        logger.info(
            "Stored S3 raw file: %s/%s (size=%d B, sha256=%s, etag=%s)",
            self.bucket,
            key,
            file_size,
            sha256_hash[:8],
            etag,
        )

        return StoredFile(
            file_id=Path(key).name,
            original_filename=original_filename,
            stored_path=key,
            file_size_bytes=file_size,
            checksum_sha256=sha256_hash,
            file_type=ext,
            storage_backend="s3",
            bucket=self.bucket,
            etag=etag,
            content_type=mime,
        )

    async def retrieve(self, stored_path: str) -> bytes:
        """Return raw file bytes from S3."""
        key = self._sanitize_key(stored_path)

        def _download() -> bytes:
            try:
                resp = self._s3_client.get_object(Bucket=self.bucket, Key=key)
                return resp["Body"].read()
            except ClientError as exc:
                error_code = exc.response.get("Error", {}).get("Code", "")
                if error_code in ("NoSuchKey", "404", "NotFound"):
                    raise FileNotFoundError(f"Raw file not found in S3 at '{key}'") from exc
                raise S3StorageError(f"Failed to retrieve S3 object '{key}': {exc}") from exc

        return await asyncio.to_thread(_download)

    async def exists(self, stored_path: str) -> bool:
        """Return True if an object exists in S3 at stored_path."""
        key = self._sanitize_key(stored_path)

        def _head() -> bool:
            try:
                self._s3_client.head_object(Bucket=self.bucket, Key=key)
                return True
            except ClientError as exc:
                error_code = exc.response.get("Error", {}).get("Code", "")
                if error_code in ("NoSuchKey", "404", "NotFound"):
                    return False
                logger.warning("Error checking S3 object existence for '%s': %s", key, exc)
                return False

        return await asyncio.to_thread(_head)

    async def delete(self, stored_path: str) -> None:
        """
        Delete an object from S3.

        CAUTION: Should only be used for non-finalised files or during transaction rollback.
        """
        key = self._sanitize_key(stored_path)

        def _delete() -> None:
            try:
                self._s3_client.delete_object(Bucket=self.bucket, Key=key)
                logger.info("Deleted S3 object: %s/%s", self.bucket, key)
            except ClientError as exc:
                logger.warning("Failed to delete S3 object '%s': %s", key, exc)

        await asyncio.to_thread(_delete)

    async def get_metadata(self, stored_path: str) -> dict[str, Any]:
        """Return metadata for S3 object."""
        key = self._sanitize_key(stored_path)

        def _head() -> dict[str, Any]:
            try:
                resp = self._s3_client.head_object(Bucket=self.bucket, Key=key)
                return {
                    "size_bytes": resp.get("ContentLength", 0),
                    "content_type": resp.get("ContentType", "application/octet-stream"),
                    "etag": resp.get("ETag", "").strip('"'),
                    "modified_at": resp.get("LastModified", datetime.now(timezone.utc)).isoformat(),
                    "backend": "s3",
                    "bucket": self.bucket,
                    "metadata": resp.get("Metadata", {}),
                }
            except ClientError as exc:
                error_code = exc.response.get("Error", {}).get("Code", "")
                if error_code in ("NoSuchKey", "404", "NotFound"):
                    raise FileNotFoundError(f"Raw file not found in S3 at '{key}'") from exc
                raise S3StorageError(f"Failed to get S3 metadata for '{key}': {exc}") from exc

        return await asyncio.to_thread(_head)

    async def generate_download_url(
        self, stored_path: str, expiry_seconds: int = 3600
    ) -> str | None:
        """
        Generate a secure pre-signed download URL for the requested object.
        """
        key = self._sanitize_key(stored_path)
        expiry = expiry_seconds or self.presigned_expiry_seconds

        def _presign() -> str:
            return self._s3_client.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=expiry,
            )

        try:
            return await asyncio.to_thread(_presign)
        except Exception as exc:
            logger.warning("Failed to generate S3 pre-signed URL for '%s': %s", key, exc)
            return None
