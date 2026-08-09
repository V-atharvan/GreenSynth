"""
GreenSynth Analytics — Unit Matcher & Converter

Normalizes measurement units between model prediction and actual laboratory characterizations
prior to error calculation.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class UnitConversionResult:
    normalized_predicted: float
    normalized_actual: float
    normalized_unit: str
    conversion_applied: bool
    warning: str | None = None


class UnitMatcher:
    """
    Normalizes measurement unit mismatches (e.g. S/cm vs mS/cm, Ohm vs kOhm).
    """

    # Scale relative to base unit
    UNIT_SCALE_MAP: dict[str, dict[str, float]] = {
        "CONDUCTIVITY": {
            "S/cm": 1.0,
            "mS/cm": 1e-3,
            "uS/cm": 1e-6,
            "S/m": 1e-2,
        },
        "RESISTANCE": {
            "Ohm": 1.0,
            "kOhm": 1e3,
            "MOhm": 1e6,
        },
        "RESISTIVITY": {
            "Ohm*cm": 1.0,
            "Ohm*m": 100.0,
        },
        "BAND_GAP": {
            "eV": 1.0,
        },
        "CRYSTALLITE_SIZE": {
            "nm": 1.0,
            "um": 1e3,
            "A": 0.1,
        },
    }

    def normalize(
        self, predicted_val: float, predicted_unit: str, actual_val: float, actual_unit: str
    ) -> UnitConversionResult:
        p_u = predicted_unit.strip()
        a_u = actual_unit.strip()

        if p_u == a_u:
            return UnitConversionResult(
                normalized_predicted=predicted_val,
                normalized_actual=actual_val,
                normalized_unit=p_u,
                conversion_applied=False,
            )

        # Search scale maps
        for _cat, scale_dict in self.UNIT_SCALE_MAP.items():
            if p_u in scale_dict and a_u in scale_dict:
                p_base = predicted_val * scale_dict[p_u]
                a_base = actual_val * scale_dict[a_u]
                return UnitConversionResult(
                    normalized_predicted=p_base,
                    normalized_actual=a_base,
                    normalized_unit="BASE_UNIT",
                    conversion_applied=True,
                    warning=f"Converted units: predicted ({p_u}) and actual ({a_u}) to common base unit.",
                )

        # Incompatible units
        return UnitConversionResult(
            normalized_predicted=predicted_val,
            normalized_actual=actual_val,
            normalized_unit=p_u,
            conversion_applied=False,
            warning=f"Unit mismatch: prediction unit '{p_u}' differs from actual lab unit '{a_u}'. Conversion not available.",
        )
