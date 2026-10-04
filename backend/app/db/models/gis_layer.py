from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base


class GISLayer(Base):
    """GIS Layer model - represents individual layers within a GIS dataset"""
    __tablename__ = "gis_layers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("gis_datasets.id", ondelete="CASCADE"), nullable=False)
    
    # Layer information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Geometry information
    geometry_type = Column(String(50), nullable=True)  # 'Point', 'LineString', 'Polygon', 'MultiPoint', etc.
    feature_count = Column(Integer, default=0)
    
    # Spatial information
    bbox = Column(JSON, nullable=True)  # Bounding box [minx, miny, maxx, maxy]
    crs = Column(String(50), nullable=True)  # Coordinate Reference System
    
    # GeoJSON data
    geojson_data = Column(JSON, nullable=True)  # Simplified GeoJSON for preview
    full_geojson_path = Column(Text, nullable=True)  # Path to full GeoJSON file if large
    
    # Styling
    style = Column(JSON, nullable=True)  # Layer styling configuration
    
    # Attributes/Properties
    properties_schema = Column(JSON, nullable=True)  # Schema of layer properties
    
    # Visibility and ordering
    is_visible = Column(Boolean, default=True)
    layer_order = Column(Integer, default=0)  # For layer ordering in map
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)  # Extra metadata (renamed from metadata to avoid SQL Alchemy reserved word)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    dataset = relationship("GISDataset", back_populates="layers")
    features = relationship("GISFeature", back_populates="layer", cascade="all, delete-orphan")
    semantic = relationship("LayerSemantic", back_populates="layer", uselist=False, cascade="all, delete-orphan")
