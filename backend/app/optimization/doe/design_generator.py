"""
GreenSynth Analytics — Pluggable DOE Generator Factory (Phase 14)

Provides:
  - DOEGeneratorFactory: Unified interface for Full Factorial, Fractional Factorial, Central Composite, Box-Behnken, and Randomized design generators.
"""

from __future__ import annotations

import random
from typing import Any

from app.optimization.doe.factorial import generate_fractional_factorial_matrix, generate_full_factorial_matrix
from app.optimization.doe.random_design import generate_random_candidates
from app.optimization.doe.response_surface import generate_box_behnken_matrix, generate_ccd_matrix
from app.optimization.doe.schemas import FactorDefinition, DOEWorkloadPreview


class DOEGeneratorFactory:
    """Pluggable factory for Design of Experiments matrix generation."""

    @staticmethod
    def preview_workload(
        design_method: str,
        factors: list[FactorDefinition],
        replicates: int = 1,
        center_points: int = 0,
        workload_threshold: int = 32,
    ) -> DOEWorkloadPreview:
        """Calculates expected run count preview and displays workload warning if runs > threshold."""
        method = design_method.upper()
        k = len(factors)
        base_runs = 0
        resolution = None
        confounding_warning = None

        if method == "FULL_FACTORIAL":
            # For 2-level factorial base: 2^k
            level_counts = [
                int(f.levels) if isinstance(f.levels, (int, float)) and f.levels >= 2 else (len(f.levels) if isinstance(f.levels, list) and len(f.levels) >= 2 else 2)
                for f in factors
            ]
            base_runs = 1
            for count in level_counts:
                base_runs *= count
            resolution = "Full Factorial (Res V+)"

        elif method == "FRACTIONAL_FACTORIAL":
            full_runs = 2 ** k
            base_runs = max(full_runs // 2, 4)
            resolution = "Res IV" if k >= 4 else "Res III"
            confounding_warning = (
                f"Fractional Factorial design ({resolution}) reduces run count from {full_runs} to {base_runs}. "
                "Main effects may be confounded with multi-factor interactions."
            )

        elif method == "CENTRAL_COMPOSITE":
            factorial_pts = 2 ** k
            axial_pts = 2 * k
            base_runs = factorial_pts + axial_pts
            resolution = "Response Surface (CCD)"

        elif method == "BOX_BEHNKEN":
            if k >= 3:
                base_runs = 2 * k * (k - 1)
            else:
                base_runs = 2 ** k + 2 * k
            resolution = "Response Surface (Box-Behnken)"

        elif method == "RANDOMIZED_CANDIDATE":
            base_runs = 10
            resolution = "Randomized Candidate"

        else:
            base_runs = 2 ** max(k, 1)
            resolution = "Custom Design"

        total_runs = (base_runs * max(replicates, 1)) + max(center_points, 0)
        requires_warning = total_runs > workload_threshold
        warning_msg = (
            f"This DOE requires {total_runs} experimental runs. Review the experimental workload before approval."
            if requires_warning
            else None
        )

        return DOEWorkloadPreview(
            design_method=method,
            factors_count=k,
            base_runs=base_runs,
            replicates=replicates,
            center_points=center_points,
            total_runs=total_runs,
            design_resolution=resolution,
            confounding_warning=confounding_warning,
            requires_workload_warning=requires_warning,
            warning_message=warning_msg,
        )

    @staticmethod
    def generate_design_matrix(
        design_method: str,
        factors: list[FactorDefinition],
        requested_runs: int = 10,
        replicates: int = 1,
        center_points: int = 0,
        random_seed: int | None = 42,
        randomize_run_order: bool = True,
    ) -> tuple[list[dict[str, Any]], str | None, str | None]:
        """Generates base matrix, applies replicates & center points, and applies seed-reproducible run order randomization."""
        method = design_method.upper()
        resolution = None
        warning = None

        if method == "FULL_FACTORIAL":
            base = generate_full_factorial_matrix(factors)
            resolution = "Full Factorial (Res V+)"
        elif method == "FRACTIONAL_FACTORIAL":
            base, resolution, warning = generate_fractional_factorial_matrix(factors)
        elif method == "CENTRAL_COMPOSITE":
            base = generate_ccd_matrix(factors)
            resolution = "Response Surface (CCD)"
        elif method == "BOX_BEHNKEN":
            base = generate_box_behnken_matrix(factors)
            resolution = "Response Surface (Box-Behnken)"
        elif method == "RANDOMIZED_CANDIDATE":
            base = generate_random_candidates(factors, requested_runs, random_seed or 42)
            resolution = "Randomized Candidate"
        else:
            base = generate_full_factorial_matrix(factors)
            resolution = "Full Factorial"

        # Apply replicates
        replicated_matrix: list[dict[str, Any]] = []
        for rep in range(1, max(replicates, 1) + 1):
            for row in base:
                row_copy = dict(row)
                row_copy["_replicate"] = rep
                row_copy["_is_center"] = False
                replicated_matrix.append(row_copy)

        # Apply center points
        if center_points > 0:
            center_row: dict[str, Any] = {}
            for f in factors:
                if f.factor_type.upper() == "CONTINUOUS":
                    low = f.lower_bound if f.lower_bound is not None else 0.0
                    high = f.upper_bound if f.upper_bound is not None else 1.0
                    center_val = f.center_value if f.center_value is not None else (low + high) / 2.0
                    center_row[f.parameter_code] = round(float(center_val), 4)
                elif isinstance(f.levels, list) and f.levels:
                    center_row[f.parameter_code] = f.levels[len(f.levels) // 2]
                else:
                    center_row[f.parameter_code] = 0.0

            for cp in range(1, center_points + 1):
                cp_copy = dict(center_row)
                cp_copy["_replicate"] = 1
                cp_copy["_is_center"] = True
                replicated_matrix.append(cp_copy)

        # Randomize run order if requested
        final_matrix = list(replicated_matrix)
        if randomize_run_order and random_seed is not None:
            rng = random.Random(random_seed)
            rng.shuffle(final_matrix)

        return final_matrix, resolution, warning
