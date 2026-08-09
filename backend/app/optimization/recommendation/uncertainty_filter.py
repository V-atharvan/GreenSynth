"""
GreenSynth Analytics — Recommendation Uncertainty Filter

Evaluates model prediction uncertainty bounds and filters/flags candidates with high uncertainty.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class UncertaintyCheckResult:
    is_acceptable: bool
    interval_width: float
    warnings: list[str] = field(default_factory=list)


class UncertaintyFilter:
    def check_uncertainty(
        self,
        predicted_value: float,
        lower_bound: float | None,
        upper_bound: float | None,
        max_acceptable_width: float | None = None,
    ) -> UncertaintyCheckResult:
        warnings: list[str] = []
        if lower_bound is None or upper_bound is None:
            return UncertaintyCheckResult(
                is_acceptable=True,
                interval_width=0.0,
                warnings=["Uncertainty bounds not available for model prediction."],
            )

        width = abs(upper_bound - lower_bound)
        is_acc = True

        if max_acceptable_width is not None and width > max_acceptable_width:
            is_acc = False
            warnings.append(
                f"Prediction uncertainty width ({width:.4f}) exceeds maximum threshold ({max_acceptable_width:.4f}). Candidate should be treated as exploratory."
            )

        return UncertaintyCheckResult(
            is_acceptable=is_acc,
            interval_width=round(width, 4),
            warnings=warnings,
        )
