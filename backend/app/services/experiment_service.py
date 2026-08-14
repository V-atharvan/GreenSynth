"""
GreenSynth Analytics — Experiment Service

Business logic for experiment management operations.
"""

from __future__ import annotations

import logging
import uuid
from typing import Sequence

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.analysis import (
    AnalysisRun,
    CalculatedProperty,
    FTIRAnnotation,
    ProcessedFile,
    SEMAnnotation,
    SEMMeasurement,
    SEMMetadata,
    XRDPeak,
)
from app.models.characterization import Characterization, RawFile
from app.models.doe import ProposedExperiment
from app.models.experiment import Experiment
from app.models.ml import MLDatasetRecord
from app.models.ml_validation import ExperimentPredictionLink
from app.models.parameter import ExperimentParameter
from app.models.recommendation import RecommendationCandidate
from app.models.sample import Sample
from app.models.validation import (
    DatasetCandidate,
    HoldoutValidation,
    ParameterDeviation,
    ProspectiveExperiment,
    RecommendationOutcome,
    ValidationResult,
)
from app.schemas.experiment import ExperimentCreate, ExperimentUpdate
from app.services.audit_service import AuditService
from app.services.project_service import ProjectNotFoundError, ProjectService

logger = logging.getLogger(__name__)


class ExperimentNotFoundError(Exception):
    """Raised when an experiment cannot be found."""


class ExperimentCodeConflictError(Exception):
    """Raised when experiment_code is already in use."""


