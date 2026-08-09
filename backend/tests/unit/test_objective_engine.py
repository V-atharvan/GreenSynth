"""
GreenSynth Analytics — Objective Engine Unit Tests
"""

import uuid
import pytest

from app.optimization.objectives.schemas import ObjectiveConstraint, ObjectiveCreateInput
from app.optimization.objectives.validation import ObjectiveValidationError, validate_objective_definition


def test_valid_maximize_objective():
    payload = ObjectiveCreateInput(
        project_id=uuid.uuid4(),
        name="High Conductivity CuO",
        target_property="Electrical Conductivity",
        direction="MAXIMIZE",
        unit="S/cm",
        weight=1.0,
    )
    # Should not raise
    validate_objective_definition(payload)


def test_valid_target_range_objective():
    payload = ObjectiveCreateInput(
        project_id=uuid.uuid4(),
        name="Optimum Band Gap",
        target_property="Band Gap",
        direction="TARGET_RANGE",
        min_value=1.4,
        max_value=1.6,
        unit="eV",
        weight=0.5,
    )
    validate_objective_definition(payload)


def test_invalid_target_range_bounds():
    payload = ObjectiveCreateInput(
        project_id=uuid.uuid4(),
        name="Invalid Range Objective",
        target_property="Band Gap",
        direction="TARGET_RANGE",
        min_value=2.0,
        max_value=1.5,  # Invalid: min >= max
        unit="eV",
        weight=1.0,
    )
    with pytest.raises(ObjectiveValidationError, match="must be strictly less than max_value"):
        validate_objective_definition(payload)


def test_missing_target_value():
    payload = ObjectiveCreateInput(
        project_id=uuid.uuid4(),
        name="Missing Target Value",
        target_property="Resistivity",
        direction="TARGET_VALUE",
        target_value=None,  # Missing
        unit="Ohm-cm",
    )
    with pytest.raises(ObjectiveValidationError, match="requires a valid target_value"):
        validate_objective_definition(payload)


def test_invalid_direction():
    payload = ObjectiveCreateInput(
        project_id=uuid.uuid4(),
        name="Bad Direction",
        target_property="Property",
        direction="OPTIMIZE_RANDOM",  # Invalid
    )
    with pytest.raises(ObjectiveValidationError, match="Invalid objective direction"):
        validate_objective_definition(payload)
