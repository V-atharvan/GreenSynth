"""
GreenSynth Analytics — Parameter Service

Business logic for parameter definitions and experiment parameter values.
Performs validation against parameter definitions without altering researcher input.
"""

from __future__ import annotations

import logging
import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.parameter import (
    ExperimentParameter,
    ParameterDataType,
    ParameterDefinition,
    ParameterStatus,
)
from app.models.experiment import Experiment
from app.schemas.parameter import (
    ExperimentParameterCreate,
    ParameterDefinitionCreate,
    ParameterDefinitionUpdate,
)
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class ParameterValidationError(ValueError):
    """Raised when parameter input fails validation against definition constraints."""


class ParameterNotFoundError(Exception):
    """Raised when a parameter definition or recorded value is not found."""


class ParameterService:
    """Service layer for project and experiment parameter management."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.audit = AuditService(db)

    # ── Parameter Definition Operations ────────────────────────

    async def get_project_definitions(
        self, project_id: uuid.UUID, active_only: bool = True
    ) -> Sequence[ParameterDefinition]:
        """Return all parameter definitions for a project."""
        q = (
            select(ParameterDefinition)
            .where(ParameterDefinition.project_id == project_id)
            .order_by(ParameterDefinition.created_at.asc())
        )
        if active_only:
            q = q.where(ParameterDefinition.status == ParameterStatus.ACTIVE.value)
        result = await self.db.execute(q)
        return result.scalars().all()

    async def get_definition_by_id(self, parameter_id: uuid.UUID) -> ParameterDefinition:
        """Return parameter definition by ID."""
        result = await self.db.execute(
            select(ParameterDefinition).where(ParameterDefinition.id == parameter_id)
        )
        pdef = result.scalar_one_or_none()
        if pdef is None:
            raise ParameterNotFoundError(f"Parameter definition {parameter_id} not found.")
        return pdef

    async def create_definition(
        self, project_id: uuid.UUID, data: ParameterDefinitionCreate
    ) -> ParameterDefinition:
        """Create a new parameter definition for a project."""
        pdef = ParameterDefinition(
            project_id=project_id,
            parameter_name=data.parameter_name,
            parameter_code=data.parameter_code,
            description=data.description,
            data_type=data.data_type.value,
            unit=data.unit,
            required=data.required,
            minimum_value=data.minimum_value,
            maximum_value=data.maximum_value,
            allowed_values=data.allowed_values,
            status=data.status.value,
        )
        self.db.add(pdef)
        await self.db.flush()
        await self.db.refresh(pdef)

        await self.audit.log(
            entity_type="ParameterDefinition",
            entity_id=pdef.id,
            action="CREATE",
            changes={"code": pdef.parameter_code, "name": pdef.parameter_name},
        )
        logger.info("Created ParameterDefinition %s for project %s", pdef.parameter_code, project_id)
        return pdef

    async def update_definition(
        self, parameter_id: uuid.UUID, data: ParameterDefinitionUpdate
    ) -> ParameterDefinition:
        """Update an existing parameter definition."""
        pdef = await self.get_definition_by_id(parameter_id)
        changes = {}
        for field, value in data.model_dump(exclude_none=True).items():
            if hasattr(pdef, field):
                val_str = value.value if hasattr(value, "value") else value
                setattr(pdef, field, val_str)
                changes[field] = str(value)

        await self.db.flush()
        await self.db.refresh(pdef)

        await self.audit.log(
            entity_type="ParameterDefinition",
            entity_id=pdef.id,
            action="UPDATE",
            changes=changes,
        )
        return pdef

    async def deactivate_definition(self, parameter_id: uuid.UUID) -> ParameterDefinition:
        """
        Deactivate a parameter definition (soft delete).

        Preserves historical experiment integrity — definitions used in past experiments
        are marked INACTIVE rather than deleted.
        """
        pdef = await self.get_definition_by_id(parameter_id)
        pdef.status = ParameterStatus.INACTIVE.value
        await self.db.flush()
        await self.db.refresh(pdef)

        await self.audit.log(
            entity_type="ParameterDefinition",
            entity_id=pdef.id,
            action="DEACTIVATE",
        )
        logger.info("Deactivated ParameterDefinition %s", parameter_id)
        return pdef

    # ── Experiment Parameter Operations ────────────────────────

    async def get_experiment_parameters(
        self, experiment_id: uuid.UUID
    ) -> Sequence[ExperimentParameter]:
        """Return all recorded parameter values for an experiment."""
        result = await self.db.execute(
            select(ExperimentParameter)
            .options(selectinload(ExperimentParameter.parameter_definition))
            .where(ExperimentParameter.experiment_id == experiment_id)
            .order_by(ExperimentParameter.created_at.asc())
        )
        return result.scalars().all()

    async def save_experiment_parameters(
        self,
        experiment_id: uuid.UUID,
        parameter_inputs: list[ExperimentParameterCreate],
    ) -> list[ExperimentParameter]:
        """
        Save or update a batch of experiment parameters.

        Validates all values against parameter definitions before saving.
        Does NOT alter researcher input — raises ParameterValidationError on invalid input.
        """
        # Fetch parent experiment
        exp_result = await self.db.execute(
            select(Experiment).where(Experiment.id == experiment_id)
        )
        experiment = exp_result.scalar_one_or_none()
        if experiment is None:
            raise ParameterNotFoundError(f"Experiment {experiment_id} not found.")

        # Fetch all project parameter definitions
        definitions = await self.get_project_definitions(experiment.project_id, active_only=False)
        def_map = {d.id: d for d in definitions}

        # Build validation map from submitted inputs
        input_map = {inp.parameter_definition_id: inp for inp in parameter_inputs}

        # 1. Validate required parameters
        for pdef in definitions:
            if pdef.required and pdef.status == ParameterStatus.ACTIVE.value:
                inp = input_map.get(pdef.id)
                if not inp or inp.value is None or str(inp.value).strip() == "":
                    raise ParameterValidationError(
                        f"Required parameter '{pdef.parameter_name}' is missing."
                    )

        # 2. Validate data types and ranges for provided inputs
        saved_params: list[ExperimentParameter] = []

        for inp in parameter_inputs:
            pdef = def_map.get(inp.parameter_definition_id)
            if not pdef:
                raise ParameterNotFoundError(
                    f"Parameter definition {inp.parameter_definition_id} does not exist for this project."
                )

            val_str = inp.value.strip() if inp.value else None
            val_num: float | None = None

            if val_str is not None and val_str != "":
                # Data type validation
                if pdef.data_type == ParameterDataType.NUMBER.value:
                    try:
                        val_num = float(val_str)
                    except ValueError:
                        raise ParameterValidationError(
                            f"Parameter '{pdef.parameter_name}' must be a numeric value."
                        )

                    # Range validation
                    if pdef.minimum_value is not None and val_num < pdef.minimum_value:
                        raise ParameterValidationError(
                            f"Parameter '{pdef.parameter_name}' ({val_num}) is below the minimum allowed limit of {pdef.minimum_value} {pdef.unit or ''}."
                        )
                    if pdef.maximum_value is not None and val_num > pdef.maximum_value:
                        raise ParameterValidationError(
                            f"Parameter '{pdef.parameter_name}' ({val_num}) exceeds the maximum allowed limit of {pdef.maximum_value} {pdef.unit or ''}."
                        )

                elif pdef.data_type == ParameterDataType.ENUM.value:
                    if pdef.allowed_values and val_str not in pdef.allowed_values:
                        allowed_str = ", ".join(pdef.allowed_values)
                        raise ParameterValidationError(
                            f"Parameter '{pdef.parameter_name}' value '{val_str}' is invalid. Allowed options: {allowed_str}."
                        )

                elif pdef.data_type == ParameterDataType.BOOLEAN.value:
                    if val_str.lower() not in ("true", "false", "1", "0", "yes", "no"):
                        raise ParameterValidationError(
                            f"Parameter '{pdef.parameter_name}' must be a boolean (true/false)."
                        )

            # Check if parameter value record already exists for this experiment
            existing = await self.db.execute(
                select(ExperimentParameter).where(
                    ExperimentParameter.experiment_id == experiment_id,
                    ExperimentParameter.parameter_definition_id == pdef.id,
                )
            )
            exp_param = existing.scalar_one_or_none()

            # Preserve unit (use parameter's submitted unit, or default from definition)
            preserved_unit = inp.unit if inp.unit is not None else pdef.unit

            if exp_param:
                exp_param.value = val_str
                exp_param.value_numeric = val_num
                exp_param.unit = preserved_unit
                exp_param.notes = inp.notes
            else:
                exp_param = ExperimentParameter(
                    experiment_id=experiment_id,
                    parameter_definition_id=pdef.id,
                    value=val_str,
                    value_numeric=val_num,
                    unit=preserved_unit,
                    notes=inp.notes,
                )
                self.db.add(exp_param)

            saved_params.append(exp_param)

        await self.db.flush()

        await self.audit.log(
            entity_type="Experiment",
            entity_id=experiment_id,
            action="SAVE_PARAMETERS",
            notes=f"Saved {len(saved_params)} synthesis parameters.",
        )
        return await self.get_experiment_parameters(experiment_id)
