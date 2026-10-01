"""
Project API Endpoints
"""
from fastapi import APIRouter, Depends, Request, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.api.deps import get_db, get_current_user
from app.db.models.user import User
from app.services import project_service
from app.schemas.project_schema import (
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ProjectResponse,
    ProjectListResponse,
    ProjectDetailResponse,
    ProjectLayerAddRequest,
    ProjectLayerUpdateRequest,
    ProjectLayerResponse,
)

router = APIRouter(prefix="/projects", tags=["Projects"])


# ==========================================================================
# PROJECT CRUD
# ==========================================================================

@router.get("", response_model=ProjectListResponse)
def get_projects(
    workspace_id: UUID = Query(..., description="Filter by workspace"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List projects in a workspace. User must be a workspace member."""
    return project_service.get_projects(db, current_user, workspace_id)


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a project inside a workspace. Workspace owner only."""
    return project_service.create_project(db, current_user, payload, request)


@router.get("/{project_id}", response_model=ProjectDetailResponse)
def get_project_detail(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get project details. User must be a workspace member."""
    return project_service.get_project_detail(db, project_id, current_user)


@router.patch("/{project_id}", response_model=ProjectDetailResponse)
def update_project(
    project_id: UUID,
    payload: ProjectUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update project. Workspace owner only."""
    return project_service.update_project(db, project_id, current_user, payload, request)


@router.delete("/{project_id}")
def delete_project(
    project_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete project. Workspace owner only. Does not delete GIS datasets."""
    return project_service.delete_project(db, project_id, current_user, request)


@router.post("/{project_id}/archive")
def archive_project(
    project_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Archive project (soft-delete). Workspace owner only."""
    return project_service.archive_project(db, project_id, current_user, request)


# ==========================================================================
# PROJECT LAYER MANAGEMENT
# ==========================================================================

@router.get("/{project_id}/layers", response_model=List[ProjectLayerResponse])
def get_project_layers(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List layers assigned to a project."""
    return project_service.get_project_layers(db, project_id, current_user)


@router.post("/{project_id}/layers", response_model=ProjectLayerResponse, status_code=status.HTTP_201_CREATED)
def add_project_layer(
    project_id: UUID,
    payload: ProjectLayerAddRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a GIS layer to the project. Workspace owner only."""
    return project_service.add_project_layer(db, project_id, current_user, payload, request)


@router.patch("/{project_id}/layers/{project_layer_id}", response_model=ProjectLayerResponse)
def update_project_layer(
    project_id: UUID,
    project_layer_id: UUID,
    payload: ProjectLayerUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update layer settings (visibility, opacity, order). Workspace owner only."""
    return project_service.update_project_layer(
        db, project_id, project_layer_id, current_user, payload, request
    )


@router.delete("/{project_id}/layers/{project_layer_id}")
def remove_project_layer(
    project_id: UUID,
    project_layer_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove layer from project. Does NOT delete GIS data. Workspace owner only."""
    return project_service.remove_project_layer(
        db, project_id, project_layer_id, current_user, request
    )
