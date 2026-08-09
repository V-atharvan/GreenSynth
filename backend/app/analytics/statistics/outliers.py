"""
GreenSynth Analytics — Outlier Detection & Traceability Engine (Phase 15 Extended)
"""

from __future__ import annotations

import math
from typing import Any
import numpy as np

from app.analytics.statistics.schemas import OutlierItem, OutlierReportResponse


def detect_outliers_iqr(
    variable_name: str,
    sample_ids_or_records: Any,
    sample_codes_or_method: Any = None,
    values_or_thresh: Any = None,
    iqr_multiplier: float = 1.5,
) -> OutlierReportResponse:
    """Supports both 4-argument signature (var, s_ids, s_codes, vals) and 2-argument signature."""
    if isinstance(sample_codes_or_method, list) and isinstance(values_or_thresh, list):
        sample_ids = sample_ids_or_records
        sample_codes = sample_codes_or_method
        values = values_or_thresh
        records = [(sid, scode, v) for sid, scode, v in zip(sample_ids, sample_codes, values)]
        return detect_outliers_iqr_or_zscore(variable_name, records, method="IQR", threshold=iqr_multiplier)
    else:
        return detect_outliers_iqr_or_zscore(variable_name, sample_ids_or_records, method="IQR", threshold=iqr_multiplier)


def detect_outliers_iqr_or_zscore(
    variable_name: str,
    records: list[tuple[Any, str, float | None]],
    method: str = "IQR",
    threshold: float = 1.5,
) -> OutlierReportResponse:
    """
    Detect outliers using IQR or Z-score method.

    FLAGS potential outliers without modifying or deleting original measurements.
    """
    valid_recs: list[tuple[Any, str, float]] = []
    for r in records:
        if len(r) == 3:
            sid, scode, val = r
        else:
            sid, scode, val = r[0], str(r[0]), r[1]
        if val is not None and not math.isnan(float(val)):
            valid_recs.append((sid, scode, float(val)))

    total_inspected = len(valid_recs)
    if total_inspected < 4:
        return OutlierReportResponse(
            variable=variable_name,
            method=method,
            threshold=threshold,
            total_inspected=total_inspected,
            outliers_found=[],
        )

    vals = np.array([r[2] for r in valid_recs])
    outliers: list[OutlierItem] = []

    if method.upper() == "IQR":
        q1 = float(np.percentile(vals, 25))
        q3 = float(np.percentile(vals, 75))
        iqr = q3 - q1
        low_bound = q1 - threshold * iqr
        high_bound = q3 + threshold * iqr

        for sid, scode, v in valid_recs:
            if v < low_bound or v > high_bound:
                dev = abs(v - float(np.median(vals)))
                score = dev / iqr if iqr > 1e-12 else dev
                outliers.append(
                    OutlierItem(
                        sample_id=str(sid),
                        sample_code=scode,
                        variable=variable_name,
                        value=round(v, 4),
                        method="IQR",
                        score=round(float(score), 4),
                    )
                )

    else:  # Z_SCORE
        mean_v = float(np.mean(vals))
        std_v = float(np.std(vals, ddof=1)) if len(vals) > 1 else 1.0

        for sid, scode, v in valid_recs:
            z_score = (v - mean_v) / std_v if std_v > 1e-12 else 0.0
            if abs(z_score) > threshold:
                outliers.append(
                    OutlierItem(
                        sample_id=str(sid),
                        sample_code=scode,
                        variable=variable_name,
                        value=round(v, 4),
                        method="Z_SCORE",
                        score=round(float(z_score), 4),
                    )
                )

    return OutlierReportResponse(
        variable=variable_name,
        method=method,
        threshold=threshold,
        total_inspected=total_inspected,
        outliers_found=outliers,
    )
