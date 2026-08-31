"""
GreenSynth Analytics — Research Group & Member Invitation Pydantic Schemas

Defines schemas for multi-step group registration, member invitations,
invitation token validation, invitation acceptance, and group status queries.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ── Input Schemas ───────────────────────────────────────────

class MemberInvitationInput(BaseModel):
    """Details of a student invited by the Group Leader."""

    full_name: str = Field(..., min_length=1, max_length=255, description="Full Name of the invited student")
    department: str = Field(..., min_length=1, max_length=128, description="Academic Department (e.g. CSE, ENTC)")
    phone: str = Field(..., min_length=1, max_length=32, description="Contact Phone Number")
    roll_number: str = Field(..., min_length=1, max_length=64, description="Departmental Roll Number")
    email: str = Field(..., description="Student Email Address")


class CreateInvitationRequest(BaseModel):
    """Payload submitted by a Group Leader or Admin to invite an individual student."""

    full_name: str = Field(..., min_length=1, max_length=255, description="Full Name of the invited student")
    email: str = Field(..., description="Student Email Address")
    department: str = Field(default="Materials Science & Semiconductor Engineering", max_length=128)
    phone: str = Field(default="N/A", max_length=32)
    roll_number: str = Field(default="N/A", max_length=64)


class LeaderRegisterInput(BaseModel):
    """Personal registration details for the Group Leader."""

    full_name: str = Field(..., min_length=1, max_length=255, description="Full Name of the Group Leader")
    department: str = Field(..., min_length=1, max_length=128, description="Academic Department (e.g. CSE, ENTC)")
    phone: str = Field(..., min_length=1, max_length=32, description="Contact Phone Number")
    roll_number: str = Field(..., min_length=1, max_length=64, description="Departmental Roll Number")
    email: str = Field(..., description="Leader Email Address")
    password: str = Field(..., min_length=8, max_length=128, description="Account Password (min 8 characters)")
    confirm_password: str | None = Field(default=None, description="Password confirmation")


class GroupMetadataInput(BaseModel):
    """Research Group metadata and project assignment."""

    name: str = Field(..., min_length=1, max_length=255, description="Research Group Name (e.g. Green Innovators)")
    project_id: UUID = Field(..., description="Target Synthesis Project UUID (P1 through P8)")


class GroupRegistrationRequest(BaseModel):
    """Complete multi-member Group Registration request payload."""

    leader: LeaderRegisterInput = Field(..., description="Group Leader credentials & profile")
    group: GroupMetadataInput = Field(..., description="Research Group details & project binding")
    members: list[MemberInvitationInput] = Field(
        ...,
        min_length=1,
        max_length=3,
        description="List of remaining group members to invite (standard is 3 members)",
    )


class AcceptInvitationPayload(BaseModel):
    """Payload submitted by an invited student to onboard and set their password."""

    token: str = Field(..., min_length=1, description="Raw URL-safe onboarding token")
    password: str = Field(..., min_length=8, max_length=128, description="New account password")
    confirm_password: str | None = Field(default=None, description="Password confirmation")
    full_name: str | None = Field(default=None, max_length=255, description="Optional updated full name")


# ── Response Schemas ────────────────────────────────────────

class InvitationSummary(BaseModel):
    """Summary of an onboarding invitation record (excludes secret tokens)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    department: str
    phone: str
    roll_number: str
    status: str
    expires_at: datetime
    created_at: datetime
    accepted_at: datetime | None = None


class GroupRegistrationResponse(BaseModel):
    """Response returned upon successful atomic group registration."""

    group_id: UUID
    group_name: str
    project_id: UUID
    project_code: str
    leader_id: UUID
    leader_name: str
    leader_email: str
    invitations: list[InvitationSummary] = Field(default_factory=list)
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class GroupDetailResponse(BaseModel):
    """Details of the authenticated user's research group."""

    model_config = ConfigDict(from_attributes=True)

    group_id: UUID
    group_name: str
    project_id: UUID
    project_code: str
    project_name: str
    leader_id: UUID
    leader_name: str
    leader_email: str
    member_count: int
    max_members: int
    user_is_leader: bool
    created_at: datetime


class GroupMemberResponse(BaseModel):
    """Representation of an active research group member."""

    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    full_name: str
    department: str
    roll_number: str
    email: str
    is_leader: bool
    status: str
    joined_at: datetime


class InvitationValidationResponse(BaseModel):
    """Safe invitation details returned to validate the onboarding token."""

    valid: bool
    group_name: str
    project_id: UUID
    project_code: str
    project_name: str
    invited_name: str
    invited_email: str
    department: str
    roll_number: str
    leader_name: str
    expires_at: datetime
