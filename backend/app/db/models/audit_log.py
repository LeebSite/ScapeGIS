from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)  # e.g., 'user.login', 'project.create'
    resource_type = Column(String(50), nullable=True)  # e.g., 'project', 'layer'
    resource_id = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=False)  # IPv4 or IPv6
    user_agent = Column(Text, nullable=True)
    details = Column(JSONB, nullable=True)  # Additional context
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    # Indexes for efficient querying
    __table_args__ = (
        Index('ix_audit_logs_user_id', 'user_id'),
        Index('ix_audit_logs_action', 'action'),
        Index('ix_audit_logs_created_at', 'created_at'),
    )
