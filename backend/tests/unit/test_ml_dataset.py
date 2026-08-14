"""
GreenSynth Analytics — Unit Tests: ML Dataset Builder, Validator & Leakage Detector
"""

from __future__ import annotations

import pytest

from app.ml.dataset.builder import DatasetBuilder
from app.ml.dataset.validator import DatasetValidator
from app.ml.dataset.leakage import LeakageDetector


def test_dataset_builder_eligibility():
    feature_specs = [
        {"feature_name": "temperature", "source_parameter": "substrate_temperature", "unit": "°C"},
        {"feature_name": "spray_rate", "source_parameter": "spray_rate", "unit": "mL/min"},
    ]
    builder = DatasetBuilder(target_property="Conductivity", target_unit="S/cm", feature_specs=feature_specs)

    candidates = [
        {
            "experiment_id": "exp-1",
            "sample_id": "smp-1",
            "experiment_status": "COMPLETED",
            "parameters": {"substrate_temperature": 350.0, "spray_rate": 3.0},
            "properties": {"Conductivity": 5.2},
        },
        {
            "experiment_id": "exp-2",
            "sample_id": "smp-2",
            "experiment_status": "PLANNED",  # Ineligible status
            "parameters": {"substrate_temperature": 300.0, "spray_rate": 2.0},
            "properties": {"Conductivity": 4.1},
        },
        {
            "experiment_id": "exp-3",
            "sample_id": "smp-3",
            "experiment_status": "COMPLETED",
            "parameters": {"substrate_temperature": 320.0},  # Missing feature spray_rate
            "properties": {"Conductivity": 4.8},
        },
        {
            "experiment_id": "exp-4",
            "sample_id": "smp-4",
            "experiment_status": "COMPLETED",
            "parameters": {"substrate_temperature": 380.0, "spray_rate": 4.0},
            "properties": {},  # Missing target
        },
    ]

    result = builder.build_records(candidates, dataset_name="Test CuO Dataset")
    assert result.eligible_count == 1
    assert result.excluded_count == 3
    assert "INCOMPLETE_EXPERIMENT" in result.exclusion_summary
    assert "MISSING_FEATURE" in result.exclusion_summary
    assert "MISSING_TARGET" in result.exclusion_summary


def test_dataset_validator():
    feature_specs = [{"feature_name": "temp", "source_parameter": "temp", "unit": "°C"}]
    builder = DatasetBuilder(target_property="Conductivity", target_unit="S/cm", feature_specs=feature_specs)

    candidates = [
        {"experiment_id": f"exp-{i}", "sample_id": f"smp-{i}", "experiment_status": "COMPLETED", "parameters": {"temp": 300.0 + i * 10}, "properties": {"Conductivity": 2.0 + i * 0.5}}
        for i in range(10)
    ]
    build_res = builder.build_records(candidates)

    validator = DatasetValidator()
    indicators = validator.validate(build_res)

    assert indicators.eligible_records == 10
    assert indicators.is_valid_for_training is True
    assert indicators.target_mean is not None
    assert indicators.target_std > 0.0


def test_dataset_builder_alias_resolution():
    """Verify parameter code aliases and target property aliases resolve correctly."""
    feature_specs = [
        {"feature_name": "precursor_concentration", "source_parameter": "precursor_concentration", "unit": "mol/L"},
        {"feature_name": "precursor_volume", "source_parameter": "precursor_solution_volume", "unit": "mL"},
        {"feature_name": "extract_concentration", "source_parameter": "mulberry_extract_concentration", "unit": "g/L"},
        {"feature_name": "extract_volume", "source_parameter": "mulberry_extract_volume", "unit": "mL"},
        {"feature_name": "solvent_volume", "source_parameter": "solvent_volume", "unit": "mL"},
        {"feature_name": "substrate_temperature", "source_parameter": "substrate_temperature", "unit": "°C"},
        {"feature_name": "spray_rate", "source_parameter": "spray_rate", "unit": "mL/min"},
    ]
    builder = DatasetBuilder(
        target_property="Electrical Conductivity",
        target_unit="S/cm",
        feature_specs=feature_specs,
    )

    candidates = [
        {
            "experiment_id": "EXP-P7-TEST-001",
            "sample_id": "SAMP-P7-TEST-001-A",
            "experiment_status": "COMPLETED",
            "parameters": {
                "copper_precursor": "Copper acetate monohydrate",
                "precursor_concentration": 0.1,
                "precursor_volume": 100.0,
                "extract_concentration": 10.0,
                "extract_volume": 20.0,
                "solvent_volume": 80.0,
                "substrate_temperature_c": 350.0,  # Alias for substrate_temperature
                "spray_rate_ml_min": 5.0,  # Alias for spray_rate
            },
            "properties": {
                "Electrical Conductivity": 5.0,
                "Electrical Resistance": 2000.0,
                "Electrical Resistivity": 0.2,
            },
        }
    ]

    result = builder.build_records(candidates, dataset_name="CuO Test Dataset")
    assert result.eligible_count == 1
    assert result.excluded_count == 0

    record = result.records[0]
    assert record.is_eligible is True
    assert record.target_value == 5.0
    assert record.feature_values["substrate_temperature"] == 350.0
    assert record.feature_values["spray_rate"] == 5.0
    assert record.feature_values["precursor_concentration"] == 0.1
    assert record.feature_values["precursor_volume"] == 100.0
    assert record.feature_values["extract_concentration"] == 10.0
    assert record.feature_values["extract_volume"] == 20.0
    assert record.feature_values["solvent_volume"] == 80.0


def test_dataset_builder_feature_values_populated_on_exclusion():
    """Verify feature values are preserved and populated in record item even when excluded."""
    feature_specs = [
        {"feature_name": "temp", "source_parameter": "substrate_temperature_c", "unit": "°C"},
        {"feature_name": "rate", "source_parameter": "spray_rate_ml_min", "unit": "mL/min"},
    ]
    builder = DatasetBuilder(
        target_property="Electrical Conductivity",
        target_unit="S/cm",
        feature_specs=feature_specs,
    )

    candidates = [
        {
            "experiment_id": "EXP-PLANNED-1",
            "sample_id": "SAMP-1",
            "experiment_status": "PLANNED",
            "parameters": {"substrate_temperature_c": 350.0, "spray_rate_ml_min": 5.0},
            "properties": {"Electrical Conductivity": 5.0},
        }
    ]

    result = builder.build_records(candidates)
    assert result.eligible_count == 0
    assert result.excluded_count == 1

    rec = result.records[0]
    assert rec.is_eligible is False
    assert "Incomplete experiment" in (rec.exclusion_reason or "")
    # Crucial check: feature_values must NOT be empty!
    assert rec.feature_values["temp"] == 350.0
    assert rec.feature_values["rate"] == 5.0


def test_leakage_detector():
    detector = LeakageDetector()

    # Direct target leakage
    res1 = detector.check_leakage(target_property="Conductivity", feature_names=["substrate_temperature", "Conductivity"])
    assert res1.has_leakage is True
    assert "Conductivity" in res1.flagged_features

    # Derived target leakage (resistivity vs conductivity)
    res2 = detector.check_leakage(target_property="Conductivity", feature_names=["substrate_temperature", "resistivity"])
    assert res2.has_leakage is True
    assert "resistivity" in res2.flagged_features

    # Safe features
    res3 = detector.check_leakage(target_property="Conductivity", feature_names=["substrate_temperature", "spray_rate"])
    assert res3.has_leakage is False
    assert len(res3.flagged_features) == 0
