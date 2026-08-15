"""
GreenSynth Analytics — Phase 19 Multi-Project Configuration & Matrix APIs
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.session import get_db
from app.models.experiment import Experiment
from app.models.ml import MLModel
from app.models.project import Project
from app.models.project_config import (
    MaterialCatalog,
    BiomassCatalog,
    ExtractCatalog,
    SolventCatalog,
    SynthesisMethodCatalog,
    ProjectDefinition,
    ProjectConfigurationVersion,
)
from app.models.sample import Sample
from app.schemas.project_config import (
    CatalogItemResponse,
    ProjectConfigurationResponse,
    ProjectMatrixRow,
    PropertyComparabilityRequest,
    PropertyComparabilityResponse,
)
from app.scientific.configuration.property_comparability import PropertyComparabilityService

router = APIRouter(prefix="", tags=["project-configuration"])


# ── 1. Project Synthesis Matrix API ──────────────────────

@router.get("/projects/matrix", response_model=list[ProjectMatrixRow])
async def get_project_matrix(
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Returns the multi-project research matrix for all 8 projects."""
    stmt = select(Project).order_by(Project.project_code.asc())
    res = await db.execute(stmt)
    projects = res.scalars().all()

    matrix_rows: list[ProjectMatrixRow] = []

    for p in projects:
        # Experiment count
        exp_stmt = select(func.count(Experiment.id)).where(Experiment.project_id == p.id)
        exp_res = await db.execute(exp_stmt)
        exp_count = exp_res.scalar() or 0

        # Sample count
        samp_stmt = (
            select(func.count(Sample.id))
            .join(Experiment, Sample.experiment_id == Experiment.id)
            .where(Experiment.project_id == p.id)
        )
        samp_res = await db.execute(samp_stmt)
        samp_count = samp_res.scalar() or 0

        # Model availability
        from app.models.ml import MLDataset, MLTrainingRun
        mdl_stmt = (
            select(func.count(MLModel.id))
            .join(MLTrainingRun, MLModel.training_run_id == MLTrainingRun.id)
            .join(MLDataset, MLTrainingRun.dataset_id == MLDataset.id)
            .where(MLDataset.project_id == p.id)
        )
        mdl_res = await db.execute(mdl_stmt)
        mdl_count = mdl_res.scalar() or 0

        # Biomass distinction for P5/P6
        biomass_val = "Rice husk" if p.project_code in ("P5", "P6") else "—"

        matrix_rows.append(
            ProjectMatrixRow(
                project_code=p.project_code,
                project_name=p.name,
                material=p.material,
                biomass=biomass_val,
                extract=p.extract,
                solvent=p.solvent,
                synthesis_method=p.synthesis_method,
                experiment_count=exp_count,
                sample_count=samp_count,
                characterization_count=exp_count * 2,
                dataset_status="CONFIGURED",
                model_status="APPROVED" if mdl_count > 0 else "NOT_TRAINED",
                optimization_status="READY",
            )
        )

    return matrix_rows


# ── 2. Project Configuration Details API ──────────────────

