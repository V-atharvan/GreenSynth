"""
GreenSynth Analytics — Applicability Domain Checker

Checks whether new input conditions fall within or outside the observed feature domain
of the training dataset to prevent unwarranted predictions far beyond observed ranges.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ApplicabilityResult:
    status: str  # VALID, CAUTION, OUT_OF_DOMAIN, MODEL_NOT_VALIDATED
    is_in_domain: bool
    feature_coverage: dict[str, dict[str, Any]]
    warnings: list[str] = field(default_factory=list)


class ApplicabilityChecker:
    """
    Compares input feature parameters against training data min/max boundaries.
    """

    def check_applicability(
        self,
        input_values: dict[str, float],
        training_feature_ranges: dict[str, dict[str, float]],
        model_status: str = "VALIDATED",
    ) -> ApplicabilityResult:
        warnings: list[str] = []
        feature_coverage: dict[str, dict[str, Any]] = {}
        out_of_domain_count = 0

        if model_status not in ("VALIDATED", "PRODUCTION_CANDIDATE"):
            warnings.append(
                f"Model status is '{model_status}'. Predictions should be used with extreme caution."
            )

        for fname, val in input_values.items():
            if fname not in training_feature_ranges:
                feature_coverage[fname] = {"status": "UNKNOWN_FEATURE", "value": val}
                warnings.append(f"Feature '{fname}' was not present in the model training dataset.")
                out_of_domain_count += 1
                continue

            r = training_feature_ranges[fname]
            f_min, f_max = r["min"], r["max"]

            # Tolerance margin (e.g. 5% beyond training range is CAUTION, beyond is OUT_OF_DOMAIN)
            margin = 0.05 * (f_max - f_min) if f_max > f_min else 1.0

            if val < f_min - margin or val > f_max + margin:
                status_str = "OUT_OF_DOMAIN"
                out_of_domain_count += 1
                warnings.append(
                    f"Input '{fname}' ({val}) is outside training range [{f_min}, {f_max}]."
                )
            elif val < f_min or val > f_max:
                status_str = "BORDERLINE"
                warnings.append(
                    f"Input '{fname}' ({val}) is slightly outside training range [{f_min}, {f_max}]."
                )
            else:
                status_str = "IN_DOMAIN"

            feature_coverage[fname] = {
                "value": val,
                "training_min": f_min,
                "training_max": f_max,
                "status": status_str,
            }

        if out_of_domain_count > 0:
            overall_status = "OUT_OF_DOMAIN"
            is_in = False
        elif any(fc.get("status") == "BORDERLINE" for fc in feature_coverage.values()):
            overall_status = "CAUTION"
            is_in = True
        else:
            overall_status = "VALID"
            is_in = True

        return ApplicabilityResult(
            status=overall_status,
            is_in_domain=is_in,
            feature_coverage=feature_coverage,
            warnings=warnings,
        )
