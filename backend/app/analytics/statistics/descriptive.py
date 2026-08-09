"""
GreenSynth Analytics — Descriptive & Grouped Statistics Engine (Phase 15 Extended)
"""

from __future__ import annotations

import math
import numpy as np

from app.analytics.statistics.schemas import DescriptiveStatsItem, GroupComparisonResponse, GroupStatsItem


def calculate_descriptive_stats(
    variable_name: str, values: list[float | None], unit: str | None = None
) -> DescriptiveStatsItem:
    """
    Calculate comprehensive descriptive statistics for a single variable.

    Calculates: count N, mean, median, std_dev, variance, min, max, range, Q1, Q3, IQR, CV.
    Always displays sample size N. Missing values are counted explicitly without zero insertion.
    """
    clean_vals = [float(v) for v in values if v is not None and not math.isnan(float(v))]
    missing_c = len(values) - len(clean_vals)
    n = len(clean_vals)

    if n == 0:
        return DescriptiveStatsItem(
            variable=variable_name,
            sample_size_n=0,
            unit=unit,
            missing_count=missing_c,
        )

    mean_v = float(np.mean(clean_vals))
    median_v = float(np.median(clean_vals))
    min_v = float(np.min(clean_vals))
    max_v = float(np.max(clean_vals))
    range_v = float(max_v - min_v)

    std_v = float(np.std(clean_vals, ddof=1)) if n > 1 else 0.0
    var_v = float(np.var(clean_vals, ddof=1)) if n > 1 else 0.0

    q1 = float(np.percentile(clean_vals, 25))
    q3 = float(np.percentile(clean_vals, 75))
    iqr = float(q3 - q1)
    cv = float((std_v / abs(mean_v)) * 100.0) if abs(mean_v) > 1e-12 else None

    return DescriptiveStatsItem(
        variable=variable_name,
        sample_size_n=n,
        unit=unit,
        mean=round(mean_v, 4),
        median=round(median_v, 4),
        std_dev=round(std_v, 4),
        variance=round(var_v, 4),
        min_val=round(min_v, 4),
        max_val=round(max_v, 4),
        val_range=round(range_v, 4),
        q1=round(q1, 4),
        q3=round(q3, 4),
        iqr=round(iqr, 4),
        cv=round(cv, 4) if cv is not None else None,
        missing_count=missing_c,
    )


def calculate_grouped_stats(
    group_variable: str,
    target_variable: str,
    group_values: list[tuple[str, float | None]],
) -> GroupComparisonResponse:
    """
    Calculate descriptive statistics grouped by factor level (e.g. Temperature 300°C, 350°C, 400°C).
    """
    grouped_data: dict[str, list[float]] = {}
    for grp, val in group_values:
        if val is not None and not math.isnan(float(val)):
            grouped_data.setdefault(str(grp), []).append(float(val))

    group_items: list[GroupStatsItem] = []
    for grp_name, vals in grouped_data.items():
        n = len(vals)
        mean_v = float(np.mean(vals)) if n > 0 else None
        med_v = float(np.median(vals)) if n > 0 else None
        std_v = float(np.std(vals, ddof=1)) if n > 1 else 0.0
        min_v = float(np.min(vals)) if n > 0 else None
        max_v = float(np.max(vals)) if n > 0 else None

        group_items.append(
            GroupStatsItem(
                group_value=grp_name,
                sample_size_n=n,
                mean=round(mean_v, 4) if mean_v is not None else None,
                median=round(med_v, 4) if med_v is not None else None,
                std_dev=round(std_v, 4) if std_v is not None else None,
                min_val=round(min_v, 4) if min_v is not None else None,
                max_val=round(max_v, 4) if max_v is not None else None,
            )
        )

    interp = f"Grouped analysis of {target_variable} across {len(group_items)} distinct levels of {group_variable}."
    return GroupComparisonResponse(
        group_variable=group_variable,
        target_variable=target_variable,
        groups=group_items,
        interpretation=interp,
    )
