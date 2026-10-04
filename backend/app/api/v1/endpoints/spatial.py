"""
Spatial Knowledge API Endpoints

Authorization chain for every endpoint:
  Authenticated User
    → Workspace Access (member or admin)
      → GIS Dataset Access (WorkspaceGISAccess.is_active)
        → Spatial Query

All PostGIS operations happen in the backend — never in the frontend.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_admin
from app.db.models.user import User
from app.db.models.workspace_member import WorkspaceMember
from app.db.models.workspace_gis_access import WorkspaceGISAccess
from app.db.models.layer_semantic import LayerSemantic
from app.db.models.gis_layer import GISLayer
from app.services.semantic import semantic_service
from app.services import spatial_analysis_service as analysis
from app.services import spatial_context_service as context_svc
from app.schemas.spatial_schema import (
    LayerSemanticResponse,
    LayerSemanticSummary,
    NearestRequest,
    RadiusRequest,
    SpatialContextRequest,
    NearestFeatureResult,
    RadiusSearchResult,
    SpatialContextResponse,
    SemanticSeedResponse,
    ContainmentRequest,
    IntersectionRequest,
    ContainmentResult,
)

router = APIRouter(prefix="/spatial", tags=["Spatial Knowledge"])


# ─── Authorization Helpers ────────────────────────────────────────────────────

def _require_workspace_member(db: Session, workspace_id: UUID, user: User) -> None:
    """Verify user is workspace member or platform admin."""
    if user.role.value == "admin":
        return
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
            detail="You are not a member of this workspace.",
        )


def _require_workspace_gis_access(db: Session, workspace_id: UUID) -> List[UUID]:
    """Return authorized dataset IDs; raise 403 if workspace has no access."""
    rows = (
        db.query(WorkspaceGISAccess.dataset_id)
        .filter(
            WorkspaceGISAccess.workspace_id == workspace_id,
            WorkspaceGISAccess.is_active == True,
        )
        .all()
    )
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No GIS datasets are authorized for this workspace. Ask an Admin to grant access.",
        )
    return [r.dataset_id for r in rows]


# ─── Semantic Layer Discovery ─────────────────────────────────────────────────

@router.get("/layers", response_model=List[LayerSemanticResponse])
def list_semantic_layers(
    workspace_id: UUID = Query(..., description="Workspace ID for authorization scope"),
    category: Optional[str] = Query(None, description="Filter by category"),
    ai_enabled_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all AI-enabled GIS layers with semantic metadata.
    Scoped to datasets authorized for the given workspace.
    """
    _require_workspace_member(db, workspace_id, current_user)

    semantics = semantic_service.get_semantics_for_workspace(db, workspace_id, ai_enabled_only)

    if category:
        semantics = [s for s in semantics if s.category == category]

    result = []
    for s in semantics:
        layer = s.layer
        result.append(
            LayerSemanticResponse(
                id=s.id,
                layer_id=s.layer_id,
                category=s.category,
                subcategory=s.subcategory,
                display_name=s.display_name,
                description=s.description,
                ai_enabled=s.ai_enabled,
                semantic_metadata=s.semantic_metadata,
                created_at=s.created_at,
                updated_at=s.updated_at,
                layer_name=layer.name if layer else None,
                geometry_type=layer.geometry_type if layer else None,
                feature_count=layer.feature_count if layer else None,
            )
        )
    return result


