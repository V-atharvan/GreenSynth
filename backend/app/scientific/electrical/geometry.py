"""
GreenSynth Analytics — Sample Geometry & Resistivity Engine

Calculates cross-sectional area A and Electrical Resistivity rho:
  A = width * thickness
  rho = R * A / L  (Ohm*cm)
"""

from __future__ import annotations

import enum
from typing import NamedTuple


class GeometryType(str, enum.Enum):
    RECTANGULAR_BAR = "RECTANGULAR_BAR"
    THIN_FILM = "THIN_FILM"
    TWO_PROBE_BAR = "TWO_PROBE_BAR"


class GeometryAreaResult(NamedTuple):
    area_cm2: float | None
    length_cm: float | None
    width_cm: float | None
    thickness_cm: float | None
    warning_msg: str | None


def calculate_sample_area_cm2(
    geometry_type: GeometryType = GeometryType.RECTANGULAR_BAR,
    length_cm: float | None = None,
    width_cm: float | None = None,
    thickness_cm: float | None = None,
) -> GeometryAreaResult:
    """
    Calculate cross-sectional area A (cm^2) from sample geometry dimensions.

    Validation:
      - If thickness_cm or width_cm or length_cm is missing, returns warning.
    """
    if length_cm is None or length_cm <= 0:
        return GeometryAreaResult(
            area_cm2=None,
            length_cm=length_cm,
            width_cm=width_cm,
            thickness_cm=thickness_cm,
            warning_msg="Cannot calculate resistivity because current path length (L) is missing or non-positive.",
        )

    if width_cm is None or width_cm <= 0:
        return GeometryAreaResult(
            area_cm2=None,
            length_cm=length_cm,
            width_cm=width_cm,
            thickness_cm=thickness_cm,
            warning_msg="Cannot calculate resistivity because sample width (W) is missing or non-positive.",
        )

    if thickness_cm is None or thickness_cm <= 0:
        return GeometryAreaResult(
            area_cm2=None,
            length_cm=length_cm,
            width_cm=width_cm,
            thickness_cm=thickness_cm,
            warning_msg="Cannot calculate resistivity because sample thickness (T) is missing or non-positive.",
        )

    area_cm2 = width_cm * thickness_cm
    return GeometryAreaResult(
        area_cm2=area_cm2,
        length_cm=length_cm,
        width_cm=width_cm,
        thickness_cm=thickness_cm,
        warning_msg=None,
    )
