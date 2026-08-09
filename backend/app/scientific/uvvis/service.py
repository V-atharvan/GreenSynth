"""
GreenSynth Analytics — UV-Vis Analysis Service

Orchestrates parsing, wavelength-to-energy conversion, Tauc plot generation,
linear regression fitting, optical band gap calculation, and DB persistence.
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
)
from app.models.characterization import Characterization, RawFile
from app.models.experiment import Experiment
from app.models.project import Project
from app.models.sample import Sample
from app.scientific.uvvis.band_gap import (
    BandGapCalculationError,
    calculate_optical_band_gap,
)
from app.scientific.uvvis.parser import parse_uvvis_file
from app.scientific.uvvis.schemas import (
    TaucDataPoint,
    TaucFitLinePoint,
    TaucProcessedResponse,
    UVVisAnalysisInput,
)
from app.scientific.uvvis.transforms import compute_tauc_transform
from app.services.audit_service import AuditService
from app.services.characterization_service import (
    CharacterizationNotFoundError,
    RawFileNotFoundError,
)
from app.storage.local import LocalFileStorage

logger = logging.getLogger(__name__)


class UVVisAnalysisService:
    """Service layer for UV-Vis analysis execution and Tauc plot data queries."""

    def __init__(self, db: AsyncSession, storage: LocalFileStorage | None = None) -> None:
        self.db = db
        self.storage = storage or LocalFileStorage()
        self.audit = AuditService(db)

    async def run_analysis(
        self,
        characterization_id: uuid.UUID,
        input_data: UVVisAnalysisInput,
        raw_file_id: uuid.UUID | None = None,
        created_by: str | None = None,
    ) -> AnalysisRun:
        """
        Execute full UV-Vis Tauc optical band gap analysis workflow.

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

        if ch.technique != "UV_VIS":
            raise ValueError(f"Characterization technique '{ch.technique}' is not UV_VIS.")

        # Locate raw file
        raw_file: RawFile | None = None
        if raw_file_id:
            raw_file = next((f for f in ch.raw_files if f.id == raw_file_id), None)
        elif ch.raw_files:
            raw_file = ch.raw_files[-1]

        if not raw_file:
            raise RawFileNotFoundError(
                f"No raw files uploaded for UV-Vis characterization {characterization_id}."
            )

        # Retrieve raw file bytes from storage
        file_bytes = await self.storage.retrieve(raw_file.storage_path)

        # Create AnalysisRun record with RUNNING status
        run = AnalysisRun(
            characterization_id=ch.id,
            input_file_id=raw_file.id,
            analysis_type="UV_VIS",
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
            parsed = parse_uvvis_file(file_bytes, raw_file.file_extension)
            arr_wl = parsed.wavelength_nm
            arr_abs = parsed.absorbance

            # 2. Optional Preprocessing
            y_proc = arr_abs.copy()
            if input_data.preprocessing.smoothing and len(y_proc) >= 5:
                from scipy.signal import savgol_filter
                wl_len = min(input_data.preprocessing.savgol_window, len(y_proc))
                if wl_len % 2 == 0:
                    wl_len -= 1
                if wl_len > input_data.preprocessing.savgol_polyorder + 1:
                    y_proc = savgol_filter(
                        y_proc,
                        window_length=wl_len,
                        polyorder=input_data.preprocessing.savgol_polyorder,
                    )

            # 3. Compute Tauc Transform
            tauc_res = compute_tauc_transform(
                arr_wl,
                y_proc,
                transition_type=input_data.tauc.transition_type,
                thickness_cm=input_data.tauc.sample_thickness_cm,
            )

            # 4. Fit Optical Band Gap
            bandgap_res = calculate_optical_band_gap(
                tauc_res.photon_energy_ev,
                tauc_res.tauc_y,
                energy_min_ev=input_data.tauc.fit_energy_min_ev,
                energy_max_ev=input_data.tauc.fit_energy_max_ev,
            )

            # 5. Store processed curve under data/processed/
            sample_res = await self.db.execute(
                select(Sample, Experiment, Project)
                .join(Experiment, Sample.experiment_id == Experiment.id)
                .join(Project, Experiment.project_id == Project.id)
                .where(Sample.id == ch.sample_id)
            )
            row = sample_res.one()
            sample, exp, proj = row[0], row[1], row[2]

            proc_df = pd.DataFrame({
                "wavelength_nm": arr_wl,
                "absorbance": arr_abs,
                "processed_absorbance": y_proc,
                "photon_energy_ev": tauc_res.photon_energy_ev,
                "tauc_y": tauc_res.tauc_y,
            })
            csv_buf = io.StringIO()
            proc_df.to_csv(csv_buf, index=False)
            proc_bytes = csv_buf.getvalue().encode("utf-8")

            settings = get_settings()
            processed_root = Path(getattr(settings, "processed_data_dir", "data/processed")).resolve()
            rel_proc_path = f"{proj.project_code}/{exp.experiment_code}/{sample.sample_code}/uvvis/{run.id!s}_processed.csv"
            dest_proc_path = processed_root / rel_proc_path
            dest_proc_path.parent.mkdir(parents=True, exist_ok=True)

            with open(dest_proc_path, "wb") as pf:
                pf.write(proc_bytes)

            proc_file = ProcessedFile(
                analysis_run_id=run.id,
                raw_file_id=raw_file.id,
                stored_path=str(rel_proc_path),
                processing_method=f"Tauc transformation ({input_data.tauc.transition_type.value})",
                processing_parameters=input_data.tauc.model_dump(),
            )
            self.db.add(proc_file)

            # 6. Store CalculatedProperty (Optical Band Gap)
            calc_prop = CalculatedProperty(
                sample_id=ch.sample_id,
                analysis_run_id=run.id,
                property_name="Optical Band Gap",
                value=bandgap_res.band_gap_ev,
                unit="eV",
                calculation_method="Tauc Plot Linear Extrapolation",
                formula=bandgap_res.formula,
                assumptions={
                    **bandgap_res.assumptions,
                    "transition_model": input_data.tauc.transition_type.value,
                    "using_absorption_coefficient": tauc_res.using_alpha,
                    "sample_thickness_cm": input_data.tauc.sample_thickness_cm,
                    "warning": tauc_res.warning_msg,
                },
                input_values={
                    "fit_energy_range": f"{bandgap_res.energy_range_min:.2f} - {bandgap_res.energy_range_max:.2f} eV",
                    "r_squared": bandgap_res.r_squared,
                    "slope": bandgap_res.slope,
                    "intercept": bandgap_res.intercept,
                },
            )
            self.db.add(calc_prop)

            # Update AnalysisRun status to COMPLETED
            run.status = AnalysisStatus.COMPLETED.value
            run.completed_at = datetime.now(timezone.utc)
            run.assumptions = {
                "band_gap_ev": bandgap_res.band_gap_ev,
                "r_squared": bandgap_res.r_squared,
                "transition_model": input_data.tauc.transition_type.value,
                "warning": tauc_res.warning_msg,
            }
            await self.db.flush()

            await self.audit.log(
                entity_type="AnalysisRun",
                entity_id=run.id,
                action="UVVIS_ANALYSIS_RUN",
                changes={"band_gap_ev": bandgap_res.band_gap_ev, "r_squared": bandgap_res.r_squared},
            )

        except Exception as exc:
            run.status = AnalysisStatus.FAILED.value
            run.error_message = str(exc)
            run.completed_at = datetime.now(timezone.utc)
            await self.db.flush()
            logger.error("UV-Vis analysis run %s failed: %s", run.id, exc)
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

    async def get_tauc_data(self, analysis_run_id: uuid.UUID) -> TaucProcessedResponse:
        """Return Tauc curve data points and linear regression fit line for Plotly rendering."""
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
        points: list[TaucDataPoint] = []
        for _, row in df.iterrows():
            points.append(
                TaucDataPoint(
                    wavelength_nm=float(row["wavelength_nm"]),
                    absorbance=float(row["absorbance"]),
                    photon_energy_ev=float(row["photon_energy_ev"]),
                    tauc_y=float(row["tauc_y"]),
                )
            )

        # Get optical band gap property if calculated
        bg_prop = next(
            (p for p in run.calculated_properties if p.property_name == "Optical Band Gap"), None
        )

        fit_line: list[TaucFitLinePoint] = []
        bg_ev: float | None = None
        r2: float | None = None

        if bg_prop and bg_prop.input_values:
            bg_ev = bg_prop.value
            r2 = bg_prop.input_values.get("r_squared")
            slope = bg_prop.input_values.get("slope")
            intercept = bg_prop.input_values.get("intercept")

            if slope and intercept:
                # Generate fit line from Eg to max energy
                e_start = bg_ev
                e_end = float(df["photon_energy_ev"].max())
                e_steps = np.linspace(e_start, e_end, 50)
                for e_val in e_steps:
                    y_val = slope * e_val + intercept
                    if y_val >= 0:
                        fit_line.append(
                            TaucFitLinePoint(
                                photon_energy_ev=float(e_val),
                                fit_y=float(y_val),
                            )
                        )

        params = run.parameters or {}
        tauc_params = params.get("tauc", {})

        return TaucProcessedResponse(
            analysis_run_id=analysis_run_id,
            transition_type=tauc_params.get("transition_type", "DIRECT_ALLOWED"),
            using_alpha=tauc_params.get("sample_thickness_cm") is not None,
            thickness_cm=tauc_params.get("sample_thickness_cm"),
            warning_msg="Insufficient data for absorption coefficient calculation because sample thickness is missing." if not tauc_params.get("sample_thickness_cm") else None,
            data_points=points,
            fit_line=fit_line,
            band_gap_ev=bg_ev,
            r_squared=r2,
            total_points=len(points),
        )
