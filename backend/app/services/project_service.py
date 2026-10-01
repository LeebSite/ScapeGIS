"""
Project Service - All business logic for project management.
Authorization is based on Workspace membership/role.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status, Request
from sqlalchemy.orm import Session

from app.db.models.audit_log import AuditLog
from app.db.models.user import User
from app.db.models.project import Project, ProjectType, ProjectStatus
from app.db.models.project_layer import ProjectLayer
from app.db.models.workspace_member import WorkspaceMember, WorkspaceMemberRole
from app.db.models.gis_dataset import GISDataset
from app.db.models.gis_layer import GISLayer
from app.repositories import project_repository as repo
from app.repositories import workspace_repository as ws_repo
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
    ip = request.client.host if request.client else "0.0.0.0"
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type="project",
        resource_id=resource_id,
        ip_address=ip,
        user_agent=request.headers.get("user-agent"),
        details=details,
    )
    db.add(log)
    db.commit()


def _get_workspace_member(db: Session, workspace_id: UUID, user_id: UUID) -> WorkspaceMember:
    """Require user to be a workspace member. Returns member record."""
    member = ws_repo.get_member(db, workspace_id, user_id)
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return member


def _require_workspace_owner(db: Session, workspace_id: UUID, user_id: UUID) -> WorkspaceMember:
    """Require workspace owner role."""
    member = _get_workspace_member(db, workspace_id, user_id)
    if member.role != WorkspaceMemberRole.OWNER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner access required")
    return member


def _get_project_or_404(db: Session, project_id: UUID) -> Project:
    """Get project or raise 404."""
    project = repo.get_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


def _validate_project_type(value: str) -> ProjectType:
    """Validate and convert project_type string to enum."""
    try:
        return ProjectType(value.lower())
    except ValueError:
        valid = [t.value for t in ProjectType]
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid project_type. Must be one of: {valid}",
        )


def _validate_project_status(value: str) -> ProjectStatus:
    """Validate and convert status string to enum."""
    try:
        return ProjectStatus(value.lower())
    except ValueError:
        valid = [s.value for s in ProjectStatus]
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status. Must be one of: {valid}",
        )


def _build_project_response(db: Session, project: Project) -> ProjectResponse:
    return ProjectResponse(
        id=project.id,
        workspace_id=project.workspace_id,
        created_by=project.created_by,
        name=project.name,
        description=project.description,
        project_type=project.project_type.value if project.project_type else "other",
        city=project.city,
        province=project.province,
        status=project.status.value if project.status else "draft",
        layer_count=repo.count_layers(db, project.id),
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


def _build_project_detail_response(db: Session, project: Project) -> ProjectDetailResponse:
    ws_name = project.workspace.name if project.workspace else None
    creator_name = project.creator.name if project.creator else None
    return ProjectDetailResponse(
        id=project.id,
        workspace_id=project.workspace_id,
        created_by=project.created_by,
        name=project.name,
        description=project.description,
        project_type=project.project_type.value if project.project_type else "other",
        city=project.city,
        province=project.province,
        status=project.status.value if project.status else "draft",
        layer_count=repo.count_layers(db, project.id),
        created_at=project.created_at,
        updated_at=project.updated_at,
        workspace_name=ws_name,
        creator_name=creator_name,
    )


def _build_project_layer_response(pl: ProjectLayer) -> ProjectLayerResponse:
    return ProjectLayerResponse(
        id=pl.id,
        project_id=pl.project_id,
        dataset_id=pl.dataset_id,
        layer_id=pl.layer_id,
        name=pl.layer.name if pl.layer else None,
        geometry_type=pl.layer.geometry_type if pl.layer else None,
        feature_count=pl.layer.feature_count if pl.layer else 0,
        bbox=pl.layer.bbox if pl.layer else None,
        is_visible=pl.is_visible,
        opacity=pl.opacity,
        layer_order=pl.layer_order,
        created_at=pl.created_at,
    )


# ==========================================================================
# PROJECT CRUD
# ==========================================================================

def create_project(
    db: Session, current_user: User, payload: ProjectCreateRequest, request: Request
) -> ProjectResponse:
    """Create project. User must be workspace owner."""
    workspace = ws_repo.get_by_id(db, payload.workspace_id)
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

    _require_workspace_owner(db, payload.workspace_id, current_user.id)

    project_type = _validate_project_type(payload.project_type)

    project = Project(
        workspace_id=payload.workspace_id,
        created_by=current_user.id,
        name=payload.name,
        description=payload.description,
        project_type=project_type,
        city=payload.city,
        province=payload.province,
        status=ProjectStatus.DRAFT,
    )
    project = repo.create(db, project)

    _create_audit_log(
        db, str(current_user.id), "project.created", request,
        resource_id=str(project.id),
        details={
            "project_name": project.name,
            "workspace_id": str(payload.workspace_id),
        },
    )

    return _build_project_response(db, project)


def get_projects(
    db: Session, current_user: User, workspace_id: UUID
) -> ProjectListResponse:
    """List projects in a workspace. User must be a member."""
    workspace = ws_repo.get_by_id(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

    _get_workspace_member(db, workspace_id, current_user.id)

    projects = repo.list_by_workspace(db, workspace_id)
    items = [_build_project_response(db, p) for p in projects]
    return ProjectListResponse(items=items, total=len(items))


def get_project_detail(
    db: Session, project_id: UUID, current_user: User
) -> ProjectDetailResponse:
    """Get project detail. User must be workspace member."""
    project = _get_project_or_404(db, project_id)
    _get_workspace_member(db, project.workspace_id, current_user.id)
    return _build_project_detail_response(db, project)


def update_project(
    db: Session, project_id: UUID, current_user: User,
    payload: ProjectUpdateRequest, request: Request,
) -> ProjectDetailResponse:
    """Update project. Workspace owner only."""
    project = _get_project_or_404(db, project_id)
    _require_workspace_owner(db, project.workspace_id, current_user.id)

    update_data = payload.model_dump(exclude_unset=True)

    if "project_type" in update_data and update_data["project_type"] is not None:
        update_data["project_type"] = _validate_project_type(update_data["project_type"])

    if "status" in update_data and update_data["status"] is not None:
        update_data["status"] = _validate_project_status(update_data["status"])

    repo.update(db, project_id, **update_data)

    _create_audit_log(
        db, str(current_user.id), "project.updated", request,
        resource_id=str(project_id),
        details={"updated_fields": list(update_data.keys())},
    )

    return get_project_detail(db, project_id, current_user)


def archive_project(
    db: Session, project_id: UUID, current_user: User, request: Request,
) -> dict:
    """Archive a project (soft-delete). Workspace owner only."""
    project = _get_project_or_404(db, project_id)
    _require_workspace_owner(db, project.workspace_id, current_user.id)

    repo.update(db, project_id, status=ProjectStatus.ARCHIVED)

    _create_audit_log(
        db, str(current_user.id), "project.archived", request,
        resource_id=str(project_id),
        details={"project_name": project.name},
    )

    return {"message": "Project archived"}


def delete_project(
    db: Session, project_id: UUID, current_user: User, request: Request,
) -> dict:
    """Hard delete project. Workspace owner only. Does NOT delete GIS datasets."""
    project = _get_project_or_404(db, project_id)
    _require_workspace_owner(db, project.workspace_id, current_user.id)
    name = project.name

    repo.delete(db, project_id)

    _create_audit_log(
        db, str(current_user.id), "project.deleted", request,
        resource_id=str(project_id),
        details={"project_name": name},
    )

    return {"message": "Project deleted"}


# ==========================================================================
# PROJECT LAYER MANAGEMENT
# ==========================================================================

def get_project_layers(
    db: Session, project_id: UUID, current_user: User
) -> List[ProjectLayerResponse]:
    """List layers in a project. User must be workspace member."""
    project = _get_project_or_404(db, project_id)
    _get_workspace_member(db, project.workspace_id, current_user.id)

    layers = repo.list_layers(db, project_id)
    return [_build_project_layer_response(pl) for pl in layers]


def add_project_layer(
    db: Session, project_id: UUID, current_user: User,
    payload: ProjectLayerAddRequest, request: Request,
) -> ProjectLayerResponse:
    """Add a GIS layer to a project. Workspace owner only."""
    project = _get_project_or_404(db, project_id)
    _require_workspace_owner(db, project.workspace_id, current_user.id)

    # Verify dataset exists
    dataset = db.query(GISDataset).filter(GISDataset.id == payload.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")

    # Verify layer exists and belongs to dataset
    layer = db.query(GISLayer).filter(
        GISLayer.id == payload.layer_id,
        GISLayer.dataset_id == payload.dataset_id,
    ).first()
    if not layer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Layer not found in the specified dataset",
        )

    # Prevent duplicates
    existing = repo.get_layer_by_project_and_gis_layer(db, project_id, payload.layer_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This layer is already added to the project",
        )

    # Determine next layer_order
    current_layers = repo.list_layers(db, project_id)
    next_order = max((pl.layer_order for pl in current_layers), default=-1) + 1

    project_layer = ProjectLayer(
        project_id=project_id,
        dataset_id=payload.dataset_id,
        layer_id=payload.layer_id,
        layer_order=next_order,
    )
    project_layer = repo.add_layer(db, project_layer)

    # Reload with relationships
    project_layer = repo.get_layer(db, project_layer.id)

    _create_audit_log(
        db, str(current_user.id), "project.layer_added", request,
        resource_id=str(project_id),
        details={
            "layer_id": str(payload.layer_id),
            "dataset_id": str(payload.dataset_id),
            "layer_name": layer.name,
        },
    )

    return _build_project_layer_response(project_layer)


def update_project_layer(
    db: Session, project_id: UUID, project_layer_id: UUID,
    current_user: User, payload: ProjectLayerUpdateRequest, request: Request,
) -> ProjectLayerResponse:
    """Update layer settings (visibility, opacity, order). Workspace owner only."""
    project = _get_project_or_404(db, project_id)
    _require_workspace_owner(db, project.workspace_id, current_user.id)

    pl = repo.get_layer(db, project_layer_id)
    if not pl or pl.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project layer not found")

    update_data = payload.model_dump(exclude_unset=True)
    repo.update_layer(db, project_layer_id, **update_data)

    # Reload
    pl = repo.get_layer(db, project_layer_id)

    _create_audit_log(
        db, str(current_user.id), "project.layer_updated", request,
        resource_id=str(project_id),
        details={"project_layer_id": str(project_layer_id), "updated_fields": list(update_data.keys())},
    )

    return _build_project_layer_response(pl)


def remove_project_layer(
    db: Session, project_id: UUID, project_layer_id: UUID,
    current_user: User, request: Request,
) -> dict:
    """Remove layer from project. Does NOT delete the GIS dataset/layer. Workspace owner only."""
    project = _get_project_or_404(db, project_id)
    _require_workspace_owner(db, project.workspace_id, current_user.id)

    pl = repo.get_layer(db, project_layer_id)
    if not pl or pl.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project layer not found")

    layer_name = pl.layer.name if pl.layer else "Unknown"
    repo.delete_layer(db, project_layer_id)

    _create_audit_log(
        db, str(current_user.id), "project.layer_removed", request,
        resource_id=str(project_id),
        details={"project_layer_id": str(project_layer_id), "layer_name": layer_name},
    )

    return {"message": "Layer removed from project"}
