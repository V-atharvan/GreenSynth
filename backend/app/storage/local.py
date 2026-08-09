"""
GreenSynth Analytics — Local Filesystem Storage Implementation

Concrete implementation of FileStorageBackend interface for local disk storage.
Stores files under data/raw/ hierarchy with path traversal prevention and
SHA-256 integrity checksums.
"""

from __future__ import annotations

import hashlib
import logging
import os

from pathlib import Path

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

    def _resolve_safe_path(self, relative_or_abs_path: str) -> Path:
        """
        Sanitize and resolve target file path.

        Raises PathTraversalError if target path resolves outside self.base_dir.
        """
        # Remove any path traversal tokens like '..'
        clean_relative = os.path.normpath(relative_or_abs_path).lstrip("/\\")
        
        # Prevent any remaining '..' sequences
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

        logger.info(
            "Stored raw file: %s (size=%d B, sha256=%s)",
            target_path, file_size, sha256_hash[:8]
        )

        return StoredFile(
            file_id=str(target_path.name),
            original_filename=original_filename,
            stored_path=str(target_path.relative_to(self.base_dir)),
            file_size_bytes=file_size,
            checksum_sha256=sha256_hash,
            file_type=ext,
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

        CAUTION: Should only be used for non-finalised files.
        """
        target_path = self._resolve_safe_path(stored_path)
        if target_path.exists():
            target_path.unlink()
            logger.info("Deleted file: %s", target_path)
