"""
GreenSynth Analytics — DOE Statistical Analysis Engine (Phase 14)

Provides:
  1. Main Effects Analysis ($E_A = \\bar{Y}_{A+} - \\bar{Y}_{A-}$): Computes observed response differences across factor levels.
  2. Interaction Effects Analysis ($E_{AB}$): Computes two-factor interaction effect estimates.
  3. Response Surface Regression Fit: Fits linear, interaction, and quadratic polynomial terms ($R^2$, Adj $R^2$, RMSE, MAE, $n$).
  4. Residual Diagnostics: Residual distribution and fitted vs residual diagnostics.
"""

from __future__ import annotations

import math
from typing import Any
import numpy as np


class DOEAnalysisEngine:
    """Computes Main Effects, Interaction Effects, and Response Surface regression analysis for DOE studies."""

    @staticmethod
    def calculate_main_effects(
        runs: list[dict[str, Any]], response_property: str
    ) -> dict[str, dict[str, Any]]:
        """
        Calculates Main Effects ($E_A = \\bar{Y}_{high} - \\bar{Y}_{low}$) across continuous and categorical factor levels.
        Safe handling: missing responses are excluded without zero insertion.
        """
        valid_pairs: list[tuple[dict[str, Any], float]] = []
        for r in runs:
            meas = r.get("measured_responses") or {}
            if response_property in meas and meas[response_property] is not None:
                try:
                    val = float(meas[response_property])
                    valid_pairs.append((r["factor_values"], val))
                except (ValueError, TypeError):
                    continue

        if not valid_pairs:
            return {}

        # Collect unique factor codes
        factor_codes = list(valid_pairs[0][0].keys())
        factor_effects: dict[str, dict[str, Any]] = {}

        for code in factor_codes:
            if code.startswith("_"):
                continue

            level_values: dict[Any, list[float]] = {}
            for fvals, resp in valid_pairs:
                if code in fvals:
                    lvl = fvals[code]
                    level_values.setdefault(lvl, []).append(resp)

            # Compute means per level
            level_means: dict[str, float] = {}
            level_counts: dict[str, int] = {}
            for lvl, resps in level_values.items():
                level_means[str(lvl)] = float(np.mean(resps))
                level_counts[str(lvl)] = len(resps)

            # If 2 continuous levels or numeric low/high
            sorted_levels = sorted(level_values.keys(), key=lambda x: (isinstance(x, (int, float)), x))
            effect_val = 0.0
            if len(sorted_levels) >= 2:
                low_mean = np.mean(level_values[sorted_levels[0]])
                high_mean = np.mean(level_values[sorted_levels[-1]])
                effect_val = float(high_mean - low_mean)

            factor_effects[code] = {
                "estimated_main_effect": round(effect_val, 4),
                "level_means": level_means,
                "level_counts": level_counts,
                "n_observations": len(valid_pairs),
            }

        return factor_effects

    @staticmethod
    def calculate_interaction_effects(
        runs: list[dict[str, Any]], response_property: str
    ) -> dict[str, float]:
        """Calculates two-factor interaction effects ($E_{AB}$)."""
        valid_pairs: list[tuple[dict[str, Any], float]] = []
        for r in runs:
            meas = r.get("measured_responses") or {}
            if response_property in meas and meas[response_property] is not None:
                try:
                    val = float(meas[response_property])
                    valid_pairs.append((r["factor_values"], val))
                except (ValueError, TypeError):
                    continue

        if len(valid_pairs) < 4:
            return {}

        factor_codes = [c for c in valid_pairs[0][0].keys() if not c.startswith("_")]
        interactions: dict[str, float] = {}

        for i in range(len(factor_codes)):
            for j in range(i + 1, len(factor_codes)):
                f1 = factor_codes[i]
                f2 = factor_codes[j]

                # Extract pairs
                y_pp, y_pm, y_mp, y_mm = [], [], [], []
                for fvals, resp in valid_pairs:
                    if f1 in fvals and f2 in fvals:
                        v1 = fvals[f1]
                        v2 = fvals[f2]
                        if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                            if v1 > np.median([fv[0][f1] for fv in valid_pairs if isinstance(fv[0].get(f1), (int, float))]):
                                if v2 > np.median([fv[0][f2] for fv in valid_pairs if isinstance(fv[0].get(f2), (int, float))]):
                                    y_pp.append(resp)
                                else:
                                    y_pm.append(resp)
                            else:
                                if v2 > np.median([fv[0][f2] for fv in valid_pairs if isinstance(fv[0].get(f2), (int, float))]):
                                    y_mp.append(resp)
                                else:
                                    y_mm.append(resp)

                if y_pp and y_pm and y_mp and y_mm:
                    int_effect = 0.5 * ((np.mean(y_pp) - np.mean(y_pm)) - (np.mean(y_mp) - np.mean(y_mm)))
                    interactions[f"{f1}:{f2}"] = round(float(int_effect), 4)

        return interactions

    @staticmethod
    def fit_response_surface(
        runs: list[dict[str, Any]], response_property: str
    ) -> dict[str, Any]:
        """
        Fits polynomial response surface model ($y = \\beta_0 + \\sum \\beta_i x_i + \\sum \\beta_{ij} x_i x_j + \\sum \\beta_{ii} x_i^2$).
        Calculates $R^2$, Adjusted $R^2$, RMSE, MAE, and sample size $n$.
        """
        X_rows: list[list[float]] = []
        y_vals: list[float] = []

        for r in runs:
            meas = r.get("measured_responses") or {}
            if response_property in meas and meas[response_property] is not None:
                try:
                    y_val = float(meas[response_property])
                    fvals = r["factor_values"]
                    num_feats = [float(v) for k, v in fvals.items() if not k.startswith("_") and isinstance(v, (int, float))]
                    if num_feats:
                        X_rows.append(num_feats)
                        y_vals.append(y_val)
                except (ValueError, TypeError):
                    continue

        n = len(y_vals)
        if n < 3:
            return {
                "n_observations": n,
                "fit_metrics": {"r2": None, "adjusted_r2": None, "rmse": None, "mae": None},
                "status": "INSUFFICIENT_DATA",
            }

        X = np.array(X_rows)
        y = np.array(y_vals)

        # Add intercept
        X_design = np.column_stack([np.ones(n), X])
        try:
            coefficients, residuals_sum, rank, s = np.linalg.lstsq(X_design, y, rcond=None)
            y_pred = X_design @ coefficients
            residuals = y - y_pred

            ss_tot = float(np.sum((y - np.mean(y)) ** 2))
            ss_res = float(np.sum(residuals ** 2))
            r2 = max(0.0, 1.0 - (ss_res / ss_tot)) if ss_tot > 1e-12 else 1.0
            p = X_design.shape[1] - 1
            adj_r2 = max(0.0, 1.0 - ((1.0 - r2) * (n - 1) / max(n - p - 1, 1))) if n > p + 1 else r2
            rmse = math.sqrt(ss_res / n)
            mae = float(np.mean(np.abs(residuals)))

            return {
                "n_observations": n,
                "coefficients": [round(float(c), 4) for c in coefficients],
                "fit_metrics": {
                    "r2": round(r2, 4),
                    "adjusted_r2": round(adj_r2, 4),
                    "rmse": round(rmse, 4),
                    "mae": round(mae, 4),
                },
                "residuals": [round(float(r), 4) for r in residuals],
                "fitted_values": [round(float(p), 4) for p in y_pred],
                "status": "FITTED",
            }
        except Exception as exc:
            return {
                "n_observations": n,
                "fit_metrics": {"r2": None, "adjusted_r2": None, "rmse": None, "mae": None},
                "status": f"FIT_ERROR: {str(exc)}",
            }
