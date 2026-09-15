from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


# Request Schemas
class GISDatasetCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_public: bool = False


class GISDatasetUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_public: Optional[bool] = None


class GISLayerCreateRequest(BaseModel):
    dataset_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    geometry_type: Optional[str] = None
    geojson_data: Optional[Dict[str, Any]] = None
    style: Optional[Dict[str, Any]] = None


class GISLayerUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_visible: Optional[bool] = None
    layer_order: Optional[int] = None
    style: Optional[Dict[str, Any]] = None


# Response Schemas
class GISLayerResponse(BaseModel):
    id: UUID
    dataset_id: UUID
    name: str
    description: Optional[str]
    geometry_type: Optional[str]
    feature_count: int
    bbox: Optional[List[float]]
    crs: Optional[str]
    geojson_data: Optional[Dict[str, Any]]
    style: Optional[Dict[str, Any]]
    is_visible: bool
    layer_order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GISDatasetResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    original_filename: str
    file_type: str
    file_size: Optional[int]
    source: Optional[str]
    bbox: Optional[List[float]]
    crs: Optional[str]
    srid: Optional[int]
    geometry_type: Optional[str]
    total_layers: int = 0
    total_features: int = 0
    status: str
    error_message: Optional[str]
    is_public: bool
    created_at: datetime
    updated_at: datetime
    layers: List[GISLayerResponse] = []

    class Config:
        from_attributes = True


class GISDatasetListResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    file_type: str
    status: str
    is_public: bool
    layer_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class GISDatasetUploadResponse(BaseModel):
    dataset_id: UUID
    message: str
    status: str
