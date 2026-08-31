"""
GreenSynth Analytics — FastAPI Dependencies

Provides dependency-injected objects for route handlers, supporting both
System Administrator (system-wide access) and Student (project-scoped access).
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import TokenDecodeError, decode_access_token
from app.database.session import AsyncSessionLocal
from app.models.group_membership import GroupMembership, MembershipStatus
from app.models.project import Project, ProjectStatus
from app.models.research_group import GroupStatus, ResearchGroup
from app.models.user import User, UserRole

# Optional bearer scheme to allow customized error messages on missing headers
bearer_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency: yields an async database session.

    The session is committed on success, rolled back on any exception,
    and always closed after the request.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_current_user(
    auth_credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency: extracts and verifies the Bearer JWT token,
    verifying user existence and active status in the database.
    Missing, invalid, expired, or inactive credentials return HTTP 401.
    """
    if auth_credentials is None or not auth_credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(auth_credentials.credentials)
    except TokenDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication token invalid: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token subject is not a valid UUID.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Database existence and status check
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account associated with this token was not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    FastAPI dependency: ensures the authenticated user is an Administrator (account_type == ADMIN).
    Returns HTTP 403 Forbidden for non-administrators.
    """
    if current_user.account_type != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "ADMIN_REQUIRED",
                "message": "Administrative privileges required.",
            },
        )
    return current_user


async def require_student(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    FastAPI dependency: ensures the authenticated user is a Student / Researcher.
    Returns HTTP 403 Forbidden for non-students when accessing Student-only flows.
    """
    if current_user.account_type != "STUDENT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "STUDENT_REQUIRED",
                "message": "Student privileges required.",
            },
        )
    return current_user


async def get_authorized_project_ids(
    user: User,
    db: AsyncSession,
) -> list[uuid.UUID]:
    """
    Resolves the set of project IDs authorized for a user.
    - Admin: All projects in the database.
    - Student: Projects associated with the student's active group memberships.
    """
    if user.is_admin:
        res = await db.execute(select(Project.id).where(Project.status == ProjectStatus.ACTIVE.value))
        return list(res.scalars().all())

    # Student active memberships
    q = (
        select(ResearchGroup.project_id)
        .join(GroupMembership, GroupMembership.group_id == ResearchGroup.id)
        .where(
            GroupMembership.user_id == user.id,
            GroupMembership.status == MembershipStatus.ACTIVE.value,
            ResearchGroup.status == GroupStatus.ACTIVE.value,
        )
    )
    res = await db.execute(q)
    return list(res.scalars().all())


async def get_current_membership(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GroupMembership:
    """
    FastAPI dependency: resolves the active group membership for the authenticated user.
    """
    result = await db.execute(
        select(GroupMembership).where(
            GroupMembership.user_id == current_user.id,
            GroupMembership.status == MembershipStatus.ACTIVE.value,
        )
    )
    membership = result.scalar_one_or_none()
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "NO_ACTIVE_GROUP",
                "message": "The user is not assigned to an active research group.",
            },
        )
    return membership


async def get_current_group(
    current_membership: GroupMembership = Depends(get_current_membership),
    db: AsyncSession = Depends(get_db),
) -> ResearchGroup:
    """
    FastAPI dependency: resolves the active research group for the current membership.
    """
    result = await db.execute(
        select(ResearchGroup).where(
            ResearchGroup.id == current_membership.group_id,
            ResearchGroup.status == GroupStatus.ACTIVE.value,
        )
    )
    group = result.scalar_one_or_none()
    if group is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "NO_ACTIVE_GROUP",
                "message": "The user's research group is not active.",
            },
        )
    return group


async def get_current_project(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Project:
    """
    FastAPI dependency: resolves the authorized research project for the authenticated user.
    - If user is ADMIN: resolves the default active project (e.g. P7 or P1) or allows access.
    - If user is STUDENT: resolves active membership -> research group -> assigned project.
    """
    if current_user.is_admin:
        # Admin can access any project; default to P7 or first active project if no specific project requested
        res = await db.execute(
            select(Project)
            .where(Project.status == ProjectStatus.ACTIVE.value)
            .order_by(Project.project_code.asc())
        )
        projects = res.scalars().all()
        # Prefer P7 if present, else first
        p7 = next((p for p in projects if p.project_code == "P7"), None)
        if p7:
            return p7
        if projects:
            return projects[0]
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NO_PROJECTS", "message": "No active projects exist in the catalog."},
        )

    # Student path
    result = await db.execute(
        select(GroupMembership, ResearchGroup, Project)
        .join(ResearchGroup, GroupMembership.group_id == ResearchGroup.id)
        .join(Project, ResearchGroup.project_id == Project.id)
        .where(
            GroupMembership.user_id == current_user.id,
            GroupMembership.status == MembershipStatus.ACTIVE.value,
            ResearchGroup.status == GroupStatus.ACTIVE.value,
        )
    )
    row = result.first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "NO_ACTIVE_GROUP",
                "message": "The user is not assigned to an active research group.",
            },
        )
    _membership, _group, project = row
    return project


def verify_project_access(
    project_id: uuid.UUID,
    current_project: Project,
    current_user: User | None = None,
) -> None:
    """
    Verifies that a requested project_id matches the authenticated user's authorized project.
    - If user is ADMIN: Always allows access.
    - If user is STUDENT: Enforces project_id matches authorized current_project.
    Raises 403 Forbidden with PROJECT_ACCESS_DENIED on mismatch.
    """
    if current_user and current_user.is_admin:
        return

    if project_id != current_project.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "PROJECT_ACCESS_DENIED",
                "message": "You do not have access to this project.",
            },
        )


async def get_current_leader(
    current_membership: GroupMembership = Depends(get_current_membership),
    current_user: User = Depends(get_current_user),
) -> User:
    """
    FastAPI dependency: ensures the authenticated user is the Group Leader.
    """
    if not current_membership.is_leader:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "LEADER_REQUIRED",
                "message": "Only the Group Leader can perform this action.",
            },
        )
    return current_user
