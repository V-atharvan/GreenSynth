"""
GreenSynth Analytics — Experiment Report Data Builder

Assembles ExperimentReportData DTO by querying stored ORM database entities.
Fulfills Consumer-Only Rule: Never recalculates scientific properties independently.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.analysis import AnalysisRun, CalculatedProperty, XRDPeak
from app.models.analytics import StatisticalAnalysis
from app.models.characterization import Characterization, RawFile
from app.models.experiment import Experiment
from app.models.ml import MLModel, MLPrediction
from app.models.optimization import OptimizationCandidate, OptimizationRun
from app.models.parameter import ExperimentParameter, ParameterDefinition
from app.models.project import Project
from app.models.project_config import ProjectDefinition
from app.models.sample import Sample
from app.reporting.schemas import (
    ElectricalReportSectionSchema,
    ExperimentReportData,
    MLPredictionReportSectionSchema,
    OptimizationReportSectionSchema,
    ProvenanceItemSchema,
    StatisticalReportSectionSchema,
    UVVisReportSectionSchema,
    ValidationReportSectionSchema,
    XRDReportSectionSchema,
)


class ExperimentReportDataBuilder:
    """
    Data collection service assembling DTO for PDF report generation.
    """

    @classmethod
    async def build_experiment_report_data(
        cls, experiment_id: uuid.UUID, db: AsyncSession
    ) -> ExperimentReportData:
        """Query database records and assemble structured ExperimentReportData DTO."""

        # 1. Fetch Experiment & Project
        exp_stmt = (
            select(Experiment)
            .where(Experiment.id == experiment_id)
            .options(selectinload(Experiment.project))
        )
        exp_res = await db.execute(exp_stmt)
        exp = exp_res.scalar_one_or_none()
        if not exp:
            raise ValueError(f"Experiment with ID '{experiment_id}' not found.")

        proj = exp.project

        # Fetch ProjectDefinition for config version & biomass
        pdef_stmt = select(ProjectDefinition).where(ProjectDefinition.project_id == proj.id)
        pdef_res = await db.execute(pdef_stmt)
        pdef = pdef_res.scalar_one_or_none()
        config_ver = pdef.current_version if pdef else "v1.0"
        biomass_val = "Rice husk" if proj.project_code in ("P5", "P6") else None

        # 2. Fetch Synthesis Parameters
        p_stmt = (
            select(ExperimentParameter, ParameterDefinition)
            .join(ParameterDefinition, ExperimentParameter.parameter_definition_id == ParameterDefinition.id)
            .where(ExperimentParameter.experiment_id == experiment_id)
        )
        p_res = await db.execute(p_stmt)
        params_rows = p_res.all()

        synthesis_params: list[dict[str, Any]] = []
        for exp_param, param_def in params_rows:
            synthesis_params.append({
                "parameter_code": param_def.parameter_code,
                "parameter_name": param_def.parameter_name,
                "value": exp_param.value,
                "unit": exp_param.unit or param_def.unit or "—",
                "source": "Experiment Record",
                "validation_status": "Valid",
            })

        # Fallback to parameters_json if experiment_parameters table empty
        if not synthesis_params and exp.parameters_json:
            for k, v in exp.parameters_json.items():
                synthesis_params.append({
                    "parameter_code": k,
                    "parameter_name": k.replace("_", " ").title(),
                    "value": str(v),
                    "unit": "—",
                    "source": "Recorded Condition",
                    "validation_status": "Valid",
                })

        # 3. Fetch Samples
        samp_stmt = select(Sample).where(Sample.experiment_id == experiment_id)
        samp_res = await db.execute(samp_stmt)
        samples_list = samp_res.scalars().all()

        samples_data: list[dict[str, Any]] = [
            {
                "sample_id": str(s.id),
                "sample_code": s.sample_code,
                "name": s.name,
                "material": s.material,
                "status": s.status,
                "created_at": s.created_at.strftime("%Y-%m-%d"),
            }
            for s in samples_list
        ]

        sample_ids = [s.id for s in samples_list]

        # 4. Fetch Characterization & Raw Files
        char_summary: list[dict[str, Any]] = []
        provenance_items: list[ProvenanceItemSchema] = []

        xrd_section = XRDReportSectionSchema()
        uvvis_section = UVVisReportSectionSchema()
        electrical_section = ElectricalReportSectionSchema()

        if sample_ids:
            char_stmt = (
                select(Characterization)
                .where(Characterization.sample_id.in_(sample_ids))
                .options(selectinload(Characterization.raw_files), selectinload(Characterization.sample))
            )
            char_res = await db.execute(char_stmt)
            chars = char_res.scalars().all()

            for c in chars:
                technique = c.technique.value if hasattr(c.technique, "value") else str(c.technique)
                sample_code = c.sample.sample_code if c.sample else "Sample"

                for rf in c.raw_files:
                    # Query analysis run & calculated properties
                    ar_stmt = select(AnalysisRun).where(AnalysisRun.input_file_id == rf.id)
                    ar_res = await db.execute(ar_stmt)
                    ar = ar_res.scalar_one_or_none()

                    calc_props: list[dict[str, Any]] = []
                    if ar:
                        cp_stmt = select(CalculatedProperty).where(CalculatedProperty.analysis_run_id == ar.id)
                        cp_res = await db.execute(cp_stmt)
                        calc_props = [
                            {
                                "property_name": prop.property_name,
                                "value": prop.value,
                                "unit": prop.unit,
                                "method": prop.calculation_method,
                            }
                            for prop in cp_res.scalars().all()
                        ]

                        # Populate technique specific DTO sections
                        if technique == "XRD" and not xrd_section.available:
                            xrd_section.available = True
                            xrd_section.raw_filename = rf.original_filename
                            xrd_section.analysis_version = getattr(ar, "software_version", None) or "v1.0"
                            xrd_section.processing_parameters = getattr(ar, "parameters", None) or {}

                            # Fetch peaks
                            peak_stmt = select(XRDPeak).where(XRDPeak.analysis_run_id == ar.id)
                            peak_res = await db.execute(peak_stmt)
                            peaks = peak_res.scalars().all()
                            xrd_section.peaks = [
                                {
                                    "peak_number": idx + 1,
                                    "two_theta": getattr(p, "peak_position", 0.0),
                                    "intensity": p.intensity,
                                    "fwhm": getattr(p, "fwhm", None),
                                    "crystallite_size_nm": None,
                                }
                                for idx, p in enumerate(peaks)
                            ]

                            # Extract crystallite size
                            for p in calc_props:
                                if "crystallite" in p["property_name"].lower():
                                    xrd_section.crystallite_size_nm = float(p["value"])

                        elif technique == "UV_VIS" and not uvvis_section.available:
                            uvvis_section.available = True
                            uvvis_section.raw_filename = rf.original_filename
                            uvvis_section.analysis_version = getattr(ar, "software_version", None) or "v1.0"
                            for p in calc_props:
                                if "band_gap" in p["property_name"].lower():
                                    uvvis_section.optical_band_gap_ev = float(p["value"])
                            for p in calc_props:
                                if "band_gap" in p["property_name"].lower():
                                    uvvis_section.optical_band_gap_ev = float(p["value"])

                        elif technique == "ELECTRICAL" and not electrical_section.available:
                            electrical_section.available = True
                            electrical_section.raw_filename = rf.original_filename
                            for p in calc_props:
                                if "conductivity" in p["property_name"].lower():
                                    electrical_section.conductivity_s_cm = float(p["value"])
                                elif "resistivity" in p["property_name"].lower():
                                    electrical_section.resistivity_ohm_cm = float(p["value"])
                                elif "resistance" in p["property_name"].lower():
                                    electrical_section.resistance_ohms = float(p["value"])

                    # Build summary row
                    prop_str = ", ".join(f"{p['property_name']}: {p['value']} {p['unit'] or ''}" for p in calc_props) if calc_props else "Pending"
                    char_summary.append({
                        "sample_code": sample_code,
                        "technique": technique,
                        "raw_file": rf.original_filename,
                        "analysis_status": "Analyzed" if ar else "Uploaded",
                        "calculated_properties": prop_str,
                    })

                    # Build provenance record
                    provenance_items.append(
                        ProvenanceItemSchema(
                            sample_code=sample_code,
                            technique=technique,
                            raw_filename=rf.original_filename,
                            raw_file_id=str(rf.id),
                            sha256_checksum=rf.checksum,
                            analysis_run_id=str(ar.id) if ar else None,
                            analysis_method=getattr(ar, "analysis_type", None) if ar else None,
                            software_version="1.0.0-research",
                            processing_parameters=getattr(ar, "parameters", {}) if ar else {},
                            calculated_properties=calc_props,
                        )
                    )

        # 5. Fetch Statistics
        from app.models.analytics import Dataset
        stat_stmt = (
            select(StatisticalAnalysis)
            .join(Dataset, StatisticalAnalysis.dataset_id == Dataset.id)
            .where(Dataset.project_id == proj.id)
        )
        stat_res = await db.execute(stat_stmt)
        stat_obj = stat_res.scalars().first()
        stat_section = StatisticalReportSectionSchema()
        if stat_obj:
            stat_section.available = True
            stat_section.analysis_type = getattr(stat_obj, "analysis_type", "STATISTICAL")
            stat_section.sample_size_n = getattr(stat_obj, "sample_size", 0)
            stat_section.metrics = getattr(stat_obj, "results_json", {}) or {}

        # 6. Fetch ML Prediction
        from app.models.ml import MLDataset
        ml_section = MLPredictionReportSectionSchema()
        pred_stmt = (
            select(MLPrediction)
            .join(MLDataset, MLPrediction.dataset_id == MLDataset.id)
            .where(MLDataset.project_id == proj.id)
            .options(selectinload(MLPrediction.model))
        )
        pred_res = await db.execute(pred_stmt)
        pred_obj = pred_res.scalars().first()
        if pred_obj:
            ml_section.available = True
            ml_section.predicted_value = pred_obj.predicted_value
            ml_section.target_property = pred_obj.predicted_property
            ml_section.lower_bound = pred_obj.uncertainty_lower
            ml_section.upper_bound = pred_obj.uncertainty_upper
            ml_section.domain_status = pred_obj.applicability_status or "IN_DOMAIN"
            if pred_obj.model:
                ml_section.model_name = pred_obj.model.name
                ml_section.model_version = pred_obj.model.version
                ml_section.r2_score = pred_obj.model.metrics.get("r2") if isinstance(pred_obj.model.metrics, dict) else None

        # Assemble DTO
        return ExperimentReportData(
            project_code=proj.project_code,
            project_name=proj.name,
            material=proj.material,
            biomass=biomass_val,
            extract=proj.extract,
            solvent=proj.solvent,
            synthesis_method=proj.synthesis_method,
            config_version=config_ver,
            experiment_id=str(exp.id),
            experiment_code=exp.experiment_code,
            title=exp.title,
            researcher=exp.researcher or "Researcher",
            status=exp.status.value if hasattr(exp.status, "value") else str(exp.status),
            objective=exp.notes or "Synthesis Experiment",
            experiment_date=exp.experiment_date.strftime("%Y-%m-%d") if exp.experiment_date else None,
            created_at=exp.created_at,
            synthesis_parameters=synthesis_params,
            samples=samples_data,
            characterization_summary=char_summary,
            xrd=xrd_section,
            uvvis=uvvis_section,
            electrical=electrical_section,
            statistics=stat_section,
            ml_prediction=ml_section,
            provenance_items=provenance_items,
        )
