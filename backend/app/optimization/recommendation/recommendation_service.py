"""
GreenSynth Analytics — Recommendation Orchestration Service

Orchestrates Recommendation Session Generation, Validated Model Gates, Candidate Scoring,
Researcher Reviews/Modifications, and PLANNED Experiment Creation.
"""

from __future__ import annotations

import logging
import uuid
from typing import Sequence

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.doe import Objective
from app.models.experiment import Experiment
from app.models.ml import MLDataset, MLDatasetRecord, MLModel
from app.models.parameter import ParameterDefinition
from app.models.project import Project
from app.models.recommendation import Recommendation, RecommendationCandidate
from app.ml.schemas import MLPredictInput
from app.ml.services.prediction_service import MLPredictionService
from app.optimization.recommendation.candidate_generator import CandidateGenerator
from app.optimization.recommendation.candidate_ranker import CandidateRanker
from app.optimization.recommendation.constraint_engine import ConstraintEngine
from app.optimization.recommendation.diversity_selector import DiversitySelector
from app.optimization.recommendation.domain_checker import DomainChecker
from app.optimization.recommendation.evidence_engine import EvidenceEngine
from app.optimization.recommendation.explanation_service import ExplanationService
from app.optimization.recommendation.schemas import CandidateModifyInput, RecommendationGenerateInput
from app.optimization.recommendation.uncertainty_filter import UncertaintyFilter
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class RecommendationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.audit = AuditService(db)
        self.generator = CandidateGenerator()
        self.constraint_engine = ConstraintEngine()
        self.domain_checker = DomainChecker()
        self.uncertainty_filter = UncertaintyFilter()
        self.evidence_engine = EvidenceEngine()
        self.ranker = CandidateRanker()
        self.diversity_selector = DiversitySelector()
        self.explanation_service = ExplanationService()

    async def generate_recommendations(
        self, payload: RecommendationGenerateInput, researcher: str | None = None
    ) -> Recommendation:
        # 1. Fetch Project
        res_p = await self.db.execute(select(Project).where(Project.id == payload.project_id))
        proj = res_p.scalar_one_or_none()
        if not proj:
            raise ValueError(f"Project {payload.project_id} not found.")

        # 2. Fetch Objective
        res_o = await self.db.execute(select(Objective).where(Objective.id == payload.objective_id))
        obj = res_o.scalar_one_or_none()
        if not obj:
            raise ValueError(f"Objective {payload.objective_id} not found.")

        # 3. Fetch Model & Validate Gates
        res_m = await self.db.execute(select(MLModel).where(MLModel.id == payload.model_id))
        model = res_m.scalar_one_or_none()
        if not model:
            raise ValueError(f"ML Model {payload.model_id} not found.")

        # Status Gate: Model must be EXPERIMENTALLY_VALIDATED or PRODUCTION_CANDIDATE
        if model.status not in ("EXPERIMENTALLY_VALIDATED", "PRODUCTION_CANDIDATE"):
            raise ValueError(
                f"Model Status Block: Model '{model.name}' has status '{model.status}'. "
                "Only EXPERIMENTALLY_VALIDATED or PRODUCTION_CANDIDATE models may generate recommendations."
            )

        # Target Property Matching Gate
        if model.target_property.strip().lower() != obj.target_property.strip().lower():
            raise ValueError(
                f"Model Target Mismatch: Model target '{model.target_property}' does not match objective target '{obj.target_property}'."
            )

        # Project Matching Gate
        res_ds = await self.db.execute(select(MLDataset).where(MLDataset.id == model.dataset_id))
        ds = res_ds.scalar_one_or_none()
        if not ds:
            raise ValueError(f"Dataset {model.dataset_id} not found.")

        if ds.project_id != payload.project_id:
            raise ValueError(f"Project Mismatch: Model dataset belongs to project {ds.project_id}, not {payload.project_id}.")

        # 4. Fetch Training Records & Feature Parameter Definitions
        res_recs = await self.db.execute(select(MLDatasetRecord).where(MLDatasetRecord.dataset_id == ds.id))
        training_records = res_recs.scalars().all()

        res_pdefs = await self.db.execute(
            select(ParameterDefinition).where(ParameterDefinition.project_id == payload.project_id)
        )
        pdefs = res_pdefs.scalars().all()

        # Build parameter ranges from parameter definitions & training records
        param_ranges: dict[str, tuple[float, float]] = {}
        for pdef in pdefs:
            if pdef.parameter_code in model.feature_names:
                min_v = pdef.minimum_value if pdef.minimum_value is not None else 100.0
                max_v = pdef.maximum_value if pdef.maximum_value is not None else 500.0
                # Fallback to dataset record min/max if available
                record_vals = [
                    r.feature_values[pdef.parameter_code]
                    for r in training_records
                    if r.is_eligible and pdef.parameter_code in r.feature_values
                ]
                if record_vals:
                    min_v = min(min_v, min(record_vals))
                    max_v = max(max_v, max(record_vals))
                param_ranges[pdef.parameter_code] = (min_v, max_v)

        if not param_ranges:
            raise ValueError("Candidate Generation Error: Configured experimental parameter ranges are missing.")

        # 5. Generate Candidate Parameter Points
        cand_points = self.generator.generate_candidates(
            parameter_ranges=param_ranges,
            training_records=training_records,
            n_candidates=30,
            random_seed=payload.random_seed,
        )

        # 6. Load Model Artifact for In-Memory Candidate Evaluation
        from app.ml.registry.artifact_store import ModelArtifactStore
        artifact_store = ModelArtifactStore()
        bundle = artifact_store.load_artifact(model.artifact_path)
        fitted_model = bundle["model"]
        pipe = bundle["pipeline"]
        val_rmse = float(model.metrics.get("cv_rmse", 1.0))

        # 6. Evaluate Predictions, Domain, Evidence, and Score each candidate
        scored_candidates: list[dict] = []

        # Count physical validations
        from app.models.validation import ValidationResult
        res_vr = await self.db.execute(select(ValidationResult).where(ValidationResult.model_id == model.id))
        n_phys_val = len(res_vr.scalars().all())

        for pt in cand_points:
            # Predict in memory
            x_row = [float(pt.parameter_set.get(fn, 0.0)) for fn in model.feature_names]
            X_in = np.array([x_row], dtype=float)
            X_scaled = pipe.transform(X_in)
            raw_pred = fitted_model.predict(X_scaled)
            pred_val = float(raw_pred[0])

            # Uncertainty calculation (95% interval)
            lower_bound = pred_val - (1.96 * val_rmse)
            upper_bound = pred_val + (1.96 * val_rmse)
            u_width = upper_bound - lower_bound

            # Constraint Evaluation
            c_res = self.constraint_engine.evaluate(pt.parameter_set, obj, proj)
            if c_res.status == "HARD_VIOLATION":
                continue

            # Domain Check
            d_res = self.domain_checker.check_domain(pt.parameter_set, training_records, ds.features)

            # Uncertainty Check
            u_res = self.uncertainty_filter.check_uncertainty(
                predicted_value=pred_val,
                lower_bound=lower_bound,
                upper_bound=upper_bound,
                max_acceptable_width=payload.max_uncertainty_width,
            )

            # Evidence Evaluation
            e_res = self.evidence_engine.evaluate_evidence(
                model=model,
                domain_status=d_res.status,
                distance_to_nearest=d_res.distance_to_nearest,
                n_physical_validations=n_phys_val,
                uncertainty_width=u_width,
            )

            # Score Candidate
            s_res = self.ranker.score_candidate(
                predicted_val=pred_val,
                objective=obj,
                constraint_penalty=c_res.penalty,
                evidence_score=e_res.evidence_score,
                distance_to_nearest=d_res.distance_to_nearest,
                uncertainty_width=u_width,
                strategy=payload.ranking_method,
            )

            scored_candidates.append({
                "parameter_set": pt.parameter_set,
                "predicted_properties": {
                    "property_name": model.target_property,
                    "predicted_value": round(pred_val, 4),
                    "unit": model.target_unit,
                },
                "uncertainty": {
                    "lower_bound": round(lower_bound, 4),
                    "upper_bound": round(upper_bound, 4),
                    "width": round(u_width, 4),
                },
                "applicability_status": d_res.status,
                "evidence_level": e_res.evidence_level,
                "evidence_score": e_res.evidence_score,
                "objective_score": s_res.objective_score,
                "constraint_status": c_res.status,
                "novelty_score": s_res.novelty_score,
                "overall_score": s_res.overall_score,
                "warning": pt.warning or (d_res.warnings[0] if d_res.warnings else None),
                "is_near_existing": pt.is_near_existing,
            })

        # Sort candidates by overall score descending
        scored_candidates.sort(key=lambda c: c["overall_score"], reverse=True)

        # Apply Diversity Selector to pick Top-N
        top_candidates = self.diversity_selector.select_diverse_subset(
            scored_candidates,
            parameter_names=list(param_ranges.keys()),
            top_n=payload.candidate_count,
        )

        # 7. Persist Recommendation Session & Candidates
        rec = Recommendation(
            project_id=payload.project_id,
            objective_id=payload.objective_id,
            model_id=model.id,
            model_version=model.version,
            dataset_id=ds.id,
            researcher=researcher,
            status="GENERATED",
            candidate_count=len(top_candidates),
            ranking_method=payload.ranking_method,
            random_seed=payload.random_seed,
            notes=payload.notes,
        )
        self.db.add(rec)
        await self.db.flush()

        for idx, cand_data in enumerate(top_candidates, start=1):
            expl = self.explanation_service.generate_explanation(
                rank=idx,
                predicted_val=cand_data["predicted_properties"]["predicted_value"],
                target_property=model.target_property,
                unit=cand_data["predicted_properties"]["unit"],
                evidence_level=cand_data["evidence_level"],
                domain_status=cand_data["applicability_status"],
                strategy=payload.ranking_method,
                constraint_status=cand_data["constraint_status"],
                is_near_existing=cand_data["is_near_existing"],
            )

            rc = RecommendationCandidate(
                recommendation_id=rec.id,
                rank=idx,
                parameter_set=cand_data["parameter_set"],
                predicted_properties=cand_data["predicted_properties"],
                uncertainty=cand_data["uncertainty"],
                applicability_status=cand_data["applicability_status"],
                evidence_level=cand_data["evidence_level"],
                evidence_score=cand_data["evidence_score"],
                objective_score=cand_data["objective_score"],
                constraint_status=cand_data["constraint_status"],
                novelty_score=cand_data["novelty_score"],
                overall_score=cand_data["overall_score"],
                explanation=expl,
                warning=cand_data["warning"],
                status="GENERATED",
            )
            self.db.add(rc)

        await self.db.flush()

        await self.audit.log(
            entity_type="Recommendation",
            entity_id=rec.id,
            action="GENERATE_RECOMMENDATIONS",
            changes={"candidates_count": len(top_candidates), "strategy": payload.ranking_method},
        )
        return await self.get_recommendation(rec.id)

    async def get_recommendation(self, recommendation_id: uuid.UUID) -> Recommendation:
        from sqlalchemy.orm import selectinload

        res = await self.db.execute(
            select(Recommendation)
            .options(selectinload(Recommendation.candidates))
            .where(Recommendation.id == recommendation_id)
        )
        rec = res.scalar_one_or_none()
        if not rec:
            raise ValueError(f"Recommendation {recommendation_id} not found.")
        return rec

    async def approve_candidate(self, candidate_id: uuid.UUID, researcher: str | None = None) -> RecommendationCandidate:
        res = await self.db.execute(select(RecommendationCandidate).where(RecommendationCandidate.id == candidate_id))
        cand = res.scalar_one_or_none()
        if not cand:
            raise ValueError(f"Recommendation Candidate {candidate_id} not found.")

        cand.status = "APPROVED"
        await self.db.flush()

        await self.audit.log(
            entity_type="RecommendationCandidate",
            entity_id=cand.id,
            action="APPROVE_RECOMMENDATION_CANDIDATE",
            changes={"status": "APPROVED"},
        )
        return cand

    async def modify_candidate(
        self, candidate_id: uuid.UUID, payload: CandidateModifyInput
    ) -> RecommendationCandidate:
        res = await self.db.execute(select(RecommendationCandidate).where(RecommendationCandidate.id == candidate_id))
        cand = res.scalar_one_or_none()
        if not cand:
            raise ValueError(f"Recommendation Candidate {candidate_id} not found.")

        cand.modified_parameter_set = payload.modified_parameter_set
        cand.modification_reason = payload.modification_reason
        cand.status = "MODIFIED"
        await self.db.flush()

        await self.audit.log(
            entity_type="RecommendationCandidate",
            entity_id=cand.id,
            action="MODIFY_RECOMMENDATION_CANDIDATE",
            changes={"modified_params": payload.modified_parameter_set, "reason": payload.modification_reason},
        )
        return cand

    async def create_experiment_from_candidate(
        self, candidate_id: uuid.UUID, researcher: str | None = None
    ) -> Experiment:
        """Pre-fills a PLANNED laboratory experiment from an approved/modified recommendation candidate."""
        res_c = await self.db.execute(select(RecommendationCandidate).where(RecommendationCandidate.id == candidate_id))
        cand = res_c.scalar_one_or_none()
        if not cand:
            raise ValueError(f"Recommendation Candidate {candidate_id} not found.")

        res_r = await self.db.execute(select(Recommendation).where(Recommendation.id == cand.recommendation_id))
        rec = res_r.scalar_one_or_none()
        if not rec:
            raise ValueError(f"Recommendation {cand.recommendation_id} not found.")

        params_to_use = cand.modified_parameter_set if cand.modified_parameter_set else cand.parameter_set

        # Create PLANNED experiment
        exp_service_exp = Experiment(
            project_id=rec.project_id,
            experiment_code=f"EXP-REC-{str(uuid.uuid4())[:8].upper()}",
            title=f"Planned Experiment from Recommendation #{cand.rank}",
            status="PLANNED",
            researcher=researcher or "Recommendation Engine",
            notes=f"Generated from Model {rec.model_id} v{rec.model_version}. Explanation: {cand.explanation}",
        )
        self.db.add(exp_service_exp)
        await self.db.flush()

        cand.created_experiment_id = exp_service_exp.id
        cand.status = "EXPERIMENT_CREATED"
        await self.db.flush()

        await self.audit.log(
            entity_type="Experiment",
            entity_id=exp_service_exp.id,
            action="CREATE_EXPERIMENT_FROM_RECOMMENDATION",
            changes={"candidate_id": str(cand.id), "status": "PLANNED"},
        )
        return exp_service_exp
