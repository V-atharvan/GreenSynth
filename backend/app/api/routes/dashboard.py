"""
GreenSynth Analytics — Dashboard API Router

Provides aggregated statistics for the research dashboard.
Admin gets global system-wide stats or specific project stats; Student gets project-scoped stats.
All data comes from the database — no fabricated values.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_project, get_current_user, get_db, verify_project_access
from app.models.project import Project
from app.models.user import User
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", summary="Get dashboard statistics")
async def get_dashboard_stats(
    project_id: uuid.UUID | None = Query(default=None, description="Optional project ID filter (Admin only)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Return aggregated statistics for the research dashboard.
    - Admin: Global system stats across all projects (or filtered by project_id).
    - Student: Strictly scoped to the student's authorized project.
    """
    service = DashboardService(db)

    if current_user.is_admin:
        return await service.get_stats(project_id=project_id)

    # Student user
    current_project = await get_current_project(current_user=current_user, db=db)
    if project_id is not None:
        verify_project_access(project_id, current_project, current_user)

    return await service.get_stats(project_id=current_project.id)
