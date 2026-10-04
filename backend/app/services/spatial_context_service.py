"""
Spatial Context Service

Converts raw GIS data into structured spatial facts about a location.
This structured context is the input that the future Gemini/AI service
will use to generate human-readable spatial analysis answers.

Authorization is enforced: only layers from workspace-authorized
datasets are included in the context.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.workspace_gis_access import WorkspaceGISAccess
from app.db.models.project import Project
from app.db.models.project_layer import ProjectLayer
from app.db.models.gis_layer import GISLayer
from app.db.models.layer_semantic import LayerSemantic
from app.services import spatial_analysis_service as analysis
from app.services.semantic import semantic_service


def _get_authorized_dataset_ids(db: Session, workspace_id: UUID) -> List[UUID]:
    """Return dataset IDs that workspace has active access to."""
    rows = (
        db.query(WorkspaceGISAccess.dataset_id)
        .filter(
            WorkspaceGISAccess.workspace_id == workspace_id,
            WorkspaceGISAccess.is_active == True,
        )
        .all()
    )
    return [r.dataset_id for r in rows]


def _get_project_workspace(db: Session, project_id: UUID) -> Optional[UUID]:
    """Return workspace_id for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    return project.workspace_id if project else None


# ─── Core Context Builder ────────────────────────────────────────────────────

def build_spatial_context(
    db: Session,
    lat: float,
    lng: float,
    workspace_id: UUID,
    project_id: Optional[UUID] = None,
) -> Dict[str, Any]:
    """
    Build a structured spatial context for location (lat, lng).

    Only includes data from datasets authorized for workspace_id.
    If project_id is provided, additional project metadata is attached.

    Returns a serializable dict suitable for future AI consumption.
    """
    authorized_ids = _get_authorized_dataset_ids(db, workspace_id)

    if not authorized_ids:
        return {
            "location": {"latitude": lat, "longitude": lng},
            "workspace_id": str(workspace_id),
            "project_id": str(project_id) if project_id else None,
            "warning": "No GIS datasets authorized for this workspace.",
            "facts": [],
        }

    # Load all AI-enabled semantics for authorized datasets
    semantics = semantic_service.get_semantics_for_workspace(
        db, workspace_id, ai_enabled_only=True
    )

    facts: List[Dict[str, Any]] = []
    transportation: Dict[str, Any] = {}
    facilities: Dict[str, Any] = {}
    religious: Dict[str, Any] = {}
    administrative: Dict[str, Any] = {}

    for sem in semantics:
        layer = sem.layer
        if not layer:
            continue

        cat = sem.category
        subcat = sem.subcategory

        # ── TRANSPORTATION ───────────────────────────────────────────────────
        if cat == "transportation":
            dist = analysis.calculate_distance_to_nearest(db, lat, lng, layer.id)
            if dist is not None:
                key = f"nearest_{subcat}"
                transportation[key] = {
                    "layer_id": str(layer.id),
                    "display_name": sem.display_name,
                    "distance_meters": round(dist, 2),
                }
                facts.append({
                    "type": "nearest_feature",
                    "category": cat,
                    "subcategory": subcat,
                    "layer_id": str(layer.id),
                    "display_name": sem.display_name,
                    "distance_meters": round(dist, 2),
                })

        # ── PUBLIC FACILITY ──────────────────────────────────────────────────
        elif cat == "public_facility":
            nearest = analysis.find_nearest_feature(db, lat, lng, layer.id)
            count_2km = analysis.count_features_within_radius(db, lat, lng, layer.id, 2000)
            if nearest is not None:
                key = subcat
                facilities[key] = {
                    "nearest_distance_meters": nearest["distance_meters"],
                    "count_within_2km": count_2km,
                    "layer_id": str(layer.id),
                    "display_name": sem.display_name,
                }
                facts.append({
                    "type": "nearest_feature",
                    "category": cat,
                    "subcategory": subcat,
                    "layer_id": str(layer.id),
                    "display_name": sem.display_name,
                    "distance_meters": nearest["distance_meters"],
                    "count_within_2km": count_2km,
                    "nearest_properties": nearest.get("properties", {}),
                })

        # ── RELIGIOUS ────────────────────────────────────────────────────────
        elif cat == "religious":
            count_1km = analysis.count_features_within_radius(db, lat, lng, layer.id, 1000)
            nearest = analysis.find_nearest_feature(db, lat, lng, layer.id)
            key = subcat
            religious[key] = {
                "count_within_1km": count_1km,
                "nearest_distance_meters": nearest["distance_meters"] if nearest else None,
                "layer_id": str(layer.id),
                "display_name": sem.display_name,
            }
            if nearest:
                facts.append({
                    "type": "count_and_nearest",
                    "category": cat,
                    "subcategory": subcat,
                    "layer_id": str(layer.id),
                    "display_name": sem.display_name,
                    "count_within_1km": count_1km,
                    "distance_meters": nearest["distance_meters"],
                })

        # ── ADMINISTRATIVE ───────────────────────────────────────────────────
        elif cat == "administrative":
            containing = analysis.find_containing_area(db, lat, lng, layer.id)
            if containing:
                props = containing.get("properties", {})
                admin_name = (
                    props.get("NAMOBJ")
                    or props.get("REMARK")
                    or props.get("name")
                    or "Unknown"
                )
                administrative[subcat] = {
                    "name": admin_name,
                    "feature_id": containing["feature_id"],
                    "properties": props,
                }
                facts.append({
                    "type": "containment",
                    "category": cat,
                    "subcategory": subcat,
                    "display_name": sem.display_name,
                    "area_name": admin_name,
                    "properties": props,
                })

    # Project context (if provided)
    project_context = None
    if project_id:
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project_context = {
                "id": str(project.id),
                "name": project.name,
                "city": project.city,
                "province": project.province,
                "project_type": project.project_type.value if project.project_type else None,
            }

    return {
        "location": {"latitude": lat, "longitude": lng},
        "workspace_id": str(workspace_id),
        "project_id": str(project_id) if project_id else None,
        "project": project_context,
        "authorized_datasets": [str(d) for d in authorized_ids],
        "transportation": transportation,
        "facilities": facilities,
        "religious": religious,
        "administrative": administrative,
        "facts": facts,
    }


