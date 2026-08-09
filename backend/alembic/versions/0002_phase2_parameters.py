"""phase2_parameters

Revision ID: 0002_phase2_parameters
Revises: 0001_initial_schema
Create Date: 2026-08-09 08:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0002_phase2_parameters'
down_revision: Union[str, None] = '0001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Parameter Definitions ───────────────────────────────────
    op.create_table(
        'parameter_definitions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parameter_name', sa.String(length=255), nullable=False),
        sa.Column('parameter_code', sa.String(length=64), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('data_type', sa.String(length=16), nullable=False, server_default='NUMBER'),
        sa.Column('unit', sa.String(length=64), nullable=True),
        sa.Column('required', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('minimum_value', sa.Float(), nullable=True),
        sa.Column('maximum_value', sa.Float(), nullable=True),
        sa.Column('allowed_values', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=16), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='RESTRICT'),
    )
    op.create_index(op.f('ix_parameter_definitions_project_id'), 'parameter_definitions', ['project_id'], unique=False)
    op.create_index(op.f('ix_parameter_definitions_status'), 'parameter_definitions', ['status'], unique=False)

    # ── Experiment Parameters ───────────────────────────────────
    op.create_table(
        'experiment_parameters',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('experiment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parameter_definition_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('value_numeric', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=64), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parameter_definition_id'], ['parameter_definitions.id'], ondelete='RESTRICT'),
    )
    op.create_index(op.f('ix_experiment_parameters_experiment_id'), 'experiment_parameters', ['experiment_id'], unique=False)
    op.create_index(op.f('ix_experiment_parameters_parameter_definition_id'), 'experiment_parameters', ['parameter_definition_id'], unique=False)
    op.create_index(op.f('ix_experiment_parameters_value_numeric'), 'experiment_parameters', ['value_numeric'], unique=False)

    # ── Audit Logs ─────────────────────────────────────────────
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('entity_type', sa.String(length=64), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.String(length=64), nullable=False),
        sa.Column('changes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
    )
    op.create_index(op.f('ix_audit_logs_entity_id'), 'audit_logs', ['entity_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_entity_type'), 'audit_logs', ['entity_type'], unique=False)
    op.create_index(op.f('ix_audit_logs_timestamp'), 'audit_logs', ['timestamp'], unique=False)
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('experiment_parameters')
    op.drop_table('parameter_definitions')
