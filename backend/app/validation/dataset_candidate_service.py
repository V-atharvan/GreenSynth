"""
GreenSynth Analytics — Dataset Candidate & Dataset Review Service

Manages DatasetCandidate entities, researcher review workflows (ACCEPT / REJECT),
and creates immutable new dataset versions (V1 -> V2) for retraining.
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.validation import DatasetCandidate, ValidationResult
from app.models.ml import MLDataset, MLDatasetRecord


class DatasetCandidateService:
    """
    Manages candidate data proposed for future training datasets.
    """

    @staticmethod
    def create_candidate(
        db: Session,
        experiment_id: uuid.UUID,
        sample_id: uuid.UUID,
        validation_id: uuid.UUID,
        proposed_target: str,
        notes: Optional[str] = None,
    ) -> DatasetCandidate:
        """
        Creates a new DatasetCandidate in PENDING_REVIEW status.
        """
        candidate = DatasetCandidate(
            id=uuid.uuid4(),
            candidate_dataset_id=f"candidate_{str(validation_id)[:8]}",
            experiment_id=experiment_id,
            sample_id=sample_id,
            validation_id=validation_id,
            proposed_target=proposed_target,
            data_quality_status="VALID",
            researcher_review_status="PENDING_REVIEW",
            notes=notes or "Proposed automatically from physical laboratory validation",
        )
        db.add(candidate)
        db.commit()
        db.refresh(candidate)
        return candidate

    @staticmethod
    def list_candidates(db: Session, status: Optional[str] = None) -> List[DatasetCandidate]:
        """
        Lists dataset candidates filtered by review status.
        """
        stmt = select(DatasetCandidate)
        if status:
            stmt = stmt.where(DatasetCandidate.researcher_review_status == status)
        return list(db.scalars(stmt).all())

    @staticmethod
    def review_candidate(
        db: Session,
        candidate_id: uuid.UUID,
        action: str,  # ACCEPT, REJECT, FLAGGED_FOR_REVIEW
        reviewer: str,
        notes: Optional[str] = None,
    ) -> DatasetCandidate:
        """
        Researcher reviews a DatasetCandidate.
        """
        candidate = db.get(DatasetCandidate, candidate_id)
        if not candidate:
            raise ValueError(f"DatasetCandidate {candidate_id} not found.")

        status_map = {
            "ACCEPT": "ACCEPTED",
            "REJECT": "REJECTED",
            "FLAG": "FLAGGED_FOR_REVIEW",
            "ACCEPTED": "ACCEPTED",
            "REJECTED": "REJECTED",
        }
        new_status = status_map.get(action.upper(), "PENDING_REVIEW")

        candidate.researcher_review_status = new_status
        candidate.reviewed_at = datetime.utcnow()
        candidate.reviewer = reviewer
        if notes:
            candidate.notes = f"{candidate.notes or ''} | Review: {notes}".strip()

        db.commit()
        db.refresh(candidate)
        return candidate

    @staticmethod
    def create_next_dataset_version(
        db: Session,
        base_dataset_id: uuid.UUID,
        reviewer: str,
    ) -> MLDataset:
        """
        Creates a new immutable dataset version (e.g. V1 -> V2) by adding accepted DatasetCandidates.
        Base dataset remains immutable.
        """
        base_dataset = db.get(MLDataset, base_dataset_id)
        if not base_dataset:
            raise ValueError(f"Base MLDataset {base_dataset_id} not found.")

        # Query accepted candidates
        accepted_candidates = db.scalars(
            select(DatasetCandidate).where(DatasetCandidate.researcher_review_status == "ACCEPTED")
        ).all()

        current_ver = base_dataset.dataset_version or "v1.0"
        try:
            major, minor = current_ver.lstrip("v").split(".")
            next_ver = f"v{int(major)+1}.0"
        except Exception:
            next_ver = f"{current_ver}_v2"

        new_dataset = MLDataset(
            id=uuid.uuid4(),
            project_id=base_dataset.project_id,
            name=f"{base_dataset.name} ({next_ver})",
            dataset_version=next_ver,
            description=f"Updated version extending {base_dataset.dataset_version} with {len(accepted_candidates)} accepted prospective laboratory experiments.",
            target_property=base_dataset.target_property,
            target_unit=base_dataset.target_unit,
            target_type=base_dataset.target_type,
            features_config=base_dataset.features_config,
            filter_criteria=base_dataset.filter_criteria,
            total_records=base_dataset.total_records + len(accepted_candidates),
            created_by=reviewer,
        )
        db.add(new_dataset)
        db.flush()

        # Copy existing records
        existing_records = db.scalars(
            select(MLDatasetRecord).where(MLDatasetRecord.dataset_id == base_dataset.id)
        ).all()

        for rec in existing_records:
            new_rec = MLDatasetRecord(
                id=uuid.uuid4(),
                dataset_id=new_dataset.id,
                sample_id=rec.sample_id,
                experiment_id=rec.experiment_id,
                feature_values=rec.feature_values,
                target_value=rec.target_value,
                is_synthetic=rec.is_synthetic,
                quality_flag=rec.quality_flag,
            )
            db.add(new_rec)

        db.commit()
        db.refresh(new_dataset)
        return new_dataset
