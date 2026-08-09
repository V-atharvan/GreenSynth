"""
GreenSynth Analytics — Recommendation Candidate Diversity Selector

Filters top candidates to ensure parameter diversity across the recommended candidate set.
"""

from __future__ import annotations

import numpy as np


class DiversitySelector:
    """
    Selects a diverse subset of top-ranked candidates to avoid recommending near-identical conditions.
    """

    def select_diverse_subset(
        self,
        ranked_candidates: list[dict],
        parameter_names: list[str],
        top_n: int = 5,
        min_diversity_threshold: float = 0.10,
    ) -> list[dict]:
        if len(ranked_candidates) <= top_n:
            return ranked_candidates

        # Estimate parameter ranges for normalization
        p_mins = {}
        p_maxs = {}
        for p in parameter_names:
            vals = [c["parameter_set"].get(p, 0.0) for c in ranked_candidates]
            p_mins[p] = min(vals) if vals else 0.0
            p_maxs[p] = max(vals) if vals else 1.0

        def normalize_point(cand_dict: dict) -> np.ndarray:
            vec = []
            for p in parameter_names:
                v = cand_dict["parameter_set"].get(p, 0.0)
                mn, mx = p_mins[p], p_maxs[p]
                span = max(mx - mn, 1e-5)
                vec.append((v - mn) / span)
            return np.array(vec, dtype=float)

        selected: list[dict] = [ranked_candidates[0]]

        for cand in ranked_candidates[1:]:
            if len(selected) >= top_n:
                break

            c_norm = normalize_point(cand)

            # Check distance to already selected candidates in normalized space
            is_diverse = True
            for sel in selected:
                s_norm = normalize_point(sel)
                d = float(np.linalg.norm(c_norm - s_norm))
                if d < min_diversity_threshold:
                    is_diverse = False
                    break

            if is_diverse:
                selected.append(cand)

        # Fill up to top_n if not enough diverse candidates
        if len(selected) < top_n:
            for cand in ranked_candidates:
                if len(selected) >= top_n:
                    break
                if cand not in selected:
                    selected.append(cand)

        return selected
