"""auth_and_groups

Revision ID: 0008_auth_and_groups
Revises: 0007_phase9_doe
Create Date: 2026-08-30 13:45:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0008_auth_and_groups'
down_revision: Union[str, None] = '0007_phase9_doe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Extend Users Table ──────────────────────────────────────
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('full_name', sa.String(length=255), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('department', sa.String(length=128), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('phone', sa.String(length=32), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('roll_number', sa.String(length=64), nullable=False, server_default=''))
        batch_op.create_index(op.f('ix_users_roll_number'), ['roll_number'], unique=False)

    # ── Research Groups Table ───────────────────────────────────
    op.create_table(
        'research_groups',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('leader_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['leader_user_id'], ['users.id'], ondelete='RESTRICT'),
    )
    op.create_index(op.f('ix_research_groups_project_id'), 'research_groups', ['project_id'], unique=False)
    op.create_index(op.f('ix_research_groups_leader_user_id'), 'research_groups', ['leader_user_id'], unique=False)
    op.create_index(op.f('ix_research_groups_status'), 'research_groups', ['status'], unique=False)

    # ── Group Memberships Table ─────────────────────────────────
    op.create_table(
        'group_memberships',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_leader', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='ACTIVE'),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['research_groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('group_id', 'user_id', name='uq_group_membership_user'),
    )
    op.create_index(op.f('ix_group_memberships_group_id'), 'group_memberships', ['group_id'], unique=False)
    op.create_index(op.f('ix_group_memberships_user_id'), 'group_memberships', ['user_id'], unique=False)
    op.create_index(op.f('ix_group_memberships_status'), 'group_memberships', ['status'], unique=False)

    # ── Invitations Table ───────────────────────────────────────
    op.create_table(
        'invitations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('department', sa.String(length=128), nullable=False),
        sa.Column('phone', sa.String(length=32), nullable=False),
        sa.Column('roll_number', sa.String(length=64), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='PENDING'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['research_groups.id'], ondelete='CASCADE'),
    )
    op.create_index(op.f('ix_invitations_group_id'), 'invitations', ['group_id'], unique=False)
    op.create_index(op.f('ix_invitations_email'), 'invitations', ['email'], unique=False)
    op.create_index(op.f('ix_invitations_status'), 'invitations', ['status'], unique=False)
    op.create_index(op.f('ix_invitations_expires_at'), 'invitations', ['expires_at'], unique=False)
    op.create_index(op.f('ix_invitations_roll_number'), 'invitations', ['roll_number'], unique=False)

    # ── Validation Criteria Table ───────────────────────────────
    with op.batch_alter_table('validation_criteria') as batch_op:
        batch_op.add_column(sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True))
        batch_op.create_foreign_key('fk_validation_criteria_project_id', 'projects', ['project_id'], ['id'], ondelete='CASCADE')
        batch_op.create_index(op.f('ix_validation_criteria_project_id'), ['project_id'], unique=False)

    # ── Audit Logs Table ────────────────────────────────────────
    with op.batch_alter_table('audit_logs') as batch_op:
        batch_op.add_column(sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True))
        batch_op.create_foreign_key('fk_audit_logs_project_id', 'projects', ['project_id'], ['id'], ondelete='SET NULL')
        batch_op.create_index(op.f('ix_audit_logs_project_id'), ['project_id'], unique=False)


def downgrade() -> None:
    # ── Revert Audit Logs ───────────────────────────────────────
    with op.batch_alter_table('audit_logs') as batch_op:
        batch_op.drop_index(op.f('ix_audit_logs_project_id'))
        batch_op.drop_column('project_id')

    # ── Revert Validation Criteria ──────────────────────────────
    with op.batch_alter_table('validation_criteria') as batch_op:
        batch_op.drop_index(op.f('ix_validation_criteria_project_id'))
        batch_op.drop_column('project_id')

    # ── Drop Tables ─────────────────────────────────────────────
    op.drop_table('invitations')
    op.drop_table('group_memberships')
    op.drop_table('research_groups')

    # ── Revert Users Table ──────────────────────────────────────
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_index(op.f('ix_users_roll_number'))
        batch_op.drop_column('roll_number')
        batch_op.drop_column('phone')
        batch_op.drop_column('department')
        batch_op.drop_column('full_name')
