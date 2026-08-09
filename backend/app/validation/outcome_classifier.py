"""
GreenSynth Analytics — Recommendation Outcome Classifier

Classifies whether physical experiment results SUPPORT, PARTIALLY SUPPORT, NOT SUPPORT,
or are INCONCLUSIVE regarding the original model recommendation.
"""

from typing import Optional


class OutcomeClassifier:
    """
    Evaluates recommendation outcomes based on relative/absolute error and prediction interval checks.
    """

    @staticmethod
    def classify_outcome(
        absolute_error: float,
        relative_error: Optional[float],
        within_prediction_interval: Optional[bool],
        data_quality_valid: bool = True,
        acceptable_rel_error_threshold: float = 0.15,
        acceptable_abs_error_threshold: float = 0.5,
    ) -> str:
        """
        Returns one of:
          - SUPPORTED
          - PARTIALLY_SUPPORTED
          - NOT_SUPPORTED
          - INCONCLUSIVE
        """
        if not data_quality_valid:
            return "INCONCLUSIVE"

        rel_ok = (relative_error is not None) and (relative_error <= acceptable_rel_error_threshold)
        abs_ok = absolute_error <= acceptable_abs_error_threshold
        interval_ok = (within_prediction_interval is True)

        if (rel_ok or abs_ok) and interval_ok:
            return "SUPPORTED"

        if rel_ok or abs_ok or interval_ok or (relative_error is not None and relative_error <= 0.30):
            return "PARTIALLY_SUPPORTED"

        if relative_error is not None and relative_error > 0.50:
            return "NOT_SUPPORTED"

        return "INCONCLUSIVE"
