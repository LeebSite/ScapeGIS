from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.db.models.user import UserRole


# User list response (for table view)
class UserListResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    auth_provider: str
    is_active: bool
    is_verified: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Detailed user information
class UserDetailResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    auth_provider: str
    avatar_url: Optional[str] = None
    is_active: bool
    is_verified: bool
    oauth_account_count: int = 0
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# User statistics for dashboard
class UserStatisticsResponse(BaseModel):
    total_users: int
    active_users: int
    inactive_users: int
    verified_users: int
    users_by_role: dict  # {"admin": 1, "developer": 10}
    users_by_auth_provider: dict  # {"local": 8, "google": 3}
    new_users_last_30_days: int


# Request schemas
class UpdateUserStatusRequest(BaseModel):
    is_active: bool


class UpdateUserRoleRequest(BaseModel):
    role: UserRole
