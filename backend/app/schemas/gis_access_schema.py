from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from app.schemas.gis_schema import GISLayerResponse


class GISAccessGrantRequest(BaseModel):
    workspace_id: UUID = Field(..., description="ID of the Workspace receiving the entitlement")
    dataset_id: UUID = Field(..., description="ID of the platform GIS Dataset")
    notes: Optional[str] = Field(None, max_length=1000, description="Optional administrative notes")


class GISAccessRevokeRequest(BaseModel):
    workspace_id: UUID = Field(..., description="ID of the Workspace losing entitlement")
    dataset_id: UUID = Field(..., description="ID of the GIS Dataset")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for revocation")


class GISAccessWorkspaceInfo(BaseModel):
    id: UUID
    name: str
    slug: str

    class Config:
        from_attributes = True


class GISAccessDatasetInfo(BaseModel):
    id: UUID
    name: str
    file_type: str
    total_layers: int = 0
    total_features: int = 0
    geometry_type: Optional[str] = None
    status: str

    class Config:
        from_attributes = True


class GISAccessGranterInfo(BaseModel):
    id: UUID
    email: str
    name: Optional[str] = None

    class Config:
        from_attributes = True


class GISAccessResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    dataset_id: UUID
    is_active: bool
    notes: Optional[str] = None
    granted_at: datetime
    revoked_at: Optional[datetime] = None
    workspace: Optional[GISAccessWorkspaceInfo] = None
    dataset: Optional[GISAccessDatasetInfo] = None
    granter: Optional[GISAccessGranterInfo] = None

    class Config:
        from_attributes = True


class GISAccessListResponse(BaseModel):
    total: int
    items: List[GISAccessResponse]


class AuthorizedDatasetResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    file_type: str
    source: Optional[str] = None
    bbox: Optional[List[float]] = None
    crs: Optional[str] = None
    srid: Optional[int] = 4326
    geometry_type: Optional[str] = None
    total_layers: int = 0
    total_features: int = 0
    status: str
    granted_at: datetime
    layers: List[GISLayerResponse] = []

    class Config:
        from_attributes = True