"""
GreenSynth Analytics — File Storage Backend Abstraction

Defines the interface that all file storage implementations must satisfy.
The MVP uses LocalFileStorage; production will use S3FileStorage.
Swapping implementations requires only changing the FastAPI dependency.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class StoredFile:
    """Metadata returned after a successful file storage operation."""

    file_id: str
    original_filename: str
    stored_path: str
    file_size_bytes: int
    checksum_sha256: str
    file_type: str


class FileStorageBackend(ABC):
    """
    Abstract base class for file storage backends.

    All raw laboratory data files are stored through this interface.
    Implementations must:
      - Never overwrite a finalised file
      - Return SHA-256 checksum on store
      - Raise FileNotFoundError if a file does not exist

    Implementations: LocalFileStorage (Phase 5), S3FileStorage (Phase 20).
    """

    @abstractmethod
    async def store(
        self,
        content: bytes,
        destination_path: str,
        original_filename: str,
    ) -> StoredFile:
        """
        Persist file content to storage.

        Must raise FileExistsError if destination_path already contains
        a finalised file.
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

        CAUTION: Should only be called for non-finalised files.
        Finalised raw data files must never be deleted.
        """
        ...
