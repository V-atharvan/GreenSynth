"""
GreenSynth Analytics — Objective Validation Engine
"""

from __future__ import annotations

from app.optimization.objectives.schemas import ObjectiveCreateInput

ALLOWED_DIRECTIONS = {"MAXIMIZE", "MINIMIZE", "TARGET_VALUE", "TARGET_RANGE"}


class ObjectiveValidationError(ValueError):
    """Raised when an objective definition fails scientific validation."""


def validate_objective_definition(payload: ObjectiveCreateInput) -> None:
    """Validate objective direction, ranges, and target values before saving or activating."""
    dir_upper = payload.direction.upper()
    if dir_upper not in ALLOWED_DIRECTIONS:
        raise ObjectiveValidationError(
            f"Invalid objective direction '{payload.direction}'. Allowed directions: {', '.join(sorted(ALLOWED_DIRECTIONS))}."
        )

    if dir_upper == "TARGET_VALUE" and payload.target_value is None:
        raise ObjectiveValidationError("Objective direction 'TARGET_VALUE' requires a valid target_value.")

    if dir_upper == "TARGET_RANGE":
        if payload.min_value is None or payload.max_value is None:
            raise ObjectiveValidationError("Objective direction 'TARGET_RANGE' requires both min_value and max_value.")
        if payload.min_value >= payload.max_value:
            raise ObjectiveValidationError(
                f"Invalid target range: min_value ({payload.min_value}) must be strictly less than max_value ({payload.max_value})."
            )

    if payload.weight <= 0:
        raise ObjectiveValidationError(f"Objective weight must be strictly positive (got {payload.weight}).")