class ExperimentService:
    """Service layer for experiment management."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(
        self,
        project_id: uuid.UUID | None = None,
        status: str | None = None,
        include_archived: bool = False,
    ) -> Sequence[Experiment]:
        """Return experiments with optional project/status filters."""
        q = (
            select(Experiment)
            .options(selectinload(Experiment.project))
            .order_by(Experiment.created_at.desc())
        )
        if project_id:
            q = q.where(Experiment.project_id == project_id)
        if status:
            q = q.where(Experiment.status == status)
        if not include_archived:
            q = q.where(Experiment.status != "ARCHIVED")
        result = await self.db.execute(q)
        return result.scalars().all()

    async def get_by_id(self, experiment_id: uuid.UUID) -> Experiment:
        """Return experiment by UUID, loading related project and samples."""
        result = await self.db.execute(
            select(Experiment)
            .options(
                selectinload(Experiment.project),
                selectinload(Experiment.samples),
            )
            .where(Experiment.id == experiment_id)
        )
        experiment = result.scalar_one_or_none()
        if experiment is None:
            raise ExperimentNotFoundError(f"Experiment {experiment_id} not found.")
        return experiment

    async def get_by_code(self, experiment_code: str) -> Experiment | None:
        result = await self.db.execute(
            select(Experiment).where(Experiment.experiment_code == experiment_code)
        )
        return result.scalar_one_or_none()

    async def create(self, data: ExperimentCreate) -> Experiment:
        """Create a new experiment. Validates parent project exists."""
        # Verify parent project exists
        project_service = ProjectService(self.db)
        try:
            await project_service.get_by_id(data.project_id)
        except ProjectNotFoundError:
            raise ProjectNotFoundError(
                f"Cannot create experiment: project {data.project_id} not found."
            )

        # Check code uniqueness
        existing = await self.get_by_code(data.experiment_code)
        if existing is not None:
            raise ExperimentCodeConflictError(
                f"Experiment code '{data.experiment_code}' is already in use."
            )

        experiment = Experiment(
            project_id=data.project_id,
            experiment_code=data.experiment_code,
            title=data.title,
            status=data.status.value,
            experiment_date=data.experiment_date,
            researcher=data.researcher,
            notes=data.notes,
        )
        self.db.add(experiment)
        await self.db.flush()
        await self.db.refresh(experiment)
        logger.info("Experiment created: %s (%s)", experiment.experiment_code, experiment.id)
        return experiment

    async def update(self, experiment_id: uuid.UUID, data: ExperimentUpdate) -> Experiment:
        """Update experiment fields. Only non-None fields are changed."""
        experiment = await self.get_by_id(experiment_id)
        update_data = data.model_dump(exclude_none=True)
        for field, value in update_data.items():
            if hasattr(experiment, field):
                setattr(experiment, field, value.value if hasattr(value, "value") else value)
        await self.db.flush()
        await self.db.refresh(experiment)
        logger.info("Experiment updated: %s", experiment_id)
        return experiment

    async def delete(self, experiment_id: uuid.UUID) -> None:
        """Permanently delete an experiment and all associated dependent records."""
        experiment = await self.get_by_id(experiment_id)
        exp_code = experiment.experiment_code

        # Gather sample IDs
        sample_res = await self.db.execute(
            select(Sample.id).where(Sample.experiment_id == experiment_id)
        )
        sample_ids = list(sample_res.scalars().all())

        # Gather characterization IDs and raw file IDs
        char_ids: list[uuid.UUID] = []
        raw_file_ids: list[uuid.UUID] = []
        if sample_ids:
            char_res = await self.db.execute(
                select(Characterization.id).where(Characterization.sample_id.in_(sample_ids))
            )
            char_ids = list(char_res.scalars().all())

            raw_res = await self.db.execute(
                select(RawFile.id).where(
                    (RawFile.sample_id.in_(sample_ids))
                    | (RawFile.characterization_id.in_(char_ids) if char_ids else False)
                )
            )
            raw_file_ids = list(raw_res.scalars().all())

        # Gather AnalysisRun IDs
        analysis_run_ids: list[uuid.UUID] = []
        if char_ids or raw_file_ids:
            an_conds = []
            if char_ids:
                an_conds.append(AnalysisRun.characterization_id.in_(char_ids))
            if raw_file_ids:
                an_conds.append(AnalysisRun.input_file_id.in_(raw_file_ids))
            an_res = await self.db.execute(select(AnalysisRun.id).where(or_(*an_conds)))
            analysis_run_ids = list(an_res.scalars().all())

        # 1. Child records of AnalysisRun
        if analysis_run_ids:
            await self.db.execute(delete(XRDPeak).where(XRDPeak.analysis_run_id.in_(analysis_run_ids)))
            await self.db.execute(
                delete(ProcessedFile).where(ProcessedFile.analysis_run_id.in_(analysis_run_ids))
            )
            await self.db.execute(
                delete(CalculatedProperty).where(
                    CalculatedProperty.analysis_run_id.in_(analysis_run_ids)
                )
            )
            await self.db.execute(
                delete(FTIRAnnotation).where(FTIRAnnotation.analysis_run_id.in_(analysis_run_ids))
            )

        if sample_ids:
            await self.db.execute(
                delete(CalculatedProperty).where(CalculatedProperty.sample_id.in_(sample_ids))
            )

        if raw_file_ids:
            await self.db.execute(
                delete(SEMMetadata).where(SEMMetadata.raw_file_id.in_(raw_file_ids))
            )
            await self.db.execute(
                delete(SEMAnnotation).where(SEMAnnotation.raw_file_id.in_(raw_file_ids))
            )
            await self.db.execute(
                delete(SEMMeasurement).where(SEMMeasurement.raw_file_id.in_(raw_file_ids))
            )
            await self.db.execute(
                delete(ProcessedFile).where(ProcessedFile.raw_file_id.in_(raw_file_ids))
            )

        # 2. Validation & Dataset Candidate records
        cand_conds = [DatasetCandidate.experiment_id == experiment_id]
        if sample_ids:
            cand_conds.append(DatasetCandidate.sample_id.in_(sample_ids))
        await self.db.execute(delete(DatasetCandidate).where(or_(*cand_conds)))

        val_conds = [ValidationResult.experiment_id == experiment_id]
        if sample_ids:
            val_conds.append(ValidationResult.sample_id.in_(sample_ids))
        val_q = await self.db.execute(select(ValidationResult.id).where(or_(*val_conds)))
        val_res_ids = list(val_q.scalars().all())

        if val_res_ids:
            await self.db.execute(
                delete(RecommendationOutcome).where(
                    RecommendationOutcome.validation_id.in_(val_res_ids)
                )
            )

        await self.db.execute(delete(ValidationResult).where(or_(*val_conds)))

        hold_conds = [HoldoutValidation.experiment_id == experiment_id]
        if sample_ids:
            hold_conds.append(HoldoutValidation.sample_id.in_(sample_ids))
        await self.db.execute(delete(HoldoutValidation).where(or_(*hold_conds)))

        # 3. AnalysisRuns, RawFiles, Characterizations
        if analysis_run_ids:
            await self.db.execute(delete(AnalysisRun).where(AnalysisRun.id.in_(analysis_run_ids)))

        if raw_file_ids:
            await self.db.execute(delete(RawFile).where(RawFile.id.in_(raw_file_ids)))

        if char_ids:
            await self.db.execute(delete(Characterization).where(Characterization.id.in_(char_ids)))

        # 4. ML & Parameters
        ml_rec_conds = [MLDatasetRecord.experiment_id == experiment_id]
        if sample_ids:
            ml_rec_conds.append(MLDatasetRecord.sample_id.in_(sample_ids))
        await self.db.execute(delete(MLDatasetRecord).where(or_(*ml_rec_conds)))

        await self.db.execute(
            delete(ExperimentPredictionLink).where(
                ExperimentPredictionLink.experiment_id == experiment_id
            )
        )
        await self.db.execute(
            delete(ParameterDeviation).where(ParameterDeviation.experiment_id == experiment_id)
        )

        # 5. Clear soft references
        prospective_conds = [ProspectiveExperiment.laboratory_experiment_id == experiment_id]
        if sample_ids:
            prospective_conds.append(ProspectiveExperiment.sample_id.in_(sample_ids))
        await self.db.execute(
            update(ProspectiveExperiment)
            .where(or_(*prospective_conds))
            .values(laboratory_experiment_id=None, sample_id=None)
        )

        await self.db.execute(
            update(ProposedExperiment)
            .where(ProposedExperiment.converted_experiment_id == experiment_id)
            .values(converted_experiment_id=None)
        )

        await self.db.execute(
            update(RecommendationCandidate)
            .where(RecommendationCandidate.created_experiment_id == experiment_id)
            .values(created_experiment_id=None)
        )

        # 6. Samples & Experiment Parameters
        if sample_ids:
            await self.db.execute(delete(Sample).where(Sample.experiment_id == experiment_id))

        await self.db.execute(
            delete(ExperimentParameter).where(ExperimentParameter.experiment_id == experiment_id)
        )

        # 7. Audit log entry
        audit_service = AuditService(self.db)
        await audit_service.log(
            entity_type="Experiment",
            entity_id=experiment_id,
            action="DELETE",
            notes=f"Permanently deleted experiment '{exp_code}' and all associated dependent records.",
        )

        # 8. Experiment record itself
        await self.db.execute(delete(Experiment).where(Experiment.id == experiment_id))
        await self.db.flush()
        logger.info("Experiment permanently deleted: %s (%s)", exp_code, experiment_id)

    async def count(
        self,
        project_id: uuid.UUID | None = None,
        include_archived: bool = False,
    ) -> int:
        q = select(func.count(Experiment.id))
        if project_id:
            q = q.where(Experiment.project_id == project_id)
        if not include_archived:
            q = q.where(Experiment.status != "ARCHIVED")
        result = await self.db.execute(q)
        return result.scalar_one()
