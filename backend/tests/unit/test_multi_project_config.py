"""
GreenSynth Analytics — Phase 19 Multi-Project Platform Unit Tests
"""

import pytest
from app.scientific.configuration.property_comparability import PropertyComparabilityService


def test_project_matrix_specs_completeness():
    from app.database.seed import ALL_PROJECT_SPECS
    assert len(ALL_PROJECT_SPECS) == 8

    codes = [p["code"] for p in ALL_PROJECT_SPECS]
    assert set(codes) == {"P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"}


def test_shared_synthesis_methods():
    from app.database.seed import ALL_PROJECT_SPECS

    sol_gel_projects = [p["code"] for p in ALL_PROJECT_SPECS if p["method"] == "Sol-gel"]
    hydrothermal_projects = [p["code"] for p in ALL_PROJECT_SPECS if p["method"] == "Hydrothermal"]
    spray_projects = [p["code"] for p in ALL_PROJECT_SPECS if p["method"] == "Spray Pyrolysis"]

    assert set(sol_gel_projects) == {"P1", "P2"}
    assert set(hydrothermal_projects) == {"P3", "P4", "P5", "P6"}
    assert set(spray_projects) == {"P7", "P8"}


def test_rice_husk_biomass_distinction_for_p5_p6():
    from app.database.seed import ALL_PROJECT_SPECS

    p5 = next(p for p in ALL_PROJECT_SPECS if p["code"] == "P5")
    p6 = next(p for p in ALL_PROJECT_SPECS if p["code"] == "P6")

    # Biomass is Rice husk, Extract is Mulberry
    assert p5["biomass"] == "Rice husk"
    assert p5["extract"] == "Mulberry"

    assert p6["biomass"] == "Rice husk"
    assert p6["extract"] == "Mulberry"


def test_property_comparability_identical():
    source = {"material": "CuO", "synthesis_method": "Spray Pyrolysis", "solvent": "Ethanol"}
    target = {"material": "CuO", "synthesis_method": "Spray Pyrolysis", "solvent": "Ethanol"}

    res = PropertyComparabilityService.evaluate_comparability(
        source, target, "electrical_conductivity", "electrical_conductivity"
    )
    assert res["comparability_status"] == "COMPARABLE"


def test_property_comparability_different_solvent():
    source = {"material": "CuO", "synthesis_method": "Spray Pyrolysis", "solvent": "Ethanol"}
    target = {"material": "CuO", "synthesis_method": "Spray Pyrolysis", "solvent": "Acetone"}

    res = PropertyComparabilityService.evaluate_comparability(
        source, target, "electrical_conductivity", "electrical_conductivity"
    )
    assert res["comparability_status"] == "COMPARABLE_WITH_WARNING"
    assert res["is_same_solvent"] is False


def test_property_comparability_different_material_system():
    source = {"material": "CuO", "synthesis_method": "Hydrothermal", "solvent": "Ethanol"}
    target = {"material": "Silica / Silicon", "synthesis_method": "Hydrothermal", "solvent": "Ethanol"}

    res = PropertyComparabilityService.evaluate_comparability(
        source, target, "electrical_conductivity", "electrical_conductivity"
    )
    assert res["comparability_status"] == "NOT_COMPARABLE"
    assert res["is_same_material_system"] is False
