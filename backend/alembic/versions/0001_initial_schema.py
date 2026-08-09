"""initial_schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-08-09 07:30:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Users ──────────────────────────────────────────────────
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('username', sa.String(length=64), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=16), nullable=False, server_default='RESEARCHER'),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # ── Projects ───────────────────────────────────────────────
    op.create_table(
        'projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_code', sa.String(length=32), nullable=False, comment='Short unique code, e.g. P7'),
        sa.Column('name', sa.String(length=512), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('material', sa.String(length=128), nullable=False, comment='e.g. CuO'),
        sa.Column('extract', sa.String(length=128), nullable=False, comment='e.g. Mulberry'),
        sa.Column('solvent', sa.String(length=128), nullable=False, comment='e.g. Ethanol'),
        sa.Column('synthesis_method', sa.String(length=128), nullable=False, comment='e.g. Spray Pyrolysis'),
        sa.Column('status', sa.String(length=16), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index(op.f('ix_projects_project_code'), 'projects', ['project_code'], unique=True)
    op.create_index(op.f('ix_projects_status'), 'projects', ['status'], unique=False)

    # ── Experiments ────────────────────────────────────────────
    op.create_table(
        'experiments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('experiment_code', sa.String(length=64), nullable=False, comment='Human-readable unique code'),
        sa.Column('title', sa.String(length=512), nullable=False),
        sa.Column('status', sa.String(length=16), nullable=False, server_default='PLANNED'),
        sa.Column('experiment_date', sa.Date(), nullable=True),
        sa.Column('researcher', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='RESTRICT'),
    )
    op.create_index(op.f('ix_experiments_experiment_code'), 'experiments', ['experiment_code'], unique=True)
    op.create_index(op.f('ix_experiments_project_id'), 'experiments', ['project_id'], unique=False)
    op.create_index(op.f('ix_experiments_status'), 'experiments', ['status'], unique=False)

    # ── Samples ────────────────────────────────────────────────
    op.create_table(
        'samples',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('experiment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sample_code', sa.String(length=64), nullable=False, comment='Human-readable unique code'),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('material', sa.String(length=128), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=16), nullable=False, server_default='PREPARED'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ondelete='RESTRICT'),
    )
    op.create_index(op.f('ix_samples_experiment_id'), 'samples', ['experiment_id'], unique=False)
    op.create_index(op.f('ix_samples_sample_code'), 'samples', ['sample_code'], unique=True)
    op.create_index(op.f('ix_samples_status'), 'samples', ['status'], unique=False)


def downgrade() -> None:
    op.drop_table('samples')
    op.drop_table('experiments')
    op.drop_table('projects')
    op.drop_table('users')
