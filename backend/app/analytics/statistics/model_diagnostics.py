"""
GreenSynth Analytics — Statistical Model Diagnostics & Q-Q Plot Engine (Phase 15)

Provides:
  1. Residual vs Fitted plot coordinates
  2. Q-Q Plot sample vs theoretical normal quantiles
  3. Heteroscedasticity detection (unequal variance check)
  4. Normality assessment warnings
"""

from __future__ import annotations

import math
import numpy as np
from scipy import stats

from app.analytics.statistics.schemas import ModelDiagnosticsResponse


class ModelDiagnosticsEngine:
    """Computes residual diagnostics, Q-Q plots, and heteroscedasticity checks."""

    @staticmethod
    def compute_diagnostics(
        residuals: list[float], fitted_values: list[float]
    ) -> ModelDiagnosticsResponse:
        """Computes Q-Q plot quantiles, heteroscedasticity warning, and diagnostic summary."""
        n = len(residuals)
        if n < 4:
            return ModelDiagnosticsResponse(
                residuals=residuals,
                fitted_values=fitted_values,
                qq_sample_quantiles=[],
                qq_theoretical_quantiles=[],
                heteroscedasticity_warning=False,
                normality_warning=False,
                diagnostic_summary="Insufficient residuals to perform formal diagnostics.",
            )

        res_arr = np.array(residuals)
        fit_arr = np.array(fitted_values)

        # Standardize residuals
        std_res = (res_arr - np.mean(res_arr)) / (np.std(res_arr, ddof=1) + 1e-12)

        # Q-Q plot quantiles
        sorted_std_res = np.sort(std_res)
        probabilities = (np.arange(1, n + 1) - 0.5) / n
        theoretical_quantiles = stats.norm.ppf(probabilities)

        # Heteroscedasticity check: compare variance of lower vs upper half of fitted values
        sorted_indices = np.argsort(fit_arr)
        half = n // 2
        lower_var = float(np.var(res_arr[sorted_indices[:half]]))
        upper_var = float(np.var(res_arr[sorted_indices[half:]]))

        var_ratio = (upper_var / lower_var) if lower_var > 1e-12 else 1.0
        hetero_warning = var_ratio > 3.0 or var_ratio < 0.33

        # Shapiro-Wilk test for normality if 3 <= n <= 5000
        normality_warning = False
        if 3 <= n <= 5000:
            stat, p_val = stats.shapiro(res_arr)
            normality_warning = p_val < 0.05

        summary = (
            f"Residual diagnostics evaluated on N={n} observations. "
            f"Heteroscedasticity ratio: {round(var_ratio, 2)}. "
            "Residual diagnostics help assess whether the chosen statistical model assumptions are appropriate."
        )

        return ModelDiagnosticsResponse(
            residuals=[round(float(r), 4) for r in residuals],
            fitted_values=[round(float(f), 4) for f in fitted_values],
            qq_sample_quantiles=[round(float(q), 4) for q in sorted_std_res],
            qq_theoretical_quantiles=[round(float(t), 4) for t in theoretical_quantiles],
            heteroscedasticity_warning=hetero_warning,
            normality_warning=normality_warning,
            diagnostic_summary=summary,
        )
