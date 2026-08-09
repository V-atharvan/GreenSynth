"""
GreenSynth Analytics — Target Property Matcher

Ensures model prediction target property matches actual laboratory characterization target property.
Prevents comparing predicted conductivity against actual resistivity without explicit configuration.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TargetMatchResult:
    is_match: bool
    predicted_target: str
    actual_target: str
    warning: str | None = None


class TargetMatcher:
    """
    Verifies that prediction target property and laboratory characterization property match.
    """

    def match(self, predicted_target: str, actual_target: str) -> TargetMatchResult:
        p_norm = predicted_target.strip().lower().replace(" ", "_")
        a_norm = actual_target.strip().lower().replace(" ", "_")

        if p_norm == a_norm:
            return TargetMatchResult(
                is_match=True,
                predicted_target=predicted_target,
                actual_target=actual_target,
            )

        return TargetMatchResult(
            is_match=False,
            predicted_target=predicted_target,
            actual_target=actual_target,
            warning=f"Target Property Mismatch: Cannot validate predicted '{predicted_target}' against actual '{actual_target}'.",
        )
