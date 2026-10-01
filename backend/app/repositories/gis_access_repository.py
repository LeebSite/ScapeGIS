from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc

from app.db.models.workspace_gis_access import WorkspaceGISAccess
from app.db.models.gis_dataset import GISDataset
from app.db.models.workspace import Workspace


def get_access(
    db: Session,
    workspace_id: UUID,
    dataset_id: UUID,
) -> Optional[WorkspaceGISAccess]:
    """Retrieve access record between a workspace and dataset."""
    return (
        db.query(WorkspaceGISAccess)
        .options(
            joinedload(WorkspaceGISAccess.workspace),
            joinedload(WorkspaceGISAccess.dataset),
            joinedload(WorkspaceGISAccess.granter),
        )
        .filter(
            WorkspaceGISAccess.workspace_id == workspace_id,
            WorkspaceGISAccess.dataset_id == dataset_id,
        )
        .first()
    )


def is_accessible(db: Session, workspace_id: UUID, dataset_id: UUID) -> bool:
    """Check if a workspace has an active grant to a dataset."""
    grant = (
        db.query(WorkspaceGISAccess.id)
        .filter(
            WorkspaceGISAccess.workspace_id == workspace_id,
            WorkspaceGISAccess.dataset_id == dataset_id,
            WorkspaceGISAccess.is_active.is_(True),
        )
        .first()
    )
    return grant is not None


def grant_access(
    db: Session,
    workspace_id: UUID,
    dataset_id: UUID,
    granted_by: Optional[UUID] = None,
    notes: Optional[str] = None,
) -> tuple[WorkspaceGISAccess, bool]:
    """
    Grant access to a dataset for a workspace.
    Returns (access_record, created_or_reactivated: bool).
    If already active, returns (existing, False).
    """
    existing = (
        db.query(WorkspaceGISAccess)
        .filter(
            WorkspaceGISAccess.workspace_id == workspace_id,
            WorkspaceGISAccess.dataset_id == dataset_id,
        )
        .first()
    )

    if existing:
        if existing.is_active:
            # Already active
            return existing, False

        # Reactivate previously revoked grant
        existing.is_active = True
        existing.revoked_at = None
        existing.granted_by = granted_by
        existing.notes = notes
        existing.granted_at = func.now()
        db.commit()
        db.refresh(existing)
        return existing, True

    # Create new grant
    new_grant = WorkspaceGISAccess(
        workspace_id=workspace_id,
        dataset_id=dataset_id,
        granted_by=granted_by,
        notes=notes,
        is_active=True,
    )
    db.add(new_grant)
    db.commit()
    db.refresh(new_grant)
    return new_grant, True


def revoke_access(
    db: Session,
    workspace_id: UUID,
    dataset_id: UUID,
) -> Optional[WorkspaceGISAccess]:
    """
    Revoke a workspace's access to a GIS dataset.
    Soft-revokes by setting is_active=False and revoked_at=now.
    Does NOT delete the GIS dataset or workspace.
    """
    grant = (
        db.query(WorkspaceGISAccess)
        .filter(
            WorkspaceGISAccess.workspace_id == workspace_id,
            WorkspaceGISAccess.dataset_id == dataset_id,
            WorkspaceGISAccess.is_active.is_(True),
        )
        .first()
    )

    if not grant:
        return None

    grant.is_active = False
    grant.revoked_at = func.now()
    db.commit()
    db.refresh(grant)
    return grant


def list_grants_for_workspace(
    db: Session,
    workspace_id: UUID,
    active_only: bool = True,
) -> List[WorkspaceGISAccess]:
    """List all dataset access grants for a workspace."""
    query = (
        db.query(WorkspaceGISAccess)
        .options(
            joinedload(WorkspaceGISAccess.dataset),
            joinedload(WorkspaceGISAccess.granter),
        )
        .filter(WorkspaceGISAccess.workspace_id == workspace_id)
    )
    if active_only:
        query = query.filter(WorkspaceGISAccess.is_active.is_(True))

    return query.order_by(desc(WorkspaceGISAccess.granted_at)).all()


def list_grants_for_dataset(
    db: Session,
    dataset_id: UUID,
    active_only: bool = True,
) -> List[WorkspaceGISAccess]:
    """List all workspaces that have access to a dataset."""
    query = (
        db.query(WorkspaceGISAccess)
        .options(
            joinedload(WorkspaceGISAccess.workspace),
            joinedload(WorkspaceGISAccess.granter),
        )
        .filter(WorkspaceGISAccess.dataset_id == dataset_id)
    )
    if active_only:
        query = query.filter(WorkspaceGISAccess.is_active.is_(True))

    return query.order_by(desc(WorkspaceGISAccess.granted_at)).all()


def list_all_grants(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    workspace_id: Optional[UUID] = None,
    dataset_id: Optional[UUID] = None,
    active_only: Optional[bool] = None,
) -> List[WorkspaceGISAccess]:
    """List all access grants across the platform with optional filters."""
    query = (
        db.query(WorkspaceGISAccess)
        .options(
            joinedload(WorkspaceGISAccess.workspace),
            joinedload(WorkspaceGISAccess.dataset),
            joinedload(WorkspaceGISAccess.granter),
        )
    )

    if workspace_id:
        query = query.filter(WorkspaceGISAccess.workspace_id == workspace_id)
    if dataset_id:
        query = query.filter(WorkspaceGISAccess.dataset_id == dataset_id)
    if active_only is not None:
        query = query.filter(WorkspaceGISAccess.is_active.is_(active_only))

    return (
        query.order_by(desc(WorkspaceGISAccess.granted_at))
        .offset(skip)
        .limit(limit)
        .all()
    )


def count_all_grants(
    db: Session,
    workspace_id: Optional[UUID] = None,
    dataset_id: Optional[UUID] = None,
    active_only: Optional[bool] = None,
) -> int:
    """Count all access grants matching filters."""
    query = db.query(func.count(WorkspaceGISAccess.id))
    if workspace_id:
        query = query.filter(WorkspaceGISAccess.workspace_id == workspace_id)
    if dataset_id:
        query = query.filter(WorkspaceGISAccess.dataset_id == dataset_id)
    if active_only is not None:
        query = query.filter(WorkspaceGISAccess.is_active.is_(active_only))
    return query.scalar() or 0


def get_authorized_datasets_for_workspace(
    db: Session,
    workspace_id: UUID,
) -> List[GISDataset]:
    """
    Get all GIS datasets that a workspace has active entitlement to access.
    Joined with layers.
    """
    return (
        db.query(GISDataset)
        .join(
            WorkspaceGISAccess,
            (WorkspaceGISAccess.dataset_id == GISDataset.id)
            & (WorkspaceGISAccess.workspace_id == workspace_id)
            & (WorkspaceGISAccess.is_active.is_(True)),
        )
        .options(joinedload(GISDataset.layers))
        .order_by(desc(WorkspaceGISAccess.granted_at))
        .all()
    )