"""
GreenSynth Analytics — XRD Analysis Service

Orchestrates parsing, preprocessing, peak detection, Scherrer crystallite size calculation,
processed data storage, and DB persistence for XRD characterizations.
"""

from __future__ import annotations

import io
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.models.analysis import (
    AnalysisRun,
    AnalysisStatus,
    CalculatedProperty,
    ProcessedFile,
    XRDPeak,
)
from app.models.characterization import Characterization, RawFile
from app.models.experiment import Experiment
from app.models.project import Project
from app.models.sample import Sample
from app.scientific.xrd.crystallite_size import (
    ScherrerCalculationError,
    calculate_scherrer_crystallite_size,
)
from app.scientific.xrd.peaks import detect_xrd_peaks
from app.scientific.xrd.preprocessing import (
    apply_savitzky_golay_smoothing,
    subtract_rolling_baseline,
)
from app.scientific.xrd.parser import parse_xrd_file
from app.scientific.xrd.schemas import XRDAnalysisInput, XRDDataPoint, XRDProcessedDataResponse
from app.services.audit_service import AuditService
from app.services.characterization_service import CharacterizationNotFoundError, RawFileNotFoundError
from app.storage.local import LocalFileStorage

logger = logging.getLogger(__name__)


class XRDAnalysisService:
    """Service layer for XRD analysis execution and result queries."""

    def __init__(self, db: AsyncSession, storage: LocalFileStorage | None = None) -> None:
        self.db = db
        self.storage = storage or LocalFileStorage()
        self.audit = AuditService(db)

    async def run_analysis(
        self,
        characterization_id: uuid.UUID,
        input_data: XRDAnalysisInput,
        raw_file_id: uuid.UUID | None = None,
        created_by: str | None = None,
    ) -> AnalysisRun:
        """
        Execute full XRD analysis workflow on a raw dataset file.

        Does NOT alter or overwrite the original raw file.
        Saves preprocessed curves under data/processed/.
        """
        # Fetch characterization
        ch_res = await self.db.execute(
            select(Characterization)
            .options(selectinload(Characterization.raw_files))
            .where(Characterization.id == characterization_id)
        )
        ch = ch_res.scalar_one_or_none()
        if ch is None:
            raise CharacterizationNotFoundError(f"Characterization {characterization_id} not found.")

        if ch.technique != "XRD":
            raise ValueError(f"Characterization technique '{ch.technique}' is not XRD.")

        # Locate raw file
        raw_file: RawFile | None = None
        if raw_file_id:
            raw_file = next((f for f in ch.raw_files if f.id == raw_file_id), None)
        elif ch.raw_files:
            raw_file = ch.raw_files[-1]

        if not raw_file:
            raise RawFileNotFoundError(
                f"No raw files uploaded for XRD characterization {characterization_id}."
            )

        # Retrieve raw file bytes from storage
        file_bytes = await self.storage.retrieve(raw_file.storage_path)

        # Create AnalysisRun record with RUNNING status
        run = AnalysisRun(
            characterization_id=ch.id,
            input_file_id=raw_file.id,
            analysis_type="XRD",
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
            parsed = parse_xrd_file(file_bytes, raw_file.file_extension)
            arr_theta = parsed.two_theta
            arr_raw_int = parsed.intensity

            # 2. Preprocessing
            y_proc = arr_raw_int.copy()

            if input_data.preprocessing.baseline_subtraction:
                y_proc = subtract_rolling_baseline(
                    y_proc, window_size=input_data.preprocessing.baseline_window
                )

            if input_data.preprocessing.smoothing:
                y_proc = apply_savitzky_golay_smoothing(
                    y_proc,
                    window_length=input_data.preprocessing.savgol_window,
                    polyorder=input_data.preprocessing.savgol_polyorder,
                )

            # 3. Store processed curve under data/processed/
            sample_res = await self.db.execute(
                select(Sample, Experiment, Project)
                .join(Experiment, Sample.experiment_id == Experiment.id)
                .join(Project, Experiment.project_id == Project.id)
                .where(Sample.id == ch.sample_id)
            )
            row = sample_res.one()
            sample, exp, proj = row[0], row[1], row[2]

            proc_df = pd.DataFrame({
                "two_theta": arr_theta,
                "raw_intensity": arr_raw_int,
                "processed_intensity": y_proc,
            })
            csv_buf = io.StringIO()
            proc_df.to_csv(csv_buf, index=False)
            proc_bytes = csv_buf.getvalue().encode("utf-8")

            settings = get_settings()
            processed_root = Path(getattr(settings, "processed_data_dir", "data/processed")).resolve()
            rel_proc_path = f"{proj.project_code}/{exp.experiment_code}/{sample.sample_code}/xrd/{run.id!s}_processed.csv"
            dest_proc_path = processed_root / rel_proc_path
            dest_proc_path.parent.mkdir(parents=True, exist_ok=True)

            with open(dest_proc_path, "wb") as pf:
                pf.write(proc_bytes)

            proc_file = ProcessedFile(
                analysis_run_id=run.id,
                raw_file_id=raw_file.id,
                stored_path=str(rel_proc_path),
                processing_method="Baseline subtraction + Savitzky-Golay smoothing",
                processing_parameters=input_data.preprocessing.model_dump(),
            )
            self.db.add(proc_file)

            # 4. Peak Detection
            detected_peaks = detect_xrd_peaks(
                arr_theta,
                y_proc,
                prominence=input_data.peak_detection.prominence,
                height=input_data.peak_detection.min_height,
                distance=input_data.peak_detection.min_distance,
            )

            created_peaks: list[XRDPeak] = []
            for dp in detected_peaks:
                peak_obj = XRDPeak(
                    analysis_run_id=run.id,
                    peak_position=dp.two_theta,
                    intensity=dp.intensity,
                    fwhm=dp.fwhm,
                    prominence=dp.prominence,
                    width=dp.width_degrees,
                    detection_parameters=input_data.peak_detection.model_dump(),
                )
                self.db.add(peak_obj)
                created_peaks.append(peak_obj)

            # 5. Scherrer Crystallite Size Calculation
            assumptions_log: dict = {"peaks_detected": len(created_peaks)}

            if input_data.scherrer.calculate_crystallite_size and created_peaks:
                # Find peak with valid FWHM and highest intensity
                candidate_peak = next((p for p in created_peaks if p.fwhm and p.fwhm > 0), None)

                if candidate_peak:
                    try:
                        sch_res = calculate_scherrer_crystallite_size(
                            peak_position_2theta_deg=candidate_peak.peak_position,
                            fwhm_deg=candidate_peak.fwhm,
                            wavelength_nm=input_data.scherrer.wavelength_nm,
                            shape_factor_k=input_data.scherrer.shape_factor_k,
                        )

                        calc_prop = CalculatedProperty(
                            sample_id=ch.sample_id,
                            analysis_run_id=run.id,
                            property_name="Crystallite Size",
                            value=sch_res.crystallite_size_nm,
                            unit="nm",
                            calculation_method="Scherrer Equation",
                            formula=sch_res.formula,
                            assumptions=sch_res.assumptions,
                            input_values={
                                "peak_position_2theta": candidate_peak.peak_position,
                                "fwhm_deg": candidate_peak.fwhm,
                                "wavelength_nm": input_data.scherrer.wavelength_nm,
                                "shape_factor_k": input_data.scherrer.shape_factor_k,
                            },
                        )
                        self.db.add(calc_prop)
                        assumptions_log["crystallite_size_calculated"] = True
                        assumptions_log["crystallite_size_nm"] = sch_res.crystallite_size_nm
                    except ScherrerCalculationError as s_exc:
                        assumptions_log["scherrer_error"] = str(s_exc)
                else:
                    assumptions_log["scherrer_warning"] = (
                        "Cannot calculate crystallite size: No detected peak had a valid FWHM determination."
                    )

            # Update AnalysisRun to COMPLETED
            run.status = AnalysisStatus.COMPLETED.value
            run.completed_at = datetime.now(timezone.utc)
            run.assumptions = assumptions_log
            await self.db.flush()

            await self.audit.log(
                entity_type="AnalysisRun",
                entity_id=run.id,
                action="XRD_ANALYSIS_RUN",
                changes={"peaks_found": len(created_peaks), "input_file": raw_file.original_filename},
            )

        except Exception as exc:
            run.status = AnalysisStatus.FAILED.value
            run.error_message = str(exc)
            run.completed_at = datetime.now(timezone.utc)
            await self.db.flush()
            logger.error("XRD analysis run %s failed: %s", run.id, exc)
            raise

        # Return loaded AnalysisRun with peaks and properties
        return await self.get_analysis_run(run.id)

    async def get_analysis_run(self, analysis_run_id: uuid.UUID) -> AnalysisRun:
        """Return AnalysisRun record with eager loaded peaks and calculated properties."""
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

    async def get_characterization_runs(
        self, characterization_id: uuid.UUID
    ) -> Sequence[AnalysisRun]:
        """Return all analysis runs for a characterization."""
        result = await self.db.execute(
            select(AnalysisRun)
            .options(
                selectinload(AnalysisRun.peaks),
                selectinload(AnalysisRun.calculated_properties),
            )
            .where(AnalysisRun.characterization_id == characterization_id)
            .order_by(AnalysisRun.started_at.desc())
        )
        return result.scalars().all()

    async def get_processed_data_points(
        self, analysis_run_id: uuid.UUID
    ) -> XRDProcessedDataResponse:
        """Return 2θ, raw, and processed intensity data points for Plotly rendering."""
        run = await self.get_analysis_run(analysis_run_id)
        if not run.processed_files:
            raise ValueError(f"No processed curve data found for analysis run {analysis_run_id}.")

        proc_file = run.processed_files[0]
        settings = get_settings()
        processed_root = Path(getattr(settings, "processed_data_dir", "data/processed")).resolve()
        file_path = processed_root / proc_file.stored_path

        if not file_path.exists():
            raise FileNotFoundError(f"Processed curve data file missing at {file_path}")

        df = pd.read_csv(file_path)
        points: list[XRDDataPoint] = []
        for _, row in df.iterrows():
            points.append(
                XRDDataPoint(
                    two_theta=float(row["two_theta"]),
                    raw_intensity=float(row["raw_intensity"]),
                    processed_intensity=float(row["processed_intensity"]) if "processed_intensity" in row else None,
                )
            )

        return XRDProcessedDataResponse(
            analysis_run_id=analysis_run_id,
            data_points=points,
            total_points=len(points),
        )
