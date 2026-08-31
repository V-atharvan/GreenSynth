"""
GreenSynth Analytics — Authentication Pydantic Schemas

Defines request and response schemas for registration, login, invitation acceptance,
and user profile retrieval. Sensitive fields (like password_hash) are never exposed.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ── User Representations ────────────────────────────────────

class UserRead(BaseModel):
    """Public user identity representation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    email: str
    full_name: str
    department: str
    phone: str
    roll_number: str
    role: str
    account_type: str = "STUDENT"
    is_active: bool
    created_at: datetime


class MembershipRead(BaseModel):
    """Membership details for an authenticated user within a research group."""

    model_config = ConfigDict(from_attributes=True)

    group_id: UUID
    group_name: str
    is_leader: bool
    status: str
    project_id: UUID
    project_code: str
    joined_at: datetime


class UserProfile(BaseModel):
    """Detailed user profile with all active research group memberships."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    email: str
    full_name: str
    department: str
    phone: str
    roll_number: str
    role: str
    account_type: str = "STUDENT"
    is_active: bool
    created_at: datetime
    memberships: list[MembershipRead] = Field(default_factory=list)


# ── Authentication Request & Response Payloads ──────────────

class TokenResponse(BaseModel):
    """Authentication success payload with access token."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserRead


class LoginRequest(BaseModel):
    """Login credentials payload."""

    email: str = Field(..., description="Student / Researcher email address")
    password: str = Field(..., min_length=1, description="Account password")


class LeaderRegisterRequest(BaseModel):
    """Registration payload for a new Group Leader."""

    full_name: str = Field(..., min_length=1, max_length=255, description="Full Name")
    department: str = Field(..., min_length=1, max_length=128, description="Academic Department (e.g. CSE, ENTC)")
    phone: str = Field(..., min_length=1, max_length=32, description="Contact Phone Number")
    password: str = Field(..., min_length=8, max_length=128, description="Account Password (min 8 characters)")
    project_id: UUID = Field(..., description="Selected Project UUID (P1 through P8)")
    roll_number: str = Field(..., min_length=1, max_length=64, description="Departmental Roll Number")
    email: str = Field(..., description="Student Email Address")
    group_name: str | None = Field(default=None, max_length=255, description="Optional custom group name")


class AcceptInvitationRequest(BaseModel):
    """Invitation onboarding payload for invited group members."""

    token: str = Field(..., min_length=1, description="Raw onboarding token received by the invited member")
    password: str = Field(..., min_length=8, max_length=128, description="New account password (min 8 characters)")


class ProfileUpdateRequest(BaseModel):
    """Payload for updating permitted user profile fields."""

    full_name: str | None = Field(default=None, min_length=1, max_length=255, description="Full Name")
    department: str | None = Field(default=None, max_length=128, description="Academic Department")
    phone: str | None = Field(default=None, max_length=32, description="Contact Phone Number")
    roll_number: str | None = Field(default=None, max_length=64, description="Departmental Roll Number")


class ChangePasswordRequest(BaseModel):
    """Payload for user password change."""

    current_password: str = Field(..., min_length=1, description="Current account password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New account password (min 8 characters)")
    confirm_password: str = Field(..., min_length=8, max_length=128, description="Confirmation of new password")


class UserStatusUpdateRequest(BaseModel):
    """Payload for administrative user status toggling."""

    is_active: bool = Field(..., description="Active status flag")

