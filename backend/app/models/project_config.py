"""
GreenSynth Analytics — Phase 19 Configuration-Driven Multi-Project ORM Models

Defines:
  1. MaterialCatalog: Material systems (CuO, Silica, Silicon).
  2. BiomassCatalog: Biomass sources (Rice husk).
  3. ExtractCatalog: Plant extracts (Mulberry extract).
  4. SolventCatalog: Solvents (Ethanol, Acetone).
  5. SynthesisMethodCatalog: Synthesis methods (SOL_GEL, HYDROTHERMAL, SPRAY_PYROLYSIS).
  6. ProjectDefinition: Links project to Material, Biomass, Extract, Solvent, Method & Capabilities.
  7. ProjectConfigurationVersion: Immutable version snapshot of project configuration.
  8. AnalysisCapability: Registered scientific analysis capabilities.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class MaterialCatalog(Base):
    """Catalog of material systems."""

    __tablename__ = "materials_catalog"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    material_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    chemical_formula: Mapped[str | None] = mapped_column(String(64), nullable=True)
    material_type: Mapped[str] = mapped_column(
        String(64), nullable=False, default="SINGLE_MATERIAL", comment="SINGLE_MATERIAL, COMPOSITE, MULTI_COMPONENT, BIOMASS_DERIVED"
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class BiomassCatalog(Base):
    """Catalog of biomass raw materials."""

    __tablename__ = "biomass_catalog"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    biomass_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    source: Mapped[str | None] = mapped_column(String(128), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ExtractCatalog(Base):
    """Catalog of plant extracts used as reducing/capping agents."""

    __tablename__ = "extracts_catalog"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    extract_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    source_plant: Mapped[str | None] = mapped_column(String(128), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class SolventCatalog(Base):
    """Catalog of solvents."""

    __tablename__ = "solvents_catalog"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    solvent_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    chemical_formula: Mapped[str | None] = mapped_column(String(64), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class SynthesisMethodCatalog(Base):
    """Catalog of synthesis methods (SOL_GEL, HYDROTHERMAL, SPRAY_PYROLYSIS)."""

    __tablename__ = "synthesis_methods_catalog"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    method_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    parameter_schema: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False, default=dict
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ProjectDefinition(Base):
    """
    Formal configuration definition linking a Project to its Catalogs and capabilities.
    """

    __tablename__ = "project_definitions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    project_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    material_system_type: Mapped[str] = mapped_column(String(64), nullable=False, default="SINGLE_MATERIAL")

    material_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("materials_catalog.id", ondelete="SET NULL"), nullable=True
    )
    biomass_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("biomass_catalog.id", ondelete="SET NULL"), nullable=True
    )
    plant_extract_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("extracts_catalog.id", ondelete="SET NULL"), nullable=True
    )
    solvent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("solvents_catalog.id", ondelete="SET NULL"), nullable=True
    )
    synthesis_method_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("synthesis_methods_catalog.id", ondelete="SET NULL"), nullable=True
    )

    current_version: Mapped[str] = mapped_column(String(32), nullable=False, default="v1.0")

    characterization_capabilities: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False, default=dict
    )
    analysis_capabilities: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False, default=dict
    )
    optimization_capabilities: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False, default=dict
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ProjectConfigurationVersion(Base):
    """
    Immutable version snapshot of a project configuration.
    """

    __tablename__ = "project_configuration_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    configuration_json: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class AnalysisCapability(Base):
    """
    Scientific analysis capability definition.
    """

    __tablename__ = "analysis_capabilities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    capability_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
