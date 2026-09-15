from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
import uuid
from app.db.base import Base


class GISFeature(Base):
    """GIS Feature model - stores individual features with PostGIS geometries"""
    __tablename__ = "gis_features"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    layer_id = Column(UUID(as_uuid=True), ForeignKey("gis_layers.id", ondelete="CASCADE"), nullable=False)
    
    # PostGIS geometry column - EPSG:4326 (WGS 84)
    geom = Column(Geometry(geometry_type='GEOMETRY', srid=4326), nullable=False)
    
    # Feature properties/attributes as JSONB
    properties = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    layer = relationship("GISLayer", back_populates="features")
