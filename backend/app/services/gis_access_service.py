from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.models.user import User, UserRole
from app.db.models.workspace import Workspace
from app.db.models.workspace_member import WorkspaceMember
from app.db.models.gis_dataset import GISDataset
from app.db.models.gis_layer import GISLayer
from app.db.models.workspace_gis_access import WorkspaceGISAccess
from app.repositories import gis_access_repository as repo
from app.schemas.gis_access_schema import (
    GISAccessGrantRequest,
    GISAccessRevokeRequest,
    GISAccessResponse,
    GISAccessListResponse,
    AuthorizedDatasetResponse,
)
from app.schemas.gis_schema import GISLayerResponse
from app.core.audit import log_audit


def _require_admin(user: User):
    """Enforce that current user is an Admin."""
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required for GIS access management",
        )


def _require_workspace_member_or_admin(db: Session, workspace_id: UUID, user: User) -> Optional[WorkspaceMember]:
    """Verify that user is a member of the workspace, or is a system admin."""
    if user.role == UserRole.ADMIN:
        return None
    member = (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user.id,
        )
        .first()
    )
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this workspace",
        )
    return member


def grant_dataset_access(
    db: Session,
    current_user: User,
    payload: GISAccessGrantRequest,
    request: Optional[Request] = None,
) -> GISAccessResponse:
    """
    Grant access to a GIS dataset for a specific workspace.
    Admin only.
    Idempotent: if already granted, returns existing active record safely.
    """
    _require_admin(current_user)

    # 1. Verify workspace exists
    workspace = db.query(Workspace).filter(Workspace.id == payload.workspace_id).first()
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    # 2. Verify dataset exists
    dataset = db.query(GISDataset).filter(GISDataset.id == payload.dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GIS Dataset not found",
        )

    # 3. Grant access via repository
    grant_record, created_or_reactivated = repo.grant_access(
        db=db,
        workspace_id=payload.workspace_id,
        dataset_id=payload.dataset_id,
        granted_by=current_user.id,
        notes=payload.notes,
    )

    # 4. Audit logging
    if created_or_reactivated:
        log_audit(
            db=db,
            user=current_user,
            action="gis.access.granted",
            resource_type="WorkspaceGISAccess",
            resource_id=str(grant_record.id),
            request=request,
            details={
                "workspace_id": str(payload.workspace_id),
                "workspace_name": workspace.name,
                "dataset_id": str(payload.dataset_id),
                "dataset_name": dataset.name,
                "notes": payload.notes,
            },
        )

    return GISAccessResponse.model_validate(grant_record)


def revoke_dataset_access(
    db: Session,
    current_user: User,
    payload: GISAccessRevokeRequest,
    request: Optional[Request] = None,
) -> GISAccessResponse:
    """
    Revoke a workspace's entitlement to a GIS dataset.
    Admin only.
    Soft-revokes access without deleting the dataset.
    """
    _require_admin(current_user)

    # Verify workspace and dataset
    workspace = db.query(Workspace).filter(Workspace.id == payload.workspace_id).first()
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    dataset = db.query(GISDataset).filter(GISDataset.id == payload.dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GIS Dataset not found",
        )

    revoked_grant = repo.revoke_access(
        db=db,
        workspace_id=payload.workspace_id,
        dataset_id=payload.dataset_id,
    )

    if not revoked_grant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active GIS access grant not found for this workspace and dataset",
        )

    # Audit logging
    log_audit(
        db=db,
        user=current_user,
        action="gis.access.revoked",
        resource_type="WorkspaceGISAccess",
        resource_id=str(revoked_grant.id),
        request=request,
        details={
            "workspace_id": str(payload.workspace_id),
            "workspace_name": workspace.name,
            "dataset_id": str(payload.dataset_id),
            "dataset_name": dataset.name,
            "reason": payload.reason,
        },
    )

    return GISAccessResponse.model_validate(revoked_grant)


