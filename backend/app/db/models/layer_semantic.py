"""
GIS Layer Semantic Metadata Model

Maps technical GIS layer names to human-readable semantic concepts.
This is the foundation for the Spatial Knowledge Layer that enables
future AI integration without depending on raw layer naming conventions.
"""
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class LayerSemantic(Base):
    """
    Semantic metadata associated with a GIS layer.

    Maps technical layer names (e.g. Dot_LOKASI_RumahSakit)
    to semantic concepts (e.g. category=public_facility, subcategory=hospital).
    """
    __tablename__ = "gis_layer_semantics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    layer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("gis_layers.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # Semantic classification
    category = Column(String(100), nullable=False)       # e.g. "transportation", "public_facility"
    subcategory = Column(String(100), nullable=False)     # e.g. "arterial_road", "hospital"

    # Human-readable names
    display_name = Column(String(255), nullable=False)    # e.g. "Jalan Arteri", "Rumah Sakit"
    description = Column(Text, nullable=True)

    # AI integration flag - controls whether this layer is discoverable
    # by the future Spatial AI context builder
    ai_enabled = Column(Boolean, default=True, nullable=False)

    # Flexible metadata for future extensions:
    #   aliases, capabilities, attribute_hints, etc.
    semantic_metadata = Column(JSONB, nullable=True, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    layer = relationship("GISLayer", back_populates="semantic", uselist=False)

    __table_args__ = (
        Index("ix_layer_semantics_layer_id", "layer_id"),
        Index("ix_layer_semantics_category", "category"),
        Index("ix_layer_semantics_subcategory", "subcategory"),
        Index("ix_layer_semantics_ai_enabled", "ai_enabled"),
    )

    def __repr__(self):
        return f"<LayerSemantic {self.display_name} ({self.category}/{self.subcategory})>"
