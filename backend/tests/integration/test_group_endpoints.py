"""
GreenSynth Analytics — Integration Tests: Group & Invitation Endpoints

Verifies:
  - POST /api/v1/groups/register
  - GET /api/v1/groups/me
  - GET /api/v1/groups/me/members
  - GET /api/v1/groups/me/invitations
  - POST /api/v1/groups/me/invitations
  - GET /api/v1/auth/invitations/validate
  - POST /api/v1/auth/invitations/accept
  - POST /api/v1/auth/invitations/{id}/resend
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_secure_invitation_token, hash_invitation_token
from app.models.group_membership import GroupMembership, MembershipStatus
from app.models.invitation import Invitation, InvitationStatus
from app.models.project import Project, ProjectStatus
from app.models.research_group import GroupStatus, ResearchGroup
from app.models.user import User


@pytest.fixture
async def active_project(db_session: AsyncSession) -> Project:
    """Fixture providing an active project."""
    proj = Project(
        project_code=f"P8-GRP-{uuid.uuid4().hex[:6].upper()}",
        name="Spray Pyrolysis Integration Project",
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
async def test_full_group_registration_and_member_onboarding_lifecycle(
    client: AsyncClient,
    db_session: AsyncSession,
    active_project: Project,
) -> None:
    """End-to-end integration test of group registration, token validation, and member acceptance."""
    # 1. Register Group with Leader and 3 Members
    register_payload = {
        "leader": {
            "full_name": "Dr. Sarah Connor",
            "department": "Nanotechnology",
            "phone": "9988776655",
            "roll_number": "NANO-001",
            "email": "sarah.connor@greensynth.edu",
            "password": "LeaderStrongPassword123!",
            "confirm_password": "LeaderStrongPassword123!",
        },
        "group": {
            "name": "Nanotech Pioneers Unit",
            "project_id": str(active_project.id),
        },
        "members": [
            {
                "full_name": "John Member",
                "department": "Nanotechnology",
                "phone": "9988776656",
                "roll_number": "NANO-002",
                "email": "john.member@greensynth.edu",
            },
            {
                "full_name": "Kyle Member",
                "department": "Nanotechnology",
                "phone": "9988776657",
                "roll_number": "NANO-003",
                "email": "kyle.member@greensynth.edu",
            },
            {
                "full_name": "T-800 Member",
                "department": "Cybernetics",
                "phone": "9988776658",
                "roll_number": "CYBER-001",
                "email": "t800.member@greensynth.edu",
            },
        ],
    }

    res = await client.post("/api/v1/groups/register", json=register_payload)
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["group_name"] == "Nanotech Pioneers Unit"
    assert data["project_code"] == active_project.project_code
    assert len(data["invitations"]) == 3
    leader_token = data["access_token"]
    assert leader_token is not None

    headers = {"Authorization": f"Bearer {leader_token}"}

    # 2. Query GET /api/v1/groups/me
    me_res = await client.get("/api/v1/groups/me", headers=headers)
    assert me_res.status_code == 200
    group_data = me_res.json()["data"]
    assert group_data["group_name"] == "Nanotech Pioneers Unit"
    assert group_data["user_is_leader"] is True
    assert group_data["member_count"] == 1
    assert group_data["max_members"] == 4

    # 3. Query GET /api/v1/groups/me/members
    members_res = await client.get("/api/v1/groups/me/members", headers=headers)
    assert members_res.status_code == 200
    members = members_res.json()["data"]
    assert len(members) == 1
    assert members[0]["full_name"] == "Dr. Sarah Connor"
    assert members[0]["is_leader"] is True

    # 4. Query GET /api/v1/groups/me/invitations
    inv_res = await client.get("/api/v1/groups/me/invitations", headers=headers)
    assert inv_res.status_code == 200
    invitations = inv_res.json()["data"]
    assert len(invitations) == 3
    first_inv_id = invitations[0]["id"]

    # 5. Leader Resends Invitation
    resend_res = await client.post(
        f"/api/v1/auth/invitations/{first_inv_id}/resend", headers=headers
    )
    assert resend_res.status_code == 200
    assert resend_res.json()["data"]["status"] == "PENDING"


@pytest.mark.asyncio
async def test_invitation_validate_and_accept_endpoints(
    client: AsyncClient,
    db_session: AsyncSession,
    active_project: Project,
) -> None:
    """Verify GET /api/v1/auth/invitations/validate and POST /api/v1/auth/invitations/accept."""
    # Create Leader & Group
    leader = User(
        username="integration_leader",
        email="int.leader@greensynth.edu",
        full_name="Integration Leader",
        department="Chemical",
        phone="5555555555",
        roll_number="CHEM-LDR",
        role="RESEARCHER",
        password_hash="hash",
    )
    db_session.add(leader)
    await db_session.flush()

    group = ResearchGroup(
        name="Integration Group",
        project_id=active_project.id,
        leader_user_id=leader.id,
        status=GroupStatus.ACTIVE.value,
    )
    db_session.add(group)
    await db_session.flush()

    membership = GroupMembership(
        group_id=group.id,
        user_id=leader.id,
        is_leader=True,
        status=MembershipStatus.ACTIVE.value,
    )
    db_session.add(membership)

    raw_token = generate_secure_invitation_token()
    invitation = Invitation(
        group_id=group.id,
        email="student.onboard@greensynth.edu",
        full_name="Student Onboard",
        department="Chemical",
        phone="5555555556",
        roll_number="CHEM-STU",
        token_hash=hash_invitation_token(raw_token),
        status=InvitationStatus.PENDING.value,
        expires_at=datetime.now(timezone.utc) + timedelta(days=2),
    )
    db_session.add(invitation)
    await db_session.flush()

    # 1. Validate Token
    val_res = await client.get(
        f"/api/v1/auth/invitations/validate?token={raw_token}"
    )
    assert val_res.status_code == 200
    val_data = val_res.json()["data"]
    assert val_data["valid"] is True
    assert val_data["group_name"] == "Integration Group"
    assert val_data["project_code"] == active_project.project_code
    assert val_data["invited_email"] == "student.onboard@greensynth.edu"

    # 2. Accept Invitation
    accept_payload = {
        "token": raw_token,
        "password": "MemberSecurePassword123!",
        "confirm_password": "MemberSecurePassword123!",
    }
    acc_res = await client.post("/api/v1/auth/invitations/accept", json=accept_payload)
    assert acc_res.status_code == 200
    acc_data = acc_res.json()["data"]
    assert acc_data["access_token"] is not None
    assert acc_data["user"]["email"] == "student.onboard@greensynth.edu"

    member_token = acc_data["access_token"]
    member_headers = {"Authorization": f"Bearer {member_token}"}

    # 3. Check /groups/me as Member
    my_group_res = await client.get("/api/v1/groups/me", headers=member_headers)
    assert my_group_res.status_code == 200
    assert my_group_res.json()["data"]["user_is_leader"] is False
    assert my_group_res.json()["data"]["member_count"] == 2  # Leader + this member
