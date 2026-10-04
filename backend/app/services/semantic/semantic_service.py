"""
Semantic Service — business logic for GIS Layer Semantic catalog.

Provides CRUD, workspace-scoped discovery, and the idempotent
Pekanbaru seeder that populates semantic metadata for existing layers.
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.models.gis_layer import GISLayer
from app.db.models.gis_dataset import GISDataset
from app.db.models.layer_semantic import LayerSemantic
from app.db.models.workspace_gis_access import WorkspaceGISAccess
from app.services.semantic.catalog_presets import PEKANBARU_CATALOG


# ─── Read Helpers ────────────────────────────────────────────────────────────

def get_semantic_by_layer(db: Session, layer_id: UUID) -> Optional[LayerSemantic]:
    return db.query(LayerSemantic).filter(LayerSemantic.layer_id == layer_id).first()


def get_all_semantics(db: Session, ai_enabled_only: bool = True) -> List[LayerSemantic]:
    q = db.query(LayerSemantic)
    if ai_enabled_only:
        q = q.filter(LayerSemantic.ai_enabled == True)
    return q.order_by(LayerSemantic.category, LayerSemantic.subcategory).all()


def get_semantics_for_workspace(
    db: Session,
    workspace_id: UUID,
    ai_enabled_only: bool = True,
) -> List[LayerSemantic]:
    """
    Return semantic records only for layers belonging to datasets
    that the given workspace is authorized to access.

    This enforces the authorization chain:
      Workspace → WorkspaceGISAccess → GISDataset → GISLayer → LayerSemantic
    """
    authorized_dataset_ids = (
        db.query(WorkspaceGISAccess.dataset_id)
        .filter(
            WorkspaceGISAccess.workspace_id == workspace_id,
            WorkspaceGISAccess.is_active == True,
        )
        .subquery()
    )

    q = (
        db.query(LayerSemantic)
        .join(GISLayer, LayerSemantic.layer_id == GISLayer.id)
        .filter(GISLayer.dataset_id.in_(authorized_dataset_ids))
    )

    if ai_enabled_only:
        q = q.filter(LayerSemantic.ai_enabled == True)

    return q.order_by(LayerSemantic.category, LayerSemantic.subcategory).all()


def get_semantics_by_category(
    db: Session,
    category: str,
    workspace_id: Optional[UUID] = None,
) -> List[LayerSemantic]:
    """Get semantics filtered by category, optionally scoped to workspace."""
    if workspace_id:
        semantics = get_semantics_for_workspace(db, workspace_id)
        return [s for s in semantics if s.category == category]

    return (
        db.query(LayerSemantic)
        .filter(LayerSemantic.category == category, LayerSemantic.ai_enabled == True)
        .all()
    )


def get_semantics_by_subcategory(
    db: Session,
    subcategory: str,
    workspace_id: Optional[UUID] = None,
) -> List[LayerSemantic]:
    """Get semantics filtered by subcategory, optionally scoped to workspace."""
    if workspace_id:
        semantics = get_semantics_for_workspace(db, workspace_id)
        return [s for s in semantics if s.subcategory == subcategory]

    return (
        db.query(LayerSemantic)
        .filter(LayerSemantic.subcategory == subcategory, LayerSemantic.ai_enabled == True)
        .all()
    )


# ─── Write Helpers ────────────────────────────────────────────────────────────

def upsert_semantic(
    db: Session,
    layer_id: UUID,
    category: str,
    subcategory: str,
    display_name: str,
    description: Optional[str] = None,
    ai_enabled: bool = True,
    semantic_metadata: Optional[dict] = None,
) -> LayerSemantic:
    """Create or update a LayerSemantic record."""
    existing = get_semantic_by_layer(db, layer_id)
    if existing:
        existing.category = category
        existing.subcategory = subcategory
        existing.display_name = display_name
        existing.description = description
        existing.ai_enabled = ai_enabled
        existing.semantic_metadata = semantic_metadata or {}
        db.commit()
        db.refresh(existing)
        return existing

    semantic = LayerSemantic(
        layer_id=layer_id,
        category=category,
        subcategory=subcategory,
        display_name=display_name,
        description=description,
        ai_enabled=ai_enabled,
        semantic_metadata=semantic_metadata or {},
    )
    db.add(semantic)
    db.commit()
    db.refresh(semantic)
    return semantic


# ─── Pekanbaru Seeder ────────────────────────────────────────────────────────

def seed_pekanbaru_semantics(db: Session) -> dict:
    """
    Idempotent seeder: populates semantic metadata for Pekanbaru GIS layers.

    Matching logic:
      - For each catalog entry, find GIS layers whose name contains
        the name_pattern (case-insensitive).
      - Prefer layers that do NOT have the _SHAPEFILE suffix as primary,
        mark duplicates as ai_enabled=False to prevent double-counting.

    Returns a summary dict with counts.
    """
    from app.services.semantic.catalog_presets import PEKANBARU_CATALOG

    created = 0
    updated = 0
    skipped = 0

    for entry in PEKANBARU_CATALOG:
        pattern = entry["name_pattern"].lower()

        # Find all matching layers across all datasets
        matching_layers = (
            db.query(GISLayer)
            .filter(func.lower(GISLayer.name).contains(pattern))
            .order_by(GISLayer.name)
            .all()
        )

        if not matching_layers:
            skipped += 1
            continue

        # Prefer non-SHAPEFILE variant as the AI-primary layer
        primary_layers = [l for l in matching_layers if "_SHAPEFILE" not in l.name.upper()]
        secondary_layers = [l for l in matching_layers if "_SHAPEFILE" in l.name.upper()]

        # If only shapefile variants exist, use them
        if not primary_layers:
            primary_layers = secondary_layers
            secondary_layers = []

        for layer in primary_layers:
            existing = get_semantic_by_layer(db, layer.id)
            semantic = upsert_semantic(
                db=db,
                layer_id=layer.id,
                category=entry["category"],
                subcategory=entry["subcategory"],
                display_name=entry["display_name"],
                description=entry.get("description"),
                ai_enabled=True,
                semantic_metadata=entry.get("semantic_metadata", {}),
            )
            if existing:
                updated += 1
            else:
                created += 1

        # Mark shapefile duplicates as ai_enabled=False (available but not primary)
        for layer in secondary_layers:
            upsert_semantic(
                db=db,
                layer_id=layer.id,
                category=entry["category"],
                subcategory=entry["subcategory"],
                display_name=entry["display_name"] + " (Shapefile)",
                description=entry.get("description"),
                ai_enabled=False,
                semantic_metadata=entry.get("semantic_metadata", {}),
            )
            updated += 1

    return {
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "total_catalog_entries": len(PEKANBARU_CATALOG),
    }
