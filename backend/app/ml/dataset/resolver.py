"""
GreenSynth Analytics — Parameter & Target Property Resolver

Provides canonical resolution and normalization for synthesis parameters and
characterization target properties across display labels, variant codes, and database schema identifiers.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

# Canonical parameter alias groups: canonical_code -> list of matching aliases/codes/names
PARAMETER_ALIASES: dict[str, list[str]] = {
    "substrate_temperature": [
        "substrate_temperature",
        "substrate_temperature_c",
        "substrate_temp",
        "temp",
        "Substrate Temperature",
    ],
    "spray_rate": [
        "spray_rate",
        "spray_rate_ml_min",
        "spray_flow_rate",
        "Spray Rate",
    ],
    "precursor_concentration": [
        "precursor_concentration",
        "copper_precursor_concentration",
        "Precursor Concentration",
    ],
    "precursor_volume": [
        "precursor_volume",
        "precursor_solution_volume",
        "Precursor Solution Volume",
    ],
    "extract_concentration": [
        "extract_concentration",
        "mulberry_extract_concentration",
        "Mulberry Extract Concentration",
    ],
    "extract_volume": [
        "extract_volume",
        "mulberry_extract_volume",
        "Mulberry Extract Volume",
    ],
    "solvent_volume": [
        "solvent_volume",
        "Solvent Volume",
    ],
    "copper_precursor": [
        "copper_precursor",
        "copper_precursor_salt",
        "precursor_salt",
        "Copper Precursor Salt",
    ],
}

# Canonical target property alias groups: canonical_property -> (list of aliases, default_unit)
TARGET_PROPERTY_ALIASES: dict[str, tuple[list[str], str]] = {
    "Electrical Conductivity": (
        [
            "Electrical Conductivity",
            "electrical_conductivity",
            "conductivity",
            "Conductivity",
            "electricalConductivity",
            "sigma",
            "conductivity_s_cm",
        ],
        "S/cm",
    ),
    "Electrical Resistivity": (
        [
            "Electrical Resistivity",
            "electrical_resistivity",
            "resistivity",
            "Resistivity",
            "rho",
            "resistivity_ohm_cm",
        ],
        "Ohm·cm",
    ),
    "Electrical Resistance": (
        [
            "Electrical Resistance",
            "electrical_resistance",
            "resistance",
            "Resistance",
            "R",
            "resistance_ohms",
        ],
        "Ohm",
    ),
    "Optical Band Gap": (
        ["Optical Band Gap", "optical_band_gap", "band_gap", "bandgap", "Band Gap", "Eg"],
        "eV",
    ),
    "Crystallite Size": (
        ["Crystallite Size", "crystallite_size", "domain_size", "Scherrer Size"],
        "nm",
    ),
    "Particle Size": (
        ["Particle Size", "particle_size", "grain_size"],
        "nm",
    ),
}

# Unit Aliases for compatibility matching
UNIT_ALIASES: dict[str, list[str]] = {
    "S/cm": ["s/cm", "siemens/cm", "siemens_per_cm", "s·cm⁻¹", "siemens per cm"],
    "Ohm": ["ohm", "ohms", "Ω"],
    "Ohm·cm": ["ohm·cm", "ohm*cm", "Ω·cm", "ohm_cm", "ohm cm"],
    "eV": ["ev", "electronvolt", "electron-volts"],
    "nm": ["nm", "nanometer", "nanometers"],
}


@dataclass
class ResolvedParameter:
    requested_name: str
    resolved_code: str
    value: float | str | None
    unit: str | None
    is_found: bool


@dataclass
class ResolvedTarget:
    requested_property: str
    resolved_property: str
    value: float | None
    unit: str
    is_found: bool


class ParameterResolver:
    """Resolves raw parameter keys from DB to canonical parameter codes & values."""

    @staticmethod
    def resolve_parameter(
        params_map: dict[str, Any],
        param_units_map: dict[str, str],
        feature_spec: dict[str, Any],
    ) -> ResolvedParameter:
        """
        Resolves a requested feature specification against candidate parameters map.
        params_map can contain stored parameter_code or parameter_name keys.
        """
        fname = feature_spec.get("feature_name", "")
        src_param = feature_spec.get("source_parameter", fname)
        target_unit = feature_spec.get("unit")

        # 1. Exact match on source_parameter or feature_name
        for candidate_key in (src_param, fname):
            if candidate_key in params_map and params_map[candidate_key] is not None:
                val = params_map[candidate_key]
                unit = param_units_map.get(candidate_key, target_unit)
                return ResolvedParameter(
                    requested_name=fname,
                    resolved_code=candidate_key,
                    value=val,
                    unit=unit,
                    is_found=True,
                )

        # 2. Check alias map
        possible_keys: list[str] = [src_param, fname]
        for canonical, aliases in PARAMETER_ALIASES.items():
            if src_param in aliases or fname in aliases or src_param == canonical or fname == canonical:
                possible_keys.extend(aliases)
                possible_keys.append(canonical)

        # Case-insensitive / normalized lookup
        norm_params = {str(k).lower().strip(): (k, v) for k, v in params_map.items()}

        for key in possible_keys:
            key_norm = str(key).lower().strip()
            if key_norm in norm_params:
                orig_key, val = norm_params[key_norm]
                if val is not None:
                    unit = param_units_map.get(orig_key, target_unit)
                    return ResolvedParameter(
                        requested_name=fname,
                        resolved_code=orig_key,
                        value=val,
                        unit=unit,
                        is_found=True,
                    )

        # Not found
        return ResolvedParameter(
            requested_name=fname,
            resolved_code=src_param,
            value=None,
            unit=target_unit,
            is_found=False,
        )


class TargetPropertyResolver:
    """Resolves target property queries against calculated properties map."""

    @staticmethod
    def is_unit_compatible(unit_a: str, unit_b: str) -> bool:
        if not unit_a or not unit_b:
            return True
        norm_a = unit_a.lower().strip()
        norm_b = unit_b.lower().strip()
        if norm_a == norm_b:
            return True
        for canonical_unit, aliases in UNIT_ALIASES.items():
            all_group = [canonical_unit.lower()] + [a.lower() for a in aliases]
            if norm_a in all_group and norm_b in all_group:
                return True
        return False

    @classmethod
    def resolve_target(
        cls,
        props_map: dict[str, float],
        prop_units_map: dict[str, str],
        requested_target: str,
        requested_unit: str = "",
    ) -> ResolvedTarget:
        """
        Resolves target property value and unit from sample calculated properties map.
        Guarantees strict separation between Resistance, Resistivity, and Conductivity.
        """
        logger.debug(
            "Target Property Resolver: resolving req_target='%s', req_unit='%s' against props_map=%s",
            requested_target,
            requested_unit,
            props_map,
        )

        req_norm = str(requested_target).lower().strip()

        # Identify target category for strict discrimination
        target_canonical: str | None = None
        for canonical, (aliases, _) in TARGET_PROPERTY_ALIASES.items():
            if req_norm == canonical.lower() or any(req_norm == a.lower() for a in aliases):
                target_canonical = canonical
                break

        # 1. Direct match
        if requested_target in props_map and props_map[requested_target] is not None:
            val = props_map[requested_target]
            unit = prop_units_map.get(requested_target, requested_unit)
            if cls.is_unit_compatible(unit, requested_unit):
                logger.info(
                    "Target Property Resolver: EXACT MATCH req='%s' -> found='%s', val=%s %s",
                    requested_target,
                    requested_target,
                    val,
                    unit,
                )
                return ResolvedTarget(
                    requested_property=requested_target,
                    resolved_property=requested_target,
                    value=val,
                    unit=unit,
                    is_found=True,
                )

        # 2. Alias matching within canonical group
        if target_canonical:
            aliases, default_unit = TARGET_PROPERTY_ALIASES[target_canonical]
            norm_props = {str(k).lower().strip(): (k, v) for k, v in props_map.items()}

            for alias in [target_canonical] + aliases:
                alias_norm = alias.lower().strip()
                if alias_norm in norm_props:
                    orig_key, val = norm_props[alias_norm]
                    if val is not None:
                        unit = prop_units_map.get(orig_key, requested_unit or default_unit)
                        if cls.is_unit_compatible(unit, requested_unit):
                            logger.info(
                                "Target Property Resolver: ALIAS MATCH req='%s' (group '%s') -> found='%s', val=%s %s",
                                requested_target,
                                target_canonical,
                                orig_key,
                                val,
                                unit,
                            )
                            return ResolvedTarget(
                                requested_property=requested_target,
                                resolved_property=orig_key,
                                value=val,
                                unit=unit,
                                is_found=True,
                            )

        logger.info(
            "Target Property Resolver: NOT FOUND req_target='%s', req_unit='%s' in props=%s",
            requested_target,
            requested_unit,
            list(props_map.keys()),
        )

        return ResolvedTarget(
            requested_property=requested_target,
            resolved_property=requested_target,
            value=None,
            unit=requested_unit,
            is_found=False,
        )
