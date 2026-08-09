"""
GreenSynth Analytics — Design of Experiments (DOE) Service Layer (Phase 14 Extended)

Orchestrates:
  - DOE Study creation, factor & response configuration
  - Workload preview calculation & workload warning checks
  - Pluggable design matrix generation (Full Factorial, Fractional, CCD, Box-Behnken, Random)
  - Constraint validation & unit compatibility enforcement
  - Replicate generation & seed-reproducible run order randomization
  - Immutable versioning workflow (V1 -> V2)
  - Conversion of approved proposed runs into PLANNED laboratory experiments
  - Measured response linking & PROPOSED vs ACTUAL parameter deviation calculation
  - Statistical effect analysis ($E_A$, $E_{AB}$) & Response Surface polynomial regression fitting
  - Markdown DOE Study Report generation & CSV export
"""

from __future__ import annotations

import csv
import io
import logging
import random
import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.doe import DOE, DOEAnalysis, Objective, ProposedExperiment
from app.models.experiment import Experiment
from app.models.project import Project
from app.optimization.doe.constraints import evaluate_candidate_constraints
from app.optimization.doe.design_generator import DOEGeneratorFactory
from app.optimization.doe.design_validator import DOEValidator
from app.optimization.doe.doe_analysis import DOEAnalysisEngine
from app.optimization.doe.experiment_linker import DOEExperimentLinker
from app.optimization.doe.schemas import (
    DOEAnalysisResponse,
    DOECreateInput,
    DOEQualityReport,
    DOEResponse,
    DOEWorkloadPreview,
    FactorCoverageItem,
    FactorDefinition,
    ResponseDefinition,
)
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class DOEService:
    """Service layer for Design of Experiments (DOE) studies, design matrix generation, and closed-loop analysis."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.audit = AuditService(db)

    async def preview_workload(self, payload: DOECreateInput) -> DOEWorkloadPreview:
        """Calculates expected run count preview and displays workload warning if runs > threshold."""
        DOEValidator.validate_factors_and_units(payload.factors)
        return DOEGeneratorFactory.preview_workload(
            design_method=payload.design_method,
            factors=payload.factors,
            replicates=payload.replicates,
            center_points=payload.center_points,
        )

    async def create_doe_and_generate(
        self, payload: DOECreateInput, created_by: str | None = None
    ) -> tuple[DOE, DOEQualityReport]:
        """Validate input, generate design matrix, apply constraints, replicates, seed randomization, and save proposed runs."""
        DOEValidator.validate_factors_and_units(payload.factors)

        # Check project exists
        from app.services.project_service import ProjectNotFoundError, ProjectService
        try:
            await ProjectService(self.db).get_by_id(payload.project_id)
        except ProjectNotFoundError as exc:
            raise ValueError(str(exc)) from exc

        # 1. Generate base design matrix using Factory
        matrix_rows, resolution, confounding_warning = DOEGeneratorFactory.generate_design_matrix(
            design_method=payload.design_method,
            factors=payload.factors,
            requested_runs=payload.requested_runs,
            replicates=payload.replicates,
            center_points=payload.center_points,
            random_seed=payload.random_seed,
            randomize_run_order=payload.randomize_run_order,
        )

        # 2. Validate constraints
        valid_rows = DOEValidator.validate_matrix_constraints(
            matrix_rows, payload.constraints, payload.factors
        )

        doe = DOE(
            project_id=payload.project_id,
            objective_id=payload.objective_id,
            name=payload.name,
            description=payload.description,
            research_question=payload.research_question,
            version="v1.0",
            design_method=payload.design_method.upper(),
            factors=[f.model_dump() for f in payload.factors],
            responses=[r.model_dump() for r in payload.responses] if payload.responses else [],
            constraints=[c.model_dump() for c in payload.constraints] if payload.constraints else [],
            requested_runs=len(valid_rows),
            replicates=payload.replicates,
            center_points=payload.center_points,
            design_resolution=resolution,
            random_seed=payload.random_seed,
            randomize_run_order=payload.randomize_run_order,
            status="GENERATED",
            created_by=created_by,
        )
        self.db.add(doe)
        await self.db.flush()

        # 3. Create proposed experiment entities
        proposed_entities: list[ProposedExperiment] = []
        design_idx = 1

        for run_idx, row in enumerate(valid_rows, start=1):
            rep_num = row.get("_replicate", 1)
            is_center = row.get("_is_center", False)
            clean_vals = {k: v for k, v in row.items() if not k.startswith("_")}

            pe = ProposedExperiment(
                doe_id=doe.id,
                design_condition_id=f"RUN-{run_idx:03d}",
                design_order=design_idx,
                run_order=run_idx,
                replicate_number=rep_num,
                is_center_point=is_center,
                block="Block_1",
                factor_values=clean_vals,
                status="PROPOSED",
                created_by=created_by,
            )
            proposed_entities.append(pe)
            design_idx += 1

        self.db.add_all(proposed_entities)

        # 4. Generate quality report
        factor_coverage: list[FactorCoverageItem] = []
        for f in payload.factors:
            code = f.parameter_code
            vals = [r[code] for r in valid_rows if code in r]
            min_v = str(min(vals)) if vals else None
            max_v = str(max(vals)) if vals else None
            uniq = len(set(vals)) if vals else 0
            factor_coverage.append(
                FactorCoverageItem(
                    parameter_code=code,
                    name=f.name,
                    factor_type=f.factor_type,
                    min_generated=min_v,
                    max_generated=max_v,
                    unique_levels=uniq,
                )
            )

        report = DOEQualityReport(
            total_proposed_runs=len(proposed_entities),
            valid_runs=len(valid_rows),
            invalid_runs=len(matrix_rows) - len(valid_rows),
            intentional_replicates=payload.replicates,
            factor_coverage=factor_coverage,
            warnings=[confounding_warning] if confounding_warning else [],
        )

        await self.audit.log(
            action="DOE_GENERATED",
            entity_type="DOE",
            entity_id=doe.id,
            notes=f"Method: {payload.design_method}, Total runs: {len(proposed_entities)}",
        )

        await self.db.commit()
        return doe, report

    async def list_project_does(self, project_id: uuid.UUID) -> Sequence[DOE]:
        """Fetch all DOE studies for a project."""
        stmt = select(DOE).where(DOE.project_id == project_id).order_by(DOE.created_at.desc())
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def get_doe(self, doe_id: uuid.UUID) -> DOE:
        """Fetch DOE study by ID."""
        stmt = select(DOE).where(DOE.id == doe_id)
        res = await self.db.execute(stmt)
        doe = res.scalar_one_or_none()
        if not doe:
            raise ValueError(f"DOE study {doe_id} not found.")
        return doe

    async def list_proposed_experiments(self, doe_id: uuid.UUID) -> Sequence[ProposedExperiment]:
        """Fetch proposed experiment runs for a DOE study."""
        stmt = (
            select(ProposedExperiment)
            .where(ProposedExperiment.doe_id == doe_id)
            .order_by(ProposedExperiment.run_order)
        )
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def approve_doe_study(self, doe_id: uuid.UUID, approved_by: str = "Dr. Chief Researcher") -> DOE:
        """Approve DOE study & lock version V1 (immutable)."""
        doe = await self.get_doe(doe_id)
        doe.status = "APPROVED"

        runs = await self.list_proposed_experiments(doe_id)
        for r in runs:
            if r.status == "PROPOSED":
                r.status = "APPROVED"

        await self.audit.log(
            action="DOE_APPROVED",
            entity_type="DOE",
            entity_id=doe.id,
            notes=f"Approved by: {approved_by}, Version: {doe.version}",
        )
        await self.db.commit()
        return doe

    async def regenerate_doe_version(
        self, doe_id: uuid.UUID, payload: DOECreateInput, created_by: str | None = None
    ) -> tuple[DOE, DOEQualityReport]:
        """Creates DOE Version v2.0 when configuration changes, keeping v1.0 immutable."""
        old_doe = await self.get_doe(doe_id)
        v_parts = old_doe.version.replace("v", "").split(".")
        new_v_num = int(v_parts[0]) + 1 if v_parts[0].isdigit() else 2
        payload.name = f"{payload.name} (v{new_v_num}.0)"

        new_doe, report = await self.create_doe_and_generate(payload, created_by=created_by)
        new_doe.version = f"v{new_v_num}.0"
        await self.db.commit()
        return new_doe, report

    async def convert_run_to_planned_experiment(
        self, proposed_id: uuid.UUID, researcher: str = "Dr. DOE Researcher"
    ) -> Experiment:
        """Convert approved DOE proposed run to a PLANNED laboratory experiment."""
        linker = DOEExperimentLinker(self.db)
        exp = await linker.convert_run_to_planned_experiment(proposed_id, researcher=researcher)
        await self.audit.log(
            action="DOE_RUN_CONVERTED_TO_EXPERIMENT",
            entity_type="ProposedExperiment",
            entity_id=proposed_id,
            notes=f"Converted to experiment_id: {exp.id}",
        )
        return exp

    async def analyze_doe(
        self, doe_id: uuid.UUID, response_property: str = "Electrical Conductivity"
    ) -> DOEAnalysis:
        """Compute Main Effects, Interaction Effects, and Response Surface model fit for a DOE study."""
        doe = await self.get_doe(doe_id)
        runs = await self.list_proposed_experiments(doe_id)
        runs_dicts = [
            {
                "id": str(r.id),
                "run_order": r.run_order,
                "factor_values": r.factor_values,
                "measured_responses": r.measured_responses,
            }
            for r in runs
        ]

        main_effects = DOEAnalysisEngine.calculate_main_effects(runs_dicts, response_property)
        interaction_effects = DOEAnalysisEngine.calculate_interaction_effects(runs_dicts, response_property)
        fit_data = DOEAnalysisEngine.fit_response_surface(runs_dicts, response_property)

        analysis = DOEAnalysis(
            id=uuid.uuid4(),
            doe_id=doe.id,
            doe_version=doe.version,
            response_property=response_property,
            sample_count=fit_data.get("n_observations", 0),
            main_effects=main_effects,
            interaction_effects=interaction_effects,
            regression_model=fit_data,
            fit_metrics=fit_data.get("fit_metrics", {}),
            residual_diagnostics={
                "residuals": fit_data.get("residuals", []),
                "fitted_values": fit_data.get("fitted_values", []),
            },
        )
        self.db.add(analysis)
        await self.db.commit()
        return analysis

    async def export_doe_csv(self, doe_id: uuid.UUID) -> str:
        """Export proposed experiments design matrix to CSV string."""
        doe = await self.get_doe(doe_id)
        runs = await self.list_proposed_experiments(doe_id)

        if not runs:
            return "Run Order,Design Order,Replicate,Status\n"

        # Determine factor headers
        factor_headers = list(runs[0].factor_values.keys())
        fieldnames = ["Run Order", "Design Condition", "Replicate", "Center Point", "Status"] + factor_headers

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(fieldnames)

        for r in runs:
            row = [
                r.run_order,
                r.design_condition_id,
                r.replicate_number,
                "Yes" if r.is_center_point else "No",
                r.status,
            ] + [r.factor_values.get(h, "") for h in factor_headers]
            writer.writerow(row)

        return output.getvalue()
