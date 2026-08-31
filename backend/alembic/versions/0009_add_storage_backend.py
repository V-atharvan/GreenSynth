"""add_storage_backend

Revision ID: 0009_add_storage_backend
Revises: 0008_auth_and_groups
Create Date: 2026-08-30 16:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0009_add_storage_backend'
down_revision: Union[str, None] = '0008_auth_and_groups'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('raw_files') as batch_op:
        batch_op.add_column(
            sa.Column(
                'storage_backend',
                sa.String(length=32),
                nullable=False,
                server_default='local',
                comment='Storage backend: local or s3',
            )
        )
        batch_op.create_index(
            op.f('ix_raw_files_storage_backend'),
            ['storage_backend'],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table('raw_files') as batch_op:
        batch_op.drop_index(op.f('ix_raw_files_storage_backend'))
        batch_op.drop_column('storage_backend')
