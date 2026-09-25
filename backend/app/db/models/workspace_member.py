import enum
import uuid
from sqlalchemy import Column, ForeignKey, DateTime, Enum, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class WorkspaceMemberRole(str, enum.Enum):
    OWNER = "owner"
    MEMBER = "member"


class WorkspaceMember(Base):
    """WorkspaceMember - represents a user's membership in a workspace"""
    __tablename__ = "workspace_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(Enum(WorkspaceMemberRole), default=WorkspaceMemberRole.MEMBER, nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    workspace = relationship("Workspace", back_populates="members")
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="uq_workspace_member"),
        Index("ix_workspace_members_workspace_id", "workspace_id"),
        Index("ix_workspace_members_user_id", "user_id"),
    )
