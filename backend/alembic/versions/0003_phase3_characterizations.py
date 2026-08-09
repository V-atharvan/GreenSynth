"""phase3_characterizations

Revision ID: 0003_phase3_characterizations
Revises: 0002_phase2_parameters
Create Date: 2026-08-09 08:30:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0003_phase3_characterizations'
down_revision: Union[str, None] = '0002_phase2_parameters'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Characterizations ───────────────────────────────────────
    op.create_table(
        'characterizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('sample_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('technique', sa.String(length=32), nullable=False, comment='XRD, UV_VIS, FTIR, SEM, ELECTRICAL'),
        sa.Column('characterization_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('operator', sa.String(length=255), nullable=True),
        sa.Column('instrument_name', sa.String(length=255), nullable=True),
        sa.Column('instrument_model', sa.String(length=255), nullable=True),
        sa.Column('instrument_id', sa.String(length=128), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='UPLOADED'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['sample_id'], ['samples.id'], ondelete='RESTRICT'),
    )
    op.create_index(op.f('ix_characterizations_sample_id'), 'characterizations', ['sample_id'], unique=False)
    op.create_index(op.f('ix_characterizations_status'), 'characterizations', ['status'], unique=False)
    op.create_index(op.f('ix_characterizations_technique'), 'characterizations', ['technique'], unique=False)

    # ── Raw Files ───────────────────────────────────────────────
    op.create_table(
        'raw_files',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('characterization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sample_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('original_filename', sa.String(length=512), nullable=False),
        sa.Column('stored_filename', sa.String(length=512), nullable=False),
        sa.Column('file_extension', sa.String(length=32), nullable=False),
        sa.Column('mime_type', sa.String(length=128), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('checksum', sa.String(length=64), nullable=False),
        sa.Column('storage_path', sa.Text(), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('uploaded_by', sa.String(length=255), nullable=True),
        sa.Column('file_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=16), nullable=False, server_default='ACTIVE'),
        sa.ForeignKeyConstraint(['characterization_id'], ['characterizations.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['sample_id'], ['samples.id'], ondelete='RESTRICT'),
    )
    op.create_index(op.f('ix_raw_files_characterization_id'), 'raw_files', ['characterization_id'], unique=False)
    op.create_index(op.f('ix_raw_files_checksum'), 'raw_files', ['checksum'], unique=False)
    op.create_index(op.f('ix_raw_files_file_extension'), 'raw_files', ['file_extension'], unique=False)
    op.create_index(op.f('ix_raw_files_status'), 'raw_files', ['status'], unique=False)


def downgrade() -> None:
    op.drop_table('raw_files')
    op.drop_table('characterizations')
