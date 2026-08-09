"""
GreenSynth Analytics — Dashboard API Router

Provides aggregated statistics for the research dashboard.
All data comes from the database — no fabricated values.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", summary="Get dashboard statistics")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Return aggregated statistics for the research dashboard.

    All values are computed from real database records.
    No values are hard-coded or fabricated.
    """
    service = DashboardService(db)
    return await service.get_stats()
