"""
GreenSynth Analytics — Group Comparison Statistics Engine

Groups a target numeric variable by a categorical factor (e.g., solvent or synthesis_method),
computing per-group sample size n, mean, median, standard deviation, min, and max.
"""

from __future__ import annotations

import numpy as np

from app.analytics.statistics.schemas import GroupComparisonResponse, GroupStatsItem


def calculate_group_comparison(
    group_var_name: str,
    target_var_name: str,
    group_values: list[str | None],
    target_values: list[float | None],
) -> GroupComparisonResponse:
    """Group target variable by categorical factor and calculate per-group descriptive stats."""
    grouped_data: dict[str, list[float]] = {}

    for g_val, t_val in zip(group_values, target_values):
        if (
            g_val is not None
            and t_val is not None
            and not np.isnan(t_val)
            and not np.isinf(t_val)
        ):
            g_str = str(g_val).strip()
            grouped_data.setdefault(g_str, []).append(float(t_val))

    groups_list: list[GroupStatsItem] = []
    for g_key, vals in sorted(grouped_data.items()):
        n = len(vals)
        arr = np.array(vals, dtype=np.float64)
        mean_val = float(np.mean(arr))
        median_val = float(np.median(arr))
        std_val = float(np.std(arr, ddof=1)) if n > 1 else 0.0

        groups_list.append(
            GroupStatsItem(
                group_value=g_key,
                sample_size_n=n,
                mean=round(mean_val, 4),
                median=round(median_val, 4),
                std_dev=round(std_val, 4),
                min_val=round(float(np.min(arr)), 4),
                max_val=round(float(np.max(arr)), 4),
            )
        )

    # Neutral non-causal comparison text
    if groups_list:
        top_group = max(groups_list, key=lambda g: g.mean or -1e9)
        interp = (
            f"Observed statistical comparison across {len(groups_list)} groups for '{target_var_name}'. "
            f"Group '{top_group.group_value}' had the highest mean value ({top_group.mean}) in the selected observations."
        )
    else:
        interp = f"No valid group observations found for '{target_var_name}'."

    return GroupComparisonResponse(
        group_variable=group_var_name,
        target_variable=target_var_name,
        groups=groups_list,
        interpretation=interp,
    )
