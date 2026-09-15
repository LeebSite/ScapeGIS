from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base


class GISDataset(Base):
    """GIS Dataset model - represents a collection of GIS layers uploaded by a user"""
    __tablename__ = "gis_datasets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Dataset information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # File information
    original_filename = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)  # 'shapefile', 'geojson', 'kml', 'geopackage'
    file_size = Column(Integer, nullable=True)  # Size in bytes
    file_path = Column(Text, nullable=True)  # Path to stored file
    source = Column(String(100), nullable=True)  # e.g., 'upload', 'external_url'
    
    # Spatial information
    bbox = Column(JSON, nullable=True)  # Bounding box [minx, miny, maxx, maxy]
    crs = Column(String(50), nullable=True)  # Original CRS string (e.g., 'EPSG:32747')
    srid = Column(Integer, default=4326)     # Target SRID (always 4326 for storage)
    geometry_type = Column(String(20), nullable=True) # Dominant geometry type
    
    # Stats
    total_layers = Column(Integer, default=0)
    total_features = Column(Integer, default=0)
    
    # Processing status
    status = Column(String(50), default='pending', nullable=False)  # 'pending', 'processing', 'completed', 'failed'
    error_message = Column(Text, nullable=True)
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)  # Additional metadata (renamed from metadata to avoid SQLAlchemy reserved word)
    is_public = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="gis_datasets")
    layers = relationship("GISLayer", back_populates="dataset", cascade="all, delete-orphan")
