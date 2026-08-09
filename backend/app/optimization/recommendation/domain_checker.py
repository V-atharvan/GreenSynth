"""
GreenSynth Analytics — Recommendation Domain Checker

Evaluates candidate parameter combinations against historical training data range bounds and
calculates distance to nearest historical experiment in normalized parameter space.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np

from app.models.ml import MLDatasetRecord


@dataclass
class DomainCheckResult:
    status: str  # "IN_DOMAIN", "OUT_OF_DOMAIN", "NEAR_BOUNDARY"
    is_in_domain: bool
    distance_to_nearest: float
    warnings: list[str] = field(default_factory=list)


class DomainChecker:
    """
    Checks candidate applicability domain relative to historical training data bounds.
    """

    def check_domain(
        self,
        candidate_params: dict[str, float],
        training_records: list[MLDatasetRecord],
        feature_specs: list[dict],
    ) -> DomainCheckResult:
        warnings: list[str] = []
        if not training_records:
            return DomainCheckResult(
                status="IN_DOMAIN",
                is_in_domain=True,
                distance_to_nearest=0.0,
                warnings=[],
            )

        # 1. Range coverage bounds check
        is_out_of_domain = False
        feat_names = [f["feature_name"] for f in feature_specs]

        for fname in feat_names:
            if fname not in candidate_params:
                continue

            val = candidate_params[fname]
            train_vals = [
                r.feature_values[fname]
                for r in training_records
                if r.is_eligible and fname in r.feature_values
            ]
            if train_vals:
                min_v = min(train_vals)
                max_v = max(train_vals)
                if val < min_v or val > max_v:
                    is_out_of_domain = True
                    warnings.append(
                        f"Out-of-domain parameter: {fname} = {val} falls outside training range [{min_v}, {max_v}]."
                    )

        # 2. Distance metric computation to nearest historical experiment
        # Extract feature matrix from training records
        matrix = []
        for r in training_records:
            if r.is_eligible and all(fn in r.feature_values for fn in feat_names):
                matrix.append([r.feature_values[fn] for fn in feat_names])

        if not matrix:
            return DomainCheckResult(
                status="OUT_OF_DOMAIN" if is_out_of_domain else "IN_DOMAIN",
                is_in_domain=not is_out_of_domain,
                distance_to_nearest=1.0,
                warnings=warnings,
            )

        X_train = np.array(matrix, dtype=float)
        cand_vec = np.array([candidate_params.get(fn, 0.0) for fn in feat_names], dtype=float)

        # Normalize by feature ranges to calculate unitless normalized Euclidean distance
        mins = np.min(X_train, axis=0)
        maxs = np.max(X_train, axis=0)
        ranges = np.where(maxs - mins > 1e-7, maxs - mins, 1.0)

        X_norm = (X_train - mins) / ranges
        cand_norm = (cand_vec - mins) / ranges

        dists = np.linalg.norm(X_norm - cand_norm, axis=1)
        min_dist = float(np.min(dists))

        if is_out_of_domain:
            status = "OUT_OF_DOMAIN"
        elif min_dist > 0.4:
            status = "NEAR_BOUNDARY"
        else:
            status = "IN_DOMAIN"

        return DomainCheckResult(
            status=status,
            is_in_domain=status != "OUT_OF_DOMAIN",
            distance_to_nearest=round(min_dist, 4),
            warnings=warnings,
        )
