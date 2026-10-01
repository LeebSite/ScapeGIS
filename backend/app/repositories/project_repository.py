"""
Project Repository - Pure SQLAlchemy DB operations only.
No business logic here.
"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional
from uuid import UUID

from app.db.models.project import Project
from app.db.models.project_layer import ProjectLayer


# ==========================================================================
# PROJECT OPERATIONS
# ==========================================================================

def create(db: Session, project: Project) -> Project:
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_by_id(db: Session, project_id: UUID) -> Optional[Project]:
    return (
        db.query(Project)
        .options(joinedload(Project.workspace))
        .filter(Project.id == project_id)
        .first()
    )


def list_by_workspace(db: Session, workspace_id: UUID) -> List[Project]:
    return (
        db.query(Project)
        .filter(Project.workspace_id == workspace_id)
        .order_by(Project.created_at.desc())
        .all()
    )


def update(db: Session, project_id: UUID, **kwargs) -> Optional[Project]:
    project = db.query(Project).filter(Project.id == project_id).first()
    if project:
        for key, value in kwargs.items():
            if hasattr(project, key):
                setattr(project, key, value)
        db.commit()
        db.refresh(project)
    return project


def delete(db: Session, project_id: UUID) -> bool:
    project = db.query(Project).filter(Project.id == project_id).first()
    if project:
        db.delete(project)
        db.commit()
        return True
    return False


def count_layers(db: Session, project_id: UUID) -> int:
    return (
        db.query(func.count(ProjectLayer.id))
        .filter(ProjectLayer.project_id == project_id)
        .scalar()
    )


# ==========================================================================
# PROJECT LAYER OPERATIONS
# ==========================================================================

def add_layer(db: Session, project_layer: ProjectLayer) -> ProjectLayer:
    db.add(project_layer)
    db.commit()
    db.refresh(project_layer)
    return project_layer


def get_layer(db: Session, project_layer_id: UUID) -> Optional[ProjectLayer]:
    return (
        db.query(ProjectLayer)
        .options(joinedload(ProjectLayer.layer), joinedload(ProjectLayer.dataset))
        .filter(ProjectLayer.id == project_layer_id)
        .first()
    )


def get_layer_by_project_and_gis_layer(
    db: Session, project_id: UUID, layer_id: UUID
) -> Optional[ProjectLayer]:
    return (
        db.query(ProjectLayer)
        .filter(
            ProjectLayer.project_id == project_id,
            ProjectLayer.layer_id == layer_id,
        )
        .first()
    )


def list_layers(db: Session, project_id: UUID) -> List[ProjectLayer]:
    return (
        db.query(ProjectLayer)
        .options(joinedload(ProjectLayer.layer), joinedload(ProjectLayer.dataset))
        .filter(ProjectLayer.project_id == project_id)
        .order_by(ProjectLayer.layer_order)
        .all()
    )


def update_layer(db: Session, project_layer_id: UUID, **kwargs) -> Optional[ProjectLayer]:
    pl = db.query(ProjectLayer).filter(ProjectLayer.id == project_layer_id).first()
    if pl:
        for key, value in kwargs.items():
            if hasattr(pl, key) and value is not None:
                setattr(pl, key, value)
        db.commit()
        db.refresh(pl)
    return pl


def delete_layer(db: Session, project_layer_id: UUID) -> bool:
    pl = db.query(ProjectLayer).filter(ProjectLayer.id == project_layer_id).first()
    if pl:
        db.delete(pl)
        db.commit()
        return True
    return False
