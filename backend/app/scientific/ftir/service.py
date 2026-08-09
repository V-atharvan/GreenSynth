"""
GreenSynth Analytics — FTIR Analysis Service

Orchestrates FTIR spectrum parsing, Savitzky-Golay noise smoothing, peak detection,
preprocessed file disk storage, database persistence, researcher peak annotations, and audit logs.
"""

from __future__ import annotations

import io
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.models.analysis import (
    AnalysisRun,
    AnalysisStatus,
    FTIRAnnotation,
    ProcessedFile,
    XRDPeak,
)
from app.models.characterization import Characterization, RawFile
from app.models.experiment import Experiment
from app.models.project import Project
from app.models.sample import Sample
from app.scientific.ftir.parser import parse_ftir_file
from app.scientific.ftir.peaks import detect_ftir_peaks
from app.scientific.ftir.preprocessing import preprocess_ftir_spectrum
from app.scientific.ftir.schemas import (
    FTIRAnalysisInput,
    FTIRAnnotationCreate,
    FTIRDataPoint,
    FTIRPeakItem,
    FTIRProcessedResponse,
)
from app.services.audit_service import AuditService
from app.services.characterization_service import (
    CharacterizationNotFoundError,
    RawFileNotFoundError,
)
from app.storage.local import LocalFileStorage

logger = logging.getLogger(__name__)


