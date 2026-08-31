"""
GreenSynth Analytics — Characterization & File Storage Service

Business logic for managing laboratory characterizations, raw file uploads,
SHA-256 checksum validation, duplicate detection, and provider-independent storage.
Supports local filesystem and S3-compatible cloud object storage with transactional rollback.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from pathlib import Path
from typing import Any, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.characterization import (
    Characterization,
    CharacterizationStatus,
    RawFile,
    RawFileStatus,
    TechniqueType,
)
from app.models.experiment import Experiment
from app.models.project import Project
from app.models.sample import Sample
from app.schemas.characterization import (
    TECHNIQUE_ALLOWED_EXTENSIONS,
    CharacterizationCreate,
    CharacterizationUpdate,
)
from app.services.audit_service import AuditService
from app.services.sample_service import SampleNotFoundError
from app.storage import (
    FileStorageBackend,
    PathTraversalError,
    S3StorageError,
    get_storage_backend,
)

logger = logging.getLogger(__name__)

# Max upload file size: 50 MB
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024


class CharacterizationNotFoundError(Exception):
    """Raised when a characterization record is not found."""


class RawFileNotFoundError(Exception):
    """Raised when a raw file record is not found."""


class InvalidFileTypeValidationError(ValueError):
    """Raised when an uploaded file's format is incompatible with the technique."""


class FileSizeExceededValidationError(ValueError):
    """Raised when an uploaded file exceeds the size limit."""


class DuplicateFileError(Exception):
    """Raised when a duplicate file with the exact same SHA-256 checksum is uploaded."""


