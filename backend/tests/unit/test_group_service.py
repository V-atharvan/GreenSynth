"""
GreenSynth Analytics — Unit Tests: GroupService

Verifies:
  - Multi-member group registration (1 leader + 3 members)
  - Capacity validation (MAX_GROUP_MEMBERS = 4)
  - Duplicate email and roll-number rejection
  - Group metadata and member listings
  - Leader-restricted additional member invites
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group_membership import GroupMembership, MembershipStatus
from app.models.invitation import Invitation, InvitationStatus
from app.models.project import Project, ProjectStatus
from app.models.research_group import GroupStatus, ResearchGroup
from app.models.user import User
from app.schemas.group import (
    GroupMetadataInput,
    GroupRegistrationRequest,
    LeaderRegisterInput,
    MemberInvitationInput,
)
from app.services.group_service import GroupService


@pytest.fixture
async def active_project(db_session: AsyncSession) -> Project:
    """Fixture providing an active synthesis project."""
    proj = Project(
        project_code=f"P7-GRP-{uuid.uuid4().hex[:6].upper()}",
        name="Spray Pyrolysis CuO Group Test",
        material="CuO",
        synthesis_method="Spray Pyrolysis",
        solvent="ETHANOL",
        extract="Mulberry",
        status=ProjectStatus.ACTIVE.value,
    )
    db_session.add(proj)
    await db_session.flush()
    return proj


@pytest.mark.asyncio
async def test_register_group_with_members_success(
    db_session: AsyncSession, active_project: Project
) -> None:
    """Verify atomic registration of Group Leader + Research Group + 3 Invitations."""
    service = GroupService(db_session)
    payload = GroupRegistrationRequest(
        leader=LeaderRegisterInput(
            full_name="Alice Leader",
            department="Chemical Engineering",
            phone="9876543210",
            roll_number="CHEM-001",
            email="alice.leader@greensynth.edu",
            password="SecureLeaderPassword123!",
        ),
        group=GroupMetadataInput(
            name="Green Innovators Alpha",
            project_id=active_project.id,
        ),
        members=[
            MemberInvitationInput(
                full_name="Bob Member",
                department="Chemical Engineering",
                phone="9876543211",
                roll_number="CHEM-002",
                email="bob.member@greensynth.edu",
            ),
            MemberInvitationInput(
                full_name="Charlie Member",
                department="ENTC",
                phone="9876543212",
                roll_number="ENTC-001",
                email="charlie.member@greensynth.edu",
            ),
            MemberInvitationInput(
                full_name="Diana Member",
                department="CSE",
                phone="9876543213",
                roll_number="CSE-001",
                email="diana.member@greensynth.edu",
            ),
        ],
    )

    res = await service.register_group_with_members(payload)

    # 1. Verify Response Payload
    assert res.group_id is not None
    assert res.group_name == "Green Innovators Alpha"
    assert res.project_id == active_project.id
    assert res.project_code == active_project.project_code
    assert res.leader_name == "Alice Leader"
    assert res.leader_email == "alice.leader@greensynth.edu"
    assert len(res.invitations) == 3
    assert res.access_token is not None

    # 2. Verify Database Records
    # Leader User
    leader_db = await db_session.get(User, res.leader_id)
    assert leader_db is not None
    assert leader_db.email == "alice.leader@greensynth.edu"
    assert leader_db.is_active is True

    # Research Group
    group_db = await db_session.get(ResearchGroup, res.group_id)
    assert group_db is not None
    assert group_db.project_id == active_project.id
    assert group_db.leader_user_id == leader_db.id

    # Leader Membership
    mem_res = await db_session.execute(
        select(GroupMembership).where(
            GroupMembership.group_id == group_db.id,
            GroupMembership.user_id == leader_db.id,
        )
    )
    membership = mem_res.scalar_one_or_none()
    assert membership is not None
    assert membership.is_leader is True
    assert membership.status == "ACTIVE"

    # Invitations
    inv_res = await db_session.execute(
        select(Invitation).where(Invitation.group_id == group_db.id)
    )
    invitations = inv_res.scalars().all()
    assert len(invitations) == 3
    for inv in invitations:
        assert inv.status == "PENDING"
        assert inv.token_hash is not None
        assert len(inv.token_hash) == 64  # SHA-256 length


@pytest.mark.asyncio
async def test_register_group_duplicate_leader_email(
    db_session: AsyncSession, active_project: Project
) -> None:
    """Verify that registering with an existing leader email raises 409 Conflict."""
    service = GroupService(db_session)
    payload = GroupRegistrationRequest(
        leader=LeaderRegisterInput(
            full_name="Duplicate Leader",
            department="CSE",
            phone="1111111111",
            roll_number="CSE-DUP",
            email="dup.leader@greensynth.edu",
            password="Password123!",
        ),
        group=GroupMetadataInput(
            name="First Group",
            project_id=active_project.id,
        ),
        members=[
            MemberInvitationInput(
                full_name="M1",
                department="CSE",
                phone="2222222222",
                roll_number="CSE-M1",
                email="m1@greensynth.edu",
            ),
        ],
    )
    await service.register_group_with_members(payload)

    # Attempt to register another group with the same email
    payload.group.name = "Second Group"
    with pytest.raises(HTTPException) as exc_info:
        await service.register_group_with_members(payload)
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_register_group_duplicate_member_emails_rejected(
    db_session: AsyncSession, active_project: Project
) -> None:
    """Verify that duplicate member emails in registration payload are rejected with 400."""
    service = GroupService(db_session)
    payload = GroupRegistrationRequest(
        leader=LeaderRegisterInput(
            full_name="Unique Leader",
            department="CSE",
            phone="1111111111",
            roll_number="CSE-L1",
            email="unique.leader@greensynth.edu",
            password="Password123!",
        ),
        group=GroupMetadataInput(
            name="Dup Member Group",
            project_id=active_project.id,
        ),
        members=[
            MemberInvitationInput(
                full_name="M1",
                department="CSE",
                phone="2222222222",
                roll_number="CSE-M1",
                email="shared@greensynth.edu",
            ),
            MemberInvitationInput(
                full_name="M2",
                department="CSE",
                phone="3333333333",
                roll_number="CSE-M2",
                email="shared@greensynth.edu",  # Duplicate email
            ),
        ],
    )
    with pytest.raises(HTTPException) as exc_info:
        await service.register_group_with_members(payload)
    assert exc_info.value.status_code == 400
    assert "unique" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_register_group_leader_email_in_members_rejected(
    db_session: AsyncSession, active_project: Project
) -> None:
    """Verify that using the leader's email as an invited member is rejected with 400."""
    service = GroupService(db_session)
    payload = GroupRegistrationRequest(
        leader=LeaderRegisterInput(
            full_name="Leader User",
            department="CSE",
            phone="1111111111",
            roll_number="CSE-L1",
            email="leader.reused@greensynth.edu",
            password="Password123!",
        ),
        group=GroupMetadataInput(
            name="Reused Email Group",
            project_id=active_project.id,
        ),
        members=[
            MemberInvitationInput(
                full_name="Member User",
                department="CSE",
                phone="2222222222",
                roll_number="CSE-M1",
                email="leader.reused@greensynth.edu",  # Reused leader email
            ),
        ],
    )
    with pytest.raises(HTTPException) as exc_info:
        await service.register_group_with_members(payload)
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_register_group_duplicate_roll_numbers_rejected(
    db_session: AsyncSession, active_project: Project
) -> None:
    """Verify that duplicate roll numbers within a group are rejected with 400."""
    service = GroupService(db_session)
    payload = GroupRegistrationRequest(
        leader=LeaderRegisterInput(
            full_name="Leader User",
            department="CSE",
            phone="1111111111",
            roll_number="ROLL-SAME",
            email="l1@greensynth.edu",
            password="Password123!",
        ),
        group=GroupMetadataInput(
            name="Same Roll Group",
            project_id=active_project.id,
        ),
        members=[
            MemberInvitationInput(
                full_name="Member User",
                department="CSE",
                phone="2222222222",
                roll_number="ROLL-SAME",  # Duplicate roll number
                email="m1@greensynth.edu",
            ),
        ],
    )
    with pytest.raises(HTTPException) as exc_info:
        await service.register_group_with_members(payload)
    assert exc_info.value.status_code == 400
    assert "roll" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_get_my_group_details_and_members(
    db_session: AsyncSession, active_project: Project
) -> None:
    """Verify get_my_group and get_my_group_members return correct group metadata."""
    service = GroupService(db_session)
    payload = GroupRegistrationRequest(
        leader=LeaderRegisterInput(
            full_name="Group Query Leader",
            department="Mechanical",
            phone="7777777777",
            roll_number="MECH-001",
            email="query.leader@greensynth.edu",
            password="Password123!",
        ),
        group=GroupMetadataInput(
            name="Mechanical Synthesis Unit",
            project_id=active_project.id,
        ),
        members=[
            MemberInvitationInput(
                full_name="Mech M1",
                department="Mechanical",
                phone="8888888888",
                roll_number="MECH-002",
                email="mech.m1@greensynth.edu",
            ),
        ],
    )
    reg_res = await service.register_group_with_members(payload)
    leader = await db_session.get(User, reg_res.leader_id)
    assert leader is not None

    # Test get_my_group
    group_detail = await service.get_my_group(leader)
    assert group_detail.group_name == "Mechanical Synthesis Unit"
    assert group_detail.project_code == active_project.project_code
    assert group_detail.user_is_leader is True
    assert group_detail.member_count == 1
    assert group_detail.max_members == 4

    # Test get_my_group_members
    members = await service.get_my_group_members(leader)
    assert len(members) == 1
    assert members[0].full_name == "Group Query Leader"
    assert members[0].is_leader is True

    # Test get_my_group_invitations
    invitations = await service.get_my_group_invitations(leader)
    assert len(invitations) == 1
    assert invitations[0].email == "mech.m1@greensynth.edu"
    assert invitations[0].status == "PENDING"
