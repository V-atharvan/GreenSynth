"""
GreenSynth Analytics — Recommendation Engine REST API Router

Endpoints for generating human-in-the-loop candidate recommendations, reviewing candidates,
modifying candidate parameters, and pre-filling PLANNED laboratory experiments with authorization.
"""

from __future__ import annotations

import logging
import uuid
from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_authorized_project_ids,
    get_current_project,
    get_current_user,
    get_db,
    verify_project_access,
)
from app.models.project import Project
from app.models.recommendation import Recommendation, RecommendationCandidate
from app.models.user import User
from app.optimization.recommendation.recommendation_service import RecommendationService
from app.optimization.recommendation.schemas import (
    CandidateModifyInput,
    RecommendationCandidateResponse,
    RecommendationGenerateInput,
    RecommendationResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recommendations", tags=["Recommendation Engine"])


@router.post(
    "/generate",
    response_model=RecommendationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate ranked candidate experimental conditions",
)
async def generate_recommendations(
    payload: RecommendationGenerateInput,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RecommendationResponse:
    """Generates ranked experimental candidates for an objective using a validated ML model."""
    if not current_user.is_admin:
        current_project = await get_current_project(current_user=current_user, db=db)
        verify_project_access(payload.project_id, current_project, current_user)

    service = RecommendationService(db)
    try:
        rec = await service.generate_recommendations(payload)
        return RecommendationResponse.model_validate(rec)
    except ValueError as exc:
        logger.error("Recommendation Generation Error: %s", exc, exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get(
    "",
    response_model=list[RecommendationResponse],
    summary="List recommendation sessions",
)
async def list_recommendations(
    project_id: uuid.UUID | None = Query(default=None, description="Optional project ID filter"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[RecommendationResponse]:
    """List recommendation sessions for authorized project scope."""
    q = select(Recommendation).order_by(Recommendation.generated_at.desc())

    if not current_user.is_admin:
        current_project = await get_current_project(current_user=current_user, db=db)
        if project_id is not None:
            verify_project_access(project_id, current_project, current_user)
        q = q.where(Recommendation.project_id == current_project.id)
    elif project_id is not None:
        q = q.where(Recommendation.project_id == project_id)

    res = await db.execute(q)
    recs = res.scalars().all()
    return [RecommendationResponse.model_validate(r) for r in recs]


@router.get(
    "/{id}",
    response_model=RecommendationResponse,
    summary="Get recommendation session details",
)
async def get_recommendation(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RecommendationResponse:
    """Get recommendation session details with ranked candidates and IDOR protection."""
    service = RecommendationService(db)
    try:
        rec = await service.get_recommendation(id)
        if not current_user.is_admin:
            auth_ids = await get_authorized_project_ids(current_user, db)
            if rec.project_id not in auth_ids:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation session not found.")
        return RecommendationResponse.model_validate(rec)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/candidates/{candidate_id}/approve",
    response_model=RecommendationCandidateResponse,
    summary="Approve recommendation candidate",
)
async def approve_candidate(
    candidate_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RecommendationCandidateResponse:
    """Approves a recommendation candidate for laboratory experiment creation with IDOR protection."""
    res = await db.execute(
        select(RecommendationCandidate, Recommendation.project_id)
        .join(Recommendation, RecommendationCandidate.recommendation_id == Recommendation.id)
        .where(RecommendationCandidate.id == candidate_id)
    )
    row = res.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found.")

    cand, p_id = row
    if not current_user.is_admin:
        auth_ids = await get_authorized_project_ids(current_user, db)
        if p_id not in auth_ids:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found.")

    service = RecommendationService(db)
    try:
        cand_updated = await service.approve_candidate(candidate_id)
        return RecommendationCandidateResponse.model_validate(cand_updated)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post(
    "/candidates/{candidate_id}/modify",
    response_model=RecommendationCandidateResponse,
    summary="Modify candidate parameter values",
)
async def modify_candidate(
    candidate_id: uuid.UUID,
    payload: CandidateModifyInput,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RecommendationCandidateResponse:
    """Stores researcher modifications to proposed candidate synthesis conditions (preserves original vs modified)."""
    res = await db.execute(
        select(RecommendationCandidate, Recommendation.project_id)
        .join(Recommendation, RecommendationCandidate.recommendation_id == Recommendation.id)
        .where(RecommendationCandidate.id == candidate_id)
    )
    row = res.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found.")

    cand, p_id = row
    if not current_user.is_admin:
        auth_ids = await get_authorized_project_ids(current_user, db)
        if p_id not in auth_ids:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found.")

    service = RecommendationService(db)
    try:
        cand_updated = await service.modify_candidate(candidate_id, payload)
        return RecommendationCandidateResponse.model_validate(cand_updated)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post(
    "/candidates/{candidate_id}/create-experiment",
    status_code=status.HTTP_201_CREATED,
    summary="Create PLANNED laboratory experiment from candidate",
)
async def create_experiment_from_candidate(
    candidate_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Pre-fills a PLANNED laboratory experiment from an approved recommendation candidate."""
    res = await db.execute(
        select(RecommendationCandidate, Recommendation.project_id)
        .join(Recommendation, RecommendationCandidate.recommendation_id == Recommendation.id)
        .where(RecommendationCandidate.id == candidate_id)
    )
    row = res.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found.")

    cand, p_id = row
    if not current_user.is_admin:
        auth_ids = await get_authorized_project_ids(current_user, db)
        if p_id not in auth_ids:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found.")

    service = RecommendationService(db)
    try:
        exp = await service.create_experiment_from_candidate(candidate_id)
        return {
            "message": "PLANNED experiment created successfully from recommendation candidate.",
            "experiment_id": str(exp.id),
            "experiment_code": exp.experiment_code,
            "status": exp.status,
        }
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
