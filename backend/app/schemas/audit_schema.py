from pydantic import BaseModel
from typing import Optional, Any, Dict, List
from datetime import datetime
from uuid import UUID

class AuditLogResponse(BaseModel):
    id: UUID
    user_id: Optional[UUID]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    ip_address: str
    user_agent: Optional[str]
    details: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True

class AuditLogListResponse(BaseModel):
    total: int
    logs: List[AuditLogResponse]
