"""
GreenSynth Analytics — Validation Quality & Evidence Level Evaluator

Determines validation evidence level (INSUFFICIENT, LIMITED, MODERATE, STRONG)
based on sample size n, error metrics, and domain coverage.
"""

class ValidationQuality:
    """
    Evaluates evidence quality level without presenting it as a false probability.
    """

    @staticmethod
    def evaluate_evidence_level(sample_count_n: int, avg_relative_error: float | None = None) -> str:
        """
        Determines Validation Evidence Level:
          - INSUFFICIENT: n < 3
          - LIMITED: 3 <= n < 5
          - MODERATE: 5 <= n < 10
          - STRONG: n >= 10
        """
        if sample_count_n < 3:
            return "INSUFFICIENT"
        elif sample_count_n < 5:
            return "LIMITED"
        elif sample_count_n < 10:
            return "MODERATE"
        else:
            return "STRONG"
