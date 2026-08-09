"""
GreenSynth Analytics — Cross-Project Property Comparability Service

Enforces strict scientific comparability rules before allowing property comparison across projects:
  - COMPARABLE: Same material system, same synthesis method, same target property & unit.
  - COMPARABLE_WITH_WARNING: Same material system & target property, but different solvent or method.
  - NOT_COMPARABLE: Different material systems (e.g. CuO vs. Silica/Silicon). Requires explicit researcher override.
"""

from __future__ import annotations

from typing import Any


class PropertyComparabilityService:
    """
    Evaluates cross-project scientific comparability.
    """

    @staticmethod
    def evaluate_comparability(
        source_project: dict[str, Any],
        target_project: dict[str, Any],
        source_prop: str,
        target_prop: str,
    ) -> dict[str, Any]:
        """
        Evaluate comparability between properties of two projects.
        """
        source_material = source_project.get("material", "CuO")
        target_material = target_project.get("material", "CuO")

        source_method = source_project.get("synthesis_method", "Spray Pyrolysis")
        target_method = target_project.get("synthesis_method", "Spray Pyrolysis")

        source_solvent = source_project.get("solvent", "Ethanol")
        target_solvent = target_project.get("solvent", "Ethanol")

        is_same_material = (source_material.strip().upper() == target_material.strip().upper())
        is_same_method = (source_method.strip().upper() == target_method.strip().upper())
        is_same_solvent = (source_solvent.strip().upper() == target_solvent.strip().upper())
        is_same_prop = (source_prop.strip().lower() == target_prop.strip().lower())

        if not is_same_prop:
            return {
                "comparability_status": "NOT_COMPARABLE",
                "source_material": source_material,
                "target_material": target_material,
                "source_method": source_method,
                "target_method": target_method,
                "is_same_material_system": is_same_material,
                "is_same_synthesis_method": is_same_method,
                "is_same_solvent": is_same_solvent,
                "reason": f"Target properties '{source_prop}' and '{target_prop}' are different physical quantities.",
            }

        if not is_same_material:
            return {
                "comparability_status": "NOT_COMPARABLE",
                "source_material": source_material,
                "target_material": target_material,
                "source_method": source_method,
                "target_method": target_method,
                "is_same_material_system": is_same_material,
                "is_same_synthesis_method": is_same_method,
                "is_same_solvent": is_same_solvent,
                "reason": f"Material systems differ ('{source_material}' vs. '{target_material}'). Direct cross-material scientific comparison requires explicit researcher confirmation.",
            }

        if not is_same_method or not is_same_solvent:
            return {
                "comparability_status": "COMPARABLE_WITH_WARNING",
                "source_material": source_material,
                "target_material": target_material,
                "source_method": source_method,
                "target_method": target_method,
                "is_same_material_system": is_same_material,
                "is_same_synthesis_method": is_same_method,
                "is_same_solvent": is_same_solvent,
                "reason": f"Same material system ({source_material}), but synthesis parameters differ (Method: {source_method} vs {target_method}, Solvent: {source_solvent} vs {target_solvent}). Comparisons reflect process variations.",
            }

        return {
            "comparability_status": "COMPARABLE",
            "source_material": source_material,
            "target_material": target_material,
            "source_method": source_method,
            "target_method": target_method,
            "is_same_material_system": True,
            "is_same_synthesis_method": True,
            "is_same_solvent": True,
            "reason": "Directly scientifically comparable (identical material system, synthesis method, and solvent).",
        }
