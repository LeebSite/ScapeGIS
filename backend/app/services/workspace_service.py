"""
Workspace Service - All business logic for workspace management.
Repository is used only for DB operations.
"""
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import List
from uuid import UUID

from fastapi import HTTPException, status, Request
from sqlalchemy.orm import Session

from app.db.models.audit_log import AuditLog
from app.db.models.user import User, UserRole
from app.db.models.workspace import Workspace
from app.db.models.workspace_member import WorkspaceMember, WorkspaceMemberRole
from app.db.models.workspace_invitation import WorkspaceInvitation
from app.repositories import workspace_repository as repo
from app.schemas.workspace_schema import (
    WorkspaceCreateRequest,
    WorkspaceUpdateRequest,
    WorkspaceCreateResponse,
    WorkspaceListResponse,
    WorkspaceDetailResponse,
    WorkspaceMemberResponse,
    InviteMemberRequest,
    InviteMemberResponse,
    AcceptInvitationResponse,
)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _create_audit_log(
    db: Session,
    user_id: str,
    action: str,
    request: Request,
    resource_id: str = None,
    details: dict = None,
):
    """Reuse existing AuditLog pattern"""
    ip = request.client.host if request.client else "0.0.0.0"
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type="workspace",
        resource_id=resource_id,
        ip_address=ip,
        user_agent=request.headers.get("user-agent"),
        details=details,
    )
    db.add(log)
    db.commit()


def _slugify(name: str) -> str:
    """Convert workspace name to a URL-safe slug"""
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    slug = re.sub(r"^-+|-+$", "", slug)
    return slug


def _make_unique_slug(db: Session, name: str) -> str:
    """Generate a unique slug, appending random suffix if needed"""
    base = _slugify(name)
    slug = base
    while repo.get_by_slug(db, slug):
        slug = f"{base}-{secrets.token_hex(3)}"
    return slug


def _require_owner(db: Session, workspace_id: UUID, user_id: UUID) -> Workspace:
    """Ensure workspace exists and current user is owner. Returns workspace."""
    workspace = repo.get_by_id(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    member = repo.get_member(db, workspace_id, user_id)
    if not member or member.role != WorkspaceMemberRole.OWNER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner access required")
    return workspace


def _require_member(db: Session, workspace_id: UUID, user_id: UUID) -> WorkspaceMember:
    """Ensure current user is a member of the workspace. Returns member record."""
    workspace = repo.get_by_id(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    member = repo.get_member(db, workspace_id, user_id)
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return member


def _build_workspace_list_response(db: Session, workspace: Workspace, user_id: UUID) -> WorkspaceListResponse:
    member = repo.get_member(db, workspace.id, user_id)
    return WorkspaceListResponse(
        id=workspace.id,
        name=workspace.name,
        slug=workspace.slug,
        description=workspace.description,
        logo_url=workspace.logo_url,
        role=member.role.value if member else "member",
        member_count=repo.count_members(db, workspace.id),
        created_at=workspace.created_at,
    )


# ==========================================================================
# WORKSPACE CRUD
# ==========================================================================

def create_workspace(
    db: Session,
    current_user: User,
    payload: WorkspaceCreateRequest,
    request: Request,
) -> WorkspaceCreateResponse:
    """Only developers can create workspaces. Owner is set automatically."""
    if current_user.role != UserRole.DEVELOPER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only developers can create workspaces",
        )

    slug = _make_unique_slug(db, payload.name)

    workspace = Workspace(
        name=payload.name,
        slug=slug,
        description=payload.description,
        owner_id=current_user.id,
    )
    workspace = repo.create(db, workspace)

    # Auto-assign creator as owner
    owner_member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=current_user.id,
        role=WorkspaceMemberRole.OWNER,
    )
    repo.add_member(db, owner_member)

    _create_audit_log(
        db, str(current_user.id), "workspace.created", request,
        resource_id=str(workspace.id),
        details={"workspace_name": workspace.name, "slug": slug},
    )

    return WorkspaceCreateResponse(message="Workspace created", workspace_id=workspace.id)


def get_workspaces(db: Session, current_user: User) -> List[WorkspaceListResponse]:
    """Return all workspaces the current user belongs to"""
    workspaces = repo.list_by_user(db, current_user.id)
    return [_build_workspace_list_response(db, ws, current_user.id) for ws in workspaces]


def get_workspace_detail(
    db: Session, workspace_id: UUID, current_user: User
) -> WorkspaceDetailResponse:
    """Return full details of a workspace. User must be a member."""
    member = _require_member(db, workspace_id, current_user.id)
    workspace = repo.get_by_id(db, workspace_id)
    return WorkspaceDetailResponse(
        id=workspace.id,
        name=workspace.name,
        slug=workspace.slug,
        description=workspace.description,
        logo_url=workspace.logo_url,
        owner_id=workspace.owner_id,
        role=member.role.value,
        member_count=repo.count_members(db, workspace.id),
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
    )


