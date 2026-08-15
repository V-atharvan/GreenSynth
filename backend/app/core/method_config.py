"""
GreenSynth Analytics — Canonical Synthesis Method & Parameter Architecture Configuration

Defines:
  1. SynthesisMethod Enum: SOL_GEL, HYDROTHERMAL, SPRAY_PYROLYSIS.
  2. Project/Method Configuration Matrix (P1 through P8).
  3. Parameter Groups by Synthesis Method.
  4. Method-aware parameter validation helpers.
"""

from __future__ import annotations

import enum
from typing import Any


class SynthesisMethod(str, enum.Enum):
    SOL_GEL = "SOL_GEL"
    HYDROTHERMAL = "HYDROTHERMAL"
    SPRAY_PYROLYSIS = "SPRAY_PYROLYSIS"


METHOD_DISPLAY_NAMES: dict[str, str] = {
    SynthesisMethod.SOL_GEL.value: "Sol-Gel",
    SynthesisMethod.HYDROTHERMAL.value: "Hydrothermal",
    SynthesisMethod.SPRAY_PYROLYSIS.value: "Spray Pyrolysis",
}


PROJECT_METHOD_MATRIX: dict[str, dict[str, Any]] = {
    "P1": {
        "project_code": "P1",
        "name": "CuO Phytochemical Synthesis via Sol-Gel using Ethanol",
        "material_system": "CuO",
        "material": "CuO",
        "method": SynthesisMethod.SOL_GEL.value,
        "solvent": "ETHANOL",
        "biomass": None,
        "extract": "Mulberry",
    },
    "P2": {
        "project_code": "P2",
        "name": "CuO Phytochemical Synthesis via Sol-Gel using Acetone",
        "material_system": "CuO",
        "material": "CuO",
        "method": SynthesisMethod.SOL_GEL.value,
        "solvent": "ACETONE",
        "biomass": None,
        "extract": "Mulberry",
    },
    "P3": {
        "project_code": "P3",
        "name": "CuO Phytochemical Synthesis via Hydrothermal using Ethanol",
        "material_system": "CuO",
        "material": "CuO",
        "method": SynthesisMethod.HYDROTHERMAL.value,
        "solvent": "ETHANOL",
        "biomass": None,
        "extract": "Mulberry",
    },
    "P4": {
        "project_code": "P4",
        "name": "CuO Phytochemical Synthesis via Hydrothermal using Acetone",
        "material_system": "CuO",
        "material": "CuO",
        "method": SynthesisMethod.HYDROTHERMAL.value,
        "solvent": "ACETONE",
        "biomass": None,
        "extract": "Mulberry",
    },
    "P5": {
        "project_code": "P5",
        "name": "Biomass-Derived Silica/Silicon Hydrothermal Synthesis using Ethanol",
        "material_system": "SILICA_SILICON",
        "material": "Silica / Silicon",
        "method": SynthesisMethod.HYDROTHERMAL.value,
        "solvent": "ETHANOL",
        "biomass": "Rice husk",
        "extract": "Mulberry",
    },
    "P6": {
        "project_code": "P6",
        "name": "Biomass-Derived Silica/Silicon Hydrothermal Synthesis using Acetone",
        "material_system": "SILICA_SILICON",
        "material": "Silica / Silicon",
        "method": SynthesisMethod.HYDROTHERMAL.value,
        "solvent": "ACETONE",
        "biomass": "Rice husk",
        "extract": "Mulberry",
    },
    "P7": {
        "project_code": "P7",
        "name": "Phytochemical synthesis of semiconducting copper oxide using mulberry extract in ethanol by spray pyrolysis",
        "material_system": "CuO",
        "material": "CuO",
        "method": SynthesisMethod.SPRAY_PYROLYSIS.value,
        "solvent": "ETHANOL",
        "biomass": None,
        "extract": "Mulberry",
    },
    "P8": {
        "project_code": "P8",
        "name": "CuO Phytochemical Synthesis via Spray Pyrolysis using Acetone",
        "material_system": "CuO",
        "material": "CuO",
        "method": SynthesisMethod.SPRAY_PYROLYSIS.value,
        "solvent": "ACETONE",
        "biomass": None,
        "extract": "Mulberry",
    },
}


