"""
GreenSynth Analytics — File Storage Backend Abstraction

Defines the interface that all file storage implementations must satisfy.
Supports LocalFileStorage (local development) and S3FileStorage (production).
Swapping implementations requires only changing the STORAGE_BACKEND configuration.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class StoredFile:
    """Metadata returned after a successful file storage operation."""

    file_id: str
    original_filename: str
    stored_path: str
    file_size_bytes: int
    checksum_sha256: str
    file_type: str
    storage_backend: str = "local"
    bucket: str | None = None
    etag: str | None = None
    content_type: str = "application/octet-stream"
    extra_metadata: dict[str, Any] = field(default_factory=dict)


class FileStorageBackend(ABC):
    """
    Abstract base class for file storage backends.

    All raw laboratory data files are stored through this interface.
    Implementations must:
      - Never overwrite an existing file (immutability)
      - Return SHA-256 checksum on store
      - Raise FileNotFoundError if a file does not exist
      - Isolate and safely validate destination paths/object keys
    """

    @abstractmethod
    async def store(
        self,
        content: bytes,
        destination_path: str,
        original_filename: str,
        content_type: str | None = None,
    ) -> StoredFile:
        """
        Persist file content to storage.

        Must raise FileExistsError if destination_path already contains
        an existing file.
        """
        ...

    @abstractmethod
    async def retrieve(self, stored_path: str) -> bytes:
        """Return the raw bytes of a stored file."""
        ...

    @abstractmethod
    async def exists(self, stored_path: str) -> bool:
        """Return True if a file exists at stored_path."""
        ...

    @abstractmethod
    async def delete(self, stored_path: str) -> None:
        """
        Delete a file from storage.

        CAUTION: Should only be called for non-finalised files or during transaction rollback.
        """
        ...

    @abstractmethod
    async def get_metadata(self, stored_path: str) -> dict[str, Any]:
        """Return object metadata (size, content_type, etag/checksum, last_modified)."""
        ...

    @abstractmethod
    async def generate_download_url(
        self, stored_path: str, expiry_seconds: int = 3600
    ) -> str | None:
        """
        Generate a temporary pre-signed download URL if supported by the backend,
        or None if direct backend streaming is required.
        """
        ...

    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Return identifier name for this storage backend (e.g. 'local', 's3')."""
        ...
