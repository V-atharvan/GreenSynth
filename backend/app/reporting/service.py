"""
GreenSynth Analytics — Report Service Facade

High-level service interface for generating formal scientific PDF reports.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.reporting.builder import ExperimentReportDataBuilder
from app.reporting.renderer import PDFReportRenderer
from app.reporting.schemas import ExperimentReportData


class ReportService:
    """
    Service facade orchestrating data DTO collection and ReportLab PDF rendering.
    """

    @classmethod
    async def generate_experiment_pdf_report(
        cls, experiment_id: uuid.UUID, db: AsyncSession
    ) -> tuple[bytes, str]:
        """
        Generates formal PDF report bytes and formatted filename for an experiment.

        Returns:
            (pdf_bytes, filename)
        """
        data: ExperimentReportData = await ExperimentReportDataBuilder.build_experiment_report_data(
            experiment_id, db
        )
        pdf_bytes = PDFReportRenderer.render_experiment_report(data)
        filename = f"Experiment_Report_{data.experiment_code}.pdf"
        return pdf_bytes, filename

    @classmethod
    async def get_experiment_report_summary(
        cls, experiment_id: uuid.UUID, db: AsyncSession
    ) -> ExperimentReportData:
        """
        Returns JSON summary DTO for an experiment report prior to downloading PDF.
        """
        return await ExperimentReportDataBuilder.build_experiment_report_data(experiment_id, db)