COMMON_PRECURSOR_EXTRACT_CODES: list[str] = [
    "copper_precursor_salt",
    "copper_precursor",
    "precursor_concentration",
    "precursor_solution_volume",
    "precursor_volume",
    "mulberry_extract_concentration",
    "extract_concentration",
    "mulberry_extract_volume",
    "extract_volume",
]

COMMON_SOLVENT_CODES: list[str] = [
    "solvent_volume",
    "ethanol_volume",
]

SPRAY_PYROLYSIS_CODES: list[str] = [
    "substrate_type",
    "substrate_temperature_c",
    "substrate_temperature",
    "spray_duration_min",
    "nozzle_substrate_distance_cm",
    "spray_rate_ml_min",
    "spray_rate",
    "carrier_gas_pressure_kpa",
    "spray_cycles",
    "ambient_temperature_c",
    "ambient_relative_humidity",
]

SOL_GEL_CODES: list[str] = [
    "sol_gel_aging_temperature_c",
    "sol_gel_aging_time_h",
    "calcination_temperature_c",
    "calcination_duration_h",
]

HYDROTHERMAL_CODES: list[str] = [
    "autoclave_fill_factor_pct",
    "hydrothermal_temperature_c",
    "hydrothermal_reaction_time_h",
    "biomass_source_mass_g",
]


METHOD_ALLOWED_PARAMETER_CODES: dict[str, set[str]] = {
    SynthesisMethod.SPRAY_PYROLYSIS.value: set(
        COMMON_PRECURSOR_EXTRACT_CODES + COMMON_SOLVENT_CODES + SPRAY_PYROLYSIS_CODES
    ),
    SynthesisMethod.SOL_GEL.value: set(
        COMMON_PRECURSOR_EXTRACT_CODES + COMMON_SOLVENT_CODES + SOL_GEL_CODES
    ),
    SynthesisMethod.HYDROTHERMAL.value: set(
        COMMON_PRECURSOR_EXTRACT_CODES + COMMON_SOLVENT_CODES + HYDROTHERMAL_CODES
    ),
}


def get_project_spec(project_code: str) -> dict[str, Any]:
    """Retrieve method configuration dictionary for a given project code (e.g. P1..P8)."""
    code_upper = project_code.upper().strip()
    return PROJECT_METHOD_MATRIX.get(code_upper, PROJECT_METHOD_MATRIX["P7"])


def get_allowed_parameter_codes(project_code: str) -> set[str]:
    """Return set of valid parameter codes for a project's synthesis method."""
    spec = get_project_spec(project_code)
    method = spec["method"]
    return METHOD_ALLOWED_PARAMETER_CODES.get(method, METHOD_ALLOWED_PARAMETER_CODES[SynthesisMethod.SPRAY_PYROLYSIS.value])


def validate_parameters_for_project(project_code: str, parameters: dict[str, Any]) -> tuple[bool, str | None]:
    """
    Validates submitted parameter dictionary against the project's synthesis method.
    Rejects parameters that belong to another synthesis method.
    """
    allowed_codes = get_allowed_parameter_codes(project_code)
    disallowed: list[str] = []

    for key in parameters.keys():
        if key.startswith("_"):
            continue
        if key not in allowed_codes:
            disallowed.append(key)

    if disallowed:
        spec = get_project_spec(project_code)
        method_name = METHOD_DISPLAY_NAMES.get(spec["method"], spec["method"])
        return (
            False,
            f"Project '{project_code}' uses synthesis method '{method_name}'. "
            f"The following parameter(s) are invalid for this method: {', '.join(disallowed)}",
        )

    return True, None
