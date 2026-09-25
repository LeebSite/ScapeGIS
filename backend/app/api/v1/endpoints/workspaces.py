"""
Workspace API Endpoints
"""
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.api.deps import get_db, get_current_user
from app.db.models.user import User
from app.services import workspace_service
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

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])
invitations_router = APIRouter(prefix="/invitations", tags=["Invitations"])


# ==========================================================================
# WORKSPACE CRUD
# ==========================================================================

@router.get("", response_model=List[WorkspaceListResponse])
def get_workspaces(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all workspaces the authenticated user belongs to"""
    return workspace_service.get_workspaces(db, current_user)


@router.post("", response_model=WorkspaceCreateResponse, status_code=status.HTTP_201_CREATED)
def create_workspace(
    payload: WorkspaceCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new workspace. Only developers can create workspaces."""
    return workspace_service.create_workspace(db, current_user, payload, request)


@router.get("/{workspace_id}", response_model=WorkspaceDetailResponse)
def get_workspace_detail(
    workspace_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get workspace details. User must be a member."""
    return workspace_service.get_workspace_detail(db, workspace_id, current_user)


@router.patch("/{workspace_id}", response_model=WorkspaceDetailResponse)
def update_workspace(
    workspace_id: UUID,
    payload: WorkspaceUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update workspace. Owner only."""
    return workspace_service.update_workspace(db, workspace_id, current_user, payload, request)


@router.delete("/{workspace_id}", status_code=status.HTTP_200_OK)
def delete_workspace(
    workspace_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete workspace and all its members/invitations. Owner only."""
    return workspace_service.delete_workspace(db, workspace_id, current_user, request)


# ==========================================================================
# MEMBER MANAGEMENT
# ==========================================================================

@router.get("/{workspace_id}/members", response_model=List[WorkspaceMemberResponse])
def list_members(
    workspace_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all members of a workspace"""
    return workspace_service.list_members(db, workspace_id, current_user)


@router.post("/{workspace_id}/invite", response_model=InviteMemberResponse, status_code=status.HTTP_201_CREATED)
def invite_member(
    workspace_id: UUID,
    payload: InviteMemberRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Invite a member by email. Owner only. Token valid 7 days."""
    return workspace_service.invite_member(db, workspace_id, current_user, payload, request)


# ==========================================================================
# INVITATION ACCEPTANCE (separate prefix /invitations)
# ==========================================================================

@invitations_router.post("/{token}/accept", response_model=AcceptInvitationResponse)
def accept_invitation(
    token: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Accept a workspace invitation using the token from the invite email/link."""
    return workspace_service.accept_invitation(db, token, current_user, request)
