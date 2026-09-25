import uuid
from sqlalchemy import Column, Text, ForeignKey, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class WorkspaceInvitation(Base):
    """WorkspaceInvitation - pending invitation to join a workspace"""
    __tablename__ = "workspace_invitations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    email = Column(Text, nullable=False)
    token = Column(Text, unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    workspace = relationship("Workspace", back_populates="invitations")

    __table_args__ = (
        Index("ix_workspace_invitations_token", "token"),
        Index("ix_workspace_invitations_email", "email"),
        Index("ix_workspace_invitations_workspace_id", "workspace_id"),
    )
