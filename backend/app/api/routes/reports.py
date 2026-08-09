"""
GreenSynth Analytics — Scientific PDF Reporting API Endpoints
"""

from __future__ import annotations

import io
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.reporting.schemas import ExperimentReportData
from app.reporting.service import ReportService

router = APIRouter(prefix="/reports", tags=["reporting"])


@router.get(
    "/experiments/{experiment_id}/pdf",
    summary="Generate formal scientific PDF report for experiment",
    response_class=StreamingResponse,
)
async def download_experiment_pdf_report(
    experiment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Generates and returns a downloadable formal PDF scientific report for an experiment.
    """
    try:
        pdf_bytes, filename = await ReportService.generate_experiment_pdf_report(experiment_id, db)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF report generation failed: {exc}",
        )

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


@router.get(
    "/experiments/{experiment_id}/summary",
    response_model=ExperimentReportData,
    summary="Get JSON metadata summary for experiment report",
)
async def get_experiment_report_summary(
    experiment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Returns JSON report DTO metadata summary before generating PDF."""
    try:
        return await ReportService.get_experiment_report_summary(experiment_id, db)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
