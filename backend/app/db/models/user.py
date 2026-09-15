from sqlalchemy import Column, String, Boolean, DateTime, Enum, Text, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(150), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)  # Nullable for OAuth users

    name = Column(String(150), nullable=True)  # Nullable until profile completion
    role = Column(Enum(UserRole), default=UserRole.DEVELOPER, nullable=False)
    birthday = Column(Date, nullable=True)  # For profile completion

    # OAuth fields
    auth_provider = Column(String(50), default='local', nullable=False)  # 'local' | 'google' | 'admin_magic_link'
    provider_id = Column(String(255), nullable=True)  # OAuth provider's user ID
    avatar_url = Column(Text, nullable=True)

    # Status fields
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    oauth_accounts = relationship("OAuthAccount", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")
    user_permissions = relationship("UserPermission", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    magic_links = relationship("MagicLink", back_populates="user", cascade="all, delete-orphan")
    gis_datasets = relationship("GISDataset", back_populates="user", cascade="all, delete-orphan")


