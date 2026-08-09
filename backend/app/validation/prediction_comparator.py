"""
GreenSynth Analytics — Prediction Comparator Engine

Calculates absolute error, signed error, relative error (handling zero denominators safely),
prediction interval coverage, target property matching, and explicit unit conversion.
"""

from typing import Dict, Any, Tuple, Optional


class PredictionComparator:
    """
    Core scientific comparator for evaluating ML predictions against actual laboratory measurements.
    """

    @staticmethod
    def calculate_errors(predicted: float, actual: float) -> Tuple[float, float, Optional[float]]:
        """
        Calculates:
          - absolute_error: abs(actual - predicted)
          - signed_error: actual - predicted
          - relative_error: abs(actual - predicted) / abs(actual) if actual != 0 else None ("NOT APPLICABLE")
        """
        signed_err = float(actual - predicted)
        abs_err = float(abs(signed_err))

        if abs(actual) < 1e-12:
            rel_err = None  # Safe handling for zero denominator -> NOT APPLICABLE
        else:
            rel_err = float(abs_err / abs(actual))

        return abs_err, signed_err, rel_err

    @staticmethod
    def check_prediction_interval(actual: float, lower_bound: Optional[float], upper_bound: Optional[float]) -> Optional[bool]:
        """
        Checks if actual measurement falls within [lower_bound, upper_bound].
        Returns True if within interval, False if outside, None if no interval exists.
        """
        if lower_bound is None or upper_bound is None:
            return None
        return bool(lower_bound <= actual <= upper_bound)

    @staticmethod
    def validate_target_and_units(
        predicted_target: str,
        actual_target: str,
        predicted_unit: str,
        actual_unit: str,
        actual_value: float,
    ) -> Tuple[float, str, Optional[str]]:
        """
        Validates target property match and unit compatibility.
        Performs explicit, traceable unit conversions (e.g. resistivity <-> conductivity).
        
        Returns: (converted_actual_value, final_unit, conversion_method_notes)
        """
        # Normalize target strings for comparison
        norm_pred_target = str(predicted_target).strip().lower().replace(" ", "_")
        norm_act_target = str(actual_target).strip().lower().replace(" ", "_")

        if norm_pred_target != norm_act_target:
            raise ValueError(
                f"Validation target mismatch: Model predicted '{predicted_target}' "
                f"but actual measurement target is '{actual_target}'."
            )

        p_unit = str(predicted_unit).strip()
        a_unit = str(actual_unit).strip()

        if p_unit == a_unit:
            return actual_value, a_unit, None

        # Unit Conversion Rules
        # Rule 1: S/cm <-> S/m
        if p_unit == "S/cm" and a_unit == "S/m":
            converted = actual_value / 100.0
            return converted, "S/cm", "Explicit unit conversion: S/m -> S/cm (divide by 100)"
        if p_unit == "S/m" and a_unit == "S/cm":
            converted = actual_value * 100.0
            return converted, "S/m", "Explicit unit conversion: S/cm -> S/m (multiply by 100)"

        # Rule 2: eV <-> J
        if p_unit == "eV" and a_unit == "J":
            converted = actual_value / 1.602176634e-19
            return converted, "eV", "Explicit unit conversion: Joules -> eV"

        # Rule 3: Resistivity (Ohm*cm) <-> Conductivity (S/cm)
        if (p_unit == "S/cm" and a_unit in ["Ohm.cm", "Ohm-cm", "Ω·cm", "Ohm cm"]) or (p_unit in ["Ohm.cm", "Ohm-cm", "Ω·cm"] and a_unit == "S/cm"):
            if abs(actual_value) < 1e-12:
                raise ValueError("Cannot convert zero resistivity to conductivity (division by zero).")
            converted = 1.0 / actual_value
            target_u = "S/cm" if p_unit == "S/cm" else "Ohm-cm"
            return converted, target_u, f"Explicit conversion between resistivity and conductivity: 1 / {actual_value:.4e} {a_unit} -> {converted:.4e} {target_u}"

        # Incompatible units block validation
        raise ValueError(
            f"Validation blocked: Predicted unit '{predicted_unit}' and actual unit '{actual_unit}' "
            f"are incompatible without an explicit conversion."
        )
