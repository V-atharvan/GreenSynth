"""
GreenSynth Analytics — Electrical Resistivity & Conductivity Engine

Routines:
  1. Resistivity rho (Ohm*cm): rho = R * A / L
  2. Conductivity sigma (S/cm): sigma = 1 / rho
"""

from __future__ import annotations

from typing import NamedTuple

from app.scientific.electrical.geometry import (
    GeometryType,
    calculate_sample_area_cm2,
)


class ResistivityResult(NamedTuple):
    resistivity_ohm_cm: float | None
    conductivity_s_cm: float | None
    resistance_ohms: float
    area_cm2: float | None
    length_cm: float | None
    warning_msg: str | None
    formula_resistivity: str
    formula_conductivity: str
    assumptions: dict[str, str | float]


def calculate_resistivity_and_conductivity(
    resistance_ohms: float,
    geometry_type: GeometryType = GeometryType.RECTANGULAR_BAR,
    length_cm: float | None = None,
    width_cm: float | None = None,
    thickness_cm: float | None = None,
) -> ResistivityResult:
    """
    Calculate Electrical Resistivity rho (Ohm*cm) and Electrical Conductivity sigma (S/cm).

    rho = R * A / L
    sigma = 1 / rho
    """
    area_res = calculate_sample_area_cm2(
        geometry_type=geometry_type,
        length_cm=length_cm,
        width_cm=width_cm,
        thickness_cm=thickness_cm,
    )

    formula_res = "rho = R * A / L  [Ohm*cm]"
    formula_cond = "sigma = 1 / rho  [S/cm]"

    if area_res.warning_msg or area_res.area_cm2 is None or area_res.length_cm is None:
        return ResistivityResult(
            resistivity_ohm_cm=None,
            conductivity_s_cm=None,
            resistance_ohms=resistance_ohms,
            area_cm2=area_res.area_cm2,
            length_cm=area_res.length_cm,
            warning_msg=area_res.warning_msg,
            formula_resistivity=formula_res,
            formula_conductivity=formula_cond,
            assumptions={
                "resistance_ohms": resistance_ohms,
                "warning": area_res.warning_msg or "Dimensions missing",
            },
        )

    # rho = R * A / L  (Ohm*cm)
    rho = (resistance_ohms * area_res.area_cm2) / area_res.length_cm
    # sigma = 1 / rho  (S/cm)
    sigma = 1.0 / rho if rho > 0 else 0.0

    assumptions = {
        "formula_resistivity": formula_res,
        "formula_conductivity": formula_cond,
        "geometry_type": geometry_type.value,
        "sample_length_cm": area_res.length_cm,
        "sample_width_cm": area_res.width_cm or 0.0,
        "sample_thickness_cm": area_res.thickness_cm or 0.0,
        "cross_sectional_area_cm2": round(area_res.area_cm2, 6),
        "resistance_ohms": resistance_ohms,
    }

    return ResistivityResult(
        resistivity_ohm_cm=round(rho, 6),
        conductivity_s_cm=round(sigma, 6),
        resistance_ohms=resistance_ohms,
        area_cm2=round(area_res.area_cm2, 6),
        length_cm=area_res.length_cm,
        warning_msg=None,
        formula_resistivity=formula_res,
        formula_conductivity=formula_cond,
        assumptions=assumptions,
    )
