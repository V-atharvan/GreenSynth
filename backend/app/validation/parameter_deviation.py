"""
GreenSynth Analytics — Parameter Deviation Calculator

Calculates differences and percentage deviations between RECOMMENDED, PLANNED, and ACTUAL
synthesis parameters for full experimental transparency.
"""

from typing import Dict, Any, List, Optional


class ParameterDeviationCalculator:
    """
    Calculates parameter deviations between recommended, planned, and actual values.
    """

    @staticmethod
    def calculate_deviation(
        parameter_name: str,
        recommended: Optional[float],
        planned: Optional[float],
        actual: Optional[float],
        unit: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Calculates absolute and percentage deviation for a single numeric parameter.
        """
        abs_dev = None
        pct_dev = None

        ref_val = planned if planned is not None else recommended

        if actual is not None and ref_val is not None:
            abs_dev = float(actual - ref_val)
            if abs(ref_val) > 1e-12:
                pct_dev = float((actual - ref_val) / abs(ref_val) * 100.0)

        return {
            "parameter_name": parameter_name,
            "recommended_value": recommended,
            "planned_value": planned,
            "actual_value": actual,
            "absolute_deviation": abs_dev,
            "percentage_deviation": pct_dev,
            "unit": unit,
            "has_deviation": abs_dev is not None and abs(abs_dev) > 1e-6,
        }

    @staticmethod
    def compare_parameter_sets(
        recommended_params: Dict[str, float],
        planned_params: Dict[str, float],
        actual_params: Dict[str, float],
    ) -> List[Dict[str, Any]]:
        """
        Compares parameter sets across RECOMMENDED, PLANNED, and ACTUAL.
        """
        all_keys = set(recommended_params.keys()).union(planned_params.keys()).union(actual_params.keys())
        results = []

        for key in sorted(all_keys):
            rec = recommended_params.get(key)
            pln = planned_params.get(key)
            act = actual_params.get(key)
            results.append(
                ParameterDeviationCalculator.calculate_deviation(
                    parameter_name=key,
                    recommended=rec,
                    planned=pln,
                    actual=act,
                )
            )

        return results
