"""
GreenSynth Analytics — Unit Tests for Phase 2 Database Schema & Models

Tests:
  1. User model persistence, required fields, and unique email constraint.
  2. ResearchGroup model creation, project link, leader link, and status enum.
  3. GroupMembership creation, is_leader flag, and duplicate user-group rejection.
  4. Invitation creation, member details, token hash, status, and expiration.
  5. Multi-project isolation lineage: User -> Membership -> Group -> Project.
  6. ValidationCriterion with optional project_id (global vs scoped).
  7. AuditLog with optional project_id.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog
from app.models.group_membership import GroupMembership, MembershipStatus
from app.models.invitation import Invitation, InvitationStatus
from app.models.project import Project, ProjectStatus
from app.models.research_group import GroupStatus, ResearchGroup
from app.models.user import User
from app.models.validation import ValidationCriterion


@pytest.mark.asyncio
async def test_user_persistence_and_fields(db_session: AsyncSession) -> None:
    """Verify that User model persists all required student identity fields."""
    user = User(
        username="atharva_cse",
        email="atharva@greensynth.edu",
        full_name="Atharva Researcher",
        department="Computer Science & Engineering",
        phone="9876543210",
        roll_number="CS-2026-001",
        password_hash="placeholder_hash_phase3",
        role="RESEARCHER",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)

    assert user.id is not None
    assert user.email == "atharva@greensynth.edu"
    assert user.full_name == "Atharva Researcher"
    assert user.department == "Computer Science & Engineering"
    assert user.phone == "9876543210"
    assert user.roll_number == "CS-2026-001"
    assert user.created_at is not None
    assert not hasattr(user, "project_id") or "project_id" not in user.__table__.columns


@pytest.mark.asyncio
async def test_user_email_uniqueness(db_session: AsyncSession) -> None:
    """Verify that duplicate user emails are rejected by unique constraint."""
    u1 = User(
        username="user_one",
        email="duplicate@greensynth.edu",
        full_name="User One",
        department="CSE",
        phone="1111111111",
        roll_number="CS-001",
        password_hash="hash1",
    )
    db_session.add(u1)
    await db_session.flush()

    u2 = User(
        username="user_two",
        email="duplicate@greensynth.edu",
        full_name="User Two",
        department="ENTC",
        phone="2222222222",
        roll_number="ET-002",
        password_hash="hash2",
    )
    db_session.add(u2)
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_research_group_and_leader(
    db_session: AsyncSession, demo_project: Project
) -> None:
    """Verify ResearchGroup links to Project and User leader."""
    leader = User(
        username="leader_p7",
        email="leader7@greensynth.edu",
        full_name="P7 Team Leader",
        department="Materials Science",
        phone="9988776655",
        roll_number="MS-2026-007",
        password_hash="leader_hash",
    )
    db_session.add(leader)
    await db_session.flush()

    group = ResearchGroup(
        name="GreenSynth P7 Team Alpha",
        project_id=demo_project.id,
        leader_user_id=leader.id,
        status=GroupStatus.ACTIVE.value,
    )
    db_session.add(group)
    await db_session.flush()
    await db_session.refresh(group)

    assert group.id is not None
    assert group.name == "GreenSynth P7 Team Alpha"
    assert group.project_id == demo_project.id
    assert group.leader_user_id == leader.id
    assert group.status == "ACTIVE"
    assert group.created_at is not None


@pytest.mark.asyncio
async def test_group_membership_and_leader_flag(
    db_session: AsyncSession, demo_project: Project
) -> None:
    """Verify GroupMembership associates User and Group with is_leader flag."""
    leader = User(
        username="leader_user",
        email="leader_mem@greensynth.edu",
        full_name="Leader User",
        department="Chemical Eng",
        phone="1234567890",
        roll_number="CH-001",
        password_hash="hash",
    )
    member = User(
        username="member_user",
        email="member_mem@greensynth.edu",
        full_name="Member User",
        department="Chemical Eng",
        phone="0987654321",
        roll_number="CH-002",
        password_hash="hash",
    )
    db_session.add_all([leader, member])
    await db_session.flush()

    group = ResearchGroup(
        name="P7 Group Beta",
        project_id=demo_project.id,
        leader_user_id=leader.id,
    )
    db_session.add(group)
    await db_session.flush()

    # Create Leader Membership
    m1 = GroupMembership(
        group_id=group.id,
        user_id=leader.id,
        is_leader=True,
        status=MembershipStatus.ACTIVE.value,
    )
    # Create Regular Member Membership
    m2 = GroupMembership(
        group_id=group.id,
        user_id=member.id,
        is_leader=False,
        status=MembershipStatus.ACTIVE.value,
    )
    db_session.add_all([m1, m2])
    await db_session.flush()

    # Query memberships
    res = await db_session.execute(
        select(GroupMembership).where(GroupMembership.group_id == group.id)
    )
    memberships = res.scalars().all()
    assert len(memberships) == 2
    assert any(m.is_leader for m in memberships)
    assert any(not m.is_leader for m in memberships)


@pytest.mark.asyncio
async def test_duplicate_group_membership_rejected(
    db_session: AsyncSession, demo_project: Project
) -> None:
    """Verify that adding the same user twice to the same group raises IntegrityError."""
    user = User(
        username="single_user",
        email="single@greensynth.edu",
        full_name="Single User",
        department="CSE",
        phone="5555555555",
        roll_number="CS-099",
        password_hash="hash",
    )
    db_session.add(user)
    await db_session.flush()

    group = ResearchGroup(
        name="P7 Group Gamma",
        project_id=demo_project.id,
        leader_user_id=user.id,
    )
    db_session.add(group)
    await db_session.flush()

    m1 = GroupMembership(group_id=group.id, user_id=user.id, is_leader=True)
    db_session.add(m1)
    await db_session.flush()

    # Attempt duplicate
    m2 = GroupMembership(group_id=group.id, user_id=user.id, is_leader=False)
    db_session.add(m2)
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_invitation_creation_and_fields(
    db_session: AsyncSession, demo_project: Project
) -> None:
    """Verify Invitation creation with student details and token hash."""
    leader = User(
        username="inv_leader",
        email="inv_leader@greensynth.edu",
        full_name="Inv Leader",
        department="Mechanical",
        phone="7777777777",
        roll_number="ME-001",
        password_hash="hash",
    )
    db_session.add(leader)
    await db_session.flush()

    group = ResearchGroup(
        name="P7 Group Delta",
        project_id=demo_project.id,
        leader_user_id=leader.id,
    )
    db_session.add(group)
    await db_session.flush()

    expires = datetime.now(timezone.utc) + timedelta(days=7)
    invitation = Invitation(
        group_id=group.id,
        email="invited_student@greensynth.edu",
        full_name="Invited Student",
        department="Mechanical",
        phone="8888888888",
        roll_number="ME-002",
        token_hash="sha256_hashed_invitation_token",
        status=InvitationStatus.PENDING.value,
        expires_at=expires,
    )
    db_session.add(invitation)
    await db_session.flush()
    await db_session.refresh(invitation)

    assert invitation.id is not None
    assert invitation.group_id == group.id
    assert invitation.email == "invited_student@greensynth.edu"
    assert invitation.full_name == "Invited Student"
    assert invitation.department == "Mechanical"
    assert invitation.phone == "8888888888"
    assert invitation.roll_number == "ME-002"
    assert invitation.token_hash == "sha256_hashed_invitation_token"
    assert invitation.status == "PENDING"
    assert invitation.accepted_at is None
    # Handle dialect datetime timezone representation
    exp_val = invitation.expires_at
    if exp_val.tzinfo is None:
        exp_val = exp_val.replace(tzinfo=timezone.utc)
    assert abs((exp_val - expires).total_seconds()) < 1


@pytest.mark.asyncio
async def test_project_isolation_lineage(
    db_session: AsyncSession, demo_project: Project
) -> None:
    """
    Verify the complete lineage:
    User -> GroupMembership -> ResearchGroup -> Project
    without any direct user.project_id column.
    """
    user = User(
        username="lineage_user",
        email="lineage@greensynth.edu",
        full_name="Lineage Student",
        department="Physics",
        phone="3333333333",
        roll_number="PH-001",
        password_hash="hash",
    )
    db_session.add(user)
    await db_session.flush()

    group = ResearchGroup(
        name="P7 Spray Pyrolysis Group",
        project_id=demo_project.id,
        leader_user_id=user.id,
    )
    db_session.add(group)
    await db_session.flush()

    membership = GroupMembership(
        group_id=group.id,
        user_id=user.id,
        is_leader=True,
    )
    db_session.add(membership)
    await db_session.flush()

    # Query project through user's active membership
    q = (
        select(Project)
        .join(ResearchGroup, ResearchGroup.project_id == Project.id)
        .join(GroupMembership, GroupMembership.group_id == ResearchGroup.id)
        .where(GroupMembership.user_id == user.id)
    )
    res = await db_session.execute(q)
    resolved_project = res.scalar_one()

    assert resolved_project.id == demo_project.id
    assert resolved_project.project_code == demo_project.project_code


@pytest.mark.asyncio
async def test_validation_criterion_with_nullable_project_id(
    db_session: AsyncSession, demo_project: Project
) -> None:
    """Verify ValidationCriterion supports both global (None) and project-scoped criteria."""
    global_crit = ValidationCriterion(
        project_id=None,
        property_name="crystallite_size_nm",
        metric="RELATIVE_ERROR",
        threshold=10.0,
        unit="%",
        comparison_operator="<=",
        description="Global default crystallite size tolerance",
    )
    scoped_crit = ValidationCriterion(
        project_id=demo_project.id,
        property_name="band_gap_ev",
        metric="ABSOLUTE_ERROR",
        threshold=0.15,
        unit="eV",
        comparison_operator="<=",
        description="P7-specific band gap error tolerance",
    )
    db_session.add_all([global_crit, scoped_crit])
    await db_session.flush()
    await db_session.refresh(global_crit)
    await db_session.refresh(scoped_crit)

    assert global_crit.project_id is None
    assert scoped_crit.project_id == demo_project.id


@pytest.mark.asyncio
async def test_audit_log_with_nullable_project_id(
    db_session: AsyncSession, demo_project: Project
) -> None:
    """Verify AuditLog supports optional project_id for group/project audit scoping."""
    log_entry = AuditLog(
        project_id=demo_project.id,
        user_id=uuid.uuid4(),
        entity_type="Experiment",
        entity_id=uuid.uuid4(),
        action="CREATE",
        notes="Experiment created by research group member",
    )
    db_session.add(log_entry)
    await db_session.flush()
    await db_session.refresh(log_entry)

    assert log_entry.project_id == demo_project.id
    assert log_entry.action == "CREATE"


def test_migration_0008_upgrade_and_downgrade(tmp_path) -> None:
    """Verify that migration 0008 upgrade and downgrade execute cleanly."""
    import importlib.util
    import os
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from alembic import op as alembic_op
    from sqlalchemy import create_engine

    test_db_file = tmp_path / "test_migration_0008.db"
    test_db_url = f"sqlite:///{test_db_file.as_posix()}"
    engine = create_engine(test_db_url)

    # Create tables
    from app.database.base import Base
    Base.metadata.create_all(engine)

    # Load 0008 migration module
    migration_file = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "alembic", "versions", "0008_auth_and_groups.py")
    )
    spec = importlib.util.spec_from_file_location("migration_0008", migration_file)
    assert spec is not None and spec.loader is not None
    mig_0008 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mig_0008)

    with engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        alembic_op._proxy = Operations(ctx)

        # Test downgrade
        mig_0008.downgrade()
        conn.commit()

        # Test upgrade
        mig_0008.upgrade()
        conn.commit()
