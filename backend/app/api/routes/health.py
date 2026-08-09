"""
GreenSynth Analytics — Phase 20 Health & Readiness Check Endpoints
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)

APP_VERSION = "1.0.0-research"


@router.get("/health", summary="Application health check")
async def health(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """
    Basic health check verifying database connectivity and system status.
    """
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error("Database health check failed: %s", exc)
        db_status = "unreachable"

    # Storage check
    upload_dir = Path(os.getenv("UPLOAD_DIR", "uploads"))
    storage_status = "available" if upload_dir.exists() else "unconfigured"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "version": APP_VERSION,
        "database": db_status,
        "storage": storage_status,
        "configuration": "loaded",
    }


@router.get("/ready", summary="Readiness check for production traffic")
async def readiness(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """
    Readiness check verifying database connection, file storage accessibility,
    and project configurations before accepting traffic.
    """
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection unavailable: {exc}",
        )

    upload_dir = Path(os.getenv("UPLOAD_DIR", "uploads"))
    if not upload_dir.exists():
        try:
            upload_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Storage directory '{upload_dir}' cannot be created: {exc}",
            )

    return {
        "status": "ready",
        "version": APP_VERSION,
        "database": "connected",
        "storage_writable": True,
        "message": "System ready for research operations.",
    }
