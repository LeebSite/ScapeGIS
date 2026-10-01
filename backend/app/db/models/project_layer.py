import uuid
from sqlalchemy import Column, Boolean, Integer, Float, ForeignKey, DateTime, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class ProjectLayer(Base):
    """ProjectLayer - links a Project to a GIS Dataset/Layer"""
    __tablename__ = "project_layers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("gis_datasets.id", ondelete="CASCADE"), nullable=False)
    layer_id = Column(UUID(as_uuid=True), ForeignKey("gis_layers.id", ondelete="CASCADE"), nullable=False)

    is_visible = Column(Boolean, default=True, nullable=False)
    opacity = Column(Float, default=1.0, nullable=False)
    layer_order = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="project_layers")
    dataset = relationship("GISDataset")
    layer = relationship("GISLayer")

    __table_args__ = (
        UniqueConstraint("project_id", "layer_id", name="uq_project_layer"),
        Index("ix_project_layers_project_id", "project_id"),
        Index("ix_project_layers_layer_id", "layer_id"),
    )
