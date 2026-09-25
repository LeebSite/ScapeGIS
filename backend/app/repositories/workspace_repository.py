"""
Workspace Repository - Pure SQLAlchemy DB operations only.
No business logic here.
"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.db.models.workspace import Workspace
from app.db.models.workspace_member import WorkspaceMember, WorkspaceMemberRole
from app.db.models.workspace_invitation import WorkspaceInvitation


# ==========================================================================
# WORKSPACE OPERATIONS
# ==========================================================================

def create(db: Session, workspace: Workspace) -> Workspace:
    """Persist a new workspace"""
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    return workspace


def get_by_id(db: Session, workspace_id: UUID) -> Optional[Workspace]:
    """Get workspace by primary key"""
    return db.query(Workspace).filter(Workspace.id == workspace_id).first()


def get_by_slug(db: Session, slug: str) -> Optional[Workspace]:
    """Get workspace by unique slug"""
    return db.query(Workspace).filter(Workspace.slug == slug).first()


def list_by_user(db: Session, user_id: UUID) -> List[Workspace]:
    """Get all workspaces where the user is a member"""
    return (
        db.query(Workspace)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .filter(WorkspaceMember.user_id == user_id)
        .order_by(Workspace.created_at.desc())
        .all()
    )


def update(db: Session, workspace_id: UUID, **kwargs) -> Optional[Workspace]:
    """Update workspace fields"""
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if workspace:
        for key, value in kwargs.items():
            if hasattr(workspace, key):
                setattr(workspace, key, value)
        db.commit()
        db.refresh(workspace)
    return workspace


def delete(db: Session, workspace_id: UUID) -> bool:
    """Hard delete a workspace (cascade handles members/invitations)"""
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if workspace:
        db.delete(workspace)
        db.commit()
        return True
    return False


def count_members(db: Session, workspace_id: UUID) -> int:
    """Count active members in a workspace"""
    return (
        db.query(func.count(WorkspaceMember.id))
        .filter(WorkspaceMember.workspace_id == workspace_id)
        .scalar()
    )


# ==========================================================================
# MEMBER OPERATIONS
# ==========================================================================

def add_member(db: Session, member: WorkspaceMember) -> WorkspaceMember:
    """Add a member to a workspace"""
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def get_member(db: Session, workspace_id: UUID, user_id: UUID) -> Optional[WorkspaceMember]:
    """Get a specific member record"""
    return (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
        .first()
    )


def list_members(db: Session, workspace_id: UUID) -> List[WorkspaceMember]:
    """Get all members of a workspace with user info"""
    return (
        db.query(WorkspaceMember)
        .options(joinedload(WorkspaceMember.user))
        .filter(WorkspaceMember.workspace_id == workspace_id)
        .order_by(WorkspaceMember.joined_at)
        .all()
    )


def remove_member(db: Session, workspace_id: UUID, user_id: UUID) -> bool:
    """Remove a member from workspace"""
    member = get_member(db, workspace_id, user_id)
    if member:
        db.delete(member)
        db.commit()
        return True
    return False


# ==========================================================================
# INVITATION OPERATIONS
# ==========================================================================

def create_invitation(db: Session, invitation: WorkspaceInvitation) -> WorkspaceInvitation:
    """Persist a new invitation"""
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return invitation


def get_invitation_by_token(db: Session, token: str) -> Optional[WorkspaceInvitation]:
    """Find invitation by its unique token"""
    return db.query(WorkspaceInvitation).filter(WorkspaceInvitation.token == token).first()


def get_pending_invitation(db: Session, workspace_id: UUID, email: str) -> Optional[WorkspaceInvitation]:
    """Check if there is already an open invitation for this email+workspace"""
    return (
        db.query(WorkspaceInvitation)
        .filter(
            WorkspaceInvitation.workspace_id == workspace_id,
            WorkspaceInvitation.email == email,
            WorkspaceInvitation.accepted_at.is_(None),
        )
        .first()
    )


def close_invitation(db: Session, invitation: WorkspaceInvitation) -> WorkspaceInvitation:
    """Mark invitation as accepted"""
    invitation.accepted_at = datetime.utcnow()
    db.commit()
    db.refresh(invitation)
    return invitation