def build_quick_nearest(
    db: Session,
    lat: float,
    lng: float,
    subcategory: str,
    workspace_id: UUID,
) -> Optional[Dict[str, Any]]:
    """
    Quick lookup: nearest feature for a given subcategory in workspace context.
    """
    authorized_ids = _get_authorized_dataset_ids(db, workspace_id)
    layers = analysis.get_layers_for_subcategory(db, subcategory, authorized_ids)

    if not layers:
        return None

    best: Optional[Dict[str, Any]] = None
    for layer in layers:
        sem = db.query(LayerSemantic).filter(LayerSemantic.layer_id == layer.id).first()
        result = analysis.find_nearest_feature(db, lat, lng, layer.id)
        if result:
            result["layer_id"] = str(layer.id)
            result["layer_name"] = layer.name
            result["display_name"] = sem.display_name if sem else layer.name
            result["subcategory"] = subcategory
            if best is None or result["distance_meters"] < best["distance_meters"]:
                best = result

    return best


def build_radius_search(
    db: Session,
    lat: float,
    lng: float,
    subcategory: str,
    radius_meters: float,
    workspace_id: UUID,
) -> Dict[str, Any]:
    """
    Search for features within radius for a given subcategory.
    """
    authorized_ids = _get_authorized_dataset_ids(db, workspace_id)
    layers = analysis.get_layers_for_subcategory(db, subcategory, authorized_ids)

    all_features: List[Dict[str, Any]] = []
    for layer in layers:
        sem = db.query(LayerSemantic).filter(LayerSemantic.layer_id == layer.id).first()
        result = analysis.find_features_within_radius(db, lat, lng, layer.id, radius_meters)
        for feat in result.get("features", []):
            feat["layer_id"] = str(layer.id)
            feat["layer_name"] = layer.name
            feat["display_name"] = sem.display_name if sem else layer.name
            all_features.append(feat)

    all_features.sort(key=lambda x: x["distance_meters"])

    return {
        "latitude": lat,
        "longitude": lng,
        "subcategory": subcategory,
        "radius_meters": radius_meters,
        "count": len(all_features),
        "features": all_features,
    }
