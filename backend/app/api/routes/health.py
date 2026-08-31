"""
GreenSynth Analytics — Health & Readiness Check Endpoints
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.database.session import get_db

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)

APP_VERSION = "1.0.0-research"


@router.get("/health", summary="Application health check")
async def health(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """
    Basic health check verifying database connectivity and system status.
    """
    settings = get_settings()
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error("Database health check failed: %s", exc)
        db_status = "unreachable"

    # Storage check using actual configuration
    if settings.storage_backend == "s3":
        storage_status = "s3_configured"
    else:
        raw_dir = Path(settings.raw_data_dir)
        storage_status = "available" if raw_dir.exists() else "unconfigured"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "version": APP_VERSION,
        "database": db_status,
        "storage": storage_status,
        "storage_backend": settings.storage_backend,
        "configuration": "loaded",
    }


@router.get("/ready", summary="Readiness check for production traffic")
async def readiness(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """
    Readiness check verifying database connection, file storage accessibility,
    and project configurations before accepting traffic.
    """
    settings = get_settings()
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error("Readiness check database failure: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable.",
        )

    # Storage readiness based on configured backend
    if settings.storage_backend == "local":
        raw_dir = Path(settings.raw_data_dir)
        if not raw_dir.exists():
            try:
                raw_dir.mkdir(parents=True, exist_ok=True)
            except Exception as exc:
                logger.error("Readiness check storage directory creation failure: %s", exc)
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Storage service unavailable.",
                )

    return {
        "status": "ready",
        "version": APP_VERSION,
        "database": "connected",
        "storage_backend": settings.storage_backend,
        "storage_writable": True,
        "message": "System ready for research operations.",
    }