@router.get("/projects/{project_id}/configuration", response_model=ProjectConfigurationResponse)
async def get_project_configuration(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get configuration definition and active capabilities for a project."""
    p_stmt = select(Project).where(Project.id == project_id)
    p_res = await db.execute(p_stmt)
    proj = p_res.scalar_one_or_none()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    pdef_stmt = select(ProjectDefinition).where(ProjectDefinition.project_id == project_id)
    pdef_res = await db.execute(pdef_stmt)
    pdef = pdef_res.scalar_one_or_none()

    curr_ver = pdef.current_version if pdef else "v1.0"
    char_caps = pdef.characterization_capabilities if pdef else {"XRD": True, "UV_Vis": True, "Electrical": True, "FTIR": True, "SEM": True}
    anal_caps = pdef.analysis_capabilities if pdef else {"PeakDetection": True, "TaucPlot": True, "ConductivityFit": True}
    opt_caps = pdef.optimization_capabilities if pdef else {"GridSearch": True, "RandomSearch": True, "ModelGuided": True}
    from app.core.method_config import get_project_spec
    spec = get_project_spec(proj.project_code)

    return ProjectConfigurationResponse(
        project_id=proj.id,
        project_code=proj.project_code,
        name=proj.name,
        material_system=spec["material_system"],
        material=proj.material,
        biomass=biomass_val,
        extract=proj.extract,
        solvent=proj.solvent,
        synthesis_method=proj.synthesis_method,
        method_code=spec["method"],
        current_version=curr_ver,
        characterization_capabilities=char_caps,
        analysis_capabilities=anal_caps,
        optimization_capabilities=opt_caps,
    )


# ── 3. Cross-Project Property Comparability API ───────────

@router.post("/projects/compare", response_model=PropertyComparabilityResponse)
async def compare_project_properties(
    payload: PropertyComparabilityRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Evaluates cross-project scientific comparability before allowing comparison."""
    # Load source project
    s_stmt = select(Project).where(Project.project_code == payload.source_project_code)
    s_res = await db.execute(s_stmt)
    source_proj = s_res.scalar_one_or_none()
    if not source_proj:
        raise HTTPException(status_code=404, detail=f"Source project '{payload.source_project_code}' not found")

    # Load target project
    t_stmt = select(Project).where(Project.project_code == payload.target_project_code)
    t_res = await db.execute(t_stmt)
    target_proj = t_res.scalar_one_or_none()
    if not target_proj:
        raise HTTPException(status_code=404, detail=f"Target project '{payload.target_project_code}' not found")

    comp_result = PropertyComparabilityService.evaluate_comparability(
        source_project={"material": source_proj.material, "synthesis_method": source_proj.synthesis_method, "solvent": source_proj.solvent},
        target_project={"material": target_proj.material, "synthesis_method": target_proj.synthesis_method, "solvent": target_proj.solvent},
        source_prop=payload.source_property,
        target_prop=payload.target_property,
    )

    return PropertyComparabilityResponse(**comp_result)


# ── 4. Catalogs API ───────────────────────────────────────

@router.get("/catalogs/materials", response_model=list[CatalogItemResponse])
async def list_materials_catalog(db: AsyncSession = Depends(get_db)) -> Any:
    """List materials catalog."""
    stmt = select(MaterialCatalog)
    res = await db.execute(stmt)
    return [CatalogItemResponse(id=m.id, code=m.material_code, name=m.name, description=m.description, status=m.status) for m in res.scalars().all()]


@router.get("/catalogs/solvents", response_model=list[CatalogItemResponse])
async def list_solvents_catalog(db: AsyncSession = Depends(get_db)) -> Any:
    """List solvents catalog."""
    stmt = select(SolventCatalog)
    res = await db.execute(stmt)
    return [CatalogItemResponse(id=s.id, code=s.solvent_code, name=s.name, description=s.description, status=s.status) for s in res.scalars().all()]


@router.get("/catalogs/extracts", response_model=list[CatalogItemResponse])
async def list_extracts_catalog(db: AsyncSession = Depends(get_db)) -> Any:
    """List plant extracts catalog."""
    stmt = select(ExtractCatalog)
    res = await db.execute(stmt)
    return [CatalogItemResponse(id=e.id, code=e.extract_code, name=e.name, description=e.description, status=e.status) for e in res.scalars().all()]


@router.get("/catalogs/biomass", response_model=list[CatalogItemResponse])
async def list_biomass_catalog(db: AsyncSession = Depends(get_db)) -> Any:
    """List biomass catalog."""
    stmt = select(BiomassCatalog)
    res = await db.execute(stmt)
    return [CatalogItemResponse(id=b.id, code=b.biomass_code, name=b.name, description=b.description, status=b.status) for b in res.scalars().all()]


@router.get("/catalogs/synthesis-methods", response_model=list[CatalogItemResponse])
async def list_synthesis_methods_catalog(db: AsyncSession = Depends(get_db)) -> Any:
    """List synthesis methods catalog."""
    stmt = select(SynthesisMethodCatalog)
    res = await db.execute(stmt)
    return [CatalogItemResponse(id=m.id, code=m.method_code, name=m.name, description=m.description, status=m.status) for m in res.scalars().all()]
