"""
GreenSynth Analytics — Recommendation Explanation Service

Generates human-readable scientific explanations and summaries for candidate rankings.
"""

from __future__ import annotations


class ExplanationService:
    def generate_explanation(
        self,
        rank: int,
        predicted_val: float,
        target_property: str,
        unit: str,
        evidence_level: str,
        domain_status: str,
        strategy: str,
        constraint_status: str,
        is_near_existing: bool,
    ) -> str:
        parts: list[str] = [
            f"Ranked #{rank} for optimizing {target_property}.",
            f"Predicted {target_property} is {predicted_val:.2f} {unit}.",
        ]

        if domain_status == "IN_DOMAIN":
            parts.append("Synthesis condition lies within the model's observed training domain.")
        elif domain_status == "NEAR_BOUNDARY":
            parts.append("Synthesis condition lies near the model's training domain boundary.")
        else:
            parts.append("Synthesis condition extends outside the model's observed training domain.")

        parts.append(f"Supported by {evidence_level} experimental evidence level.")

        if constraint_status == "SATISFIED":
            parts.append("All synthesis parameter constraints are satisfied.")
        elif constraint_status == "SOFT_VIOLATION":
            parts.append("Satisfies hard constraints with a minor soft constraint adjustment.")

        if is_near_existing:
            parts.append("Note: Condition is close to an existing historical experiment.")

        return " ".join(parts)