class FTIRAnalysisService:
    """Service layer for FTIR spectroscopy analysis and researcher annotations."""

    def __init__(self, db: AsyncSession, storage: LocalFileStorage | None = None) -> None:
        self.db = db
        self.storage = storage or LocalFileStorage()
        self.audit = AuditService(db)

    async def run_analysis(
        self,
        characterization_id: uuid.UUID,
        input_data: FTIRAnalysisInput,
        raw_file_id: uuid.UUID | None = None,
        created_by: str | None = None,
    ) -> AnalysisRun:
        """Execute FTIR spectrum preprocessing & peak detection."""
        ch_res = await self.db.execute(
            select(Characterization)
            .options(selectinload(Characterization.raw_files))
            .where(Characterization.id == characterization_id)
        )
        ch = ch_res.scalar_one_or_none()
        if ch is None:
            raise CharacterizationNotFoundError(f"Characterization {characterization_id} not found.")

        if ch.technique != "FTIR":
            raise ValueError(f"Characterization technique '{ch.technique}' is not FTIR.")

        raw_file: RawFile | None = None
        if raw_file_id:
            raw_file = next((f for f in ch.raw_files if f.id == raw_file_id), None)
        elif ch.raw_files:
            raw_file = ch.raw_files[-1]

        if not raw_file:
            raise RawFileNotFoundError(
                f"No raw files uploaded for FTIR characterization {characterization_id}."
            )

        file_bytes = await self.storage.retrieve(raw_file.storage_path)

        run = AnalysisRun(
            characterization_id=ch.id,
            input_file_id=raw_file.id,
            analysis_type="FTIR",
            status=AnalysisStatus.RUNNING.value,
            software_version="0.1.0",
            parameters=input_data.model_dump(),
            notes=input_data.notes,
            created_by=created_by,
        )
        self.db.add(run)
        await self.db.flush()

        try:
            # 1. Parse raw data
            parsed = parse_ftir_file(file_bytes, raw_file.file_extension)

            # 2. Preprocess spectrum
            proc_sig = preprocess_ftir_spectrum(
                parsed.wavenumber,
                parsed.signal,
                smoothing=input_data.preprocessing.smoothing,
                savgol_window=input_data.preprocessing.savgol_window,
                savgol_polyorder=input_data.preprocessing.savgol_polyorder,
            )

            # 3. Detect FTIR peaks / absorption bands
            detected_peaks = detect_ftir_peaks(
                parsed.wavenumber,
                proc_sig,
                signal_type=parsed.signal_type,
                prominence=input_data.peak_detection.prominence,
                min_distance=input_data.peak_detection.min_distance,
            )

            # 4. Save preprocessed curve under data/processed/
            sample_res = await self.db.execute(
                select(Sample, Experiment, Project)
                .join(Experiment, Sample.experiment_id == Experiment.id)
                .join(Project, Experiment.project_id == Project.id)
                .where(Sample.id == ch.sample_id)
            )
            row = sample_res.one()
            sample, exp, proj = row[0], row[1], row[2]

            proc_df = pd.DataFrame({
                "wavenumber_cm1": parsed.wavenumber,
                "signal": proc_sig,
            })
            csv_buf = io.StringIO()
            proc_df.to_csv(csv_buf, index=False)
            proc_bytes = csv_buf.getvalue().encode("utf-8")

            settings = get_settings()
            processed_root = Path(getattr(settings, "processed_data_dir", "data/processed")).resolve()
            rel_proc_path = f"{proj.project_code}/{exp.experiment_code}/{sample.sample_code}/ftir/{run.id!s}_processed.csv"
            dest_proc_path = processed_root / rel_proc_path
            dest_proc_path.parent.mkdir(parents=True, exist_ok=True)

            with open(dest_proc_path, "wb") as pf:
                pf.write(proc_bytes)

            proc_file = ProcessedFile(
                analysis_run_id=run.id,
                raw_file_id=raw_file.id,
                stored_path=str(rel_proc_path),
                processing_method=f"Savitzky-Golay smoothing ({parsed.signal_type})",
                processing_parameters=input_data.model_dump(),
            )
            self.db.add(proc_file)

            # 5. Store detected peaks in XRDPeak table (generic peak store)
            for p in detected_peaks:
                peak_obj = XRDPeak(
                    analysis_run_id=run.id,
                    peak_position=p.wavenumber_cm1,
                    intensity=p.signal_value,
                    prominence=p.prominence,
                    width=p.width_cm1,
                    detection_parameters={"signal_type": parsed.signal_type},
                )
                self.db.add(peak_obj)

            run.status = AnalysisStatus.COMPLETED.value
            run.completed_at = datetime.now(timezone.utc)
            run.assumptions = {
                "signal_type": parsed.signal_type,
                "total_peaks_detected": len(detected_peaks),
            }
            await self.db.flush()

            await self.audit.log(
                entity_type="AnalysisRun",
                entity_id=run.id,
                action="FTIR_ANALYSIS_RUN",
                changes={"signal_type": parsed.signal_type, "peaks_count": len(detected_peaks)},
            )

        except Exception as exc:
            run.status = AnalysisStatus.FAILED.value
            run.error_message = str(exc)
            run.completed_at = datetime.now(timezone.utc)
            await self.db.flush()
            logger.error("FTIR analysis run %s failed: %s", run.id, exc)
            raise

        return await self.get_analysis_run(run.id)

    async def get_analysis_run(self, analysis_run_id: uuid.UUID) -> AnalysisRun:
        """Return AnalysisRun with peaks, calculated properties, and processed files."""
        result = await self.db.execute(
            select(AnalysisRun)
            .options(
                selectinload(AnalysisRun.peaks),
                selectinload(AnalysisRun.calculated_properties),
                selectinload(AnalysisRun.processed_files),
            )
            .where(AnalysisRun.id == analysis_run_id)
        )
        run = result.scalar_one_or_none()
        if run is None:
            raise ValueError(f"AnalysisRun {analysis_run_id} not found.")
        return run

    async def get_ftir_data(self, analysis_run_id: uuid.UUID) -> FTIRProcessedResponse:
        """Return FTIR spectrum data points and detected peaks list."""
        run = await self.get_analysis_run(analysis_run_id)
        if not run.processed_files:
            raise ValueError(f"No processed spectrum data found for analysis run {analysis_run_id}.")

        proc_file = run.processed_files[0]
        settings = get_settings()
        processed_root = Path(getattr(settings, "processed_data_dir", "data/processed")).resolve()
        file_path = processed_root / proc_file.stored_path

        if not file_path.exists():
            raise FileNotFoundError(f"Processed spectrum file missing at {file_path}")

        df = pd.read_csv(file_path)
        data_points: list[FTIRDataPoint] = []
        for _, r in df.iterrows():
            data_points.append(
                FTIRDataPoint(
                    wavenumber_cm1=float(r["wavenumber_cm1"]),
                    signal_value=float(r["signal"]),
                )
            )

        peaks: list[FTIRPeakItem] = []
        for p in run.peaks:
            peaks.append(
                FTIRPeakItem(
                    wavenumber_cm1=p.peak_position,
                    signal_value=p.intensity,
                    prominence=p.prominence or 0.0,
                    width_cm1=p.width or 0.0,
                )
            )

        sig_type = run.assumptions.get("signal_type", "TRANSMITTANCE") if run.assumptions else "TRANSMITTANCE"

        return FTIRProcessedResponse(
            analysis_run_id=analysis_run_id,
            signal_type=sig_type,
            data_points=data_points,
            detected_peaks=peaks,
            total_points=len(data_points),
        )

    async def add_annotation(
        self,
        analysis_run_id: uuid.UUID,
        payload: FTIRAnnotationCreate,
        created_by: str | None = None,
    ) -> FTIRAnnotation:
        """Add researcher peak annotation for a specific wavenumber."""
        run = await self.get_analysis_run(analysis_run_id)

        ann = FTIRAnnotation(
            analysis_run_id=run.id,
            wavenumber_cm1=payload.wavenumber_cm1,
            label=payload.label,
            interpretation=payload.interpretation,
            confidence=payload.confidence,
            created_by=created_by,
            notes=payload.notes,
        )
        self.db.add(ann)
        await self.db.flush()

        await self.audit.log(
            entity_type="FTIRAnnotation",
            entity_id=ann.id,
            action="ADD_FTIR_ANNOTATION",
            changes={"label": ann.label, "wavenumber": ann.wavenumber_cm1},
        )
        return ann

    async def list_annotations(self, analysis_run_id: uuid.UUID) -> list[FTIRAnnotation]:
        """List all researcher peak annotations for an FTIR analysis run."""
        res = await self.db.execute(
            select(FTIRAnnotation)
            .where(FTIRAnnotation.analysis_run_id == analysis_run_id)
            .order_by(FTIRAnnotation.wavenumber_cm1.asc())
        )
        return list(res.scalars().all())
