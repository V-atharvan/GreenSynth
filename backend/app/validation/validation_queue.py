"""
GreenSynth Analytics — Validation Queue Helper

Identifies experiments created from model recommendations that have completed characterization data
ready for validation.
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.validation import ProspectiveExperiment, ValidationResult
from app.models.experiment import Experiment
from app.models.sample import Sample
from app.models.analysis import CalculatedProperty


class ValidationQueueHelper:
    """
    Helper to query pending experiments ready for prediction vs actual validation.
    """

    @staticmethod
    def get_pending_queue(db: Session, project_id: str | None = None) -> List[Dict[str, Any]]:
        """
        Retrieves pending prospective experiments that have completed physical characterization calculations.
        """
        stmt = select(ProspectiveExperiment)
        if project_id:
            stmt = stmt.where(ProspectiveExperiment.project_id == project_id)

        prospective_list = db.scalars(stmt).all()
        queue_items = []

        for p_exp in prospective_list:
            # Check if validation result already exists
            existing_val = db.scalar(
                select(ValidationResult).where(ValidationResult.experiment_id == p_exp.laboratory_experiment_id)
            ) if p_exp.laboratory_experiment_id else None

            if existing_val:
                continue  # Already validated

            lab_exp = None
            sample = None
            calc_prop = None

            if p_exp.laboratory_experiment_id:
                lab_exp = db.get(Experiment, p_exp.laboratory_experiment_id)
            if p_exp.sample_id:
                sample = db.get(Sample, p_exp.sample_id)
                if sample:
                    calc_prop = db.scalar(
                        select(CalculatedProperty).where(CalculatedProperty.sample_id == sample.id)
                    )

            queue_items.append({
                "prospective_id": str(p_exp.id),
                "model_id": str(p_exp.model_id),
                "model_version": p_exp.model_version,
                "prediction_id": str(p_exp.prediction_id),
                "project_id": str(p_exp.project_id),
                "approval_status": p_exp.approval_status,
                "laboratory_experiment_id": str(p_exp.laboratory_experiment_id) if p_exp.laboratory_experiment_id else None,
                "sample_id": str(p_exp.sample_id) if p_exp.sample_id else None,
                "has_calculated_property": calc_prop is not None,
                "calculated_property": calc_prop.property_name if calc_prop else None,
                "calculated_value": calc_prop.value if calc_prop else None,
                "calculated_unit": calc_prop.unit if calc_prop else None,
                "created_at": p_exp.created_at.isoformat() if p_exp.created_at else None,
            })

        return queue_items
