"""phase4_xrd

Revision ID: 0004_phase4_xrd
Revises: 0003_phase3_characterizations
Create Date: 2026-08-09 08:35:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0004_phase4_xrd'
down_revision: Union[str, None] = '0003_phase3_characterizations'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Analysis Runs ───────────────────────────────────────────
    op.create_table(
        'analysis_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('characterization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('input_file_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('analysis_type', sa.String(length=32), nullable=False, server_default='XRD'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='COMPLETED'),
        sa.Column('software_version', sa.String(length=32), nullable=False, server_default='0.1.0'),
        sa.Column('parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('assumptions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['characterization_id'], ['characterizations.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['input_file_id'], ['raw_files.id'], ondelete='RESTRICT'),
    )
    op.create_index(op.f('ix_analysis_runs_analysis_type'), 'analysis_runs', ['analysis_type'], unique=False)
    op.create_index(op.f('ix_analysis_runs_characterization_id'), 'analysis_runs', ['characterization_id'], unique=False)
    op.create_index(op.f('ix_analysis_runs_input_file_id'), 'analysis_runs', ['input_file_id'], unique=False)
    op.create_index(op.f('ix_analysis_runs_status'), 'analysis_runs', ['status'], unique=False)

    # ── XRD Peaks ───────────────────────────────────────────────
    op.create_table(
        'xrd_peaks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('analysis_run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('peak_position', sa.Float(), nullable=False, comment='2θ angle in degrees'),
        sa.Column('intensity', sa.Float(), nullable=False),
        sa.Column('fwhm', sa.Float(), nullable=True),
        sa.Column('prominence', sa.Float(), nullable=True),
        sa.Column('width', sa.Float(), nullable=True),
        sa.Column('detection_parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['analysis_run_id'], ['analysis_runs.id'], ondelete='CASCADE'),
    )
    op.create_index(op.f('ix_xrd_peaks_analysis_run_id'), 'xrd_peaks', ['analysis_run_id'], unique=False)
    op.create_index(op.f('ix_xrd_peaks_peak_position'), 'xrd_peaks', ['peak_position'], unique=False)

    # ── Processed Files ─────────────────────────────────────────
    op.create_table(
        'processed_files',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('analysis_run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('raw_file_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('stored_path', sa.Text(), nullable=False),
        sa.Column('processing_method', sa.String(length=128), nullable=False),
        sa.Column('processing_parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['analysis_run_id'], ['analysis_runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['raw_file_id'], ['raw_files.id'], ondelete='RESTRICT'),
    )
    op.create_index(op.f('ix_processed_files_analysis_run_id'), 'processed_files', ['analysis_run_id'], unique=False)
    op.create_index(op.f('ix_processed_files_raw_file_id'), 'processed_files', ['raw_file_id'], unique=False)

    # ── Calculated Properties ───────────────────────────────────
    op.create_table(
        'calculated_properties',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('sample_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('analysis_run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('property_name', sa.String(length=128), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=32), nullable=False),
        sa.Column('calculation_method', sa.String(length=128), nullable=False),
        sa.Column('formula', sa.String(length=255), nullable=True),
        sa.Column('assumptions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('input_values', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['analysis_run_id'], ['analysis_runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sample_id'], ['samples.id'], ondelete='RESTRICT'),
    )
    op.create_index(op.f('ix_calculated_properties_analysis_run_id'), 'calculated_properties', ['analysis_run_id'], unique=False)
    op.create_index(op.f('ix_calculated_properties_property_name'), 'calculated_properties', ['property_name'], unique=False)
    op.create_index(op.f('ix_calculated_properties_sample_id'), 'calculated_properties', ['sample_id'], unique=False)


def downgrade() -> None:
    op.drop_table('calculated_properties')
    op.drop_table('processed_files')
    op.drop_table('xrd_peaks')
    op.drop_table('analysis_runs')
