"""
GreenSynth Analytics — Candidate Ranker

Ranks candidate parameter sets according to objective direction (MAXIMIZE, MINIMIZE, TARGET_VALUE, TARGET_RANGE)
and recommendation strategy (EXPLOITATION, BALANCED, EXPLORATION).
"""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from app.models.doe import Objective


@dataclass
class CandidateScoringResult:
    objective_score: float
    novelty_score: float
    overall_score: float


class CandidateRanker:
    """
    Computes objective scores and ranks experimental candidates.
    """

    def score_candidate(
        self,
        predicted_val: float,
        objective: Objective,
        constraint_penalty: float,
        evidence_score: float,
        distance_to_nearest: float,
        uncertainty_width: float,
        strategy: str = "BALANCED",
    ) -> CandidateScoringResult:
        dir_upper = objective.direction.upper()

        # 1. Standardized Objective Score calculation (0.0 to 1.0)
        obj_score = 0.5
        if dir_upper == "MAXIMIZE":
            # Higher predicted value -> higher score
            obj_score = 1.0 / (1.0 + np.exp(-0.5 * (predicted_val - (objective.target_value or 0.0))))
        elif dir_upper == "MINIMIZE":
            # Lower predicted value -> higher score
            obj_score = 1.0 / (1.0 + np.exp(0.5 * (predicted_val - (objective.target_value or 0.0))))
        elif dir_upper in ("TARGET_VALUE", "TARGET_RANGE", "TARGET"):
            t_val = objective.target_value or 0.0
            diff = abs(predicted_val - t_val)
            obj_score = max(0.0, 1.0 - (diff / (abs(t_val) + 1.0)))

        obj_score = max(0.0, min(1.0, float(obj_score)))

        # 2. Novelty Score (based on distance to historical experiments)
        novelty_score = max(0.0, min(1.0, float(distance_to_nearest)))

        # 3. Apply Strategy Weighting
        if strategy == "EXPLOITATION":
            # Heavily weight objective score & evidence score, penalize uncertainty
            w_obj, w_ev, w_nov = 0.7, 0.3, 0.0
        elif strategy == "EXPLORATION":
            # Heavily weight novelty score & uncertainty exploration
            w_obj, w_ev, w_nov = 0.2, 0.2, 0.6
        else:  # BALANCED
            w_obj, w_ev, w_nov = 0.5, 0.3, 0.2

        overall = (
            w_obj * obj_score + w_ev * evidence_score + w_nov * novelty_score - constraint_penalty
        )
        overall = max(0.0, min(1.0, float(overall)))

        return CandidateScoringResult(
            objective_score=round(obj_score, 4),
            novelty_score=round(novelty_score, 4),
            overall_score=round(overall, 4),
        )
