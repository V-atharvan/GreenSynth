"""
GreenSynth Analytics — DOE Experiment Linker & Parameter Deviation Engine (Phase 14)

Provides:
  1. Experiment Conversion: Converts approved DOE design runs into PLANNED laboratory experiments.
  2. Measured Response Linker: Links measured characterization results back to DOE design runs.
  3. Parameter Deviation Calculator: Computes absolute & signed parameter deviations (PROPOSED vs ACTUAL).
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import CalculatedProperty
from app.models.doe import DOE, ProposedExperiment
from app.models.experiment import Experiment, ExperimentStatus
from app.models.parameter import ExperimentParameter, ParameterDefinition
from app.models.sample import Sample, SampleStatus


class DOEExperimentLinker:
    """Links DOE proposed runs with laboratory execution lifecycle and measured responses."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def convert_run_to_planned_experiment(
        self, proposed_id: uuid.UUID, researcher: str = "Dr. DOE Researcher"
    ) -> Experiment:
        """Converts an APPROVED DOE proposed run into a real PLANNED laboratory experiment."""
        res_p = await self.db.execute(
            select(ProposedExperiment).where(ProposedExperiment.id == proposed_id)
        )
        pe = res_p.scalar_one_or_none()
        if not pe:
            raise ValueError(f"ProposedExperiment {proposed_id} not found.")

        if pe.status not in ("PROPOSED", "APPROVED"):
            raise ValueError(f"ProposedExperiment {proposed_id} is in invalid status '{pe.status}' for conversion.")

        # Fetch DOE explicitly to avoid async lazy load MissingGreenlet
        res_doe = await self.db.execute(select(DOE).where(DOE.id == pe.doe_id))
        doe_obj = res_doe.scalar_one_or_none()
        project_id = doe_obj.project_id if doe_obj else uuid.uuid4()

        # Create PLANNED experiment
        exp_code = f"EXP-DOE-{pe.run_order:03d}"
        exp = Experiment(
            id=uuid.uuid4(),
            project_id=project_id,
            experiment_code=exp_code,
            title=f"DOE Proposed Synthesis Run #{pe.run_order} (Replicate #{pe.replicate_number})",
            status=ExperimentStatus.PLANNED,
            researcher=researcher,
            notes=f"Converted from DOE study {pe.doe_id} condition {pe.design_condition_id}",
        )
        self.db.add(exp)
        await self.db.flush()

        # Record proposed parameters as ExperimentParameters
        for param_code, val in pe.factor_values.items():
            if param_code.startswith("_"):
                continue
            res_pd = await self.db.execute(
                select(ParameterDefinition).where(
                    ParameterDefinition.parameter_code == param_code,
                    ParameterDefinition.project_id == project_id,
                )
            )
            pdef = res_pd.scalars().first()
            if not pdef:
                res_pd_fallback = await self.db.execute(
                    select(ParameterDefinition).where(
                        ParameterDefinition.parameter_code == param_code
                    )
                )
                pdef = res_pd_fallback.scalars().first()
            if pdef:
                ep = ExperimentParameter(
                    id=uuid.uuid4(),
                    experiment_id=exp.id,
                    parameter_definition_id=pdef.id,
                    value=str(val),
                    value_numeric=float(val) if isinstance(val, (int, float)) else None,
                    unit=pdef.unit,
                )
                self.db.add(ep)

        # Update proposed experiment status
        pe.status = "PLANNED"
        pe.converted_experiment_id = exp.id
        await self.db.commit()
        return exp

    @staticmethod
    def calculate_parameter_deviation(
        proposed_values: dict[str, Any], actual_values: dict[str, Any]
    ) -> dict[str, dict[str, float]]:
        """
        Calculates parameter deviations between DOE PROPOSED parameter values and ACTUAL measured parameters.

        Returns:
            {"substrate_temperature": {"proposed": 350.0, "actual": 357.0, "deviation": 7.0, "percentage_deviation": 2.0}}
        """
        deviations: dict[str, dict[str, float]] = {}
        for code, prop_val in proposed_values.items():
            if code.startswith("_") or code not in actual_values:
                continue
            try:
                p_num = float(prop_val)
                a_num = float(actual_values[code])
                dev = a_num - p_num
                pct = (abs(dev) / abs(p_num) * 100.0) if abs(p_num) > 1e-12 else 0.0
                deviations[code] = {
                    "proposed": p_num,
                    "actual": a_num,
                    "deviation": round(dev, 4),
                    "percentage_deviation": round(pct, 4),
                }
            except (ValueError, TypeError):
                continue
        return deviations
