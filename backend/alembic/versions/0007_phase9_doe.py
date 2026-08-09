"""phase9_doe

Revision ID: 0007_phase9_doe
Revises: 0006_phase8_analytics
Create Date: 2026-08-09 09:14:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0007_phase9_doe'
down_revision: Union[str, None] = '0006_phase8_analytics'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Objectives Table ─────────────────────────────────────────
    op.create_table(
        'objectives',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('version', sa.String(length=32), nullable=False, server_default='v1'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('target_property', sa.String(length=128), nullable=False),
        sa.Column('direction', sa.String(length=64), nullable=False),
        sa.Column('target_value', sa.Float(), nullable=True),
        sa.Column('min_value', sa.Float(), nullable=True),
        sa.Column('max_value', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=64), nullable=True),
        sa.Column('weight', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('synthesis_method', sa.String(length=128), nullable=True),
        sa.Column('solvent', sa.String(length=128), nullable=True),
        sa.Column('constraints', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='DRAFT'),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    )
    op.create_index(op.f('ix_objectives_project_id'), 'objectives', ['project_id'], unique=False)

    # ── DOES Table ───────────────────────────────────────────────
    op.create_table(
        'does',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('objective_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('design_method', sa.String(length=64), nullable=False),
        sa.Column('factors', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('constraints', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('requested_runs', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('replicates', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('random_seed', sa.Integer(), nullable=True, server_default='42'),
        sa.Column('randomize_run_order', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='GENERATED'),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['objective_id'], ['objectives.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    )
    op.create_index(op.f('ix_does_objective_id'), 'does', ['objective_id'], unique=False)
    op.create_index(op.f('ix_does_project_id'), 'does', ['project_id'], unique=False)

    # ── Proposed Experiments Table ────────────────────────────────
    op.create_table(
        'proposed_experiments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('doe_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('design_condition_id', sa.String(length=64), nullable=False),
        sa.Column('design_order', sa.Integer(), nullable=False),
        sa.Column('run_order', sa.Integer(), nullable=False),
        sa.Column('replicate_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('factor_values', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='PROPOSED'),
        sa.Column('converted_experiment_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['converted_experiment_id'], ['experiments.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['doe_id'], ['does.id'], ondelete='CASCADE'),
    )
    op.create_index(op.f('ix_proposed_experiments_doe_id'), 'proposed_experiments', ['doe_id'], unique=False)


def downgrade() -> None:
    op.drop_table('proposed_experiments')
    op.drop_table('does')
    op.drop_table('objectives')