@router.get("/layers/{layer_id}", response_model=LayerSemanticResponse)
def get_semantic_layer(
    layer_id: UUID,
    workspace_id: UUID = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get semantic metadata for a specific GIS layer."""
    _require_workspace_member(db, workspace_id, current_user)

    semantic = (
        db.query(LayerSemantic)
        .join(GISLayer, LayerSemantic.layer_id == GISLayer.id)
        .filter(LayerSemantic.layer_id == layer_id)
        .first()
    )
    if not semantic:
        raise HTTPException(status_code=404, detail="Semantic metadata not found for this layer.")

    # Verify the layer belongs to an authorized dataset
    authorized_ids = _require_workspace_gis_access(db, workspace_id)
    layer = semantic.layer
    if layer and layer.dataset_id not in authorized_ids:
        raise HTTPException(status_code=403, detail="Layer not authorized for this workspace.")

    return LayerSemanticResponse(
        id=semantic.id,
        layer_id=semantic.layer_id,
        category=semantic.category,
        subcategory=semantic.subcategory,
        display_name=semantic.display_name,
        description=semantic.description,
        ai_enabled=semantic.ai_enabled,
        semantic_metadata=semantic.semantic_metadata,
        created_at=semantic.created_at,
        updated_at=semantic.updated_at,
        layer_name=layer.name if layer else None,
        geometry_type=layer.geometry_type if layer else None,
        feature_count=layer.feature_count if layer else None,
    )


# ─── Spatial Operations ───────────────────────────────────────────────────────

@router.post("/nearest", response_model=NearestFeatureResult)
def find_nearest(
    payload: NearestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Find the nearest feature for a given semantic subcategory.

    Example: nearest hospital, nearest arterial road, nearest mosque.
    Authorization: workspace_id must be authorized for the relevant GIS dataset.
    """
    _require_workspace_member(db, payload.workspace_id, current_user)

    result = context_svc.build_quick_nearest(
        db=db,
        lat=payload.latitude,
        lng=payload.longitude,
        subcategory=payload.subcategory,
        workspace_id=payload.workspace_id,
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No features found for subcategory '{payload.subcategory}' in authorized datasets.",
        )

    return NearestFeatureResult(**result)


@router.post("/radius", response_model=RadiusSearchResult)
def radius_search(
    payload: RadiusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Find all features within radius_meters for a semantic subcategory.

    Example: hospitals within 2km, mosques within 1km.
    """
    _require_workspace_member(db, payload.workspace_id, current_user)

    result = context_svc.build_radius_search(
        db=db,
        lat=payload.latitude,
        lng=payload.longitude,
        subcategory=payload.subcategory,
        radius_meters=payload.radius_meters,
        workspace_id=payload.workspace_id,
    )

    return RadiusSearchResult(**result)


@router.post("/context")
def spatial_context(
    payload: SpatialContextRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Build a complete spatial context for a location.

    Returns structured facts about transportation, facilities, religious
    sites, and administrative boundaries — all within workspace scope.

    This endpoint is designed as the foundation for future AI integration.
    """
    _require_workspace_member(db, payload.workspace_id, current_user)

    context = context_svc.build_spatial_context(
        db=db,
        lat=payload.latitude,
        lng=payload.longitude,
        workspace_id=payload.workspace_id,
        project_id=payload.project_id,
    )

    return context


@router.post("/containment", response_model=Optional[ContainmentResult])
def containment_check(
    payload: ContainmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Check which polygon feature contains the given point.
    Useful for: "Which kecamatan is this location in?"
    """
    _require_workspace_member(db, payload.workspace_id, current_user)
    authorized_ids = _require_workspace_gis_access(db, payload.workspace_id)

    # Verify layer belongs to authorized dataset
    layer = db.query(GISLayer).filter(GISLayer.id == payload.layer_id).first()
    if not layer:
        raise HTTPException(status_code=404, detail="Layer not found.")
    if layer.dataset_id not in authorized_ids:
        raise HTTPException(status_code=403, detail="Layer not authorized for this workspace.")

    result = analysis.find_containing_area(db, payload.latitude, payload.longitude, payload.layer_id)
    if not result:
        return None

    return ContainmentResult(**result)


@router.post("/intersection")
def intersection_check(
    payload: IntersectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Find features that intersect a buffered point.
    Useful for: "Which roads are near this location?"
    """
    _require_workspace_member(db, payload.workspace_id, current_user)
    authorized_ids = _require_workspace_gis_access(db, payload.workspace_id)

    layer = db.query(GISLayer).filter(GISLayer.id == payload.layer_id).first()
    if not layer:
        raise HTTPException(status_code=404, detail="Layer not found.")
    if layer.dataset_id not in authorized_ids:
        raise HTTPException(status_code=403, detail="Layer not authorized for this workspace.")

    return analysis.find_intersecting_features(
        db, payload.latitude, payload.longitude, payload.layer_id, payload.buffer_meters
    )


# ─── Admin: Seed Semantic Catalog ────────────────────────────────────────────

@router.post("/admin/seed-semantics", response_model=SemanticSeedResponse)
def seed_semantics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Admin only: Seed semantic metadata for existing Pekanbaru GIS layers.
    This is idempotent — safe to run multiple times.
    """
    summary = semantic_service.seed_pekanbaru_semantics(db)
    return SemanticSeedResponse(
        **summary,
        message=f"Semantic catalog seeded successfully. {summary['created']} created, {summary['updated']} updated.",
    )
