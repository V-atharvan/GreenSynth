"""
GreenSynth Analytics — SEM Image Analysis & Measurement Service

Orchestrates SEM image metadata management, scale bar calibration (nm/pixel),
manual researcher length measurements (e.g. particle size), and visual annotations.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import SEMAnnotation, SEMMeasurement, SEMMetadata
from app.models.characterization import RawFile
from app.scientific.sem.calibration import calculate_physical_distance
from app.scientific.sem.schemas import (
    SEMAnnotationCreate,
    SEMMeasurementCreate,
    SEMMetadataUpdate,
)
from app.services.audit_service import AuditService
from app.services.characterization_service import RawFileNotFoundError

logger = logging.getLogger(__name__)


class SEMAnalysisService:
    """Service layer for SEM image metadata, scale calibration, and manual measurements."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.audit = AuditService(db)

    async def get_raw_file(self, raw_file_id: uuid.UUID) -> RawFile:
        """Fetch raw file or raise error."""
        res = await self.db.execute(select(RawFile).where(RawFile.id == raw_file_id))
        rf = res.scalar_one_or_none()
        if rf is None:
            raise RawFileNotFoundError(f"Raw image file {raw_file_id} not found.")
        return rf

    async def get_or_create_metadata(self, raw_file_id: uuid.UUID) -> SEMMetadata:
        """Fetch existing SEMMetadata or initialize empty record."""
        await self.get_raw_file(raw_file_id)
        res = await self.db.execute(select(SEMMetadata).where(SEMMetadata.raw_file_id == raw_file_id))
        meta = res.scalar_one_or_none()
        if meta is None:
            now = datetime.now(timezone.utc)
            meta = SEMMetadata(raw_file_id=raw_file_id, created_at=now, updated_at=now)
            self.db.add(meta)
            await self.db.flush()
        return meta

    async def update_metadata(
        self, raw_file_id: uuid.UUID, payload: SEMMetadataUpdate
    ) -> SEMMetadata:
        """Update SEM image metadata and calculate scale bar ratio (nm/pixel)."""
        meta = await self.get_or_create_metadata(raw_file_id)
        now = datetime.now(timezone.utc)
        meta.updated_at = now

        if payload.magnification is not None:
            meta.magnification = payload.magnification
        if payload.accelerating_voltage_kv is not None:
            meta.accelerating_voltage_kv = payload.accelerating_voltage_kv
        if payload.working_distance_mm is not None:
            meta.working_distance_mm = payload.working_distance_mm
        if payload.detector is not None:
            meta.detector = payload.detector
        if payload.scale_bar_nm is not None:
            meta.scale_bar_nm = payload.scale_bar_nm
        if payload.scale_bar_pixels is not None:
            meta.scale_bar_pixels = payload.scale_bar_pixels
        if payload.notes is not None:
            meta.notes = payload.notes

        # Calculate nm_per_pixel if scale bar info exists
        if meta.scale_bar_nm is not None and meta.scale_bar_pixels is not None and meta.scale_bar_pixels > 0:
            meta.nm_per_pixel = round(float(meta.scale_bar_nm) / float(meta.scale_bar_pixels), 4)

        await self.db.flush()
        await self.db.refresh(meta)

        await self.audit.log(
            entity_type="SEMMetadata",
            entity_id=meta.id,
            action="UPDATE_SEM_METADATA",
            changes={"nm_per_pixel": meta.nm_per_pixel},
        )
        return meta

    async def add_annotation(
        self, raw_file_id: uuid.UUID, payload: SEMAnnotationCreate, created_by: str | None = None
    ) -> SEMAnnotation:
        """Add visual annotation (point, line, rectangle) to SEM image."""
        await self.get_raw_file(raw_file_id)

        ann = SEMAnnotation(
            raw_file_id=raw_file_id,
            annotation_type=payload.annotation_type,
            coordinates_json=payload.coordinates_json,
            label=payload.label,
            notes=payload.notes,
            created_by=created_by,
        )
        self.db.add(ann)
        await self.db.flush()

        await self.audit.log(
            entity_type="SEMAnnotation",
            entity_id=ann.id,
            action="ADD_SEM_ANNOTATION",
            changes={"label": ann.label, "type": ann.annotation_type},
        )
        return ann

    async def list_annotations(self, raw_file_id: uuid.UUID) -> Sequence[SEMAnnotation]:
        """List all visual annotations for an SEM raw image."""
        res = await self.db.execute(
            select(SEMAnnotation)
            .where(SEMAnnotation.raw_file_id == raw_file_id)
            .order_by(SEMAnnotation.created_at.asc())
        )
        return res.scalars().all()

    async def add_manual_measurement(
        self, raw_file_id: uuid.UUID, payload: SEMMeasurementCreate, created_by: str | None = None
    ) -> SEMMeasurement:
        """Record manual physical distance measurement using image scale calibration."""
        meta = await self.get_or_create_metadata(raw_file_id)

        phys_res = calculate_physical_distance(
            pixel_distance=payload.pixel_distance,
            scale_bar_nm=meta.scale_bar_nm,
            scale_bar_pixels=meta.scale_bar_pixels,
            nm_per_pixel=meta.nm_per_pixel,
        )

        meas = SEMMeasurement(
            raw_file_id=raw_file_id,
            pixel_distance=payload.pixel_distance,
            physical_distance_nm=phys_res.physical_distance_nm,
            unit=phys_res.unit,
            label=payload.label,
            calibration_info={
                "nm_per_pixel": meta.nm_per_pixel,
                "scale_bar_nm": meta.scale_bar_nm,
                "scale_bar_pixels": meta.scale_bar_pixels,
                "warning": phys_res.warning_msg,
            },
            created_by=created_by,
        )
        self.db.add(meas)
        await self.db.flush()

        await self.audit.log(
            entity_type="SEMMeasurement",
            entity_id=meas.id,
            action="ADD_SEM_MEASUREMENT",
            changes={"pixel_distance": meas.pixel_distance, "physical_distance": meas.physical_distance_nm},
        )
        return meas

    async def list_measurements(self, raw_file_id: uuid.UUID) -> Sequence[SEMMeasurement]:
        """List all manual physical measurements for an SEM raw image."""
        res = await self.db.execute(
            select(SEMMeasurement)
            .where(SEMMeasurement.raw_file_id == raw_file_id)
            .order_by(SEMMeasurement.created_at.asc())
        )
        return res.scalars().all()
