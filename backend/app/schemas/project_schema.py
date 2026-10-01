from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# ==========================================================================
# REQUEST SCHEMAS
# ==========================================================================

class ProjectCreateRequest(BaseModel):
    workspace_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    project_type: str = Field(default="other")
    city: Optional[str] = Field(None, max_length=255)
    province: Optional[str] = Field(None, max_length=255)


class ProjectUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    project_type: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    status: Optional[str] = None


class ProjectLayerAddRequest(BaseModel):
    dataset_id: UUID
    layer_id: UUID


class ProjectLayerUpdateRequest(BaseModel):
    is_visible: Optional[bool] = None
    opacity: Optional[float] = Field(None, ge=0.0, le=1.0)
    layer_order: Optional[int] = None


# ==========================================================================
# RESPONSE SCHEMAS
# ==========================================================================

class ProjectResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    created_by: Optional[UUID] = None
    name: str
    description: Optional[str] = None
    project_type: str
    city: Optional[str] = None
    province: Optional[str] = None
    status: str
    layer_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    items: List[ProjectResponse]
    total: int


class ProjectDetailResponse(ProjectResponse):
    workspace_name: Optional[str] = None
    creator_name: Optional[str] = None


class ProjectLayerResponse(BaseModel):
    id: UUID
    project_id: UUID
    dataset_id: UUID
    layer_id: UUID
    # From GIS layer
    name: Optional[str] = None
    geometry_type: Optional[str] = None
    feature_count: int = 0
    bbox: Optional[list] = None
    # ProjectLayer settings
    is_visible: bool = True
    opacity: float = 1.0
    layer_order: int = 0
    created_at: datetime

    class Config:
        from_attributes = True
