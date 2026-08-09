"""phase7_ftir_sem

Revision ID: 0005_phase7_ftir_sem
Revises: 0004_phase4_xrd
Create Date: 2026-08-09 08:50:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0005_phase7_ftir_sem'
down_revision: Union[str, None] = '0004_phase4_xrd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── FTIR Annotations ─────────────────────────────────────────
    op.create_table(
        'ftir_annotations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('analysis_run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('wavenumber_cm1', sa.Float(), nullable=False),
        sa.Column('label', sa.String(length=128), nullable=False),
        sa.Column('interpretation', sa.Text(), nullable=True),
        sa.Column('confidence', sa.String(length=32), nullable=True, server_default='Tentative'),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['analysis_run_id'], ['analysis_runs.id'], ondelete='CASCADE'),
    )
    op.create_index(op.f('ix_ftir_annotations_analysis_run_id'), 'ftir_annotations', ['analysis_run_id'], unique=False)

    # ── SEM Metadata ─────────────────────────────────────────────
    op.create_table(
        'sem_metadata',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('raw_file_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('magnification', sa.Float(), nullable=True),
        sa.Column('accelerating_voltage_kv', sa.Float(), nullable=True),
        sa.Column('working_distance_mm', sa.Float(), nullable=True),
        sa.Column('detector', sa.String(length=64), nullable=True),
        sa.Column('scale_bar_nm', sa.Float(), nullable=True),
        sa.Column('scale_bar_pixels', sa.Float(), nullable=True),
        sa.Column('nm_per_pixel', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['raw_file_id'], ['raw_files.id'], ondelete='CASCADE'),
    )
    op.create_index(op.f('ix_sem_metadata_raw_file_id'), 'sem_metadata', ['raw_file_id'], unique=True)

    # ── SEM Annotations ──────────────────────────────────────────
    op.create_table(
        'sem_annotations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('raw_file_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('annotation_type', sa.String(length=32), nullable=False, server_default='point'),
        sa.Column('coordinates_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('label', sa.String(length=128), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['raw_file_id'], ['raw_files.id'], ondelete='CASCADE'),
    )
    op.create_index(op.f('ix_sem_annotations_raw_file_id'), 'sem_annotations', ['raw_file_id'], unique=False)

    # ── SEM Measurements ─────────────────────────────────────────
    op.create_table(
        'sem_measurements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('raw_file_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('pixel_distance', sa.Float(), nullable=False),
        sa.Column('physical_distance_nm', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=32), nullable=False, server_default='nm'),
        sa.Column('label', sa.String(length=128), nullable=True),
        sa.Column('calibration_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['raw_file_id'], ['raw_files.id'], ondelete='CASCADE'),
    )
    op.create_index(op.f('ix_sem_measurements_raw_file_id'), 'sem_measurements', ['raw_file_id'], unique=False)


def downgrade() -> None:
    op.drop_table('sem_measurements')
    op.drop_table('sem_annotations')
    op.drop_table('sem_metadata')
    op.drop_table('ftir_annotations')
