"""
GreenSynth Analytics — Administrator Endpoints

Exposes system-wide administrative oversight APIs protected by require_admin.
All endpoints require active Admin account credentials (account_type == "ADMIN").
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, require_admin
from app.models.characterization import Characterization
from app.models.experiment import Experiment
from app.models.ml import MLModel
from app.models.optimization import OptimizationRun
from app.models.project import Project, ProjectStatus
from app.models.recommendation import Recommendation
from app.models.research_group import GroupStatus, ResearchGroup
from app.models.sample import Sample
from app.models.user import User, UserRole
from app.schemas.admin import AdminOverviewResponse
from app.schemas.auth import UserRead, UserStatusUpdateRequest
from app.schemas.common import APIResponse
from app.schemas.experiment import ExperimentSummary
from app.schemas.group import GroupDetailResponse
from app.schemas.project import ProjectSummary
from app.schemas.sample import SampleSummary

router = APIRouter(
    prefix="/admin",
    tags=["Administrator Management"],
    dependencies=[Depends(require_admin)],
)


@router.get(
    "/overview",
    response_model=APIResponse[AdminOverviewResponse],
    status_code=status.HTTP_200_OK,
    summary="Get System-Wide Administrator Overview Metrics",
    description="Calculates system-wide aggregate metrics across all projects, groups, experiments, and ML models.",
)
async def get_admin_overview(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> APIResponse[AdminOverviewResponse]:
    """Retrieve global system metrics for Platform Administrators."""
    # 1. Total Projects
    res_proj = await db.execute(
        select(func.count(Project.id)).where(Project.status == ProjectStatus.ACTIVE.value)
    )
    total_projects = res_proj.scalar() or 0

    # 2. Total Groups
    res_grp = await db.execute(
        select(func.count(ResearchGroup.id)).where(ResearchGroup.status == GroupStatus.ACTIVE.value)
    )
    total_groups = res_grp.scalar() or 0

    # 3. Total Students
    res_stu = await db.execute(
        select(func.count(User.id)).where(User.role != UserRole.ADMIN)
    )
    total_students = res_stu.scalar() or 0

    # 4. Total Experiments
    res_exp = await db.execute(select(func.count(Experiment.id)))
    total_experiments = res_exp.scalar() or 0

    # 5. Total Samples
    res_smp = await db.execute(select(func.count(Sample.id)))
    total_samples = res_smp.scalar() or 0

    # 6. Total Characterizations
    res_char = await db.execute(select(func.count(Characterization.id)))
    total_characterizations = res_char.scalar() or 0

    # 7. Total ML Models
    res_ml = await db.execute(select(func.count(MLModel.id)))
    total_ml_models = res_ml.scalar() or 0

    # 8. Total Recommendations
    res_rec = await db.execute(select(func.count(Recommendation.id)))
    total_recommendations = res_rec.scalar() or 0

    # 9. Total Optimization Runs
    res_opt = await db.execute(select(func.count(OptimizationRun.id)))
    total_optimization_runs = res_opt.scalar() or 0

    overview = AdminOverviewResponse(
        total_projects=total_projects,
        total_groups=total_groups,
        total_students=total_students,
        total_experiments=total_experiments,
        total_samples=total_samples,
        total_characterizations=total_characterizations,
        total_ml_models=total_ml_models,
        total_recommendations=total_recommendations,
        total_optimization_runs=total_optimization_runs,
    )

    return APIResponse(
        data=overview,
        message="System-wide administrator overview retrieved successfully.",
    )


@router.get(
    "/projects",
    response_model=APIResponse[list[ProjectSummary]],
    status_code=status.HTTP_200_OK,
    summary="List All System Projects (Admin)",
    description="Returns all active synthesis projects (P1 through P8).",
)
async def list_admin_projects(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> APIResponse[list[ProjectSummary]]:
    """Retrieve all synthesis projects."""
    query = (
        select(Project)
        .where(Project.status == ProjectStatus.ACTIVE.value)
        .order_by(Project.project_code.asc())
    )
    result = await db.execute(query)
    projects = result.scalars().all()
    return APIResponse(
        data=[ProjectSummary.model_validate(p) for p in projects],
        message="All synthesis projects retrieved successfully.",
    )


@router.get(
    "/groups",
    response_model=APIResponse[list[GroupDetailResponse]],
    status_code=status.HTTP_200_OK,
    summary="List All Research Groups (Admin)",
    description="Returns all registered research groups across all projects.",
)
async def list_admin_groups(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> APIResponse[list[GroupDetailResponse]]:
    """Retrieve all research groups with leaders and project links."""
    from app.services.group_service import GroupService

    service = GroupService(db)
    groups = await service.list_all_groups()
    return APIResponse(
        data=groups,
        message="All research groups retrieved successfully.",
    )


@router.get(
    "/users",
    response_model=APIResponse[list[UserRead]],
    status_code=status.HTTP_200_OK,
    summary="List All System Users (Admin)",
    description="Returns all user accounts registered in the platform without exposing password hashes.",
)
async def list_admin_users(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> APIResponse[list[UserRead]]:
    """Retrieve all registered users."""
    query = select(User).order_by(User.created_at.desc())
    result = await db.execute(query)
    users = result.scalars().all()
    return APIResponse(
        data=[UserRead.model_validate(u) for u in users],
        message="All system users retrieved successfully.",
    )


@router.patch(
    "/users/{user_id}/status",
    response_model=APIResponse[UserRead],
    status_code=status.HTTP_200_OK,
    summary="Update User Account Active Status (Admin)",
    description="Allows administrators to activate or deactivate user accounts.",
)
async def update_user_status(
    user_id: uuid.UUID,
    payload: UserStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> APIResponse[UserRead]:
    """Toggle user active status (Admin only)."""
    from app.services.auth_service import AuthService

    service = AuthService(db)
    updated_user = await service.update_user_status(user_id, payload.is_active, admin_user)
    return APIResponse(
        data=updated_user,
        message=f"User status updated to {'Active' if payload.is_active else 'Inactive'}.",
    )



@router.get(
    "/experiments",
    response_model=APIResponse[list[ExperimentSummary]],
    status_code=status.HTTP_200_OK,
    summary="List All Experiments (Admin)",
    description="Returns experiments across all synthesis projects with optional project filtering.",
)
async def list_admin_experiments(
    project_id: Optional[uuid.UUID] = Query(default=None, description="Optional Project UUID filter"),
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> APIResponse[list[ExperimentSummary]]:
    """Retrieve experiments system-wide."""
    query = select(Experiment).order_by(Experiment.created_at.desc())
    if project_id:
        query = query.where(Experiment.project_id == project_id)

    result = await db.execute(query)
    experiments = result.scalars().all()
    return APIResponse(
        data=[ExperimentSummary.model_validate(e) for e in experiments],
        message="Experiments retrieved successfully.",
    )


@router.get(
    "/samples",
    response_model=APIResponse[list[SampleSummary]],
    status_code=status.HTTP_200_OK,
    summary="List All Samples (Admin)",
    description="Returns samples across all projects with optional experiment filtering.",
)
async def list_admin_samples(
    experiment_id: Optional[uuid.UUID] = Query(default=None, description="Optional Experiment UUID filter"),
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> APIResponse[list[SampleSummary]]:
    """Retrieve synthesized samples system-wide."""
    query = select(Sample).order_by(Sample.created_at.desc())
    if experiment_id:
        query = query.where(Sample.experiment_id == experiment_id)

    result = await db.execute(query)
    samples = result.scalars().all()
    return APIResponse(
        data=[SampleSummary.model_validate(s) for s in samples],
        message="Samples retrieved successfully.",
    )
