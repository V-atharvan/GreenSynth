"""
GreenSynth Analytics — Objective Scoring Service

Converts model predictions into comparable normalized scores:
  - MAXIMIZE: higher predicted value = higher score (0.0 to 1.0)
  - MINIMIZE: lower predicted value = higher score (0.0 to 1.0)
  - TARGET: closer predicted value to target = higher score (0.0 to 1.0)

For multi-objective configurations:
  - Normalizes individual objective scores.
  - Applies explicit researcher weights (e.g. 0.6 * score_1 + 0.4 * score_2).
  - Exposes exact contribution breakdowns for complete scientific explainability (no black-box scores).
"""

from __future__ import annotations

from typing import Any


class ObjectiveScoringService:
    """
    Computes objective scores and transparent score contribution breakdowns.
    """

    @staticmethod
    def score_single_objective(
        prediction_val: float,
        direction: str,
        target_val: float | None = None,
        min_val: float | None = None,
        max_val: float | None = None,
    ) -> float:
        """
        Calculate normalized score (0.0 to 1.0) for a single objective.
        """
        pred = float(prediction_val)
        dir_upper = direction.upper()

        if dir_upper == "MAXIMIZE":
            if min_val is not None and max_val is not None and max_val > min_val:
                score = (pred - min_val) / (max_val - min_val)
            else:
                score = 1.0 / (1.0 + math.exp(-pred)) if abs(pred) <= 100 else (1.0 if pred > 0 else 0.0)
            return max(0.0, min(1.0, float(score)))

        elif dir_upper == "MINIMIZE":
            if min_val is not None and max_val is not None and max_val > min_val:
                score = (max_val - pred) / (max_val - min_val)
            else:
                score = 1.0 - (1.0 / (1.0 + math.exp(-pred))) if abs(pred) <= 100 else (0.0 if pred > 0 else 1.0)
            return max(0.0, min(1.0, float(score)))

        elif dir_upper in ("TARGET", "TARGET_VALUE"):
            if target_val is None:
                return 0.5
            diff = abs(pred - float(target_val))
            span = (max_val - min_val) if (min_val is not None and max_val is not None and max_val > min_val) else max(abs(target_val) * 0.5, 1.0)
            score = max(0.0, 1.0 - (diff / span))
            return float(score)

        return 0.5

    @classmethod
    def evaluate_objectives(
        cls,
        predictions: dict[str, float],
        objectives: list[dict[str, Any]],
    ) -> tuple[float, dict[str, Any]]:
        """
        Calculate weighted total objective score and transparent contribution breakdown.

        Returns:
          (total_objective_score, score_breakdown_dict)
        """
        if not objectives:
            return 0.5, {"summary": "No objectives defined", "total_score": 0.5}

        # Normalize weights
        total_weight = sum(float(o.get("weight", 1.0)) for o in objectives)
        if total_weight <= 0:
            total_weight = 1.0

        contributions: dict[str, Any] = {}
        total_score = 0.0

        for idx, obj in enumerate(objectives):
            target_prop = obj.get("target_property", f"property_{idx}")
            pred_val = predictions.get(target_prop, 0.0)

            direction = obj.get("direction", "MAXIMIZE")
            target_val = obj.get("target_value")
            min_val = obj.get("min_value") or obj.get("minimum_value")
            max_val = obj.get("max_value") or obj.get("maximum_value")
            raw_weight = float(obj.get("weight", 1.0))
            norm_weight = raw_weight / total_weight

            raw_score = cls.score_single_objective(
                prediction_val=pred_val,
                direction=direction,
                target_val=target_val,
                min_val=min_val,
                max_val=max_val,
            )

            contribution = raw_score * norm_weight
            total_score += contribution

            contributions[target_prop] = {
                "predicted_value": pred_val,
                "direction": direction,
                "raw_score": round(raw_score, 4),
                "configured_weight": raw_weight,
                "normalized_weight": round(norm_weight, 4),
                "weighted_contribution": round(contribution, 4),
            }

        breakdown = {
            "total_objective_score": round(total_score, 4),
            "objectives_evaluated_count": len(objectives),
            "contributions": contributions,
            "weight_normalization_applied": total_weight != 1.0,
            "total_configured_weight": round(total_weight, 4),
        }

        return round(total_score, 4), breakdown


import math
