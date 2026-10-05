"""
Spatial AI Context & Authorization Manager

Builds safe, compact, deterministic context for LLM reasoning.
Ensures the LLM never sees unauthorized datasets or layers,
and never receives raw data dumps (no raw GeoJSON or full feature tables).
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session

from app.db.models.user import User
from app.db.models.workspace import Workspace
from app.db.models.workspace_member import WorkspaceMember
from app.db.models.workspace_gis_access import WorkspaceGISAccess
from app.db.models.project import Project
from app.db.models.gis_layer import GISLayer
from app.db.models.layer_semantic import LayerSemantic
from app.services.semantic import semantic_service
from app.spatial_ai.exceptions import SpatialAIAuthorizationError


# ── Authorization Validation Helpers ──

def validate_user_workspace_access(db: Session, user: User, workspace_id: UUID) -> Workspace:
    """
    Enforces that user is either a Platform Admin or an active Workspace Member.
    Source of truth is ALWAYS the authenticated User object from JWT, never LLM input.
    """
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise SpatialAIAuthorizationError(
            f"Workspace with ID '{workspace_id}' does not exist.",
            details={"workspace_id": str(workspace_id)},
        )

    # Admin bypass
    if user.role.value == "admin":
        return workspace

    member = (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user.id,
        )
        .first()
    )
    if not member:
        raise SpatialAIAuthorizationError(
            f"User '{user.email}' is not an authorized member of workspace '{workspace.name}'.",
            details={"workspace_id": str(workspace_id), "user_id": str(user.id)},
        )

    return workspace


def validate_project_access(db: Session, workspace_id: UUID, project_id: UUID) -> Project:
    """Verifies project exists and belongs strictly to the authorized workspace."""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.workspace_id == workspace_id)
        .first()
    )
    if not project:
        raise SpatialAIAuthorizationError(
            f"Project with ID '{project_id}' was not found in workspace '{workspace_id}'.",
            details={"project_id": str(project_id), "workspace_id": str(workspace_id)},
        )
    return project


def get_authorized_dataset_ids(db: Session, workspace_id: UUID) -> List[UUID]:
    """Retrieves all active dataset IDs explicitly granted to this workspace."""
    rows = (
        db.query(WorkspaceGISAccess.dataset_id)
        .filter(
            WorkspaceGISAccess.workspace_id == workspace_id,
            WorkspaceGISAccess.is_active == True,
        )
        .all()
    )
    return [r.dataset_id for r in rows]


def validate_layer_authorization(
    db: Session,
    layer_id: UUID,
    authorized_dataset_ids: List[UUID],
) -> GISLayer:
    """Ensures a specific layer belongs to a dataset currently authorized for the workspace."""
    layer = db.query(GISLayer).filter(GISLayer.id == layer_id).first()
    if not layer:
        raise SpatialAIAuthorizationError(
            f"GIS Layer '{layer_id}' does not exist.",
            details={"layer_id": str(layer_id)},
        )

    if layer.dataset_id not in authorized_dataset_ids:
        raise SpatialAIAuthorizationError(
            f"GIS Layer '{layer.name}' belongs to an unauthorized dataset. Access denied.",
            details={"layer_id": str(layer_id), "dataset_id": str(layer.dataset_id)},
        )

    return layer


# ── Spatial AI Context Models ──

class SpatialConceptSummary(BaseModel):
    category: str
    subcategory: str
    display_name: str
    description: Optional[str] = None
    capabilities: List[str] = Field(default_factory=list)
    layer_name: Optional[str] = None


class SpatialAIContext(BaseModel):
    """
    Deterministic context prepared for an AI Agent / LLM.
    Contains solely verified metadata, authorized concepts, and tools.
    """
    user_id: str
    user_email: str
    workspace_id: str
    workspace_name: str
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    project_city: Optional[str] = None
    project_province: Optional[str] = None
    project_type: Optional[str] = None
    authorized_dataset_ids: List[str] = Field(default_factory=list)
    authorized_datasets: List[Dict[str, Any]] = Field(default_factory=list)
    available_concepts: List[SpatialConceptSummary] = Field(default_factory=list)
    available_tools: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

    def to_system_prompt_summary(self) -> str:
        """
        Generates a token-efficient text summary suitable for injection
        into Gemini's system instructions. (< 400 tokens).
        """
        lines = [
            f"=== SCAPEGIS SPATIAL INTELLIGENCE ENVIRONMENT ===",
            f"Workspace: {self.workspace_name} (ID: {self.workspace_id})",
        ]
        if self.project_name:
            lines.append(
                f"Project: {self.project_name} | Location: {self.project_city or 'Unknown'}, {self.project_province or 'Unknown'} | Type: {self.project_type or 'General'}"
            )

        ds_names = [d.get("name", "GIS Dataset") for d in self.authorized_datasets]
        lines.append(f"Authorized GIS Datasets ({len(ds_names)}): {', '.join(ds_names) if ds_names else 'None'}")

        # Group concepts by category
        grouped: Dict[str, List[str]] = {}
        for c in self.available_concepts:
            grouped.setdefault(c.category, []).append(f"{c.subcategory} ({c.display_name})")

        lines.append("Available Spatial Concepts:")
        for cat, items in grouped.items():
            lines.append(f"  • {cat.capitalize()}: {', '.join(items)}")

        lines.append(f"Callable Spatial Tools: {', '.join(self.available_tools)}")
        lines.append(
            "RULE: Always call backend spatial tools to retrieve facts. Never invent or hallucinate distances, counts, or boundaries."
        )
        return "\n".join(lines)


# ── Context Builder ──

def build_spatial_ai_context(
    db: Session,
    user: User,
    workspace_id: UUID,
    project_id: Optional[UUID] = None,
) -> SpatialAIContext:
    """
    Constructs a verified, safe SpatialAIContext object.
    Enforces authorization, loads active semantic concepts,
    and returns a clean model for AI prompt injection.
    """
    workspace = validate_user_workspace_access(db, user, workspace_id)

    project_name = None
    project_city = None
    project_province = None
    project_type = None

    if project_id:
        proj = validate_project_access(db, workspace_id, project_id)
        project_name = proj.name
        project_city = proj.city
        project_province = proj.province
        project_type = proj.project_type.value if proj.project_type else None

    # Authorized datasets
    auth_dataset_ids = get_authorized_dataset_ids(db, workspace_id)
    auth_datasets_info = []
    if auth_dataset_ids:
        from app.db.models.gis_dataset import GISDataset
        ds_rows = db.query(GISDataset).filter(GISDataset.id.in_(auth_dataset_ids)).all()
        for ds in ds_rows:
            auth_datasets_info.append({
                "id": str(ds.id),
                "name": ds.name,
                "file_type": ds.file_type,
                "status": ds.status,
            })

    # Available semantic concepts
    semantics = semantic_service.get_semantics_for_workspace(
        db, workspace_id, ai_enabled_only=True
    )

    concepts: List[SpatialConceptSummary] = []
    seen_subcategories = set()

    for sem in semantics:
        if sem.subcategory in seen_subcategories:
            continue
        seen_subcategories.add(sem.subcategory)

        # Capabilities mapping based on geometry/category
        caps = ["nearest", "radius_search"]
        if sem.category == "administrative":
            caps.append("containment")
        if sem.category == "transportation":
            caps.append("intersection")

        layer_name = sem.layer.name if sem.layer else None

        concepts.append(
            SpatialConceptSummary(
                category=sem.category,
                subcategory=sem.subcategory,
                display_name=sem.display_name,
                description=sem.description,
                capabilities=caps,
                layer_name=layer_name,
            )
        )

    # Core available spatial tools
    core_tools = [
        "get_spatial_context",
        "find_nearest",
        "search_radius",
        "check_containment",
        "find_intersections",
    ]

    return SpatialAIContext(
        user_id=str(user.id),
        user_email=user.email,
        workspace_id=str(workspace.id),
        workspace_name=workspace.name,
        project_id=str(project_id) if project_id else None,
        project_name=project_name,
        project_city=project_city,
        project_province=project_province,
        project_type=project_type,
        authorized_dataset_ids=[str(i) for i in auth_dataset_ids],
        authorized_datasets=auth_datasets_info,
        available_concepts=concepts,
        available_tools=core_tools,
    )
