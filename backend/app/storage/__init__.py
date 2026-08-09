"""
GreenSynth Analytics — Storage Module

STATUS: Partial implementation — FileStorageBackend interface defined

This module provides the file storage abstraction layer for raw laboratory
data files (XRD spectra, UV-Vis data, SEM images, etc.).

Architecture:
  FileStorageBackend (ABC)
    ├── LocalFileStorage  ← MVP implementation
    └── S3FileStorage     ← Future cloud implementation (Phase 20)

All implementations must:
  1. Never overwrite a file that has is_finalised=True
  2. Compute and return SHA-256 checksums on storage
  3. Store files under a deterministic path:
     <storage_root>/<project_id>/<experiment_id>/<sample_id>/
  4. Be injectable via FastAPI dependency injection

Development phase: 5
"""

from app.storage.base import FileStorageBackend, StoredFile

__all__ = ["FileStorageBackend", "StoredFile"]
