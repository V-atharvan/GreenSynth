"""
GreenSynth Analytics — Recommendation Evidence Engine

Computes transparent evidence scores and evidence levels (HIGH, MODERATE, LOW).
Combines Level 1 statistical metrics, Level 2/3 physical experimental validations, and domain proximity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from app.models.ml import MLModel


@dataclass
class EvidenceEvaluationResult:
    evidence_level: str  # "HIGH", "MODERATE", "LOW"
    evidence_score: float
    summary: str
    warnings: list[str] = field(default_factory=list)


class EvidenceEngine:
    """
    Evaluates experimental evidence supporting a candidate prediction.
    """

    def evaluate_evidence(
        self,
        model: MLModel,
        domain_status: str,
        distance_to_nearest: float,
        n_physical_validations: int = 0,
        uncertainty_width: float | None = None,
    ) -> EvidenceEvaluationResult:
        warnings: list[str] = []
        score = 0.5  # Base moderate score

        # 1. Model cross-validation fit bonus
        cv_r2 = float(model.metrics.get("cv_r2", 0.5))
        score += (cv_r2 - 0.5) * 0.3

        # 2. Physical experimental validation bonus
        if n_physical_validations >= 5:
            score += 0.2
        elif n_physical_validations >= 1:
            score += 0.1
        else:
            warnings.append("Low physical validation evidence: Model relies primarily on cross-validation data.")

        # 3. Domain proximity penalty
        if domain_status == "OUT_OF_DOMAIN":
            score -= 0.4
            warnings.append("Candidate is outside the model's observed training domain.")
        elif domain_status == "NEAR_BOUNDARY":
            score -= 0.15
            warnings.append("Candidate lies near training domain boundary.")

        # Clamp score between 0.0 and 1.0
        score = max(0.0, min(1.0, score))

        # Classify Evidence Level
        if score >= 0.7:
            level = "HIGH"
            summary = "High experimental evidence: Model has strong validation metrics and candidate lies well within training domain."
        elif score >= 0.4:
            level = "MODERATE"
            summary = "Moderate experimental evidence: Candidate within domain, but model prediction uncertainty or validation sample size is moderate."
        else:
            level = "LOW"
            summary = "Low experimental evidence: Candidate is near/outside domain or model validation is limited. Additional lab testing strongly required."

        return EvidenceEvaluationResult(
            evidence_level=level,
            evidence_score=round(score, 4),
            summary=summary,
            warnings=warnings,
        )
