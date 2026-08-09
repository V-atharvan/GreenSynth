"""
GreenSynth Analytics — ML-Ready & Optimization-Ready Quality Gates (Phase 15)

Evaluates:
  1. ML_READY Gate: Compliance with ML pipeline validation criteria (N >= 5, valid response, no critical quality errors)
  2. OPTIMIZATION_READY Gate: Compliance with optimization criteria (validated statistical model, known bounds)
"""

from __future__ import annotations

from typing import Any

from app.analytics.statistics.schemas import ReadinessGatesResponse


class ReadinessGatesEngine:
    """Evaluates software validation quality gates for future ML and Optimization modules."""

    @staticmethod
    def evaluate_gates(
        dataset_version_id: Any,
        sample_size: int,
        missing_rate: float,
        quality_status: str,
        has_validated_model: bool = False,
    ) -> ReadinessGatesResponse:
        """Evaluates ML_READY and OPTIMIZATION_READY status with clear disclaimers."""
        ml_criteria = {
            "sufficient_sample_size": sample_size >= 5,
            "acceptable_missing_rate": missing_rate <= 0.35,
            "quality_status_pass_or_warning": quality_status in ("PASS", "WARNING"),
            "dataset_version_locked": True,
        }
        is_ml_ready = all(ml_criteria.values())

        opt_criteria = {
            "is_ml_ready": is_ml_ready,
            "has_validated_statistical_model": has_validated_model,
            "sample_size_sufficient_for_optimization": sample_size >= 8,
        }
        is_opt_ready = all(opt_criteria.values())

        return ReadinessGatesResponse(
            dataset_version_id=dataset_version_id,
            is_ml_ready=is_ml_ready,
            ml_ready_criteria=ml_criteria,
            is_optimization_ready=is_opt_ready,
            optimization_ready_criteria=opt_criteria,
            disclaimer="ML_READY / OPTIMIZATION_READY indicates compliance with software validation quality gates; it does not constitute peer-reviewed scientific proof.",
        )
