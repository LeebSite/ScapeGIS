"""
Spatial API Pydantic Schemas
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


# ─── Layer Semantic Schemas ───────────────────────────────────────────────────

class LayerSemanticResponse(BaseModel):
    id: UUID
    layer_id: UUID
    category: str
    subcategory: str
    display_name: str
    description: Optional[str] = None
    ai_enabled: bool
    semantic_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    # Joined from GISLayer
    layer_name: Optional[str] = None
    geometry_type: Optional[str] = None
    feature_count: Optional[int] = None

    class Config:
        from_attributes = True


class LayerSemanticSummary(BaseModel):
    layer_id: UUID
    category: str
    subcategory: str
    display_name: str
    ai_enabled: bool

    class Config:
        from_attributes = True


# ─── Spatial Request Schemas ──────────────────────────────────────────────────

class CoordinateRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude (WGS 84)")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude (WGS 84)")

    @field_validator("latitude")
    @classmethod
    def lat_not_zero(cls, v: float) -> float:
        return v

    @field_validator("longitude")
    @classmethod
    def lng_not_zero(cls, v: float) -> float:
        return v


class NearestRequest(CoordinateRequest):
    subcategory: str = Field(..., description="Semantic subcategory (e.g. 'hospital', 'arterial_road')")
    workspace_id: UUID


class RadiusRequest(CoordinateRequest):
    subcategory: str = Field(..., description="Semantic subcategory")
    radius_meters: float = Field(2000.0, gt=0, le=50000, description="Search radius in meters")
    workspace_id: UUID


class SpatialContextRequest(CoordinateRequest):
    workspace_id: UUID
    project_id: Optional[UUID] = None


class ContainmentRequest(CoordinateRequest):
    layer_id: UUID
    workspace_id: UUID


class IntersectionRequest(CoordinateRequest):
    layer_id: UUID
    workspace_id: UUID
    buffer_meters: float = Field(100.0, gt=0, le=5000)


# ─── Spatial Response Schemas ─────────────────────────────────────────────────

class NearestFeatureResult(BaseModel):
    feature_id: str
    distance_meters: float
    properties: Dict[str, Any]
    layer_id: Optional[str] = None
    layer_name: Optional[str] = None
    display_name: Optional[str] = None
    subcategory: Optional[str] = None


class RadiusFeature(BaseModel):
    feature_id: str
    distance_meters: float
    properties: Dict[str, Any]
    layer_id: Optional[str] = None
    display_name: Optional[str] = None


class RadiusSearchResult(BaseModel):
    latitude: float
    longitude: float
    subcategory: str
    radius_meters: float
    count: int
    features: List[RadiusFeature]


class ContainmentResult(BaseModel):
    feature_id: str
    properties: Dict[str, Any]


class SpatialFactItem(BaseModel):
    type: str
    category: str
    subcategory: str
    display_name: Optional[str] = None
    layer_id: Optional[str] = None
    distance_meters: Optional[float] = None
    count_within_2km: Optional[int] = None
    count_within_1km: Optional[int] = None
    area_name: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None


class SpatialContextResponse(BaseModel):
    location: Dict[str, float]
    workspace_id: str
    project_id: Optional[str] = None
    project: Optional[Dict[str, Any]] = None
    authorized_datasets: List[str]
    transportation: Dict[str, Any]
    facilities: Dict[str, Any]
    religious: Dict[str, Any]
    administrative: Dict[str, Any]
    facts: List[SpatialFactItem]
    warning: Optional[str] = None


# ─── Seed Response ────────────────────────────────────────────────────────────

class SemanticSeedResponse(BaseModel):
    created: int
    updated: int
    skipped: int
    total_catalog_entries: int
    message: str