class CharacterizationService:
    """Service layer for characterization runs and raw laboratory file management."""

    def __init__(self, db: AsyncSession, storage: FileStorageBackend | None = None) -> None:
        self.db = db
        self.storage = storage or get_storage_backend()
        self.audit = AuditService(db)

    async def create_characterization(
        self, data: CharacterizationCreate
    ) -> Characterization:
        """Create a new characterization run for a sample."""
        # Verify parent sample exists
        sample_res = await self.db.execute(
            select(Sample).where(Sample.id == data.sample_id)
        )
        sample = sample_res.scalar_one_or_none()
        if sample is None:
            raise SampleNotFoundError(f"Sample {data.sample_id} not found.")

        ch = Characterization(
            sample_id=data.sample_id,
            technique=data.technique.value,
            characterization_date=data.characterization_date,
            operator=data.operator,
            instrument_name=data.instrument_name,
            instrument_model=data.instrument_model,
            instrument_id=data.instrument_id,
            notes=data.notes,
            status=CharacterizationStatus.UPLOADED.value,
        )
        self.db.add(ch)
        await self.db.flush()

        # Eagerly load raw_files before returning
        result = await self.db.execute(
            select(Characterization)
            .options(selectinload(Characterization.raw_files))
            .where(Characterization.id == ch.id)
        )
        ch_loaded = result.scalar_one()

        await self.audit.log(
            entity_type="Characterization",
            entity_id=ch.id,
            action="CREATE",
            changes={"technique": ch.technique, "sample_id": str(ch.sample_id)},
        )
        logger.info("Created Characterization %s (%s)", ch.id, ch.technique)
        return ch_loaded

    async def get_by_id(
        self, characterization_id: uuid.UUID, project_id: uuid.UUID | None = None
    ) -> Characterization:
        """Get single characterization record with loaded raw files, scoped to project if specified."""
        q = (
            select(Characterization)
            .options(selectinload(Characterization.raw_files))
            .where(Characterization.id == characterization_id)
        )
        if project_id is not None:
            q = (
                q.join(Sample, Characterization.sample_id == Sample.id)
                .join(Experiment, Sample.experiment_id == Experiment.id)
                .where(Experiment.project_id == project_id)
            )

        result = await self.db.execute(q)
        ch = result.scalar_one_or_none()
        if ch is None:
            raise CharacterizationNotFoundError(
                f"Characterization {characterization_id} not found."
            )
        return ch

    async def list_sample_characterizations(
        self, sample_id: uuid.UUID, project_id: uuid.UUID | None = None
    ) -> Sequence[Characterization]:
        """Return all characterizations for a sample, scoped to project if specified."""
        q = (
            select(Characterization)
            .options(selectinload(Characterization.raw_files))
            .where(Characterization.sample_id == sample_id)
            .order_by(Characterization.created_at.desc())
        )
        if project_id is not None:
            q = (
                q.join(Sample, Characterization.sample_id == Sample.id)
                .join(Experiment, Sample.experiment_id == Experiment.id)
                .where(Experiment.project_id == project_id)
            )

        result = await self.db.execute(q)
        return result.scalars().all()

    async def upload_raw_file(
        self,
        characterization_id: uuid.UUID,
        file_bytes: bytes,
        original_filename: str,
        content_type: str | None = None,
        uploader: str | None = None,
    ) -> RawFile:
        """
        Safely validate, store, and record an immutable raw laboratory file.

        1. Validates extension against technique allowed list.
        2. Validates max file size limit (50MB).
        3. Computes SHA-256 checksum and checks for duplicate files in database.
        4. Resolves hierarchy lineage: projects/{project_code}/experiments/{exp_code}/samples/{sample_code}/{ch_id}/{filename}.
        5. Uploads to configured storage provider (Local / S3).
        6. Creates RawFile database record with storage_backend metadata.
        7. If DB operation fails, safely removes the stored object to prevent orphaned files.
        """
        ch = await self.get_by_id(characterization_id)

        # 1. Validate file extension against technique
        ext = Path(original_filename).suffix.lstrip(".").lower()
        technique_enum = TechniqueType(ch.technique)
        allowed_exts = TECHNIQUE_ALLOWED_EXTENSIONS.get(technique_enum, set())

        if ext not in allowed_exts:
            allowed_str = ", ".join(sorted(list(allowed_exts)))
            raise InvalidFileTypeValidationError(
                f"File format '.{ext}' is not supported for {ch.technique} characterization. "
                f"Allowed formats: {allowed_str}."
            )

        # 2. Validate size
        file_size = len(file_bytes)
        if file_size > MAX_FILE_SIZE_BYTES:
            raise FileSizeExceededValidationError(
                f"File size ({file_size / (1024*1024):.2f} MB) exceeds the maximum limit of 50 MB."
            )

        # 3. Compute SHA-256 checksum & check duplicate
        checksum = hashlib.sha256(file_bytes).hexdigest()

        dup_res = await self.db.execute(
            select(RawFile).where(RawFile.checksum == checksum)
        )
        existing_dup = dup_res.scalar_one_or_none()
        if existing_dup is not None:
            raise DuplicateFileError(
                f"Duplicate file detected: SHA-256 checksum ({checksum[:8]}...) has already "
                f"been uploaded as '{existing_dup.original_filename}'."
            )

        # 4. Resolve hierarchy path for storage (deterministic object key)
        sample_res = await self.db.execute(
            select(Sample, Experiment, Project)
            .join(Experiment, Sample.experiment_id == Experiment.id)
            .join(Project, Experiment.project_id == Project.id)
            .where(Sample.id == ch.sample_id)
        )
        row = sample_res.one()
        sample, exp, proj = row[0], row[1], row[2]

        file_uuid = uuid.uuid4()
        stored_filename = f"{file_uuid!s}.{ext}"
        relative_path = (
            f"projects/{proj.project_code}/experiments/{exp.experiment_code}/"
            f"samples/{sample.sample_code}/{ch.id!s}/{stored_filename}"
        )

        # 5. Store file via backend (Local or S3)
        try:
            stored_meta = await self.storage.store(
                content=file_bytes,
                destination_path=relative_path,
                original_filename=original_filename,
                content_type=content_type,
            )
        except PathTraversalError as exc:
            raise ValueError(f"Security error during file upload: {exc}") from exc
        except (S3StorageError, Exception) as exc:
            logger.error("Storage backend upload failed for %s: %s", relative_path, exc)
            raise ValueError(f"Storage upload error: {exc}") from exc

        # 6. Create RawFile record in DB with rollback cleanup guard
        try:
            raw_file = RawFile(
                id=file_uuid,
                characterization_id=ch.id,
                sample_id=ch.sample_id,
                original_filename=original_filename,
                stored_filename=stored_filename,
                file_extension=ext,
                mime_type=content_type or stored_meta.content_type,
                file_size=file_size,
                checksum=checksum,
                storage_path=stored_meta.stored_path,
                storage_backend=stored_meta.storage_backend,
                uploaded_by=uploader,
                file_metadata={
                    "storage_backend": stored_meta.storage_backend,
                    "bucket": stored_meta.bucket,
                    "etag": stored_meta.etag,
                },
                status=RawFileStatus.ACTIVE.value,
            )
            self.db.add(raw_file)

            # Update characterization status
            ch.status = CharacterizationStatus.READY_FOR_ANALYSIS.value
            await self.db.flush()
            await self.db.refresh(raw_file)
            self.db.expire(ch, ["raw_files"])

        except Exception as exc:
            # Transaction failed: clean up newly created storage object to prevent orphaned files
            logger.error(
                "Database error recording RawFile metadata; rolling back storage object %s: %s",
                stored_meta.stored_path,
                exc,
            )
            await self.storage.delete(stored_meta.stored_path)
            raise exc

        await self.audit.log(
            entity_type="RawFile",
            entity_id=raw_file.id,
            action="RAW_FILE_UPLOAD",
            changes={
                "original_filename": original_filename,
                "checksum": checksum,
                "file_size": file_size,
                "storage_backend": stored_meta.storage_backend,
                "characterization_id": str(ch.id),
            },
        )
        logger.info(
            "Uploaded raw file %s [%s] for characterization %s",
            original_filename,
            stored_meta.storage_backend,
            ch.id,
        )
        return raw_file

    async def get_raw_file_by_id(
        self, file_id: uuid.UUID, project_id: uuid.UUID | None = None
    ) -> RawFile:
        """Return raw file metadata by ID, scoped to project if specified."""
        q = select(RawFile).where(RawFile.id == file_id)
        if project_id is not None:
            q = (
                q.join(Characterization, RawFile.characterization_id == Characterization.id)
                .join(Sample, Characterization.sample_id == Sample.id)
                .join(Experiment, Sample.experiment_id == Experiment.id)
                .where(Experiment.project_id == project_id)
            )

        result = await self.db.execute(q)
        raw_file = result.scalar_one_or_none()
        if raw_file is None:
            raise RawFileNotFoundError(f"Raw file {file_id} not found.")
        return raw_file

    async def download_raw_file(
        self, file_id: uuid.UUID, project_id: uuid.UUID | None = None
    ) -> tuple[bytes, str, str]:
        """
        Retrieve raw file bytes for download.

        Returns tuple of (file_bytes, original_filename, mime_type).
        """
        raw_file = await self.get_raw_file_by_id(file_id, project_id=project_id)
        content = await self.storage.retrieve(raw_file.storage_path)

        await self.audit.log(
            entity_type="RawFile",
            entity_id=raw_file.id,
            action="RAW_FILE_DOWNLOAD",
        )
        return content, raw_file.original_filename, raw_file.mime_type or "application/octet-stream"

    async def generate_download_url(
        self,
        file_id: uuid.UUID,
        project_id: uuid.UUID | None = None,
        expiry_seconds: int = 3600,
    ) -> str | None:
        """
        Generate temporary pre-signed download URL for S3 files (None for local).
        """
        raw_file = await self.get_raw_file_by_id(file_id, project_id=project_id)
        return await self.storage.generate_download_url(
            raw_file.storage_path, expiry_seconds=expiry_seconds
        )

    async def preview_raw_file(
        self, file_id: uuid.UUID, project_id: uuid.UUID | None = None, max_lines: int = 100
    ) -> dict[str, Any]:
        """
        Retrieve a safe preview (header lines / metadata) of an authorized raw laboratory file.
        """
        raw_file = await self.get_raw_file_by_id(file_id, project_id=project_id)
        content = await self.storage.retrieve(raw_file.storage_path)

        preview_text = None
        if raw_file.file_extension in {"csv", "txt", "tsv", "dat", "json"}:
            try:
                decoded = content.decode("utf-8", errors="replace")
                lines = decoded.splitlines()[:max_lines]
                preview_text = "\n".join(lines)
            except Exception:
                preview_text = None

        return {
            "file_id": str(raw_file.id),
            "original_filename": raw_file.original_filename,
            "mime_type": raw_file.mime_type,
            "file_size": raw_file.file_size,
            "checksum": raw_file.checksum,
            "preview_text": preview_text,
        }

    async def delete_raw_file(
        self, file_id: uuid.UUID, project_id: uuid.UUID | None = None
    ) -> bool:
        """
        Delete a raw file record and its underlying storage object, scoped to project if specified.
        """
        raw_file = await self.get_raw_file_by_id(file_id, project_id=project_id)
        # Delete from storage backend
        try:
            await self.storage.delete(raw_file.storage_path)
        except Exception as exc:
            logger.warning("Failed to delete storage file %s: %s", raw_file.storage_path, exc)

        # Delete from database
        await self.db.delete(raw_file)
        await self.db.flush()
        await self.audit.log(
            entity_type="RawFile",
            entity_id=raw_file.id,
            action="RAW_FILE_DELETE",
            changes={"original_filename": raw_file.original_filename},
        )
        return True

