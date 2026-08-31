"""
GreenSynth Analytics — File Storage Subsystem (Phase 9)

Provides provider-independent storage abstractions for raw laboratory data files:
  - FileStorageBackend (ABC)
  - LocalFileStorage (Local filesystem, dev & tests)
  - S3FileStorage (S3-compatible cloud object storage, production)
  - get_storage_backend / create_storage_backend (Factory)
"""

from app.storage.base import FileStorageBackend, StoredFile
from app.storage.factory import create_storage_backend, get_storage_backend
from app.storage.local import LocalFileStorage, PathTraversalError
from app.storage.s3 import S3FileStorage, S3StorageError

__all__ = [
    "FileStorageBackend",
    "StoredFile",
    "LocalFileStorage",
    "S3FileStorage",
    "S3StorageError",
    "PathTraversalError",
    "get_storage_backend",
    "create_storage_backend",
]
