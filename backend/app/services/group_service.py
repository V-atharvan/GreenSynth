"""
GreenSynth Analytics — Research Group Service

Handles:
  1. Atomic multi-member Group Registration (Leader + Group + Memberships + Invitations).
  2. Research group details and capacity querying.
  3. Group member listings and invitation status management.
  4. Adding additional members within the configured maximum capacity.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    generate_secure_invitation_token,
    hash_invitation_token,
    hash_password,
)
from app.models.group_membership import GroupMembership, MembershipStatus
from app.models.invitation import Invitation, InvitationStatus
from app.models.project import Project, ProjectStatus
from app.models.research_group import GroupStatus, ResearchGroup
from app.models.user import User
from app.schemas.group import (
    GroupDetailResponse,
    GroupMemberResponse,
    GroupRegistrationRequest,
    GroupRegistrationResponse,
    InvitationSummary,
    MemberInvitationInput,
)
from app.services.audit_service import AuditService
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


class GroupService:
    """Service layer for research group management and multi-member onboarding."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.settings = get_settings()
        self.audit = AuditService(db)
        self.email_service = EmailService()

    async def register_group_with_members(
        self, payload: GroupRegistrationRequest
    ) -> GroupRegistrationResponse:
        """
        Atomically register a new Group Leader, initialize their Research Group,
        assign the selected Project, create the Leader membership, and generate
        invitations for all remaining members.
        """
        # 1. Normalize and validate emails
        leader_email = payload.leader.email.strip().lower()
        member_emails = [m.email.strip().lower() for m in payload.members]
        all_emails = [leader_email] + member_emails

        if len(set(all_emails)) != len(all_emails):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Leader and member email addresses must all be unique.",
            )

        # 2. Check for duplicate roll numbers in group
        leader_roll = payload.leader.roll_number.strip().upper()
        member_rolls = [m.roll_number.strip().upper() for m in payload.members]
        all_rolls = [leader_roll] + member_rolls

        if len(set(all_rolls)) != len(all_rolls):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Roll numbers must be unique among group members.",
            )

        # 3. Check group capacity
        total_requested = 1 + len(payload.members)
        if total_requested > self.settings.max_group_members:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Total group size ({total_requested}) exceeds the maximum allowed "
                    f"capacity of {self.settings.max_group_members} members."
                ),
            )

        # 4. Check if leader email is already registered
        existing_leader = await self.db.execute(
            select(User).where(User.email == leader_email)
        )
        if existing_leader.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with the Group Leader's email already exists.",
            )

        # 5. Validate project existence and active status
        proj_res = await self.db.execute(
            select(Project).where(Project.id == payload.group.project_id)
        )
        project = proj_res.scalar_one_or_none()
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Selected project '{payload.group.project_id}' does not exist.",
            )
        if project.status != ProjectStatus.ACTIVE.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Project '{project.project_code}' is {project.status} and cannot be assigned.",
            )

        # 6. Check if group name already exists
        group_name = payload.group.name.strip()
        if not group_name:
            group_name = f"{project.project_code}-{leader_roll}"

        grp_check = await self.db.execute(
            select(ResearchGroup).where(ResearchGroup.name == group_name)
        )
        if grp_check.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A research group named '{group_name}' already exists.",
            )

        try:
            # 7. Create Leader User
            base_username = leader_email.split("@")[0][:60]
            u_check = await self.db.execute(
                select(User).where(User.username == base_username)
            )
            if u_check.scalar_one_or_none() is not None:
                base_username = f"{base_username[:50]}_{uuid.uuid4().hex[:6]}"

            leader = User(
                username=base_username,
                email=leader_email,
                full_name=payload.leader.full_name.strip(),
                department=payload.leader.department.strip(),
                phone=payload.leader.phone.strip(),
                roll_number=payload.leader.roll_number.strip(),
                role="RESEARCHER",
                password_hash=hash_password(payload.leader.password),
                is_active=True,
            )
            self.db.add(leader)
            await self.db.flush()

            # 8. Create ResearchGroup
            group = ResearchGroup(
                name=group_name,
                project_id=project.id,
                leader_user_id=leader.id,
                status=GroupStatus.ACTIVE.value,
            )
            self.db.add(group)
            await self.db.flush()

            # 9. Create Leader Membership
            leader_membership = GroupMembership(
                group_id=group.id,
                user_id=leader.id,
                is_leader=True,
                status=MembershipStatus.ACTIVE.value,
            )
            self.db.add(leader_membership)
            await self.db.flush()

            # 10. Generate Invitations for Remaining Members
            invitations: list[Invitation] = []
            invitation_tokens: list[tuple[Invitation, str]] = []

            for member_data in payload.members:
                raw_token = generate_secure_invitation_token()
                token_hash = hash_invitation_token(raw_token)
                expires_at = datetime.now(timezone.utc) + timedelta(
                    hours=self.settings.invitation_expiry_hours
                )

                inv = Invitation(
                    group_id=group.id,
                    email=member_data.email.strip().lower(),
                    full_name=member_data.full_name.strip(),
                    department=member_data.department.strip(),
                    phone=member_data.phone.strip(),
                    roll_number=member_data.roll_number.strip(),
                    token_hash=token_hash,
                    status=InvitationStatus.PENDING.value,
                    expires_at=expires_at,
                )
                self.db.add(inv)
                invitations.append(inv)
                invitation_tokens.append((inv, raw_token))

            await self.db.flush()

            # 11. Dispatch invitation emails (fire-and-forget, non-blocking)
            async def _dispatch_emails():
                """Background task: send invitation emails without blocking registration."""
                for inv_rec, raw_tok in invitation_tokens:
                    try:
                        await self.email_service.send_group_invitation(
                            to_email=inv_rec.email,
                            recipient_name=inv_rec.full_name,
                            group_name=group.name,
                            project_name=project.name,
                            project_code=project.project_code,
                            leader_name=leader.full_name,
                            raw_token=raw_tok,
                            expires_at=inv_rec.expires_at,
                        )
                    except Exception as email_exc:
                        logger.error(
                            "Email dispatch failed for invitation %s to %s: %s",
                            inv_rec.id, inv_rec.email, email_exc,
                        )

            asyncio.create_task(_dispatch_emails())

            # 12. Record Audit Trail
            await self.audit.log(
                entity_type="ResearchGroup",
                entity_id=group.id,
                action="REGISTER_GROUP",
                project_id=project.id,
                user_id=leader.id,
                notes=(
                    f"Created group '{group.name}' for {project.project_code} "
                    f"with {len(invitations)} member invitations"
                ),
            )

        except IntegrityError as exc:
            logger.warning("Integrity error during group registration: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Registration conflict: email, username, or group name already exists.",
            ) from exc

        # 13. Generate JWT for the Leader
        token = create_access_token(leader.id, account_type=leader.account_type)
        expires_seconds = self.settings.access_token_expire_minutes * 60

        return GroupRegistrationResponse(
            group_id=group.id,
            group_name=group.name,
            project_id=project.id,
            project_code=project.project_code,
            leader_id=leader.id,
            leader_name=leader.full_name,
            leader_email=leader.email,
            invitations=[InvitationSummary.model_validate(inv) for inv in invitations],
            access_token=token,
            token_type="bearer",
            expires_in=expires_seconds,
        )

    async def get_my_group(self, current_user: User) -> GroupDetailResponse:
        """Fetch the active research group details for the current user."""
        q = (
            select(GroupMembership, ResearchGroup, Project, User)
            .join(ResearchGroup, GroupMembership.group_id == ResearchGroup.id)
            .join(Project, ResearchGroup.project_id == Project.id)
            .join(User, ResearchGroup.leader_user_id == User.id)
            .where(
                GroupMembership.user_id == current_user.id,
                GroupMembership.status == MembershipStatus.ACTIVE.value,
            )
        )
        res = await self.db.execute(q)
        row = res.first()

        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You do not currently belong to an active research group.",
            )

        membership, group, project, leader = row

        # Count active members
        count_res = await self.db.execute(
            select(func.count(GroupMembership.id)).where(
                GroupMembership.group_id == group.id,
                GroupMembership.status == MembershipStatus.ACTIVE.value,
            )
        )
        member_count = count_res.scalar() or 0

        return GroupDetailResponse(
            group_id=group.id,
            group_name=group.name,
            project_id=project.id,
            project_code=project.project_code,
            project_name=project.name,
            leader_id=leader.id,
            leader_name=leader.full_name,
            leader_email=leader.email,
            member_count=member_count,
            max_members=self.settings.max_group_members,
            user_is_leader=membership.is_leader,
            created_at=group.created_at,
        )

    async def get_my_group_members(
        self, current_user: User
    ) -> list[GroupMemberResponse]:
        """Fetch all active members of the current user's research group."""
        mem_q = select(GroupMembership).where(
            GroupMembership.user_id == current_user.id,
            GroupMembership.status == MembershipStatus.ACTIVE.value,
        )
        mem_res = await self.db.execute(mem_q)
        my_membership = mem_res.scalar_one_or_none()

        if my_membership is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You do not belong to an active research group.",
            )

        q = (
            select(GroupMembership, User)
            .join(User, GroupMembership.user_id == User.id)
            .where(
                GroupMembership.group_id == my_membership.group_id,
                GroupMembership.status == MembershipStatus.ACTIVE.value,
            )
            .order_by(GroupMembership.is_leader.desc(), GroupMembership.joined_at.asc())
        )
        res = await self.db.execute(q)
        rows = res.all()

        return [
            GroupMemberResponse(
                user_id=u.id,
                full_name=u.full_name,
                department=u.department,
                roll_number=u.roll_number,
                email=u.email,
                is_leader=m.is_leader,
                status=m.status,
                joined_at=m.joined_at,
            )
            for m, u in rows
        ]

    async def get_my_group_invitations(
        self, current_user: User
    ) -> list[InvitationSummary]:
        """Fetch all invitation records for the current user's research group."""
        mem_q = select(GroupMembership).where(
            GroupMembership.user_id == current_user.id,
            GroupMembership.status == MembershipStatus.ACTIVE.value,
        )
        mem_res = await self.db.execute(mem_q)
        my_membership = mem_res.scalar_one_or_none()

        if my_membership is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You do not belong to an active research group.",
            )

        q = (
            select(Invitation)
            .where(Invitation.group_id == my_membership.group_id)
            .order_by(Invitation.created_at.desc())
        )
        res = await self.db.execute(q)
        invitations = res.scalars().all()

        return [InvitationSummary.model_validate(inv) for inv in invitations]

    async def invite_member_to_my_group(
        self, current_user: User, payload: MemberInvitationInput
    ) -> InvitationSummary:
        """
        Send an additional invitation to a student if the group is under max capacity.
        Restricted to the Group Leader.
        """
        mem_q = select(GroupMembership, ResearchGroup, Project).join(
            ResearchGroup, GroupMembership.group_id == ResearchGroup.id
        ).join(
            Project, ResearchGroup.project_id == Project.id
        ).where(
            GroupMembership.user_id == current_user.id,
            GroupMembership.status == MembershipStatus.ACTIVE.value,
        )
        mem_res = await self.db.execute(mem_q)
        row = mem_res.first()

        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You do not belong to an active research group.",
            )

        membership, group, project = row

        if not membership.is_leader:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the Group Leader can invite new members.",
            )

        # Capacity check
        count_res = await self.db.execute(
            select(func.count(GroupMembership.id)).where(
                GroupMembership.group_id == group.id,
                GroupMembership.status == MembershipStatus.ACTIVE.value,
            )
        )
        current_members = count_res.scalar() or 0
        if current_members >= self.settings.max_group_members:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"This research group has reached its maximum capacity of {self.settings.max_group_members} members.",
            )

        clean_email = payload.email.strip().lower()
        # Check if already pending invitation
        inv_check = await self.db.execute(
            select(Invitation).where(
                Invitation.group_id == group.id,
                Invitation.email == clean_email,
                Invitation.status == InvitationStatus.PENDING.value,
            )
        )
        if inv_check.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A pending invitation already exists for this email address.",
            )

        raw_token = generate_secure_invitation_token()
        token_hash = hash_invitation_token(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(
            hours=self.settings.invitation_expiry_hours
        )

        invitation = Invitation(
            group_id=group.id,
            email=clean_email,
            full_name=payload.full_name.strip(),
            department=payload.department.strip(),
            phone=payload.phone.strip(),
            roll_number=payload.roll_number.strip(),
            token_hash=token_hash,
            status=InvitationStatus.PENDING.value,
            expires_at=expires_at,
        )
        self.db.add(invitation)
        await self.db.flush()

        # Send email
        await self.email_service.send_group_invitation(
            to_email=invitation.email,
            recipient_name=invitation.full_name,
            group_name=group.name,
            project_name=project.name,
            project_code=project.project_code,
            leader_name=current_user.full_name,
            raw_token=raw_token,
            expires_at=invitation.expires_at,
        )

        return InvitationSummary.model_validate(invitation)

    async def list_all_groups(self) -> list[GroupDetailResponse]:
        """Fetch all research groups across all projects (Admin)."""
        q = (
            select(ResearchGroup, Project, User)
            .join(Project, ResearchGroup.project_id == Project.id)
            .join(User, ResearchGroup.leader_user_id == User.id)
            .order_by(ResearchGroup.created_at.desc())
        )
        res = await self.db.execute(q)
        rows = res.all()

        results: list[GroupDetailResponse] = []
        for group, project, leader in rows:
            count_res = await self.db.execute(
                select(func.count(GroupMembership.id)).where(
                    GroupMembership.group_id == group.id,
                    GroupMembership.status == MembershipStatus.ACTIVE.value,
                )
            )
            member_count = count_res.scalar() or 0

            results.append(
                GroupDetailResponse(
                    group_id=group.id,
                    group_name=group.name,
                    project_id=project.id,
                    project_code=project.project_code,
                    project_name=project.name,
                    leader_id=leader.id,
                    leader_name=leader.full_name,
                    leader_email=leader.email,
                    member_count=member_count,
                    max_members=self.settings.max_group_members,
                    user_is_leader=False,
                    created_at=group.created_at,
                )
            )
        return results

    async def get_group_by_id(self, group_id: uuid.UUID) -> GroupDetailResponse:
        """Fetch group details by group UUID."""
        q = (
            select(ResearchGroup, Project, User)
            .join(Project, ResearchGroup.project_id == Project.id)
            .join(User, ResearchGroup.leader_user_id == User.id)
            .where(ResearchGroup.id == group_id)
        )
        res = await self.db.execute(q)
        row = res.first()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research group not found.")

        group, project, leader = row
        count_res = await self.db.execute(
            select(func.count(GroupMembership.id)).where(
                GroupMembership.group_id == group.id,
                GroupMembership.status == MembershipStatus.ACTIVE.value,
            )
        )
        member_count = count_res.scalar() or 0

        return GroupDetailResponse(
            group_id=group.id,
            group_name=group.name,
            project_id=project.id,
            project_code=project.project_code,
            project_name=project.name,
            leader_id=leader.id,
            leader_name=leader.full_name,
            leader_email=leader.email,
            member_count=member_count,
            max_members=self.settings.max_group_members,
            user_is_leader=False,
            created_at=group.created_at,
        )

    async def get_group_members_by_id(self, group_id: uuid.UUID) -> list[GroupMemberResponse]:
        """Fetch all active members of a specific research group."""
        q = (
            select(GroupMembership, User)
            .join(User, GroupMembership.user_id == User.id)
            .where(
                GroupMembership.group_id == group_id,
                GroupMembership.status == MembershipStatus.ACTIVE.value,
            )
            .order_by(GroupMembership.is_leader.desc(), GroupMembership.joined_at.asc())
        )
        res = await self.db.execute(q)
        rows = res.all()
        return [
            GroupMemberResponse(
                user_id=u.id,
                full_name=u.full_name,
                department=u.department,
                roll_number=u.roll_number,
                email=u.email,
                is_leader=m.is_leader,
                status=m.status,
                joined_at=m.joined_at,
            )
            for m, u in rows
        ]
