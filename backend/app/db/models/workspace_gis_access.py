import uuid
from sqlalchemy import Column, String, Text, Boolean, ForeignKey, DateTime, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class WorkspaceGISAccess(Base):
    """
    WorkspaceGISAccess model - represents an entitlement grant
    giving a Workspace access to a platform GIS Dataset.
    """
    __tablename__ = "workspace_gis_access"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    dataset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("gis_datasets.id", ondelete="CASCADE"),
        nullable=False,
    )
    granted_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(Text, nullable=True)

    granted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    workspace = relationship("Workspace", back_populates="gis_accesses")
    dataset = relationship("GISDataset", back_populates="workspace_accesses")
    granter = relationship("User", foreign_keys=[granted_by])

    __table_args__ = (
        UniqueConstraint("workspace_id", "dataset_id", name="uq_workspace_gis_access"),
        Index("ix_workspace_gis_access_workspace_id", "workspace_id"),
        Index("ix_workspace_gis_access_dataset_id", "dataset_id"),
        Index("ix_workspace_gis_access_is_active", "is_active"),
    )