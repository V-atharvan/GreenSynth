"""
GreenSynth Analytics — Invitation Service

Handles:
  1. Secure token generation and SHA-256 database hashing.
  2. Safe token validation for frontend pre-checks.
  3. Transactional member onboarding and account activation.
  4. Leader-controlled invitation re-issuance and email dispatch.
"""

from __future__ import annotations

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
from app.models.project import Project
from app.models.research_group import GroupStatus, ResearchGroup
from app.models.user import User
from app.schemas.auth import TokenResponse, UserRead
from app.schemas.group import (
    AcceptInvitationPayload,
    CreateInvitationRequest,
    InvitationSummary,
    InvitationValidationResponse,
)
from app.services.audit_service import AuditService
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


class InvitationService:
    """Service layer for invitation validation, acceptance, and re-issuance."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.settings = get_settings()
        self.audit = AuditService(db)
        self.email_service = EmailService()

    async def validate_invitation(self, raw_token: str) -> InvitationValidationResponse:
        """
        Validate an onboarding token and return safe, sanitized group & project metadata.
        Excludes passwords, token hashes, and internal records.
        """
        clean_token = raw_token.strip()
        if not clean_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation token is required.",
            )

        token_hash = hash_invitation_token(clean_token)

        q = (
            select(Invitation, ResearchGroup, Project, User)
            .join(ResearchGroup, Invitation.group_id == ResearchGroup.id)
            .join(Project, ResearchGroup.project_id == Project.id)
            .join(User, ResearchGroup.leader_user_id == User.id)
            .where(Invitation.token_hash == token_hash)
        )
        res = await self.db.execute(q)
        row = res.first()

        if row is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired invitation token.",
            )

        invitation, group, project, leader = row

        # Check status
        if invitation.status != InvitationStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"This invitation is no longer pending (status: {invitation.status}).",
            )

        # Check expiration
        exp = invitation.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp < datetime.now(timezone.utc):
            invitation.status = InvitationStatus.EXPIRED.value
            await self.db.flush()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This invitation token has expired. Please ask your group leader to resend it.",
            )

        # Check group capacity
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

        return InvitationValidationResponse(
            valid=True,
            group_name=group.name,
            project_id=project.id,
            project_code=project.project_code,
            project_name=project.name,
            invited_name=invitation.full_name,
            invited_email=invitation.email,
            department=invitation.department,
            roll_number=invitation.roll_number,
            leader_name=leader.full_name,
            expires_at=invitation.expires_at,
        )

    async def accept_invitation(
        self, payload: AcceptInvitationPayload
    ) -> TokenResponse:
        """
        Accept an invitation, activate/create student user account, assign group membership,
        and return an authenticated JWT session.
        """
        if len(payload.password) < 8:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Password must be at least 8 characters in length.",
            )

        if payload.confirm_password and payload.password != payload.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Passwords do not match.",
            )

        token_hash = hash_invitation_token(payload.token.strip())

        q = (
            select(Invitation, ResearchGroup, Project)
            .join(ResearchGroup, Invitation.group_id == ResearchGroup.id)
            .join(Project, ResearchGroup.project_id == Project.id)
            .where(Invitation.token_hash == token_hash)
        )
        res = await self.db.execute(q)
        row = res.first()

        if row is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired invitation token.",
            )

        invitation, group, project = row

        if invitation.status == InvitationStatus.ACCEPTED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This invitation has already been accepted.",
            )

        if invitation.status == InvitationStatus.CANCELLED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This invitation is no longer active.",
            )

        if invitation.status != InvitationStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"This invitation is no longer pending (status: {invitation.status}).",
            )

        exp = invitation.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp < datetime.now(timezone.utc):
            invitation.status = InvitationStatus.EXPIRED.value
            await self.db.flush()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This invitation token has expired.",
            )

        # Enforce capacity
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

        norm_email = invitation.email.strip().lower()

        try:
            # Check if an account with this email already exists
            user_res = await self.db.execute(
                select(User).where(func.lower(User.email) == norm_email)
            )
            user = user_res.scalar_one_or_none()

            if user is None:
                base_username = norm_email.split("@")[0][:60]
                u_check = await self.db.execute(
                    select(User).where(User.username == base_username)
                )
                if u_check.scalar_one_or_none() is not None:
                    base_username = f"{base_username[:50]}_{uuid.uuid4().hex[:6]}"

                user = User(
                    username=base_username,
                    email=norm_email,
                    full_name=payload.full_name or invitation.full_name,
                    department=invitation.department,
                    phone=invitation.phone,
                    roll_number=invitation.roll_number,
                    role="RESEARCHER",
                    password_hash=hash_password(payload.password),
                    is_active=True,
                )
                self.db.add(user)
                await self.db.flush()
            else:
                # Disallow modifying/joining existing Admin accounts via student invite
                if user.is_admin or user.role == "ADMIN":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Administrator accounts cannot be joined via student invitation.",
                    )

                # If existing user, verify they do not already belong to this group
                mem_check = await self.db.execute(
                    select(GroupMembership).where(
                        GroupMembership.group_id == group.id,
                        GroupMembership.user_id == user.id,
                    )
                )
                if mem_check.scalar_one_or_none() is not None:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="User is already a member of this research group.",
                    )
                # Update password and activate account
                user.password_hash = hash_password(payload.password)
                user.is_active = True
                if payload.full_name:
                    user.full_name = payload.full_name
                await self.db.flush()

            # Create GroupMembership (is_leader=False)
            membership = GroupMembership(
                group_id=group.id,
                user_id=user.id,
                is_leader=False,
                status=MembershipStatus.ACTIVE.value,
            )
            self.db.add(membership)

            # Mark invitation as ACCEPTED
            invitation.status = InvitationStatus.ACCEPTED.value
            invitation.accepted_at = datetime.now(timezone.utc)
            await self.db.flush()

            # Record audit event
            await self.audit.log(
                entity_type="Invitation",
                entity_id=invitation.id,
                action="ACCEPT_INVITATION",
                project_id=project.id,
                user_id=user.id,
                notes=f"Student {user.full_name} accepted invitation for {group.name}",
            )

        except HTTPException:
            raise
        except IntegrityError as exc:
            logger.warning("Integrity conflict during invitation acceptance: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Membership conflict: student is already assigned to a group.",
            ) from exc

        token = create_access_token(user.id, account_type=user.account_type)
        expires_seconds = self.settings.access_token_expire_minutes * 60

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=expires_seconds,
            user=UserRead.model_validate(user),
        )

    async def create_invitation(
        self, group_id: uuid.UUID, payload: CreateInvitationRequest, current_user: User
    ) -> InvitationSummary:
        """
        Create a new invitation for a research group and dispatch an onboarding email.
        Authorized for the Group Leader of the group or System Administrators.
        """
        # Fetch group
        group_res = await self.db.execute(
            select(ResearchGroup).where(ResearchGroup.id == group_id)
        )
        group = group_res.scalar_one_or_none()
        if group is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Research group not found.",
            )

        # Authorization: Must be Admin or Group Leader
        if not current_user.is_admin:
            if group.leader_user_id != current_user.id:
                # Also check active membership is_leader
                mem_res = await self.db.execute(
                    select(GroupMembership).where(
                        GroupMembership.group_id == group_id,
                        GroupMembership.user_id == current_user.id,
                        GroupMembership.status == MembershipStatus.ACTIVE.value,
                        GroupMembership.is_leader.is_(True),
                    )
                )
                if mem_res.scalar_one_or_none() is None:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Only the Group Leader or an Administrator can invite members to this research group.",
                    )

        # Email normalization & validation
        norm_email = payload.email.strip().lower()
        try:
            self.email_service.validate_recipient_email(norm_email)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid email address format: {exc}",
            ) from exc

        # Check if user is already an active member of this group
        member_check = await self.db.execute(
            select(GroupMembership)
            .join(User, GroupMembership.user_id == User.id)
            .where(
                GroupMembership.group_id == group.id,
                GroupMembership.status == MembershipStatus.ACTIVE.value,
                User.email == norm_email,
            )
        )
        if member_check.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already an active member of this research group.",
            )

        # Check for active pending invitation for this group + email
        pending_check = await self.db.execute(
            select(Invitation).where(
                Invitation.group_id == group.id,
                Invitation.email == norm_email,
                Invitation.status == InvitationStatus.PENDING.value,
            )
        )
        existing_inv = pending_check.scalar_one_or_none()
        if existing_inv is not None:
            exp = existing_inv.expires_at
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            if exp > datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A pending invitation already exists for this email address. Please use resend if needed.",
                )
            else:
                existing_inv.status = InvitationStatus.EXPIRED.value
                await self.db.flush()

        # Check group capacity
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

        # Generate secure random token and hash
        raw_token = generate_secure_invitation_token()
        token_hash = hash_invitation_token(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(
            hours=self.settings.invitation_expiry_hours
        )

        invitation = Invitation(
            group_id=group.id,
            email=norm_email,
            full_name=payload.full_name.strip(),
            department=payload.department.strip() if payload.department else "Materials Science",
            phone=payload.phone.strip() if payload.phone else "N/A",
            roll_number=payload.roll_number.strip() if payload.roll_number else "N/A",
            token_hash=token_hash,
            status=InvitationStatus.PENDING.value,
            expires_at=expires_at,
        )
        self.db.add(invitation)
        await self.db.flush()

        # Fetch project for email template
        proj_res = await self.db.execute(select(Project).where(Project.id == group.project_id))
        project = proj_res.scalar_one_or_none()

        # Dispatch email
        try:
            await self.email_service.send_group_invitation(
                to_email=norm_email,
                recipient_name=payload.full_name.strip(),
                group_name=group.name,
                project_name=project.name if project else "Synthesis Project",
                project_code=project.project_code if project else "P-SYNTH",
                leader_name=current_user.full_name or "Research Group Leader",
                raw_token=raw_token,
                expires_at=expires_at,
            )
        except Exception as email_exc:
            logger.error("Email dispatch failed for invitation %s to %s: %s", invitation.id, norm_email, email_exc)

        # Audit log
        await self.audit.log(
            entity_type="Invitation",
            entity_id=invitation.id,
            action="CREATE_INVITATION",
            project_id=group.project_id,
            user_id=current_user.id,
            notes=f"User {current_user.email} invited {norm_email} to {group.name}",
        )

        return InvitationSummary.model_validate(invitation)

    async def list_group_invitations(
        self, group_id: uuid.UUID, current_user: User
    ) -> list[InvitationSummary]:
        """
        List all invitations for a specific research group.
        Restricted to the Group Leader or System Administrators.
        """
        group_res = await self.db.execute(
            select(ResearchGroup).where(ResearchGroup.id == group_id)
        )
        group = group_res.scalar_one_or_none()
        if group is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Research group not found.",
            )

        if not current_user.is_admin:
            if group.leader_user_id != current_user.id:
                mem_res = await self.db.execute(
                    select(GroupMembership).where(
                        GroupMembership.group_id == group_id,
                        GroupMembership.user_id == current_user.id,
                        GroupMembership.status == MembershipStatus.ACTIVE.value,
                        GroupMembership.is_leader.is_(True),
                    )
                )
                if mem_res.scalar_one_or_none() is None:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Only the Group Leader or an Administrator can view invitations for this research group.",
                    )

        q = (
            select(Invitation)
            .where(Invitation.group_id == group_id)
            .order_by(Invitation.created_at.desc())
        )
        res = await self.db.execute(q)
        rows = res.scalars().all()
        return [InvitationSummary.model_validate(inv) for inv in rows]

    async def list_all_invitations(self, current_user: User) -> list[InvitationSummary]:
        """
        List all invitations system-wide across all groups (Admin only).
        """
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only System Administrators can view all invitations system-wide.",
            )

        q = select(Invitation).order_by(Invitation.created_at.desc())
        res = await self.db.execute(q)
        rows = res.scalars().all()
        return [InvitationSummary.model_validate(inv) for inv in rows]

    async def resend_invitation(
        self,
        invitation_id: uuid.UUID,
        current_user: User,
        group_id: uuid.UUID | None = None,
    ) -> InvitationSummary:
        """
        Regenerate an invitation token, invalidate previous token, and re-dispatch email.
        Restricted to the Group Leader or System Administrators with a 60s cooldown.
        """
        q = (
            select(Invitation, ResearchGroup, Project)
            .join(ResearchGroup, Invitation.group_id == ResearchGroup.id)
            .join(Project, ResearchGroup.project_id == Project.id)
            .where(Invitation.id == invitation_id)
        )
        if group_id is not None:
            q = q.where(Invitation.group_id == group_id)

        res = await self.db.execute(q)
        row = res.first()

        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation record not found.",
            )

        invitation, group, project = row

        # Authorization check
        if not current_user.is_admin:
            if group.leader_user_id != current_user.id:
                mem_res = await self.db.execute(
                    select(GroupMembership).where(
                        GroupMembership.group_id == group.id,
                        GroupMembership.user_id == current_user.id,
                        GroupMembership.status == MembershipStatus.ACTIVE.value,
                        GroupMembership.is_leader.is_(True),
                    )
                )
                if mem_res.scalar_one_or_none() is None:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Only the Group Leader or an Administrator can resend invitations.",
                    )

        if invitation.status == InvitationStatus.ACCEPTED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot resend an invitation that has already been accepted.",
            )

        # Rate limit cooldown: min 60 seconds between successive resends
        if invitation.updated_at is not None and invitation.created_at is not None:
            last_upd = invitation.updated_at
            if last_upd.tzinfo is None:
                last_upd = last_upd.replace(tzinfo=timezone.utc)
            created = invitation.created_at
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            
            # If invitation has been updated after creation, enforce 60s cooldown from last update
            if abs((last_upd - created).total_seconds()) > 0.0001:
                elapsed = (datetime.now(timezone.utc) - last_upd).total_seconds()
                if elapsed < 60:
                    wait_sec = max(1, int(60 - max(0.0, elapsed)))
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Please wait {wait_sec} seconds before requesting another invitation resend.",
                    )

        # Generate new random token and update expiration
        raw_token = generate_secure_invitation_token()
        invitation.token_hash = hash_invitation_token(raw_token)
        invitation.expires_at = datetime.now(timezone.utc) + timedelta(
            hours=self.settings.invitation_expiry_hours
        )
        invitation.status = InvitationStatus.PENDING.value
        # Ensure updated_at is distinctly after created_at
        invitation.updated_at = datetime.now(timezone.utc) + timedelta(milliseconds=10)
        await self.db.flush()

        # Re-dispatch email
        try:
            await self.email_service.send_group_invitation(
                to_email=invitation.email,
                recipient_name=invitation.full_name,
                group_name=group.name,
                project_name=project.name,
                project_code=project.project_code,
                leader_name=current_user.full_name or "Research Group Leader",
                raw_token=raw_token,
                expires_at=invitation.expires_at,
            )
        except Exception as email_exc:
            logger.error("Email resend failed for invitation %s: %s", invitation.id, email_exc)

        # Log audit record
        await self.audit.log(
            entity_type="Invitation",
            entity_id=invitation.id,
            action="RESEND_INVITATION",
            project_id=project.id,
            user_id=current_user.id,
            notes=f"User {current_user.email} resent invitation to {invitation.email}",
        )

        return InvitationSummary.model_validate(invitation)

    async def revoke_invitation(
        self,
        invitation_id: uuid.UUID,
        current_user: User,
        group_id: uuid.UUID | None = None,
    ) -> InvitationSummary:
        """
        Revoke a pending invitation, invalidating the token.
        Restricted to the Group Leader or System Administrators.
        """
        q = (
            select(Invitation, ResearchGroup)
            .join(ResearchGroup, Invitation.group_id == ResearchGroup.id)
            .where(Invitation.id == invitation_id)
        )
        if group_id is not None:
            q = q.where(Invitation.group_id == group_id)

        res = await self.db.execute(q)
        row = res.first()

        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation record not found.",
            )

        invitation, group = row

        if not current_user.is_admin:
            if group.leader_user_id != current_user.id:
                mem_res = await self.db.execute(
                    select(GroupMembership).where(
                        GroupMembership.group_id == group.id,
                        GroupMembership.user_id == current_user.id,
                        GroupMembership.status == MembershipStatus.ACTIVE.value,
                        GroupMembership.is_leader.is_(True),
                    )
                )
                if mem_res.scalar_one_or_none() is None:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Only the Group Leader or an Administrator can revoke invitations.",
                    )

        if invitation.status == InvitationStatus.ACCEPTED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot revoke an invitation that has already been accepted.",
            )

        invitation.status = InvitationStatus.CANCELLED.value
        invitation.updated_at = datetime.now(timezone.utc)
        await self.db.flush()

        await self.audit.log(
            entity_type="Invitation",
            entity_id=invitation.id,
            action="REVOKE_INVITATION",
            project_id=group.project_id,
            user_id=current_user.id,
            notes=f"User {current_user.email} revoked invitation to {invitation.email}",
        )

        return InvitationSummary.model_validate(invitation)