def update_workspace(
    db: Session,
    workspace_id: UUID,
    current_user: User,
    payload: WorkspaceUpdateRequest,
    request: Request,
) -> WorkspaceDetailResponse:
    """Only the workspace owner can update it."""
    workspace = _require_owner(db, workspace_id, current_user.id)

    update_data = payload.model_dump(exclude_unset=True)
    if "name" in update_data and update_data["name"] != workspace.name:
        update_data["slug"] = _make_unique_slug(db, update_data["name"])

    repo.update(db, workspace_id, **update_data)

    _create_audit_log(
        db, str(current_user.id), "workspace.updated", request,
        resource_id=str(workspace_id),
        details={"updated_fields": list(update_data.keys())},
    )

    return get_workspace_detail(db, workspace_id, current_user)


def delete_workspace(
    db: Session,
    workspace_id: UUID,
    current_user: User,
    request: Request,
) -> dict:
    """Only the workspace owner can delete it."""
    workspace = _require_owner(db, workspace_id, current_user.id)
    name = workspace.name

    repo.delete(db, workspace_id)

    _create_audit_log(
        db, str(current_user.id), "workspace.deleted", request,
        resource_id=str(workspace_id),
        details={"workspace_name": name},
    )

    return {"message": "Workspace deleted"}


# ==========================================================================
# MEMBER MANAGEMENT
# ==========================================================================

def list_members(
    db: Session, workspace_id: UUID, current_user: User
) -> List[WorkspaceMemberResponse]:
    """Any workspace member can view the member list."""
    _require_member(db, workspace_id, current_user.id)
    members = repo.list_members(db, workspace_id)

    result = []
    for m in members:
        result.append(
            WorkspaceMemberResponse(
                id=m.id,
                workspace_id=m.workspace_id,
                user_id=m.user_id,
                role=m.role.value,
                joined_at=m.joined_at,
                user_name=m.user.name if m.user else None,
                user_email=m.user.email if m.user else None,
                user_avatar_url=m.user.avatar_url if m.user else None,
            )
        )
    return result


def invite_member(
    db: Session,
    workspace_id: UUID,
    current_user: User,
    payload: InviteMemberRequest,
    request: Request,
) -> InviteMemberResponse:
    """Only owner can invite. Generates a unique token valid for 7 days."""
    _require_owner(db, workspace_id, current_user.id)

    # Check if email already has a pending invitation
    existing = repo.get_pending_invitation(db, workspace_id, payload.email)
    if existing and existing.expires_at > datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A pending invitation already exists for this email",
        )

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    invitation = WorkspaceInvitation(
        workspace_id=workspace_id,
        email=payload.email,
        token=token,
        expires_at=expires_at,
    )
    invitation = repo.create_invitation(db, invitation)

    _create_audit_log(
        db, str(current_user.id), "workspace.member_invited", request,
        resource_id=str(workspace_id),
        details={"invited_email": payload.email},
    )

    return InviteMemberResponse(
        message="Invitation created",
        token=token,
        invitation_id=invitation.id,
    )


def accept_invitation(
    db: Session,
    token: str,
    current_user: User,
    request: Request,
) -> AcceptInvitationResponse:
    """
    Accept a workspace invitation by token.
    - Token must exist and not be expired.
    - Email in token must match authenticated user email.
    """
    invitation = repo.get_invitation_by_token(db, token)

    if not invitation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")

    if invitation.accepted_at is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invitation already accepted")

    now = datetime.now(timezone.utc)
    if invitation.expires_at.tzinfo is None:
        expires_aware = invitation.expires_at.replace(tzinfo=timezone.utc)
    else:
        expires_aware = invitation.expires_at

    if now > expires_aware:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Invitation has expired")

    if invitation.email.lower() != current_user.email.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This invitation was not sent to your email address",
        )

    # Check if already a member
    existing_member = repo.get_member(db, invitation.workspace_id, current_user.id)
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You are already a member of this workspace",
        )

    # Add as member
    member = WorkspaceMember(
        workspace_id=invitation.workspace_id,
        user_id=current_user.id,
        role=WorkspaceMemberRole.MEMBER,
    )
    repo.add_member(db, member)

    # Close invitation
    repo.close_invitation(db, invitation)

    workspace = repo.get_by_id(db, invitation.workspace_id)

    _create_audit_log(
        db, str(current_user.id), "workspace.member_joined", request,
        resource_id=str(invitation.workspace_id),
        details={"workspace_name": workspace.name},
    )

    return AcceptInvitationResponse(
        message="Successfully joined the workspace",
        workspace_id=workspace.id,
        workspace_name=workspace.name,
    )
