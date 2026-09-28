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

        # Bulk query all samples, parameters, and calculated properties for project to avoid N+1 WAN latency
        exp_ids = [exp.id for exp in experiments]

        # 2a. Bulk fetch all samples
        s_res = await self.db.execute(
            select(Sample).where(Sample.experiment_id.in_(exp_ids))
        )
        all_samples = s_res.scalars().all()
        samples_by_exp: dict[uuid.UUID, list[Sample]] = {}
        for s in all_samples:
            samples_by_exp.setdefault(s.experiment_id, []).append(s)

        # 2b. Bulk fetch all experiment parameters
        p_res = await self.db.execute(
            select(
                ExperimentParameter,
                ParameterDefinition.parameter_code,
                ParameterDefinition.parameter_name,
            )
            .join(ParameterDefinition, ExperimentParameter.parameter_definition_id == ParameterDefinition.id)
            .where(ExperimentParameter.experiment_id.in_(exp_ids))
        )
        params_by_exp: dict[uuid.UUID, tuple[dict[str, Any], dict[str, str]]] = {}
        for ep, pcode, pname in p_res.all():
            num_val = ep.value_numeric
            if num_val is None and ep.value:
                try:
                    num_val = float(ep.value)
                except ValueError:
                    num_val = ep.value
            val_to_store = num_val if num_val is not None else ep.value
            if val_to_store is not None:
                if ep.experiment_id not in params_by_exp:
                    params_by_exp[ep.experiment_id] = ({}, {})
                pmap, pumap = params_by_exp[ep.experiment_id]
                pmap[pcode] = val_to_store
                pmap[pname] = val_to_store
                if ep.unit:
                    pumap[pcode] = ep.unit
                    pumap[pname] = ep.unit

        # 2c. Bulk fetch all calculated properties
        all_sample_ids = [s.id for s in all_samples]
        props_by_sample: dict[uuid.UUID, list[CalculatedProperty]] = {}
        if all_sample_ids:
            cp_res = await self.db.execute(
                select(CalculatedProperty).where(CalculatedProperty.sample_id.in_(all_sample_ids))
            )
            for cp in cp_res.scalars().all():
                props_by_sample.setdefault(cp.sample_id, []).append(cp)

        candidate_items: list[dict] = []
        for exp in experiments:
            exp_samples = samples_by_exp.get(exp.id, [])
            params_map, param_units_map = params_by_exp.get(exp.id, ({}, {}))

            for smp in exp_samples:
                calc_props = props_by_sample.get(smp.id, [])
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
                    "sample_code": smp.sample_code,
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
        is_ready = quality_indicators.is_valid_for_training and build_result.eligible_count > 0
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
            status="READY" if is_ready else "DRAFT",
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
                exclusion_reason=item.exclusion_reason[:64] if item.exclusion_reason else None,
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
