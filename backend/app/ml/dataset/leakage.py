"""
GreenSynth Analytics — Data Leakage Detector

Inspects selected feature variables against target properties to prevent data leakage,
such as using derived target properties (e.g. resistivity when target is conductivity)
as input features.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LeakageCheckResult:
    target_property: str
    feature_names: list[str]
    has_leakage: bool
    leakage_warnings: list[str] = field(default_factory=list)
    flagged_features: list[str] = field(default_factory=list)


class LeakageDetector:
    """
    Checks feature definitions against target property to prevent target leakage.
    Maintain explicit scientific derivation mappings.
    """

    KNOWN_DERIVED_PAIRS: list[set[str]] = [
        {"conductivity", "resistivity"},
        {"electrical_conductivity", "electrical_resistivity"},
        {"band_gap", "bandgap", "absorption_edge"},
        {"crystallite_size", "fwhm"},
    ]

    def check_leakage(self, target_property: str, feature_names: list[str]) -> LeakageCheckResult:
        target_norm = target_property.strip().lower().replace(" ", "_")
        flagged: list[str] = []
        warnings: list[str] = []

        for fname in feature_names:
            fname_norm = fname.strip().lower().replace(" ", "_")

            # 1. Exact match leakage
            if fname_norm == target_norm:
                flagged.append(fname)
                warnings.append(
                    f"Direct Target Leakage: Feature '{fname}' is identical to target property '{target_property}'."
                )
                continue

            # 2. Known derived pair leakage
            for pair in self.KNOWN_DERIVED_PAIRS:
                if target_norm in pair and fname_norm in pair:
                    flagged.append(fname)
                    warnings.append(
                        f"Potential Derived Target Leakage: Feature '{fname}' is mathematically derived from/with target property '{target_property}'."
                    )
                    break

        has_leakage = len(flagged) > 0
        return LeakageCheckResult(
            target_property=target_property,
            feature_names=feature_names,
            has_leakage=has_leakage,
            leakage_warnings=warnings,
            flagged_features=flagged,
        )
