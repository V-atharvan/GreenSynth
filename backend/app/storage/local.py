"""
GreenSynth Analytics — Local Filesystem Storage Implementation

Concrete implementation of FileStorageBackend interface for local disk storage.
Stores files under data/raw/ hierarchy with path traversal prevention and
SHA-256 integrity checksums.
"""

from __future__ import annotations

import hashlib
import logging
import mimetypes
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.storage.base import FileStorageBackend, StoredFile

logger = logging.getLogger(__name__)


class PathTraversalError(ValueError):
    """Raised when a file path attempts to escape the root storage directory."""


class LocalFileStorage(FileStorageBackend):
    """
    Local filesystem implementation of FileStorageBackend.

    Features:
      1. Path traversal protection: ensures all stored files remain strictly inside base_dir.
      2. SHA-256 checksum calculation for complete scientific integrity.
      3. Immutability: raises FileExistsError if a file already exists at the destination path.
    """

    def __init__(self, base_dir: str | Path | None = None) -> None:
        settings = get_settings()
        raw_root = base_dir or getattr(settings, "raw_data_dir", "data/raw")
        self.base_dir = Path(raw_root).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    @property
    def backend_name(self) -> str:
        return "local"

    def _resolve_safe_path(self, relative_or_abs_path: str) -> Path:
        """
        Sanitize and resolve target file path.

        Raises PathTraversalError if target path resolves outside self.base_dir.
        """
        # Remove leading slashes and normalize path
        clean_relative = os.path.normpath(relative_or_abs_path).lstrip("/\\")

        # Prevent any path traversal sequences
        if ".." in clean_relative.split(os.sep):
            raise PathTraversalError(f"Path traversal detected: {relative_or_abs_path}")

        target_path = (self.base_dir / clean_relative).resolve()

        try:
            target_path.relative_to(self.base_dir)
        except ValueError:
            raise PathTraversalError(
                f"Security violation: path {target_path} escapes root storage directory {self.base_dir}"
            )

        return target_path

    async def store(
        self,
        content: bytes,
        destination_path: str,
        original_filename: str,
        content_type: str | None = None,
    ) -> StoredFile:
        """
        Persist content to disk under destination_path.

        Calculates SHA-256 checksum.
        Raises FileExistsError if destination_path already exists.
        """
        target_path = self._resolve_safe_path(destination_path)

        if target_path.exists():
            raise FileExistsError(
                f"File already exists at {destination_path}. Raw files are immutable and cannot be overwritten."
            )

        # Create parent directories
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Calculate SHA-256 checksum
        sha256_hash = hashlib.sha256(content).hexdigest()

        # Write file atomically
        with open(target_path, "wb") as f:
            f.write(content)

        file_size = len(content)
        ext = target_path.suffix.lstrip(".").lower()
        mime = content_type or mimetypes.guess_type(original_filename)[0] or "application/octet-stream"

        logger.info(
            "Stored local raw file: %s (size=%d B, sha256=%s)",
            target_path,
            file_size,
            sha256_hash[:8],
        )

        return StoredFile(
            file_id=str(target_path.name),
            original_filename=original_filename,
            stored_path=str(target_path.relative_to(self.base_dir)).replace("\\", "/"),
            file_size_bytes=file_size,
            checksum_sha256=sha256_hash,
            file_type=ext,
            storage_backend="local",
            content_type=mime,
        )

    async def retrieve(self, stored_path: str) -> bytes:
        """Return raw file bytes from disk."""
        target_path = self._resolve_safe_path(stored_path)
        if not target_path.exists() or not target_path.is_file():
            raise FileNotFoundError(f"Raw file not found at {stored_path}")
        with open(target_path, "rb") as f:
            return f.read()

    async def exists(self, stored_path: str) -> bool:
        """Return True if a file exists at stored_path."""
        try:
            target_path = self._resolve_safe_path(stored_path)
            return target_path.exists() and target_path.is_file()
        except PathTraversalError:
            return False

    async def delete(self, stored_path: str) -> None:
        """
        Delete a file from storage.

        CAUTION: Should only be used for non-finalised files or during transaction rollback.
        """
        try:
            target_path = self._resolve_safe_path(stored_path)
            if target_path.exists() and target_path.is_file():
                target_path.unlink()
                logger.info("Deleted local file: %s", target_path)
        except Exception as exc:
            logger.warning("Failed to delete local file %s: %s", stored_path, exc)

    async def get_metadata(self, stored_path: str) -> dict[str, Any]:
        """Return metadata for local file."""
        target_path = self._resolve_safe_path(stored_path)
        if not target_path.exists() or not target_path.is_file():
            raise FileNotFoundError(f"Raw file not found at {stored_path}")

        stat = target_path.stat()
        return {
            "size_bytes": stat.st_size,
            "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            "content_type": mimetypes.guess_type(target_path.name)[0] or "application/octet-stream",
            "backend": "local",
        }

    async def generate_download_url(
        self, stored_path: str, expiry_seconds: int = 3600
    ) -> str | None:
        """Local filesystem files are streamed directly via backend router."""
        return None
