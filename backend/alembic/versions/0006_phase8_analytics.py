"""phase8_analytics

Revision ID: 0006_phase8_analytics
Revises: 0005_phase7_ftir_sem
Create Date: 2026-08-09 08:55:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0006_phase8_analytics'
down_revision: Union[str, None] = '0005_phase7_ftir_sem'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Datasets Table ──────────────────────────────────────────
    op.create_table(
        'datasets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('version', sa.String(length=32), nullable=False, server_default='v1'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sample_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('variables', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('filters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    )
    op.create_index(op.f('ix_datasets_project_id'), 'datasets', ['project_id'], unique=False)

    # ── Statistical Analyses Table ───────────────────────────────
    op.create_table(
        'statistical_analyses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('dataset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('analysis_run_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('analysis_type', sa.String(length=64), nullable=False),
        sa.Column('x_variable', sa.String(length=128), nullable=True),
        sa.Column('y_variable', sa.String(length=128), nullable=True),
        sa.Column('group_variable', sa.String(length=128), nullable=True),
        sa.Column('method', sa.String(length=128), nullable=False),
        sa.Column('sample_size', sa.Integer(), nullable=False),
        sa.Column('results_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('assumptions_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('warnings_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['analysis_run_id'], ['analysis_runs.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
    )
    op.create_index(op.f('ix_statistical_analyses_analysis_run_id'), 'statistical_analyses', ['analysis_run_id'], unique=False)
    op.create_index(op.f('ix_statistical_analyses_analysis_type'), 'statistical_analyses', ['analysis_type'], unique=False)
    op.create_index(op.f('ix_statistical_analyses_dataset_id'), 'statistical_analyses', ['dataset_id'], unique=False)


def downgrade() -> None:
    op.drop_table('statistical_analyses')
    op.drop_table('datasets')
