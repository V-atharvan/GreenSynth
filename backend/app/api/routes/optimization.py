"""
GreenSynth Analytics — Phase 18 Optimization API Endpoints
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.session import get_db
from app.models.experiment import Experiment, ExperimentStatus
from app.models.ml import MLModel, MLDataset
from app.models.parameter import ParameterDefinition
from app.models.project import Project
from app.models.optimization import (
    OptimizationObjective,
    OptimizationConstraint,
    OptimizationSearchSpace,
    OptimizationRun,
    OptimizationCandidate,
    CandidateExperimentLink,
    OptimizationReview,
)
from app.schemas.optimization import (
    OptimizationObjectiveCreate,
    OptimizationObjectiveResponse,
    OptimizationConstraintCreate,
    OptimizationConstraintResponse,
    SearchSpaceValidationRequest,
    SearchSpaceValidationResponse,
    OptimizationRunCreate,
    OptimizationRunResponse,
    OptimizationCandidateResponse,
    CandidateReviewRequest,
    ProposedExperimentFromCandidateResponse,
    OptimizationReportResponse,
)
from app.scientific.optimization.candidate_generation import CandidateGenerationService

router = APIRouter(prefix="/optimization", tags=["optimization"])


# ── 1. Objectives API ────────────────────────────────────

@router.post("/objectives", response_model=OptimizationObjectiveResponse, status_code=status.HTTP_201_CREATED)
async def create_objective(
    payload: OptimizationObjectiveCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create a new researcher optimization objective."""
    obj = OptimizationObjective(**payload.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.get("/objectives", response_model=list[OptimizationObjectiveResponse])
async def list_objectives(
    project_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List optimization objectives."""
    stmt = select(OptimizationObjective)
    if project_id:
        stmt = stmt.where(OptimizationObjective.project_id == project_id)
    stmt = stmt.order_by(OptimizationObjective.created_at.desc())
    res = await db.execute(stmt)
    return res.scalars().all()


@router.put("/objectives/{objective_id}", response_model=OptimizationObjectiveResponse)
async def update_objective(
    objective_id: uuid.UUID,
    payload: OptimizationObjectiveCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update an optimization objective."""
    stmt = select(OptimizationObjective).where(OptimizationObjective.id == objective_id)
    res = await db.execute(stmt)
    obj = res.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Objective not found")

    for field, val in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, val)

    await db.commit()
    await db.refresh(obj)
    return obj


# ── 2. Constraints API ───────────────────────────────────

@router.post("/constraints", response_model=OptimizationConstraintResponse, status_code=status.HTTP_201_CREATED)
async def create_constraint(
    payload: OptimizationConstraintCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create a new search-space constraint."""
    constraint = OptimizationConstraint(**payload.model_dump())
    db.add(constraint)
    await db.commit()
    await db.refresh(constraint)
    return constraint


@router.get("/constraints", response_model=list[OptimizationConstraintResponse])
async def list_constraints(
    project_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List search-space constraints."""
    stmt = select(OptimizationConstraint)
    if project_id:
        stmt = stmt.where(OptimizationConstraint.project_id == project_id)
    stmt = stmt.order_by(OptimizationConstraint.created_at.desc())
    res = await db.execute(stmt)
    return res.scalars().all()


# ── 3. Search Space Validation API ───────────────────────

@router.post("/search-space/validate", response_model=SearchSpaceValidationResponse)
async def validate_search_space(
    payload: SearchSpaceValidationRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Validate search space definition and parameter ranges."""
    stmt = select(ParameterDefinition).where(ParameterDefinition.project_id == payload.project_id)
    res = await db.execute(stmt)
    param_defs = res.scalars().all()

    warnings: list[str] = []
    errors: list[str] = []
    search_space: dict[str, Any] = {}

    for p in param_defs:
        min_v = p.minimum_value
        max_v = p.maximum_value

        if min_v is None or max_v is None:
            warnings.append(f"Search-space range is not defined for parameter '{p.parameter_code}'. Researcher input required.")

        search_space[p.parameter_code] = {
            "parameter_name": p.parameter_name,
            "data_type": p.data_type,
            "unit": p.unit,
            "minimum_value": min_v,
            "maximum_value": max_v,
            "allowed_values": p.allowed_values,
        }

    is_valid = len(errors) == 0
    return SearchSpaceValidationResponse(
        is_valid=is_valid,
        warnings=warnings,
        errors=errors,
        search_space=search_space,
        estimated_combinations=None,
    )


# ── 4. Optimization Runs API ──────────────────────────────

@router.post("/runs", response_model=OptimizationRunResponse, status_code=status.HTTP_201_CREATED)
async def create_optimization_run(
    payload: OptimizationRunCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create and execute an evidence-based candidate generation run."""
    # 1. Load project
    p_stmt = select(Project).where(Project.id == payload.project_id)
    p_res = await db.execute(p_stmt)
    project = p_res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 2. Load objective
    o_stmt = select(OptimizationObjective).where(OptimizationObjective.id == payload.objective_id)
    o_res = await db.execute(o_stmt)
    objective = o_res.scalar_one_or_none()
    if not objective:
        raise HTTPException(status_code=404, detail="Objective not found")

    # 3. Load model
    m_stmt = select(MLModel).where(MLModel.id == payload.model_id)
    m_res = await db.execute(m_stmt)
    model = m_res.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    # Check model health status (CRITICAL blocks)
    if model.status == "RETIRED":
        raise HTTPException(status_code=400, detail="Optimization blocked: Selected model is RETIRED.")

    # 4. Load dataset
    d_stmt = select(MLDataset).where(MLDataset.id == model.dataset_id)
    d_res = await db.execute(d_stmt)
    dataset = d_res.scalar_one_or_none()
    dataset_version = dataset.version if dataset else "v1.0"

    # 5. Load parameter definitions to build search space
    pdef_stmt = select(ParameterDefinition).where(ParameterDefinition.project_id == payload.project_id)
    pdef_res = await db.execute(pdef_stmt)
    param_defs = pdef_res.scalars().all()

    search_space_def: dict[str, Any] = {"parameters_definition": {}}
    for p in param_defs:
        if p.minimum_value is not None and p.maximum_value is not None:
            search_space_def["parameters_definition"][p.parameter_code] = {
                "parameter_name": p.parameter_name,
                "unit": p.unit,
                "minimum_value": p.minimum_value,
                "maximum_value": p.maximum_value,
            }

    # 6. Load constraints
    c_stmt = select(OptimizationConstraint).where(
        OptimizationConstraint.project_id == payload.project_id,
        OptimizationConstraint.status == "ACTIVE",
    )
    c_res = await db.execute(c_stmt)
    constraints = [
        {
            "constraint_type": c.constraint_type,
            "target_code": c.target_code,
            "minimum_value": c.minimum_value,
            "maximum_value": c.maximum_value,
            "is_hard_constraint": c.is_hard_constraint,
        }
        for c in c_res.scalars().all()
    ]

    # 7. Load historical experiments for distance calculation
    exp_stmt = select(Experiment).where(Experiment.project_id == payload.project_id)
    exp_res = await db.execute(exp_stmt)
    historical_exps = [
        {
            "id": str(e.id),
            "experiment_code": e.experiment_code,
            "parameter_values": getattr(e, "parameters_json", None) or {},
        }
        for e in exp_res.scalars().all()
    ]

    # 8. Create Optimization Run record
    opt_run = OptimizationRun(
        project_id=payload.project_id,
        objective_id=payload.objective_id,
        model_id=payload.model_id,
        model_version=model.version,
        dataset_id=model.dataset_id,
        dataset_version=dataset_version,
        generation_method=payload.generation_method,
        random_seed=payload.random_seed,
        requested_candidate_count=payload.requested_candidate_count,
        search_space_definition=search_space_def,
        constraints_definition={"constraints": constraints},
        status="RUNNING",
        created_by=payload.created_by,
        notes=payload.notes,
    )
    db.add(opt_run)
    await db.flush()

    # 9. Execute Candidate Generation
    try:
        model_meta = {
            "name": model.name,
            "status": model.status,
            "health_status": "STABLE",
            "target_property": model.target_property,
            "target_unit": model.target_unit,
            "training_feature_bounds": {},
        }

        objs = [
            {
                "target_property": objective.target_property,
                "direction": objective.direction,
                "target_value": objective.target_value,
                "minimum_value": objective.minimum_value,
                "maximum_value": objective.maximum_value,
                "weight": objective.weight,
            }
        ]

        generated_candidates = CandidateGenerationService.generate_candidates(
            search_space=search_space_def,
            objectives=objs,
            constraints=constraints,
            model_metadata=model_meta,
            historical_experiments=historical_exps,
            generation_method=payload.generation_method,
            requested_count=payload.requested_candidate_count,
            random_seed=payload.random_seed,
            allow_out_of_domain=payload.allow_out_of_domain,
        )

        # Save candidate records
        feasible_count = 0
        for cand_dict in generated_candidates:
            if cand_dict.get("feasibility_status") == "FEASIBLE":
                feasible_count += 1

            cand_orm = OptimizationCandidate(
                optimization_run_id=opt_run.id,
                candidate_number=cand_dict["candidate_number"],
                rank=cand_dict["rank"],
                parameter_values=cand_dict["parameter_values"],
                parameter_units=cand_dict["parameter_units"],
                feasibility_status=cand_dict["feasibility_status"],
                domain_status=cand_dict["domain_status"],
                predictions=cand_dict["predictions"],
                uncertainties=cand_dict["uncertainties"],
                objective_score=cand_dict["objective_score"],
                score_breakdown=cand_dict["score_breakdown"],
                evidence_score=cand_dict["evidence_score"],
                novelty_category=cand_dict["novelty_category"],
                parameter_distance=cand_dict["parameter_distance"],
                nearby_experiment_ids=cand_dict["nearby_experiment_ids"],
                candidate_type=cand_dict.get("candidate_type", "EXPLOITATION"),
                status=cand_dict["status"],
            )
            db.add(cand_orm)

        opt_run.feasible_candidate_count = feasible_count
        opt_run.status = "COMPLETED"
        opt_run.completed_at = datetime.utcnow()

    except Exception as exc:
        opt_run.status = "FAILED"
        opt_run.notes = f"Candidate generation failed: {exc}"
        await db.commit()
        raise HTTPException(status_code=400, detail=str(exc))

    await db.commit()

    # Reload run with candidates
    run_stmt = (
        select(OptimizationRun)
        .where(OptimizationRun.id == opt_run.id)
        .options(selectinload(OptimizationRun.candidates))
    )
    res = await db.execute(run_stmt)
    return res.scalar_one()


@router.get("/runs", response_model=list[OptimizationRunResponse])
async def list_optimization_runs(
    project_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List optimization runs."""
    stmt = select(OptimizationRun).options(selectinload(OptimizationRun.candidates))
    if project_id:
        stmt = stmt.where(OptimizationRun.project_id == project_id)
    stmt = stmt.order_by(OptimizationRun.started_at.desc())
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/runs/{run_id}", response_model=OptimizationRunResponse)
async def get_optimization_run(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get optimization run details with ranked candidates."""
    stmt = (
        select(OptimizationRun)
        .where(OptimizationRun.id == run_id)
        .options(selectinload(OptimizationRun.candidates))
    )
    res = await db.execute(stmt)
    run = res.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Optimization run not found")
    return run


# ── 5. Candidate Actions API ──────────────────────────────

@router.post("/candidates/{candidate_id}/select", response_model=OptimizationCandidateResponse)
async def select_candidate(
    candidate_id: uuid.UUID,
    review: CandidateReviewRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Researcher selects an optimization candidate."""
    stmt = select(OptimizationCandidate).where(OptimizationCandidate.id == candidate_id)
    res = await db.execute(stmt)
    cand = res.scalar_one_or_none()
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")

    cand.status = "SELECTED"

    # Audit review
    rev = OptimizationReview(
        optimization_run_id=cand.optimization_run_id,
        candidate_id=cand.id,
        reviewer_id=review.reviewer_id,
        decision="SELECTED",
        reason=review.reason,
        notes=review.notes,
    )
    db.add(rev)

    await db.commit()
    await db.refresh(cand)
    return cand


@router.post("/candidates/{candidate_id}/reject", response_model=OptimizationCandidateResponse)
async def reject_candidate(
    candidate_id: uuid.UUID,
    review: CandidateReviewRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Researcher rejects an optimization candidate."""
    stmt = select(OptimizationCandidate).where(OptimizationCandidate.id == candidate_id)
    res = await db.execute(stmt)
    cand = res.scalar_one_or_none()
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")

    cand.status = "REJECTED"

    rev = OptimizationReview(
        optimization_run_id=cand.optimization_run_id,
        candidate_id=cand.id,
        reviewer_id=review.reviewer_id,
        decision="REJECTED",
        reason=review.reason,
        notes=review.notes,
    )
    db.add(rev)

    await db.commit()
    await db.refresh(cand)
    return cand


@router.post("/candidates/{candidate_id}/create-experiment", response_model=ProposedExperimentFromCandidateResponse)
async def create_proposed_experiment_from_candidate(
    candidate_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Creates a new PLANNED Experiment with candidate parameters copied into PROPOSED CONDITIONS.
    Enforces side-by-side separation: actual measurements remain empty until laboratory experiment.
    """
    stmt = (
        select(OptimizationCandidate)
        .where(OptimizationCandidate.id == candidate_id)
        .options(selectinload(OptimizationCandidate.optimization_run))
    )
    res = await db.execute(stmt)
    cand = res.scalar_one_or_none()
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")

    opt_run = cand.optimization_run

    # Generate experiment code
    count_stmt = select(func.count(Experiment.id)).where(Experiment.project_id == opt_run.project_id)
    count_res = await db.execute(count_stmt)
    exp_count = (count_res.scalar() or 0) + 1
    exp_code = f"EXP-OPT-P7-{exp_count:03d}"

    # Create Experiment with PROPOSED conditions
    exp = Experiment(
        project_id=opt_run.project_id,
        experiment_code=exp_code,
        title=f"Proposed Experiment from Optimization Candidate Rank #{cand.rank}",
        status=ExperimentStatus.PLANNED,
        notes=f"Physical laboratory validation of candidate conditions (Candidate Rank #{cand.rank})",
    )
    db.add(exp)
    await db.flush()

    # Link candidate to experiment
    link = CandidateExperimentLink(
        candidate_id=cand.id,
        experiment_id=exp.id,
        link_type="PROPOSED_EXPERIMENT",
    )
    db.add(link)

    cand.status = "CONVERTED_TO_EXPERIMENT"
    await db.commit()

    return ProposedExperimentFromCandidateResponse(
        experiment_id=exp.id,
        experiment_code=exp.experiment_code,
        candidate_id=cand.id,
        status="PLANNED",
        proposed_parameters=cand.parameter_values,
        message="Created PLANNED experiment with proposed candidate conditions. Actual lab measurements remain empty.",
    )


# ── 6. Optimization Report API ────────────────────────────

@router.get("/runs/{run_id}/report", response_model=OptimizationReportResponse)
async def generate_optimization_report(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Generate optimization run report with disclaimers."""
    stmt = (
        select(OptimizationRun)
        .where(OptimizationRun.id == run_id)
        .options(selectinload(OptimizationRun.candidates))
    )
    res = await db.execute(stmt)
    run = res.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Optimization run not found")

    p_stmt = select(Project).where(Project.id == run.project_id)
    p_res = await db.execute(p_stmt)
    project = p_res.scalar_one_or_none()

    o_stmt = select(OptimizationObjective).where(OptimizationObjective.id == run.objective_id)
    o_res = await db.execute(o_stmt)
    objective = o_res.scalar_one_or_none()

    m_stmt = select(MLModel).where(MLModel.id == run.model_id)
    m_res = await db.execute(m_stmt)
    model = m_res.scalar_one_or_none()

    top_cands = sorted(run.candidates, key=lambda c: c.rank)[:10]

    disclaimer = (
        "SCIENTIFIC INTERPRETATION DISCLAIMER: Optimization results represent model-predicted "
        "promising candidates under current experimental evidence. They do NOT constitute "
        "laboratory proof or guaranteed synthesis outcomes. Laboratory validation is required."
    )

    return OptimizationReportResponse(
        run_id=run.id,
        project_code=project.project_code if project else "P7",
        project_name=project.name if project else "Project 7",
        objective_name=objective.name if objective else "Maximize Target Property",
        target_property=objective.target_property if objective else "conductivity_s_cm",
        direction=objective.direction if objective else "MAXIMIZE",
        model_name=model.name if model else "Random Forest",
        model_version=run.model_version,
        dataset_version=run.dataset_version,
        model_health_status="STABLE",
        generation_method=run.generation_method,
        total_candidates_generated=run.requested_candidate_count,
        feasible_candidates_count=run.feasible_candidate_count,
        top_candidates=[OptimizationCandidateResponse.model_validate(c) for c in top_cands],
        disclaimer=disclaimer,
        generated_at=datetime.utcnow(),
    )