def list_all_grants(
    db: Session,
    current_user: User,
    skip: int = 0,
    limit: int = 100,
    workspace_id: Optional[UUID] = None,
    dataset_id: Optional[UUID] = None,
    active_only: Optional[bool] = None,
) -> GISAccessListResponse:
    """List all GIS access grants. Admin only."""
    _require_admin(current_user)

    items = repo.list_all_grants(
        db=db,
        skip=skip,
        limit=limit,
        workspace_id=workspace_id,
        dataset_id=dataset_id,
        active_only=active_only,
    )
    total = repo.count_all_grants(
        db=db,
        workspace_id=workspace_id,
        dataset_id=dataset_id,
        active_only=active_only,
    )

    return GISAccessListResponse(
        total=total,
        items=[GISAccessResponse.model_validate(i) for i in items],
    )


def list_grants_for_workspace(
    db: Session,
    workspace_id: UUID,
    current_user: User,
    active_only: bool = True,
) -> List[GISAccessResponse]:
    """List dataset grants for a workspace. Accessible by workspace members or Admin."""
    _require_workspace_member_or_admin(db, workspace_id, current_user)
    grants = repo.list_grants_for_workspace(db, workspace_id, active_only=active_only)
    return [GISAccessResponse.model_validate(g) for g in grants]


def list_grants_for_dataset(
    db: Session,
    dataset_id: UUID,
    current_user: User,
    active_only: bool = True,
) -> List[GISAccessResponse]:
    """List workspaces that have access to a dataset. Admin only."""
    _require_admin(current_user)
    grants = repo.list_grants_for_dataset(db, dataset_id, active_only=active_only)
    return [GISAccessResponse.model_validate(g) for g in grants]


def get_authorized_datasets_for_workspace(
    db: Session,
    workspace_id: UUID,
    current_user: User,
) -> List[AuthorizedDatasetResponse]:
    """
    Get all GIS datasets authorized for the given workspace.
    Accessible by workspace members or Admin.
    """
    _require_workspace_member_or_admin(db, workspace_id, current_user)

    # Query active access records for this workspace
    access_records = (
        db.query(WorkspaceGISAccess)
        .filter(
            WorkspaceGISAccess.workspace_id == workspace_id,
            WorkspaceGISAccess.is_active.is_(True),
        )
        .order_by(desc(WorkspaceGISAccess.granted_at))
        .all()
    )

    results: List[AuthorizedDatasetResponse] = []
    for access in access_records:
        ds = access.dataset
        if not ds or ds.status != "completed":
            continue

        layers_dto = [GISLayerResponse.model_validate(l) for l in ds.layers]
        results.append(
            AuthorizedDatasetResponse(
                id=ds.id,
                name=ds.name,
                description=ds.description,
                file_type=ds.file_type,
                source=ds.source,
                bbox=ds.bbox,
                crs=ds.crs,
                srid=ds.srid or 4326,
                geometry_type=ds.geometry_type,
                total_layers=ds.total_layers,
                total_features=ds.total_features,
                status=ds.status,
                granted_at=access.granted_at,
                layers=layers_dto,
            )
        )

    return results


def is_dataset_accessible_by_workspace(
    db: Session,
    workspace_id: UUID,
    dataset_id: UUID,
) -> bool:
    """Check if workspace is entitled to access the dataset."""
    return repo.is_accessible(db, workspace_id, dataset_id)


def verify_layer_authorized_for_workspace(
    db: Session,
    workspace_id: UUID,
    layer_id: UUID,
) -> tuple[GISLayer, GISDataset]:
    """
    Verify that layer belongs to a dataset authorized for the workspace.
    Raises HTTPException 404 or 403 if unauthorized.
    """
    layer = db.query(GISLayer).filter(GISLayer.id == layer_id).first()
    if not layer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GIS Layer not found",
        )

    if not is_dataset_accessible_by_workspace(db, workspace_id, layer.dataset_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Workspace does not have access to the dataset containing this layer",
        )

    dataset = db.query(GISDataset).filter(GISDataset.id == layer.dataset_id).first()
    return layer, dataset