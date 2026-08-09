"""
GreenSynth Analytics — Analysis & Scientific Calculation ORM Models

Defines:
  1. AnalysisRun: Record of a scientific analysis execution (XRD, UV-Vis, etc.)
  2. XRDPeak: Detected diffraction peak positions, FWHM, and intensities
  3. ProcessedFile: Pointer to preprocessed data curves stored on disk
  4. CalculatedProperty: Traceable derived material property (e.g. Scherrer crystallite size)
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class AnalysisStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AnalysisRun(Base):
    """
    Scientific analysis execution run.

    Stores software version, parameters, assumptions, execution status,
    and errors for reproducibility.
    """

    __tablename__ = "analysis_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    characterization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("characterizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    input_file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("raw_files.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    analysis_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="XRD", index=True
    )

    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=AnalysisStatus.COMPLETED.value, index=True
    )
    software_version: Mapped[str] = mapped_column(
        String(32), nullable=False, default="0.1.0"
    )

    parameters: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True, comment="Input parameters used"
    )
    assumptions: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True, comment="Scientific assumptions"
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    characterization: Mapped["Characterization"] = relationship(  # type: ignore[name-defined]
        "Characterization", backref="analysis_runs"
    )
    input_file: Mapped["RawFile"] = relationship("RawFile")  # type: ignore[name-defined]

    peaks: Mapped[list[XRDPeak]] = relationship(
        "XRDPeak", back_populates="analysis_run", cascade="all, delete-orphan"
    )
    calculated_properties: Mapped[list[CalculatedProperty]] = relationship(
        "CalculatedProperty", back_populates="analysis_run", cascade="all, delete-orphan"
    )
    processed_files: Mapped[list[ProcessedFile]] = relationship(
        "ProcessedFile", back_populates="analysis_run", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<AnalysisRun id={self.id!s} type={self.analysis_type!r} "
            f"status={self.status!r}>"
        )


class XRDPeak(Base):
    """
    Detected XRD diffraction peak.

    Stores peak position (2θ in degrees), intensity, FWHM (degrees),
    and prominence.
    """

    __tablename__ = "xrd_peaks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    analysis_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    peak_position: Mapped[float] = mapped_column(
        Float, nullable=False, index=True, comment="2θ angle in degrees"
    )
    intensity: Mapped[float] = mapped_column(
        Float, nullable=False, comment="Peak intensity (counts or a.u.)"
    )
    fwhm: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Full Width at Half Maximum in degrees"
    )
    prominence: Mapped[float | None] = mapped_column(Float, nullable=True)
    width: Mapped[float | None] = mapped_column(Float, nullable=True)

    detection_parameters: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationship
    analysis_run: Mapped[AnalysisRun] = relationship(
        "AnalysisRun", back_populates="peaks"
    )

    def __repr__(self) -> str:
        return (
            f"<XRDPeak 2θ={self.peak_position:.2f}° I={self.intensity:.1f} "
            f"FWHM={self.fwhm if self.fwhm else 'N/A'}>"
        )


class ProcessedFile(Base):
    """
    Pointer to preprocessed data curves stored on disk under data/processed/.
    """

    __tablename__ = "processed_files"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    analysis_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    raw_file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("raw_files.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    stored_path: Mapped[str] = mapped_column(Text, nullable=False)
    processing_method: Mapped[str] = mapped_column(String(128), nullable=False)
    processing_parameters: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationship
    analysis_run: Mapped[AnalysisRun] = relationship(
        "AnalysisRun", back_populates="processed_files"
    )

    def __repr__(self) -> str:
        return f"<ProcessedFile id={self.id!s} method={self.processing_method!r}>"


class CalculatedProperty(Base):
    """
    Traceable calculated material property (e.g. Scherrer crystallite size).

    Stores value, unit, calculation formula, inputs, and assumptions.
    """

    __tablename__ = "calculated_properties"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    sample_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("samples.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    analysis_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    property_name: Mapped[str] = mapped_column(
        String(128), nullable=False, index=True, comment="e.g. Crystallite Size"
    )
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False, comment="e.g. nm, Å")
    calculation_method: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="e.g. Scherrer Equation"
    )
    formula: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="e.g. D = K * lambda / (beta * cos(theta))"
    )

    assumptions: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    input_values: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationship
    analysis_run: Mapped[AnalysisRun] = relationship(
        "AnalysisRun", back_populates="calculated_properties"
    )

    def __repr__(self) -> str:
        return (
            f"<CalculatedProperty {self.property_name}={self.value:.2f} {self.unit} "
            f"via {self.calculation_method!r}>"
        )


class FTIRAnnotation(Base):
    """
    Researcher peak annotation for FTIR spectroscopy (e.g. functional group identification).
    """

    __tablename__ = "ftir_annotations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    analysis_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    wavenumber_cm1: Mapped[float] = mapped_column(Float, nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    interpretation: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[str | None] = mapped_column(String(32), nullable=True, default="Tentative")
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    analysis_run: Mapped[AnalysisRun] = relationship("AnalysisRun")


class SEMMetadata(Base):
    """
    SEM Image Metadata and Scale Bar Calibration info.
    """

    __tablename__ = "sem_metadata"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    raw_file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("raw_files.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    magnification: Mapped[float | None] = mapped_column(Float, nullable=True)
    accelerating_voltage_kv: Mapped[float | None] = mapped_column(Float, nullable=True)
    working_distance_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    detector: Mapped[str | None] = mapped_column(String(64), nullable=True)
    scale_bar_nm: Mapped[float | None] = mapped_column(Float, nullable=True)
    scale_bar_pixels: Mapped[float | None] = mapped_column(Float, nullable=True)
    nm_per_pixel: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class SEMAnnotation(Base):
    """
    Researcher visual annotations on SEM images (Point, Line, Rectangle, Free Note).
    """

    __tablename__ = "sem_annotations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    raw_file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("raw_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    annotation_type: Mapped[str] = mapped_column(String(32), nullable=False, default="point")
    coordinates_json: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class SEMMeasurement(Base):
    """
    Manual physical length measurement made by researcher on scale-calibrated SEM images.
    """

    __tablename__ = "sem_measurements"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    raw_file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("raw_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    pixel_distance: Mapped[float] = mapped_column(Float, nullable=False)
    physical_distance_nm: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String(32), nullable=False, default="nm")
    label: Mapped[str | None] = mapped_column(String(128), nullable=True)
    calibration_info: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
