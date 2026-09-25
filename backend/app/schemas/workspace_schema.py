from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# ==========================================================================
# REQUEST SCHEMAS
# ==========================================================================

class WorkspaceCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Workspace name")
    description: Optional[str] = Field(None, max_length=1000)


class WorkspaceUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    logo_url: Optional[str] = None


class InviteMemberRequest(BaseModel):
    email: str = Field(..., description="Email of the person to invite")


# ==========================================================================
# RESPONSE SCHEMAS
# ==========================================================================

class WorkspaceMemberResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    user_id: UUID
    role: str
    joined_at: datetime
    # Nested user info
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    user_avatar_url: Optional[str] = None

    class Config:
        from_attributes = True


class WorkspaceListResponse(BaseModel):
    """Lightweight workspace info for list view"""
    id: UUID
    name: str
    slug: str
    description: Optional[str]
    logo_url: Optional[str]
    role: str           # Current user's role in this workspace
    member_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class WorkspaceDetailResponse(BaseModel):
    """Full workspace details"""
    id: UUID
    name: str
    slug: str
    description: Optional[str]
    logo_url: Optional[str]
    owner_id: UUID
    role: str           # Current user's role in this workspace
    member_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkspaceCreateResponse(BaseModel):
    message: str
    workspace_id: UUID


class InviteMemberResponse(BaseModel):
    message: str
    token: str
    invitation_id: UUID


class AcceptInvitationResponse(BaseModel):
    message: str
    workspace_id: UUID
    workspace_name: str
