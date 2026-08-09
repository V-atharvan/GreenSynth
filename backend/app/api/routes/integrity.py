"""
GreenSynth Analytics — Phase 20 Data Integrity & Audit APIs
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.scientific.verification.integrity import DataIntegrityService

router = APIRouter(prefix="/integrity", tags=["integrity"])


@router.get("/report", summary="Generate research data integrity audit report")
async def get_integrity_report(
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Returns a full audit report of system record counts, lineage, and file integrity."""
    return await DataIntegrityService.generate_integrity_report(db)


@router.post("/verify-storage", summary="Run SHA-256 storage verification")
async def verify_storage(
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Recalculates cryptographic SHA-256 hashes of raw files and verifies storage integrity."""
    return await DataIntegrityService.verify_storage(db)


@router.post("/verify-database", summary="Run database relational integrity check")
async def verify_database(
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Performs relational orphan check across database models."""
    return await DataIntegrityService.verify_database(db)
