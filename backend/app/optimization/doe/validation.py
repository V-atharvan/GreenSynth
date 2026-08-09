"""
GreenSynth Analytics — DOE Validation Engine
"""

from __future__ import annotations

from app.optimization.doe.schemas import DOECreateInput

ALLOWED_DESIGN_METHODS = {
    "FULL_FACTORIAL",
    "FRACTIONAL_FACTORIAL",
    "CENTRAL_COMPOSITE",
    "BOX_BEHNKEN",
    "RANDOMIZED_CANDIDATE",
}


class DOEValidationError(ValueError):
    """Raised when DOE parameters or factor ranges are invalid."""


def validate_doe_input(payload: DOECreateInput) -> None:
    """Validate factor definitions and design method parameters."""
    method_upper = payload.design_method.upper()
    if method_upper not in ALLOWED_DESIGN_METHODS:
        raise DOEValidationError(
            f"Invalid design method '{payload.design_method}'. Allowed methods: {', '.join(sorted(ALLOWED_DESIGN_METHODS))}."
        )

    if not payload.factors:
        raise DOEValidationError("DOE configuration must include at least one factor definition.")

    for f in payload.factors:
        ftype = f.factor_type.upper()
        if ftype == "CONTINUOUS":
            if f.lower_bound is None or f.upper_bound is None:
                raise DOEValidationError(f"Continuous factor '{f.name}' ({f.parameter_code}) requires lower_bound and upper_bound.")
            if f.lower_bound >= f.upper_bound:
                raise DOEValidationError(
                    f"Invalid factor range for '{f.name}': lower_bound ({f.lower_bound}) must be strictly less than upper_bound ({f.upper_bound})."
                )
