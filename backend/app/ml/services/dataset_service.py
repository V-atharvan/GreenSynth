"""
GreenSynth Analytics — ML Dataset Service

Database-aware service layer for creating, building, previewing, and querying ML datasets.
"""

from __future__ import annotations

import logging
import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import CalculatedProperty
from app.models.experiment import Experiment
from app.models.ml import MLDataset, MLDatasetRecord
from app.models.parameter import ExperimentParameter, ParameterDefinition
from app.models.sample import Sample
from app.ml.dataset.builder import DatasetBuilder, DatasetBuildResult
from app.ml.dataset.leakage import LeakageDetector
from app.ml.dataset.validator import DatasetValidator, DatasetQualityIndicators
from app.ml.schemas import MLDatasetCreateInput
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class MLDatasetService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.audit = AuditService(db)

    async def create_dataset(
        self, payload: MLDatasetCreateInput, created_by: str | None = None
    ) -> tuple[MLDataset, DatasetQualityIndicators]:
        """
        Creates an ML dataset definition, extracts eligible experimental observations from DB,
        validates target leakage and quality indicators, and persists dataset records.
        """
        # 1. Leakage Check
        feat_names = [f.feature_name for f in payload.features]
        detector = LeakageDetector()
        leakage_res = detector.check_leakage(payload.target_property, feat_names)

        # 2. Query Candidate Experiments, Samples, Parameters & Properties
        q_exp = select(Experiment).where(Experiment.project_id == payload.project_id)
        if payload.experiment_ids:
            q_exp = q_exp.where(Experiment.id.in_(payload.experiment_ids))
        exp_res = await self.db.execute(q_exp)
        experiments = exp_res.scalars().all()

        candidate_items: list[dict] = []
        for exp in experiments:
            # Query samples for this experiment
            s_res = await self.db.execute(select(Sample).where(Sample.experiment_id == exp.id))
            samples = s_res.scalars().all()

            # Query recorded parameters for this experiment
            p_res = await self.db.execute(
                select(ExperimentParameter, ParameterDefinition.parameter_code)
                .join(ParameterDefinition, ExperimentParameter.parameter_definition_id == ParameterDefinition.id)
                .where(ExperimentParameter.experiment_id == exp.id)
            )
            param_rows = p_res.all()
            params_map: dict[str, float] = {}
            param_units_map: dict[str, str] = {}
            for ep, pcode in param_rows:
                num_val = ep.value_numeric
                if num_val is None and ep.value:
                    try:
                        num_val = float(ep.value)
                    except ValueError:
                        num_val = None
                if num_val is not None:
                    params_map[pcode] = num_val
                    if ep.unit:
                        param_units_map[pcode] = ep.unit

            for smp in samples:
                # Query calculated properties for sample
                cp_res = await self.db.execute(
                    select(CalculatedProperty).where(CalculatedProperty.sample_id == smp.id)
                )
                calc_props = cp_res.scalars().all()
                props_map: dict[str, float] = {}
                prop_units_map: dict[str, str] = {}
                analysis_run_id = None

                for cp in calc_props:
                    props_map[cp.property_name] = cp.value
                    prop_units_map[cp.property_name] = cp.unit
                    analysis_run_id = str(cp.analysis_run_id)

                candidate_items.append({
                    "experiment_id": str(exp.id),
                    "sample_id": str(smp.id),
                    "experiment_status": exp.status,
                    "parameters": params_map,
                    "properties": props_map,
                    "parameter_units": param_units_map,
                    "property_units": prop_units_map,
                    "analysis_run_id": analysis_run_id,
                })

        # 3. Assemble Records via DatasetBuilder
        feature_specs_dicts = [f.model_dump() for f in payload.features]
        builder = DatasetBuilder(
            target_property=payload.target_property,
            target_unit=payload.target_unit,
            feature_specs=feature_specs_dicts,
        )
        build_result: DatasetBuildResult = builder.build_records(
            candidate_items, dataset_name=payload.name
        )

        # 4. Validate Dataset Quality
        validator = DatasetValidator()
        quality_indicators = validator.validate(build_result)
        if leakage_res.has_leakage:
            quality_indicators.warnings.extend(leakage_res.leakage_warnings)

        # 5. Persist MLDataset ORM
        dataset = MLDataset(
            project_id=payload.project_id,
            name=payload.name,
            version="v1",
            description=payload.description,
            target_property=payload.target_property,
            target_type=payload.target_type,
            target_unit=payload.target_unit,
            features=feature_specs_dicts,
            filters=payload.filters,
            status="READY" if quality_indicators.is_valid_for_training else "DRAFT",
            eligible_count=build_result.eligible_count,
            excluded_count=build_result.excluded_count,
            exclusion_summary=build_result.exclusion_summary,
            created_by=created_by,
        )
        self.db.add(dataset)
        await self.db.flush()

        # 6. Persist Records
        for item in build_result.records:
            rec = MLDatasetRecord(
                dataset_id=dataset.id,
                experiment_id=uuid.UUID(item.experiment_id),
                sample_id=uuid.UUID(item.sample_id),
                analysis_run_id=uuid.UUID(item.analysis_run_id) if item.analysis_run_id else None,
                feature_values=item.feature_values,
                target_value=item.target_value,
                target_unit=item.target_unit,
                is_eligible=item.is_eligible,
                exclusion_reason=item.exclusion_reason,
                provenance_details=item.provenance_details,
            )
            self.db.add(rec)

        await self.db.flush()

        await self.audit.log(
            entity_type="MLDataset",
            entity_id=dataset.id,
            action="CREATE_ML_DATASET",
            changes={"name": dataset.name, "eligible_count": dataset.eligible_count},
        )
        return dataset, quality_indicators

    async def get_dataset(self, dataset_id: uuid.UUID) -> MLDataset:
        res = await self.db.execute(select(MLDataset).where(MLDataset.id == dataset_id))
        ds = res.scalar_one_or_none()
        if ds is None:
            raise ValueError(f"ML Dataset {dataset_id} not found.")
        return ds

    async def list_datasets(self, project_id: uuid.UUID) -> Sequence[MLDataset]:
        res = await self.db.execute(
            select(MLDataset)
            .where(MLDataset.project_id == project_id)
            .order_by(MLDataset.created_at.desc())
        )
        return res.scalars().all()

    async def list_dataset_records(self, dataset_id: uuid.UUID) -> Sequence[MLDatasetRecord]:
        res = await self.db.execute(
            select(MLDatasetRecord)
            .where(MLDatasetRecord.dataset_id == dataset_id)
            .order_by(MLDatasetRecord.is_eligible.desc())
        )
        return res.scalars().all()
