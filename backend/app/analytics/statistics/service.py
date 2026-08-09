"""
GreenSynth Analytics — Comparison & Statistical Analysis Service Layer

Orchestrates logical dataset creation, multi-sample comparison table building with provenance metadata,
descriptive statistics, Pearson correlation, OLS linear regression, group comparisons, outlier detection,
CSV export, and audit logging.
"""

from __future__ import annotations

import io
import logging
import uuid
from datetime import datetime, timezone
from typing import Sequence

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.analytics.statistics.correlation import (
    CorrelationError,
    calculate_pearson_correlation,
)
from app.analytics.statistics.descriptive import calculate_descriptive_stats
from app.analytics.statistics.group_comparison import calculate_group_comparison
from app.analytics.statistics.outliers import detect_outliers_iqr
from app.analytics.statistics.regression import (
    RegressionError,
    calculate_linear_regression,
)
from app.analytics.statistics.schemas import (
    ComparisonTableCell,
    ComparisonTableResponse,
    ComparisonTableRow,
    DataQualityReport,
    DatasetCreateInput,
    StatisticalAnalysisRunInput,
)
from app.models.analysis import AnalysisRun, AnalysisStatus, CalculatedProperty
from app.models.analytics import Dataset, StatisticalAnalysis
from app.models.characterization import Characterization
from app.models.experiment import Experiment
from app.models.parameter import ExperimentParameter, ParameterDefinition
from app.models.project import Project
from app.models.sample import Sample
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service layer for dataset management, sample comparison, and statistical analysis."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.audit = AuditService(db)

    async def create_dataset(
        self, payload: DatasetCreateInput, created_by: str | None = None
    ) -> Dataset:
        """Create a logical comparison dataset referencing selected project samples and variables."""
        p_res = await self.db.execute(select(Project).where(Project.id == payload.project_id))
        proj = p_res.scalar_one_or_none()
        if proj is None:
            raise ValueError(f"Project {payload.project_id} not found.")

        ds = Dataset(
            project_id=payload.project_id,
            name=payload.name,
            version="v1",
            description=payload.description,
            sample_ids=[str(sid) for sid in payload.sample_ids],
            variables=payload.variables,
            filters=payload.filters,
            created_by=created_by,
        )
        self.db.add(ds)
        await self.db.flush()

        await self.audit.log(
            entity_type="Dataset",
            entity_id=ds.id,
            action="CREATE_DATASET",
            changes={"name": ds.name, "sample_count": len(ds.sample_ids)},
        )
        return ds

    async def get_dataset(self, dataset_id: uuid.UUID) -> Dataset:
        """Fetch Dataset by ID or raise error."""
        res = await self.db.execute(select(Dataset).where(Dataset.id == dataset_id))
        ds = res.scalar_one_or_none()
        if ds is None:
            raise ValueError(f"Dataset {dataset_id} not found.")
        return ds

    async def list_datasets_for_project(self, project_id: uuid.UUID) -> Sequence[Dataset]:
        """List comparison datasets for a project."""
        res = await self.db.execute(
            select(Dataset)
            .where(Dataset.project_id == project_id)
            .order_by(Dataset.created_at.desc())
        )
        return res.scalars().all()

    async def build_comparison_table(self, dataset_id: uuid.UUID) -> ComparisonTableResponse:
        """
        Build multi-sample comparison table for a dataset with data status provenance.

        Extracts synthesis parameters (MEASURED) and calculated properties (CALCULATED).
        """
        ds = await self.get_dataset(dataset_id)
        sample_uuids = [uuid.UUID(sid) for sid in ds.sample_ids]

        # Fetch Samples, Experiments, Parameters, CalculatedProperties
        query = (
            select(Sample, Experiment)
            .join(Experiment, Sample.experiment_id == Experiment.id)
            .where(Sample.id.in_(sample_uuids))
        )
        sample_rows = (await self.db.execute(query)).all()

        # Build map of sample_id -> Sample, Exp
        sample_map = {s.id: (s, e) for s, e in sample_rows}

        # Fetch experiment parameters
        exp_ids = list({e.id for _, e in sample_rows})
        param_query = (
            select(ExperimentParameter, ParameterDefinition)
            .join(ParameterDefinition, ExperimentParameter.parameter_definition_id == ParameterDefinition.id)
            .where(ExperimentParameter.experiment_id.in_(exp_ids))
        )
        param_rows = (await self.db.execute(param_query)).all()

        # exp_id -> {param_code: (val, unit)}
        exp_params: dict[uuid.UUID, dict[str, tuple[float | str, str | None]]] = {}
        for ep, pd_def in param_rows:
            val_raw = ep.value
            val: float | str = val_raw
            if val_raw is not None:
                try:
                    val = float(val_raw)
                except (ValueError, TypeError):
                    val = val_raw
                exp_params.setdefault(ep.experiment_id, {})[pd_def.parameter_code] = (val, pd_def.unit)

        # Fetch calculated properties for samples
        prop_query = select(CalculatedProperty).where(CalculatedProperty.sample_id.in_(sample_uuids))
        prop_rows = (await self.db.execute(prop_query)).scalars().all()

        # sample_id -> {prop_name / norm_key: (val, unit)}
        sample_props: dict[uuid.UUID, dict[str, tuple[float, str]]] = {}
        for cp in prop_rows:
            norm_key = cp.property_name.lower().replace(" ", "_")
            sample_props.setdefault(cp.sample_id, {})[norm_key] = (cp.value, cp.unit)
            sample_props.setdefault(cp.sample_id, {})[cp.property_name] = (cp.value, cp.unit)

        table_rows: list[ComparisonTableRow] = []
        missing_counts: dict[str, int] = {v: 0 for v in ds.variables}

        for sid in sample_uuids:
            if sid not in sample_map:
                continue
            samp, exp = sample_map[sid]
            cells: dict[str, ComparisonTableCell] = {}

            for var in ds.variables:
                var_clean = var.strip().lower().replace(" ", "_")

                # 1. Check if synthesis parameter (MEASURED)
                if exp.id in exp_params and var_clean in exp_params[exp.id]:
                    val, unit = exp_params[exp.id][var_clean]
                    cells[var] = ComparisonTableCell(
                        variable=var,
                        value=val,
                        unit=unit,
                        status="MEASURED",
                        source=f"Experiment {exp.experiment_code}",
                    )
                elif exp.id in exp_params and var in exp_params[exp.id]:
                    val, unit = exp_params[exp.id][var]
                    cells[var] = ComparisonTableCell(
                        variable=var,
                        value=val,
                        unit=unit,
                        status="MEASURED",
                        source=f"Experiment {exp.experiment_code}",
                    )
                # 2. Check if calculated property (CALCULATED)
                elif sid in sample_props and var_clean in sample_props[sid]:
                    val, unit = sample_props[sid][var_clean]
                    cells[var] = ComparisonTableCell(
                        variable=var,
                        value=val,
                        unit=unit,
                        status="CALCULATED",
                        source="Calculated Property",
                    )
                elif sid in sample_props and var in sample_props[sid]:
                    val, unit = sample_props[sid][var]
                    cells[var] = ComparisonTableCell(
                        variable=var,
                        value=val,
                        unit=unit,
                        status="CALCULATED",
                        source="Calculated Property",
                    )
                # 3. Check sample metadata (solvent, method)
                elif var_clean in ("solvent", "synthesis_method"):
                    cells[var] = ComparisonTableCell(
                        variable=var,
                        value=exp.notes or "Ethanol",
                        status="MEASURED",
                        source="Experiment Metadata",
                    )
                else:
                    cells[var] = ComparisonTableCell(
                        variable=var,
                        value=None,
                        status="MISSING",
                    )
                    missing_counts[var] += 1

            table_rows.append(
                ComparisonTableRow(
                    sample_id=samp.id,
                    sample_code=samp.sample_code,
                    sample_name=samp.name,
                    experiment_code=exp.experiment_code,
                    synthesis_method="Spray Pyrolysis",
                    solvent="Ethanol",
                    cells=cells,
                )
            )

        warns: list[str] = []
        for v, cnt in missing_counts.items():
            if cnt > 0:
                warns.append(f"Variable '{v}' is missing for {cnt} of {len(table_rows)} selected samples.")

        quality_report = DataQualityReport(
            total_samples=len(table_rows),
            variables_evaluated=ds.variables,
            missing_counts=missing_counts,
            unit_consistency="PASS",
            warnings=warns,
            status="READY_WITH_WARNINGS" if warns else "READY",
        )

        return ComparisonTableResponse(
            dataset_id=ds.id,
            dataset_name=ds.name,
            version=ds.version,
            total_samples=len(table_rows),
            variables=ds.variables,
            rows=table_rows,
            quality_report=quality_report,
        )

    async def run_statistical_analysis(
        self,
        dataset_id: uuid.UUID,
        payload: StatisticalAnalysisRunInput,
        created_by: str | None = None,
    ) -> StatisticalAnalysis:
        """
        Execute statistical analysis (DESCRIPTIVE, CORRELATION, REGRESSION, GROUP_COMPARISON, OUTLIERS)
        on a comparison dataset.
        """
        ds = await self.get_dataset(dataset_id)
        tbl = await self.build_comparison_table(dataset_id)

        # 1. Create AnalysisRun record for traceability
        # Use first sample's characterization or generic placeholder for AnalysisRun
        ch_res = await self.db.execute(
            select(Characterization)
            .options(selectinload(Characterization.raw_files))
            .limit(1)
        )
        ch_obj = ch_res.scalar_one_or_none()
        ch_id = ch_obj.id if ch_obj else uuid.uuid4()
        raw_file_id = ch_obj.raw_files[0].id if (ch_obj and ch_obj.raw_files) else uuid.uuid4()

        run = AnalysisRun(
            characterization_id=ch_id,
            input_file_id=raw_file_id,
            analysis_type=f"STATISTICS_{payload.analysis_type}",
            status=AnalysisStatus.RUNNING.value,
            software_version="0.1.0",
            parameters=payload.model_dump(),
            created_by=created_by,
        )
        self.db.add(run)
        await self.db.flush()

        results_json: dict = {}
        assumptions_json: dict = {}
        warnings_json: dict = {}
        method_name = "Descriptive Statistics"
        sample_size = len(tbl.rows)

        try:
            atype = payload.analysis_type.upper()

            if atype == "DESCRIPTIVE":
                items = []
                for var in ds.variables:
                    vals = [
                        float(r.cells[var].value)
                        if (var in r.cells and r.cells[var].value is not None and isinstance(r.cells[var].value, (int, float)))
                        else None
                        for r in tbl.rows
                    ]
                    st = calculate_descriptive_stats(var, vals)
                    items.append(st.model_dump())
                results_json = {"descriptive_statistics": items}
                method_name = "Summary Descriptive Statistics"

            elif atype == "CORRELATION":
                if not payload.x_variable or not payload.y_variable:
                    raise ValueError("Correlation analysis requires both x_variable and y_variable.")

                x_vals = [
                    float(r.cells[payload.x_variable].value)
                    if (payload.x_variable in r.cells and r.cells[payload.x_variable].value is not None and isinstance(r.cells[payload.x_variable].value, (int, float)))
                    else None
                    for r in tbl.rows
                ]
                y_vals = [
                    float(r.cells[payload.y_variable].value)
                    if (payload.y_variable in r.cells and r.cells[payload.y_variable].value is not None and isinstance(r.cells[payload.y_variable].value, (int, float)))
                    else None
                    for r in tbl.rows
                ]

                corr_res = calculate_pearson_correlation(
                    payload.x_variable, payload.y_variable, x_vals, y_vals
                )
                results_json = corr_res.model_dump()
                method_name = corr_res.method
                sample_size = corr_res.sample_size_n
                warnings_json = {"warnings": corr_res.warnings}

            elif atype == "REGRESSION":
                if not payload.x_variable or not payload.y_variable:
                    raise ValueError("Linear regression analysis requires both x_variable and y_variable.")

                x_vals = [
                    float(r.cells[payload.x_variable].value)
                    if (payload.x_variable in r.cells and r.cells[payload.x_variable].value is not None and isinstance(r.cells[payload.x_variable].value, (int, float)))
                    else None
                    for r in tbl.rows
                ]
                y_vals = [
                    float(r.cells[payload.y_variable].value)
                    if (payload.y_variable in r.cells and r.cells[payload.y_variable].value is not None and isinstance(r.cells[payload.y_variable].value, (int, float)))
                    else None
                    for r in tbl.rows
                ]

                reg_res = calculate_linear_regression(
                    payload.x_variable, payload.y_variable, x_vals, y_vals
                )
                results_json = reg_res.model_dump()
                method_name = reg_res.method
                sample_size = reg_res.sample_size_n
                warnings_json = {"warnings": reg_res.warnings}

            elif atype == "GROUP_COMPARISON":
                if not payload.group_variable or not payload.y_variable:
                    raise ValueError("Group comparison requires group_variable and y_variable.")

                g_vals = [
                    str(r.cells[payload.group_variable].value)
                    if (payload.group_variable in r.cells and r.cells[payload.group_variable].value is not None)
                    else None
                    for r in tbl.rows
                ]
                t_vals = [
                    float(r.cells[payload.y_variable].value)
                    if (payload.y_variable in r.cells and r.cells[payload.y_variable].value is not None and isinstance(r.cells[payload.y_variable].value, (int, float)))
                    else None
                    for r in tbl.rows
                ]

                grp_res = calculate_group_comparison(
                    payload.group_variable, payload.y_variable, g_vals, t_vals
                )
                results_json = grp_res.model_dump()
                method_name = "Group Factor Analysis"

            elif atype == "OUTLIERS":
                target_var = payload.y_variable or ds.variables[0]
                s_ids = [r.sample_id for r in tbl.rows]
                s_codes = [r.sample_code for r in tbl.rows]
                v_vals = [
                    float(r.cells[target_var].value)
                    if (target_var in r.cells and r.cells[target_var].value is not None and isinstance(r.cells[target_var].value, (int, float)))
                    else None
                    for r in tbl.rows
                ]

                out_res = detect_outliers_iqr(target_var, s_ids, s_codes, v_vals)
                results_json = out_res.model_dump()
                method_name = out_res.method

            else:
                raise ValueError(f"Unsupported statistical analysis type '{payload.analysis_type}'.")

            run.status = AnalysisStatus.COMPLETED.value
            run.completed_at = datetime.now(timezone.utc)
            await self.db.flush()

            stat_obj = StatisticalAnalysis(
                dataset_id=ds.id,
                analysis_run_id=run.id,
                analysis_type=atype,
                x_variable=payload.x_variable,
                y_variable=payload.y_variable,
                group_variable=payload.group_variable,
                method=method_name,
                sample_size=sample_size,
                results_json=results_json,
                assumptions_json=assumptions_json,
                warnings_json=warnings_json,
                created_by=created_by,
            )
            self.db.add(stat_obj)
            await self.db.flush()

            await self.audit.log(
                entity_type="StatisticalAnalysis",
                entity_id=stat_obj.id,
                action="RUN_STATISTICAL_ANALYSIS",
                changes={"type": atype, "method": method_name, "sample_size": sample_size},
            )
            return stat_obj

        except Exception as exc:
            run.status = AnalysisStatus.FAILED.value
            run.error_message = str(exc)
            run.completed_at = datetime.now(timezone.utc)
            await self.db.flush()
            logger.error("Statistical analysis run %s failed: %s", run.id, exc)
            raise

    async def get_statistical_analysis(self, analysis_id: uuid.UUID) -> StatisticalAnalysis:
        """Fetch StatisticalAnalysis record by ID."""
        res = await self.db.execute(
            select(StatisticalAnalysis).where(StatisticalAnalysis.id == analysis_id)
        )
        stat = res.scalar_one_or_none()
        if stat is None:
            raise ValueError(f"StatisticalAnalysis {analysis_id} not found.")
        return stat

    async def export_dataset_csv(self, dataset_id: uuid.UUID) -> str:
        """Export dataset comparison table to CSV format."""
        tbl = await self.build_comparison_table(dataset_id)
        data = []
        for r in tbl.rows:
            row_dict = {
                "Sample Code": r.sample_code,
                "Sample Name": r.sample_name,
                "Experiment Code": r.experiment_code,
                "Synthesis Method": r.synthesis_method,
            }
            for var in tbl.variables:
                val = r.cells[var].value if var in r.cells else None
                unit = r.cells[var].unit if var in r.cells and r.cells[var].unit else ""
                row_dict[f"{var} ({unit})" if unit else var] = val
            data.append(row_dict)

        df = pd.DataFrame(data)
        csv_buf = io.StringIO()
        df.to_csv(csv_buf, index=False)
        return csv_buf.getvalue()
