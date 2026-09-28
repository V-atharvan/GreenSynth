"""
GreenSynth Analytics — Project P7 Downstream Workflow Integration Test
Tests DOEService to generate a Central Composite Design (CCD) matrix for P7
based on our synthetic research dataset and trained ML models.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
import uuid
from pathlib import Path
from typing import Any

sys.path.insert(0, "backend")

from sqlalchemy import select

from app.database.session import AsyncSessionLocal
from app.models.doe import ProposedExperiment
from app.models.project import Project
from app.optimization.doe.schemas import (
    DOECreateInput,
    FactorDefinition,
    ResponseDefinition,
)
from app.optimization.doe.service import DOEService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("test_doe")


async def run_doe_test() -> dict[str, Any]:
    logger.info("Initializing DOE Study for Project P7...")
    async with AsyncSessionLocal() as session:
        proj_res = await session.execute(select(Project).where(Project.project_code == "P7"))
        project = proj_res.scalars().first()
        if not project:
            raise RuntimeError("Project P7 not found!")

        doe_input = DOECreateInput(
            project_id=project.id,
            name="P7 Central Composite Design — Conductivity Optimization",
            description="4-factor response surface study to maximize electrical conductivity of spray pyrolyzed CuO thin films.",
            research_question="What are the optimal substrate temperature and extract volume to maximize CuO film conductivity?",
            design_method="CENTRAL_COMPOSITE",
            factors=[
                FactorDefinition(
                    parameter_code="substrate_temperature_c",
                    name="Substrate Temperature",
                    factor_type="CONTINUOUS",
                    lower_bound=300.0,
                    upper_bound=420.0,
                    center_value=360.0,
                    unit="°C",
                    levels=3,
                ),
                FactorDefinition(
                    parameter_code="precursor_concentration",
                    name="Precursor Concentration",
                    factor_type="CONTINUOUS",
                    lower_bound=0.10,
                    upper_bound=0.35,
                    center_value=0.22,
                    unit="mol/L",
                    levels=3,
                ),
                FactorDefinition(
                    parameter_code="mulberry_extract_concentration",
                    name="Mulberry Extract Concentration",
                    factor_type="CONTINUOUS",
                    lower_bound=5.0,
                    upper_bound=30.0,
                    center_value=17.5,
                    unit="g/L",
                    levels=3,
                ),
                FactorDefinition(
                    parameter_code="mulberry_extract_volume",
                    name="Mulberry Extract Volume",
                    factor_type="CONTINUOUS",
                    lower_bound=10.0,
                    upper_bound=40.0,
                    center_value=25.0,
                    unit="mL",
                    levels=3,
                ),
            ],
            responses=[
                ResponseDefinition(
                    property_name="Electrical Conductivity",
                    unit="S/cm",
                    direction="MAXIMIZE",
                    preferred_value=1.0,
                    weight=1.0,
                )
            ],
            requested_runs=30,
            replicates=1,
            center_points=4,
            random_seed=20260928,
            randomize_run_order=True,
        )

        doe_service = DOEService(session)
        created_doe, quality_report = await doe_service.create_doe_and_generate(
            payload=doe_input, created_by="GreenSynth Synthetic Research Team"
        )
        await session.commit()

        # Eagerly query proposed experiments
        pe_res = await session.execute(
            select(ProposedExperiment)
            .where(ProposedExperiment.doe_id == created_doe.id)
            .order_by(ProposedExperiment.run_order)
        )
        proposed_runs = pe_res.scalars().all()

        logger.info(
            f"DOE Study created: {created_doe.name} (ID: {created_doe.id}) | "
            f"Method: {created_doe.design_method} | Proposed Runs: {len(proposed_runs)}"
        )

        # Output sample of proposed experiments
        sample_runs = []
        for pe in proposed_runs[:5]:
            sample_runs.append({
                "run_order": pe.run_order,
                "factor_values": pe.factor_values,
                "status": pe.status,
            })
            logger.info(f"Proposed Run #{pe.run_order}: {pe.factor_values}")

        result = {
            "doe_id": str(created_doe.id),
            "name": created_doe.name,
            "method": created_doe.design_method,
            "total_runs": len(proposed_runs),
            "sample_runs": sample_runs,
        }

        out_path = Path("synthetic_data/p7/doe_test_results.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        logger.info(f"Saved DOE test output -> {out_path}")
        return result


if __name__ == "__main__":
    asyncio.run(run_doe_test())
