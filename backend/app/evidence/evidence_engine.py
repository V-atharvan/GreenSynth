"""
GreenSynth Analytics — Scientific Evidence & Score Engine (Phase 15)

Enforces:
  1. Conservative scientific evidence statement formulation (no automatic causality claims)
  2. Transparent evidence scoring logic based on sample size N, replication, completeness, and model diagnostics
  3. Evidence Record creation & researcher approval workflow
"""

from __future__ import annotations

import math
from typing import Any


class EvidenceEngine:
    """Formulates cautious scientific evidence statements and computes transparent evidence scores."""

    @staticmethod
    def generate_conservative_statement(
        variables: list[str],
        evidence_type: str,
        effect_estimate: float | None,
        statistical_method: str,
        sample_size: int,
    ) -> str:
        """
        Generates conservative scientific statements.

        Allowed: "Observed increase in conductivity with increasing temperature in the tested range."
        Avoided: "Temperature causes conductivity to increase."
        """
        v1 = variables[0] if len(variables) > 0 else "parameter"
        v2 = variables[1] if len(variables) > 1 else "response"

        eff_str = f" (estimated effect: {round(effect_estimate, 4)})" if effect_estimate is not None else ""

        if evidence_type == "OBSERVATION":
            return f"Within the analyzed dataset (N={sample_size}), {v2} was observed under tested {v1} conditions."
        elif evidence_type == "ASSOCIATION":
            direction = "positive" if (effect_estimate or 0) >= 0 else "inverse"
            return (
                f"Within the analyzed dataset (N={sample_size}), {v2} showed a statistically detectable {direction} "
                f"association with {v1} using {statistical_method}{eff_str}."
            )
        elif evidence_type == "STATISTICAL_EFFECT":
            return (
                f"Under the specified experimental design (N={sample_size}), factor {v1} demonstrated an estimated "
                f"main effect on {v2} using {statistical_method}{eff_str}."
            )
        elif evidence_type == "MODEL_ESTIMATE":
            return (
                f"Statistical regression fitting using {statistical_method} (N={sample_size}) estimated response "
                f"variation in {v2} as a function of {v1}{eff_str}."
            )
        else:
            return f"Validated statistical result (N={sample_size}) evaluating relationship between {v1} and {v2} using {statistical_method}."

    @staticmethod
    def compute_evidence_score(
        sample_size: int,
        has_replicates: bool,
        missing_rate: float,
        r_squared: float | None = None,
        heteroscedasticity_warning: bool = False,
    ) -> tuple[float, dict[str, Any]]:
        """
        Computes transparent internal evidence quality score (0.0 to 100.0).

        Scoring Criteria:
          - Sample Size N (up to 30 pts): 3 pts per N up to 10 N
          - Replicate Tracking (up to 20 pts): 20 pts if intentional replicates exist
          - Data Completeness (up to 20 pts): 20 * (1 - missing_rate)
          - Model Diagnostics (up to 30 pts): R^2 fit and no heteroscedasticity penalty
        """
        n_pts = min(sample_size * 3.0, 30.0)
        rep_pts = 20.0 if has_replicates else 5.0
        comp_pts = max(0.0, 20.0 * (1.0 - missing_rate))

        diag_pts = 0.0
        if r_squared is not None:
            diag_pts += r_squared * 20.0
        else:
            diag_pts += 10.0

        if not heteroscedasticity_warning:
            diag_pts += 10.0

        total_score = round(n_pts + rep_pts + comp_pts + diag_pts, 1)
        total_score = min(max(total_score, 0.0), 100.0)

        criteria = {
            "version": "v1.0",
            "sample_size_points": n_pts,
            "replicate_points": rep_pts,
            "completeness_points": comp_pts,
            "diagnostics_points": diag_pts,
            "total_score": total_score,
            "quality_category": "HIGH" if total_score >= 75.0 else ("MODERATE" if total_score >= 50.0 else "LOW"),
        }

        return total_score, criteria
