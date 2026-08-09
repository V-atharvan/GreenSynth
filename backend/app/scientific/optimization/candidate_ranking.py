"""
GreenSynth Analytics — Candidate Ranking & Categorization Service

Ranks candidate experimental conditions according to:
  1. Feasibility (excludes hard-infeasible candidates)
  2. Domain Status (excludes OUT_OF_DOMAIN candidates by default unless explicitly allowed)
  3. Total Objective Score
  4. Categorizes candidates into EXPLOITATION (performance-focused) vs EXPLORATION (high distance from historical data)
"""

from __future__ import annotations

from typing import Any


class CandidateRankingService:
    """
    Ranks candidates and separates exploitation vs exploration candidates.
    """

    @staticmethod
    def rank_and_categorize(
        candidates: list[dict[str, Any]],
        allow_out_of_domain: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Filter, rank, and assign rank numbers to candidate list.
        """
        valid_candidates: list[dict[str, Any]] = []

        for cand in candidates:
            feasibility = cand.get("feasibility_status", "FEASIBLE")
            domain_status = cand.get("domain_status", "IN_DOMAIN")

            # Exclude hard infeasible
            if feasibility == "INFEASIBLE":
                cand["rank"] = 999
                cand["status"] = "REJECTED"
                continue

            # Exclude out-of-domain unless allowed
            if domain_status == "OUT_OF_DOMAIN" and not allow_out_of_domain:
                cand["rank"] = 999
                cand["status"] = "REJECTED"
                continue

            # Categorize candidate type
            novelty = cand.get("novelty_category", "LOW_DISTANCE")
            if novelty == "HIGH_DISTANCE":
                cand["candidate_type"] = "EXPLORATION"
            else:
                cand["candidate_type"] = "EXPLOITATION"

            valid_candidates.append(cand)

        # Sort valid candidates descending by objective score, breaking ties by lower uncertainty
        valid_candidates.sort(
            key=lambda c: (
                c.get("objective_score", 0.0),
                -abs(c.get("uncertainties", {}).get("width", 0.0)),
            ),
            reverse=True,
        )

        # Assign 1-indexed rank
        for rank_idx, cand in enumerate(valid_candidates, start=1):
            cand["rank"] = rank_idx
            cand["status"] = "GENERATED"

        return valid_candidates
