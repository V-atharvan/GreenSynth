"""
GreenSynth Analytics — Linear, Interaction & Quadratic Regression Engine (Phase 15 Extended)
"""

from __future__ import annotations

import math
from typing import Any
import numpy as np

from app.analytics.statistics.schemas import RegressionResponse


class RegressionError(ValueError):
    """Raised when regression cannot be performed due to insufficient observations or mathematical error."""
    pass


def calculate_linear_regression(
    x_variable: str,
    y_variable: str,
    x_vals_or_paired: list[float | None] | list[tuple[float | None, float | None]],
    y_vals: list[float | None] | None = None,
) -> RegressionResponse:
    """Calculates OLS linear regression for simple paired values."""
    if y_vals is not None:
        paired = list(zip(x_vals_or_paired, y_vals))  # type: ignore[arg-type]
    elif x_vals_or_paired and isinstance(x_vals_or_paired[0], (tuple, list)):
        paired = x_vals_or_paired  # type: ignore[assignment]
    else:
        paired = []

    clean_pairs = [
        (float(x), float(y))
        for x, y in paired
        if x is not None and y is not None and not math.isnan(float(x)) and not math.isnan(float(y))
    ]
    if len(clean_pairs) < 3:
        raise RegressionError("At least 3 valid paired data points are required to compute linear regression.")

    rows = [{x_variable: p[0], y_variable: p[1]} for p in clean_pairs]
    res = fit_regression_model([x_variable], y_variable, rows, model_type="SIMPLE_LINEAR")
    res.warnings.append("Linear regression model is an empirical fit and not a universal physical law.")
    return res


def fit_regression_model(
    x_variables: list[str],
    y_variable: str,
    data_rows: list[dict[str, float | None]],
    model_type: str = "SIMPLE_LINEAR",
    include_interaction: bool = False,
    include_quadratic: bool = False,
) -> RegressionResponse:
    """
    Fits Ordinary Least Squares regression model (Simple Linear, Multiple Linear, Interaction, Quadratic).
    Calculates R^2, Adj R^2, RMSE, MAE, AIC, BIC, and overfitting warnings.
    """
    valid_rows: list[dict[str, float]] = []
    for r in data_rows:
        y_val = r.get(y_variable)
        if y_val is None or math.isnan(float(y_val)):
            continue
        x_vals = {x: float(r[x]) for x in x_variables if r.get(x) is not None and not math.isnan(float(r[x]))}
        if len(x_vals) == len(x_variables):
            x_vals[y_variable] = float(y_val)
            valid_rows.append(x_vals)

    n = len(valid_rows)
    warnings: list[str] = []

    if n < len(x_variables) + 2:
        return RegressionResponse(
            y_variable=y_variable,
            x_variables=x_variables,
            model_type=model_type,
            formula=f"{y_variable} ~ " + " + ".join(x_variables),
            coefficients={},
            slope=0.0,
            intercept=0.0,
            r_squared=0.0,
            adjusted_r_squared=0.0,
            rmse=0.0,
            mae=0.0,
            sample_size_n=n,
            interpretation=f"Insufficient observations (N={n}) to fit regression model.",
            warnings=["Insufficient observations for statistical regression fitting."],
        )

    # Build design matrix X and response vector y
    X_base = np.array([[r[x] for x in x_variables] for r in valid_rows])
    y = np.array([r[y_variable] for r in valid_rows])

    feature_names = list(x_variables)
    X_cols = [X_base[:, i] for i in range(len(x_variables))]

    # Add interaction terms if requested
    if include_interaction and len(x_variables) >= 2:
        for i in range(len(x_variables)):
            for j in range(i + 1, len(x_variables)):
                interaction_term = X_base[:, i] * X_base[:, j]
                X_cols.append(interaction_term)
                feature_names.append(f"{x_variables[i]}:{x_variables[j]}")

    # Add quadratic terms if requested
    if include_quadratic:
        for i in range(len(x_variables)):
            quad_term = X_base[:, i] ** 2
            X_cols.append(quad_term)
            feature_names.append(f"{x_variables[i]}^2")

    X_design = np.column_stack([np.ones(n)] + X_cols)
    p = X_design.shape[1] - 1  # Number of predictors excluding intercept

    # Overfitting Warning Check
    if n < 5 * p:
        warnings.append(f"Model complexity (p={p}) is high relative to available observations (N={n}). Model may be overfitted.")

    coefficients, residuals_sum, rank, s = np.linalg.lstsq(X_design, y, rcond=None)
    y_pred = X_design @ coefficients
    residuals = y - y_pred

    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    ss_res = float(np.sum(residuals ** 2))

    r2 = max(0.0, 1.0 - (ss_res / ss_tot)) if ss_tot > 1e-12 else 1.0
    adj_r2 = max(0.0, 1.0 - ((1.0 - r2) * (n - 1) / max(n - p - 1, 1))) if n > p + 1 else r2

    rmse = math.sqrt(ss_res / n)
    mae = float(np.mean(np.abs(residuals)))

    # Calculate AIC & BIC
    log_likelihood = -0.5 * n * (math.log(2 * math.pi * (ss_res / n) + 1e-12) + 1)
    aic = 2 * (p + 1) - 2 * log_likelihood
    bic = (p + 1) * math.log(n) - 2 * log_likelihood

    intercept = float(coefficients[0])
    slope = float(coefficients[1]) if len(coefficients) > 1 else 0.0
    coef_dict = {name: round(float(coefficients[idx + 1]), 4) for idx, name in enumerate(feature_names)}

    if len(x_variables) == 1 and not include_interaction and not include_quadratic:
        sign = "+" if intercept >= 0 else "-"
        formula = f"{y_variable} = {slope:.4f} * {x_variables[0]} {sign} {abs(intercept):.4f}"
    else:
        formula_terms = [f"{v} * {name}" for name, v in coef_dict.items()]
        formula = f"{y_variable} = {round(intercept, 4)} + " + " + ".join(formula_terms)

    interp = (
        f"Statistically fitted model for {y_variable} using {p} predictors (R² = {round(r2, 4)}, "
        f"Adj R² = {round(adj_r2, 4)}, RMSE = {round(rmse, 4)}, N = {n})."
    )

    return RegressionResponse(
        y_variable=y_variable,
        x_variables=x_variables,
        model_type=model_type,
        method="Ordinary Least Squares Regression",
        formula=formula,
        coefficients=coef_dict,
        slope=round(slope, 4),
        intercept=round(intercept, 4),
        r_squared=round(r2, 4),
        adjusted_r_squared=round(adj_r2, 4),
        rmse=round(rmse, 4),
        mae=round(mae, 4),
        aic=round(aic, 2),
        bic=round(bic, 2),
        confidence_interval={"slope": [round(float(np.min(coefficients[1:])), 4), round(float(np.max(coefficients[1:])), 4)]} if len(coefficients) > 1 else None,
        prediction_interval={"y_pred": [round(float(np.min(y_pred)), 4), round(float(np.max(y_pred)), 4)]},
        sample_size_n=n,
        interpretation=interp,
        warnings=warnings,
    )
