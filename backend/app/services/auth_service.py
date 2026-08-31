"""
GreenSynth Analytics — Authentication Service

Encapsulates business logic for Group Leader registration, email/password login,
member invitation acceptance, and user profile resolution.
All multi-record operations are executed within atomic transactions.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    hash_invitation_token,
    hash_password,
    verify_password,
)
from app.models.group_membership import GroupMembership, MembershipStatus
from app.models.invitation import Invitation, InvitationStatus
from app.models.project import Project, ProjectStatus
from app.models.research_group import GroupStatus, ResearchGroup
from app.models.user import User
from app.schemas.auth import (
    AcceptInvitationRequest,
    ChangePasswordRequest,
    LeaderRegisterRequest,
    LoginRequest,
    MembershipRead,
    ProfileUpdateRequest,
    TokenResponse,
    UserProfile,
    UserRead,
)
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class AuthService:
    """Service layer for user registration, authentication, and onboarding."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.audit = AuditService(db)
        self.settings = get_settings()

    async def register_leader(
        self, payload: LeaderRegisterRequest
    ) -> TokenResponse:
        """
        Atomically register a new Group Leader, create their ResearchGroup,
        and assign their leader membership.
        """
        clean_email = payload.email.strip().lower()
        if not clean_email or "@" not in clean_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A valid email address is required.",
            )

        # 1. Check if email is already registered
        existing_user = await self.db.execute(
            select(User).where(User.email == clean_email)
        )
        if existing_user.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email address already exists.",
            )

        # 2. Validate selected project
        proj_res = await self.db.execute(
            select(Project).where(Project.id == payload.project_id)
        )
        project = proj_res.scalar_one_or_none()
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Project with ID '{payload.project_id}' does not exist.",
            )
        if project.status != ProjectStatus.ACTIVE.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Project '{project.project_code}' is currently {project.status} and cannot be selected.",
            )

        # 3. Derive username from email with unique fallback if needed
        base_username = clean_email.split("@")[0][:60]
        u_check = await self.db.execute(
            select(User).where(User.username == base_username)
        )
        if u_check.scalar_one_or_none() is not None:
            base_username = f"{base_username[:50]}_{uuid.uuid4().hex[:6]}"

        # 4. Determine Group Name
        group_name = payload.group_name.strip() if payload.group_name else ""
        if not group_name:
            group_name = f"{project.project_code}-{payload.roll_number.strip()}"

        try:
            # 5. Create User
            user = User(
                username=base_username,
                email=clean_email,
                full_name=payload.full_name.strip(),
                department=payload.department.strip(),
                phone=payload.phone.strip(),
                roll_number=payload.roll_number.strip(),
                role="RESEARCHER",
                password_hash=hash_password(payload.password),
                is_active=True,
            )
            self.db.add(user)
            await self.db.flush()

            # 6. Create ResearchGroup
            group = ResearchGroup(
                name=group_name,
                project_id=project.id,
                leader_user_id=user.id,
                status=GroupStatus.ACTIVE.value,
            )
            self.db.add(group)
            await self.db.flush()

            # 7. Create Leader GroupMembership
            membership = GroupMembership(
                group_id=group.id,
                user_id=user.id,
                is_leader=True,
                status=MembershipStatus.ACTIVE.value,
            )
            self.db.add(membership)
            await self.db.flush()

            # 8. Log Audit Record
            await self.audit.log(
                entity_type="User",
                entity_id=user.id,
                action="REGISTER_LEADER",
                project_id=project.id,
                user_id=user.id,
                notes=f"Group Leader registered for group {group_name} (Project {project.project_code})",
            )

        except IntegrityError as exc:
            logger.warning("Integrity error during leader registration: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Registration conflict: email or username already exists.",
            ) from exc

        # 9. Issue JWT token
        token = create_access_token(user.id, account_type=user.account_type)
        expires_seconds = self.settings.access_token_expire_minutes * 60

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=expires_seconds,
            user=UserRead.model_validate(user),
        )

    async def authenticate_user(self, payload: LoginRequest) -> TokenResponse:
        """
        Authenticate an existing user via email and password, returning a JWT token.
        Returns a generic 401 on failure to prevent account enumeration.
        """
        clean_email = payload.email.strip().lower()
        if not clean_email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 1. Query user by email
        result = await self.db.execute(
            select(User).where(User.email == clean_email)
        )
        user = result.scalar_one_or_none()

        # 2. Constant-time password check
        if user is None or not verify_password(payload.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 3. Account active check
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated. Please contact your system administrator.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 4. Issue JWT access token
        token = create_access_token(user.id, account_type=user.account_type)
        expires_seconds = self.settings.access_token_expire_minutes * 60

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=expires_seconds,
            user=UserRead.model_validate(user),
        )

    async def accept_invitation(
        self, payload: AcceptInvitationRequest
    ) -> TokenResponse:
        """
        Validate an invitation token, create or activate the invited student's account,
        and assign them to the research group as a regular member (is_leader=False).
        """
        token_hash = hash_invitation_token(payload.token)

        # 1. Query invitation by hash
        inv_res = await self.db.execute(
            select(Invitation).where(Invitation.token_hash == token_hash)
        )
        invitation = inv_res.scalar_one_or_none()

        if invitation is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired invitation token.",
            )

        # 2. Check invitation status
        if invitation.status != InvitationStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"This invitation is no longer pending (status: {invitation.status}).",
            )

        # 3. Check expiration
        exp = invitation.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp < datetime.now(timezone.utc):
            invitation.status = InvitationStatus.EXPIRED.value
            await self.db.flush()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This invitation has expired. Please ask your group leader for a new invitation.",
            )

        # 4. Verify research group exists
        grp_res = await self.db.execute(
            select(ResearchGroup).where(ResearchGroup.id == invitation.group_id)
        )
        group = grp_res.scalar_one_or_none()
        if group is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Associated research group was not found.",
            )

        try:
            # 5. Check if user with invitation email already exists
            user_res = await self.db.execute(
                select(User).where(User.email == invitation.email)
            )
            user = user_res.scalar_one_or_none()

            if user is None:
                base_username = invitation.email.split("@")[0][:60]
                u_check = await self.db.execute(
                    select(User).where(User.username == base_username)
                )
                if u_check.scalar_one_or_none() is not None:
                    base_username = f"{base_username[:50]}_{uuid.uuid4().hex[:6]}"

                user = User(
                    username=base_username,
                    email=invitation.email,
                    full_name=invitation.full_name,
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
                # Update password and activate if existing account
                user.password_hash = hash_password(payload.password)
                user.is_active = True
                await self.db.flush()

            # 6. Check for duplicate membership
            mem_res = await self.db.execute(
                select(GroupMembership).where(
                    GroupMembership.group_id == group.id,
                    GroupMembership.user_id == user.id,
                )
            )
            existing_mem = mem_res.scalar_one_or_none()
            if existing_mem is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User is already a member of this research group.",
                )

            # 7. Create GroupMembership (is_leader=False)
            membership = GroupMembership(
                group_id=group.id,
                user_id=user.id,
                is_leader=False,
                status=MembershipStatus.ACTIVE.value,
            )
            self.db.add(membership)

            # 8. Mark invitation as ACCEPTED
            invitation.status = InvitationStatus.ACCEPTED.value
            invitation.accepted_at = datetime.now(timezone.utc)
            await self.db.flush()

            # 9. Log Audit Record
            await self.audit.log(
                entity_type="Invitation",
                entity_id=invitation.id,
                action="ACCEPT_INVITATION",
                project_id=group.project_id,
                user_id=user.id,
                notes=f"Student {user.full_name} accepted invitation for group {group.name}",
            )

        except IntegrityError as exc:
            logger.warning("Integrity error during invitation acceptance: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Membership conflict: user is already assigned to this group.",
            ) from exc

        # 10. Issue JWT access token
        token = create_access_token(user.id, account_type=user.account_type)
        expires_seconds = self.settings.access_token_expire_minutes * 60

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=expires_seconds,
            user=UserRead.model_validate(user),
        )

    async def get_user_profile(self, user: User) -> UserProfile:
        """
        Resolve the complete user profile including active research group memberships
        and associated project metadata.
        """
        q = (
            select(GroupMembership, ResearchGroup, Project)
            .join(ResearchGroup, GroupMembership.group_id == ResearchGroup.id)
            .join(Project, ResearchGroup.project_id == Project.id)
            .where(GroupMembership.user_id == user.id)
        )
        res = await self.db.execute(q)
        rows = res.all()

        memberships: list[MembershipRead] = []
        for mem, grp, proj in rows:
            memberships.append(
                MembershipRead(
                    group_id=grp.id,
                    group_name=grp.name,
                    is_leader=mem.is_leader,
                    status=mem.status,
                    project_id=proj.id,
                    project_code=proj.project_code,
                    joined_at=mem.joined_at,
                )
            )

        return UserProfile(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            department=user.department,
            phone=user.phone,
            roll_number=user.roll_number,
            role=user.role,
            account_type=user.account_type,
            is_active=user.is_active,
            created_at=user.created_at,
            memberships=memberships,
        )

    async def list_all_users(self) -> list[UserRead]:
        """Fetch all system user accounts (Admin only)."""
        res = await self.db.execute(select(User).order_by(User.created_at.desc()))
        users = res.scalars().all()
        return [UserRead.model_validate(u) for u in users]

    async def update_user_profile(
        self, user: User, payload: ProfileUpdateRequest
    ) -> UserProfile:
        """
        Safely update permitted user profile attributes.
        Role, account_type, email, and group/project assignments are strictly immutable here.
        """
        if payload.full_name is not None and payload.full_name.strip():
            user.full_name = payload.full_name.strip()
        if payload.department is not None:
            user.department = payload.department.strip()
        if payload.phone is not None:
            user.phone = payload.phone.strip()
        if payload.roll_number is not None:
            user.roll_number = payload.roll_number.strip()

        await self.db.flush()
        await self.audit.log(
            entity_type="User",
            entity_id=user.id,
            action="UPDATE_PROFILE",
            user_id=user.id,
            notes=f"User {user.email} updated their profile.",
        )
        return await self.get_user_profile(user)

    async def change_password(
        self, user: User, payload: ChangePasswordRequest
    ) -> dict[str, str]:
        """
        Verify current password, validate new password matches confirmation,
        and update password hash.
        """
        if not verify_password(payload.current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect.",
            )

        clean_new = payload.new_password.strip()
        clean_confirm = payload.confirm_password.strip()

        if clean_new != clean_confirm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password and confirmation do not match.",
            )

        if len(clean_new) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be at least 8 characters long.",
            )

        if verify_password(clean_new, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from current password.",
            )

        user.password_hash = hash_password(clean_new)
        await self.db.flush()
        await self.audit.log(
            entity_type="User",
            entity_id=user.id,
            action="CHANGE_PASSWORD",
            user_id=user.id,
            notes=f"User {user.email} successfully changed their account password.",
        )
        return {"status": "success", "message": "Password changed successfully."}

    async def update_user_status(
        self, user_id: uuid.UUID, is_active: bool, admin_user: User
    ) -> UserRead:
        """Toggle active status for a user account (Admin only)."""
        res = await self.db.execute(select(User).where(User.id == user_id))
        target_user = res.scalar_one_or_none()
        if target_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        if target_user.id == admin_user.id and not is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate your own administrator account.",
            )

        target_user.is_active = is_active
        await self.db.flush()
        await self.audit.log(
            entity_type="User",
            entity_id=target_user.id,
            action="UPDATE_USER_STATUS",
            user_id=admin_user.id,
            notes=f"Administrator {admin_user.email} updated user {target_user.email} active status to {is_active}.",
        )
        return UserRead.model_validate(target_user)

