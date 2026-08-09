"""
GreenSynth Analytics — Electrical Analysis Service

Orchestrates parsing, unit conversions, I-V linear regression resistance calculation,
sample geometry area, resistivity, conductivity, and DB persistence.
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
from app.scientific.electrical.geometry import GeometryType
from app.scientific.electrical.parser import parse_electrical_file
from app.scientific.electrical.resistance import (
    ResistanceCalculationError,
    calculate_resistance_from_iv,
)
from app.scientific.electrical.resistivity import calculate_resistivity_and_conductivity
from app.scientific.electrical.schemas import (
    ElectricalAnalysisInput,
    ElectricalProcessedResponse,
    IVDataPoint,
    IVFitLinePoint,
)
from app.scientific.electrical.units import (
    convert_current_to_amperes,
    convert_length_to_cm,
    convert_voltage_to_volts,
)
from app.services.audit_service import AuditService
from app.services.characterization_service import (
    CharacterizationNotFoundError,
    RawFileNotFoundError,
)
from app.storage.local import LocalFileStorage

logger = logging.getLogger(__name__)


class ElectricalAnalysisService:
    """Service layer for electrical measurement analysis execution."""

    def __init__(self, db: AsyncSession, storage: LocalFileStorage | None = None) -> None:
        self.db = db
        self.storage = storage or LocalFileStorage()
        self.audit = AuditService(db)

    async def run_analysis(
        self,
        characterization_id: uuid.UUID,
        input_data: ElectricalAnalysisInput,
        raw_file_id: uuid.UUID | None = None,
        created_by: str | None = None,
    ) -> AnalysisRun:
        """
        Execute full electrical I-V resistance, resistivity, and conductivity analysis.

        Does NOT alter or overwrite original raw file.
        Saves preprocessed curves under data/processed/.
        """
        ch_res = await self.db.execute(
            select(Characterization)
            .options(selectinload(Characterization.raw_files))
            .where(Characterization.id == characterization_id)
        )
        ch = ch_res.scalar_one_or_none()
        if ch is None:
            raise CharacterizationNotFoundError(f"Characterization {characterization_id} not found.")

        if ch.technique != "ELECTRICAL":
            raise ValueError(f"Characterization technique '{ch.technique}' is not ELECTRICAL.")

        raw_file: RawFile | None = None
        if raw_file_id:
            raw_file = next((f for f in ch.raw_files if f.id == raw_file_id), None)
        elif ch.raw_files:
            raw_file = ch.raw_files[-1]

        if not raw_file:
            raise RawFileNotFoundError(
                f"No raw files uploaded for Electrical characterization {characterization_id}."
            )

        file_bytes = await self.storage.retrieve(raw_file.storage_path)

        run = AnalysisRun(
            characterization_id=ch.id,
            input_file_id=raw_file.id,
            analysis_type="ELECTRICAL",
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
            parsed = parse_electrical_file(file_bytes, raw_file.file_extension)

            # 2. Convert units to SI base (Volts & Amperes)
            v_volts = convert_voltage_to_volts(parsed.voltage, input_data.units.voltage_unit)
            i_amps = convert_current_to_amperes(parsed.current, input_data.units.current_unit)

            # Convert fit region bounds if provided
            vmin_v = (
                convert_voltage_to_volts(input_data.fit_voltage_min, input_data.units.voltage_unit)
                if input_data.fit_voltage_min is not None
                else None
            )
            vmax_v = (
                convert_voltage_to_volts(input_data.fit_voltage_max, input_data.units.voltage_unit)
                if input_data.fit_voltage_max is not None
                else None
            )

            # 3. Calculate Resistance R via I-V Linear Fit
            res_result = calculate_resistance_from_iv(
                v_volts, i_amps, voltage_min_v=vmin_v, voltage_max_v=vmax_v
            )

            # 4. Geometry & Resistivity / Conductivity Calculation
            l_cm = (
                convert_length_to_cm(input_data.geometry.length, input_data.units.length_unit)
                if input_data.geometry.length is not None
                else None
            )
            w_cm = (
                convert_length_to_cm(input_data.geometry.width, input_data.units.length_unit)
                if input_data.geometry.width is not None
                else None
            )
            t_cm = (
                convert_length_to_cm(input_data.geometry.thickness, input_data.units.length_unit)
                if input_data.geometry.thickness is not None
                else None
            )

            resis_result = calculate_resistivity_and_conductivity(
                resistance_ohms=res_result.resistance_ohms,
                geometry_type=input_data.geometry.geometry_type,
                length_cm=l_cm,
                width_cm=w_cm,
                thickness_cm=t_cm,
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
                "voltage_v": v_volts,
                "current_a": i_amps,
            })
            csv_buf = io.StringIO()
            proc_df.to_csv(csv_buf, index=False)
            proc_bytes = csv_buf.getvalue().encode("utf-8")

            settings = get_settings()
            processed_root = Path(getattr(settings, "processed_data_dir", "data/processed")).resolve()
            rel_proc_path = f"{proj.project_code}/{exp.experiment_code}/{sample.sample_code}/electrical/{run.id!s}_processed.csv"
            dest_proc_path = processed_root / rel_proc_path
            dest_proc_path.parent.mkdir(parents=True, exist_ok=True)

            with open(dest_proc_path, "wb") as pf:
                pf.write(proc_bytes)

            proc_file = ProcessedFile(
                analysis_run_id=run.id,
                raw_file_id=raw_file.id,
                stored_path=str(rel_proc_path),
                processing_method="Unit conversion (V, A) + I-V linear regression",
                processing_parameters=input_data.model_dump(),
            )
            self.db.add(proc_file)

            # 6. Store Calculated Properties
            # A. Resistance
            prop_r = CalculatedProperty(
                sample_id=ch.sample_id,
                analysis_run_id=run.id,
                property_name="Electrical Resistance",
                value=res_result.resistance_ohms,
                unit="Ohm",
                calculation_method="Ohm's Law Linear Regression",
                formula=res_result.formula,
                assumptions=res_result.assumptions,
                input_values={
                    "r_squared": res_result.r_squared,
                    "slope": res_result.slope,
                    "intercept": res_result.intercept,
                    "voltage_range_v": f"{res_result.voltage_range_min_v:.2f} - {res_result.voltage_range_max_v:.2f} V",
                },
            )
            self.db.add(prop_r)

            # B. Resistivity & Conductivity (if geometry dimensions were provided)
            if resis_result.resistivity_ohm_cm is not None:
                prop_rho = CalculatedProperty(
                    sample_id=ch.sample_id,
                    analysis_run_id=run.id,
                    property_name="Electrical Resistivity",
                    value=resis_result.resistivity_ohm_cm,
                    unit="Ohm*cm",
                    calculation_method="Geometric Resistance Formula",
                    formula=resis_result.formula_resistivity,
                    assumptions=resis_result.assumptions,
                    input_values={
                        "resistance_ohms": res_result.resistance_ohms,
                        "area_cm2": resis_result.area_cm2,
                        "length_cm": resis_result.length_cm,
                    },
                )
                self.db.add(prop_rho)

            if resis_result.conductivity_s_cm is not None:
                prop_sigma = CalculatedProperty(
                    sample_id=ch.sample_id,
                    analysis_run_id=run.id,
                    property_name="Electrical Conductivity",
                    value=resis_result.conductivity_s_cm,
                    unit="S/cm",
                    calculation_method="Reciprocal Resistivity",
                    formula=resis_result.formula_conductivity,
                    assumptions=resis_result.assumptions,
                    input_values={
                        "resistivity_ohm_cm": resis_result.resistivity_ohm_cm,
                    },
                )
                self.db.add(prop_sigma)

            # Update AnalysisRun status to COMPLETED
            run.status = AnalysisStatus.COMPLETED.value
            run.completed_at = datetime.now(timezone.utc)
            run.assumptions = {
                "resistance_ohms": res_result.resistance_ohms,
                "r_squared": res_result.r_squared,
                "resistivity_ohm_cm": resis_result.resistivity_ohm_cm,
                "conductivity_s_cm": resis_result.conductivity_s_cm,
                "warning": resis_result.warning_msg,
            }
            await self.db.flush()

            await self.audit.log(
                entity_type="AnalysisRun",
                entity_id=run.id,
                action="ELECTRICAL_ANALYSIS_RUN",
                changes={"resistance_ohms": res_result.resistance_ohms, "r_squared": res_result.r_squared},
            )

        except Exception as exc:
            run.status = AnalysisStatus.FAILED.value
            run.error_message = str(exc)
            run.completed_at = datetime.now(timezone.utc)
            await self.db.flush()
            logger.error("Electrical analysis run %s failed: %s", run.id, exc)
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

    async def get_electrical_data(
        self, analysis_run_id: uuid.UUID
    ) -> ElectricalProcessedResponse:
        """Return Voltage V, Current A data points and linear regression fit line for Plotly rendering."""
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
        points: list[IVDataPoint] = []
        for _, row in df.iterrows():
            points.append(
                IVDataPoint(
                    voltage_v=float(row["voltage_v"]),
                    current_a=float(row["current_a"]),
                )
            )

        r_prop = next(
            (p for p in run.calculated_properties if p.property_name == "Electrical Resistance"), None
        )
        rho_prop = next(
            (p for p in run.calculated_properties if p.property_name == "Electrical Resistivity"), None
        )
        sigma_prop = next(
            (p for p in run.calculated_properties if p.property_name == "Electrical Conductivity"), None
        )

        fit_line: list[IVFitLinePoint] = []
        r_ohms: float | None = None
        r2: float | None = None

        if r_prop and r_prop.input_values:
            r_ohms = r_prop.value
            r2 = r_prop.input_values.get("r_squared")
            slope = r_prop.input_values.get("slope")
            intercept = r_prop.input_values.get("intercept")

            if slope is not None and intercept is not None:
                i_min = float(df["current_a"].min())
                i_max = float(df["current_a"].max())
                i_steps = np.linspace(i_min, i_max, 50)
                for i_val in i_steps:
                    v_val = float(slope) * float(i_val) + float(intercept)
                    fit_line.append(
                        IVFitLinePoint(
                            current_a=float(i_val),
                            fit_voltage_v=float(v_val),
                        )
                    )

        params = run.parameters or {}
        units_params = params.get("units", {})
        warn = run.assumptions.get("warning") if run.assumptions else None

        return ElectricalProcessedResponse(
            analysis_run_id=analysis_run_id,
            voltage_unit=units_params.get("voltage_unit", "V"),
            current_unit=units_params.get("current_unit", "A"),
            resistance_ohms=r_ohms,
            r_squared=r2,
            resistivity_ohm_cm=rho_prop.value if rho_prop else None,
            conductivity_s_cm=sigma_prop.value if sigma_prop else None,
            warning_msg=warn,
            data_points=points,
            fit_line=fit_line,
            total_points=len(points),
        )
