"""
GIS Access / Grant Endpoints
Handles administrative entitlement grants and workspace-scoped GIS dataset access
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_admin
from app.db.models.user import User
from app.services import gis_access_service
from app.services import gis_service
from app.schemas.gis_access_schema import (
    GISAccessGrantRequest,
    GISAccessRevokeRequest,
    GISAccessResponse,
    GISAccessListResponse,
    AuthorizedDatasetResponse,
    GISAccessWorkspaceInfo,
    GISAccessDatasetInfo,
)
from app.schemas.gis_schema import GISLayerResponse

admin_router = APIRouter(prefix="/admin/gis-access", tags=["Admin GIS Access"])
workspace_gis_router = APIRouter(prefix="/workspaces/{workspace_id}/gis", tags=["Workspace GIS"])


# ==============================================================================
# ADMIN GIS ACCESS MANAGEMENT
# ==============================================================================


@admin_router.get("/workspaces", response_model=List[GISAccessWorkspaceInfo])
def get_all_workspaces_for_grant(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """List all workspaces for Admin GIS grant dropdown."""
    from app.repositories import workspace_repository as ws_repo
    workspaces = ws_repo.list_all(db)
    return [GISAccessWorkspaceInfo.model_validate(w) for w in workspaces]


@admin_router.get("/datasets", response_model=List[GISAccessDatasetInfo])
def get_all_datasets_for_grant(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """List all completed GIS datasets for Admin GIS grant dropdown."""
    from app.db.models.gis_dataset import GISDataset
    datasets = db.query(GISDataset).filter(GISDataset.status == "completed").order_by(GISDataset.name.asc()).all()
    return [GISAccessDatasetInfo.model_validate(d) for d in datasets]

@admin_router.get("", response_model=GISAccessListResponse)
def list_all_access_grants(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    workspace_id: Optional[UUID] = Query(None, description="Filter by workspace"),
    dataset_id: Optional[UUID] = Query(None, description="Filter by dataset"),
    active_only: Optional[bool] = Query(None, description="Filter active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """List all GIS access grants across the platform. Admin only."""
    return gis_access_service.list_all_grants(
        db=db,
        current_user=current_user,
        skip=skip,
        limit=limit,
        workspace_id=workspace_id,
        dataset_id=dataset_id,
        active_only=active_only,
    )


@admin_router.post("/grant", response_model=GISAccessResponse, status_code=status.HTTP_201_CREATED)
def grant_gis_access(
    payload: GISAccessGrantRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Grant access to a GIS dataset for a specific workspace. Admin only.
    Safe against duplicates: if already active, returns existing record.
    """
    return gis_access_service.grant_dataset_access(
        db=db,
        current_user=current_user,
        payload=payload,
        request=request,
    )


@admin_router.post("/revoke", response_model=GISAccessResponse)
def revoke_gis_access(
    payload: GISAccessRevokeRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Revoke a workspace's entitlement to a GIS dataset. Admin only.
    Soft-revokes access without deleting the dataset.
    """
    return gis_access_service.revoke_dataset_access(
        db=db,
        current_user=current_user,
        payload=payload,
        request=request,
    )


@admin_router.get("/workspace/{workspace_id}", response_model=List[GISAccessResponse])
def get_grants_by_workspace(
    workspace_id: UUID,
    active_only: bool = Query(True, description="Only return active grants"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """List all dataset grants for a specific workspace. Admin only."""
    return gis_access_service.list_grants_for_workspace(
        db=db,
        workspace_id=workspace_id,
        current_user=current_user,
        active_only=active_only,
    )


@admin_router.get("/dataset/{dataset_id}", response_model=List[GISAccessResponse])
def get_grants_by_dataset(
    dataset_id: UUID,
    active_only: bool = Query(True, description="Only return active grants"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """List all workspaces that have access to a specific dataset. Admin only."""
    return gis_access_service.list_grants_for_dataset(
        db=db,
        dataset_id=dataset_id,
        current_user=current_user,
        active_only=active_only,
    )


# ==============================================================================
# WORKSPACE SCOPED GIS ACCESS (FOR DEVELOPER / MEMBERS)
# ==============================================================================

@workspace_gis_router.get("/datasets", response_model=List[AuthorizedDatasetResponse])
def get_workspace_authorized_datasets(
    workspace_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all GIS datasets that the workspace is entitled to access.
    Workspace members or Admin only.
    """
    return gis_access_service.get_authorized_datasets_for_workspace(
        db=db,
        workspace_id=workspace_id,
        current_user=current_user,
    )


@workspace_gis_router.get("/datasets/{dataset_id}/layers", response_model=List[GISLayerResponse])
def get_workspace_dataset_layers(
    workspace_id: UUID,
    dataset_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get layers for an authorized dataset in a workspace.
    Verifies workspace entitlement before returning layers.
    """
    gis_access_service._require_workspace_member_or_admin(db, workspace_id, current_user)

    if not gis_access_service.is_dataset_accessible_by_workspace(db, workspace_id, dataset_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Workspace does not have access to this GIS dataset",
        )

    return gis_service.get_dataset_layers(db, dataset_id)


@workspace_gis_router.get("/layers/{layer_id}/geojson")
def get_workspace_layer_geojson(
    workspace_id: UUID,
    layer_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get GeoJSON for a layer with workspace entitlement verification.
    """
    gis_access_service._require_workspace_member_or_admin(db, workspace_id, current_user)
    gis_access_service.verify_layer_authorized_for_workspace(db, workspace_id, layer_id)

    return gis_service.get_layer_geojson(db, layer_id)