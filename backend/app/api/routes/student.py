"""
GreenSynth Analytics — Student Portal Endpoints

Exposes student-contextualized APIs protected by require_student.
Derives student's assigned project, group, and research statistics automatically
from database relationships without trusting frontend state.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_group,
    get_current_membership,
    get_current_project,
    get_current_user,
    get_db,
    require_student,
)
from app.models.group_membership import GroupMembership
from app.models.project import Project
from app.models.research_group import ResearchGroup
from app.models.user import User
from app.schemas.auth import UserProfile
from app.schemas.common import APIResponse
from app.schemas.group import GroupDetailResponse
from app.schemas.project import ProjectResponse
from app.services.auth_service import AuthService
from app.services.dashboard_service import DashboardService
from app.services.group_service import GroupService

router = APIRouter(
    prefix="/student",
    tags=["Student Portal"],
    dependencies=[Depends(require_student)],
)


@router.get(
    "/me",
    response_model=APIResponse[UserProfile],
    status_code=status.HTTP_200_OK,
    summary="Get Student Profile and Authorization Context",
)
async def get_student_profile(
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[UserProfile]:
    """Returns the authenticated student's profile including active memberships and project."""
    auth_service = AuthService(db)
    profile = await auth_service.get_user_profile(current_user)
    return APIResponse(
        data=profile,
        message="Student profile retrieved successfully.",
    )


@router.get(
    "/project",
    response_model=APIResponse[ProjectResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Student's Authorized Project",
    description="Returns the synthesis project assigned to the student's active research group.",
)
async def get_student_authorized_project(
    current_project: Project = Depends(get_current_project),
    current_user: User = Depends(require_student),
) -> APIResponse[ProjectResponse]:
    """Returns the project assigned to the student's active research group."""
    return APIResponse(
        data=ProjectResponse.model_validate(current_project),
        message=f"Authorized project {current_project.project_code} retrieved successfully.",
    )


@router.get(
    "/group",
    response_model=APIResponse[GroupDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Student's Active Research Group",
    description="Returns the active research group for the student including group leader and members.",
)
async def get_student_active_group(
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[GroupDetailResponse]:
    """Returns the active research group for the student."""
    service = GroupService(db)
    detail = await service.get_my_group(current_user)
    return APIResponse(
        data=detail,
        message="Student research group retrieved successfully.",
    )


@router.get(
    "/dashboard",
    status_code=status.HTTP_200_OK,
    summary="Get Student's Project-Scoped Dashboard Statistics",
    description="Returns aggregated metrics strictly scoped to the student's authorized project.",
)
async def get_student_dashboard_stats(
    current_project: Project = Depends(get_current_project),
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Returns dashboard statistics scoped strictly to the student's assigned project."""
    service = DashboardService(db)
    return await service.get_stats(project_id=current_project.id)
