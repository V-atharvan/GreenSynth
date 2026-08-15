"""
Unit tests for Method-Aware Experiment Parameter Architecture (app.core.method_config)
"""

import pytest
from app.core.method_config import (
    SynthesisMethod,
    get_allowed_parameter_codes,
    get_project_spec,
    validate_parameters_for_project,
)


def test_project_method_mapping():
    p7 = get_project_spec("P7")
    assert p7["method"] == SynthesisMethod.SPRAY_PYROLYSIS.value
    assert p7["solvent"] == "ETHANOL"
    assert p7["material_system"] == "CuO"

    p1 = get_project_spec("P1")
    assert p1["method"] == SynthesisMethod.SOL_GEL.value
    assert p1["solvent"] == "ETHANOL"
    assert p1["material_system"] == "CuO"

    p3 = get_project_spec("P3")
    assert p3["method"] == SynthesisMethod.HYDROTHERMAL.value
    assert p3["solvent"] == "ETHANOL"
    assert p3["material_system"] == "CuO"

    p5 = get_project_spec("P5")
    assert p5["method"] == SynthesisMethod.HYDROTHERMAL.value
    assert p5["solvent"] == "ETHANOL"
    assert p5["material_system"] == "SILICA_SILICON"
    assert p5["biomass"] == "Rice husk"

    p8 = get_project_spec("P8")
    assert p8["method"] == SynthesisMethod.SPRAY_PYROLYSIS.value
    assert p8["solvent"] == "ACETONE"


def test_p7_contains_spray_parameters():
    codes = get_allowed_parameter_codes("P7")
    assert "spray_rate_ml_min" in codes
    assert "substrate_temperature_c" in codes
    assert "copper_precursor_salt" in codes
    assert "solvent_volume" in codes


def test_p1_does_not_contain_spray_parameters():
    codes = get_allowed_parameter_codes("P1")
    assert "spray_rate_ml_min" not in codes
    assert "spray_duration_min" not in codes
    assert "sol_gel_aging_temperature_c" in codes
    assert "solvent_volume" in codes


def test_p3_does_not_contain_spray_parameters():
    codes = get_allowed_parameter_codes("P3")
    assert "spray_rate_ml_min" not in codes
    assert "hydrothermal_temperature_c" in codes
    assert "solvent_volume" in codes


def test_method_specific_parameter_validation():
    # Valid P7 payload
    valid, msg = validate_parameters_for_project(
        "P7",
        {
            "copper_precursor_salt": "Copper acetate",
            "precursor_concentration": 0.1,
            "solvent_volume": 80,
            "spray_rate_ml_min": 5,
        },
    )
    assert valid is True
    assert msg is None

    # Invalid P1 payload submitting spray_rate_ml_min
    valid_p1, msg_p1 = validate_parameters_for_project(
        "P1",
        {
            "copper_precursor_salt": "Copper acetate",
            "precursor_concentration": 0.1,
            "solvent_volume": 80,
            "spray_rate_ml_min": 5,
        },
    )
    assert valid_p1 is False
    assert "Sol-Gel" in msg_p1
    assert "spray_rate_ml_min" in msg_p1
