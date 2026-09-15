from fastapi import Request
from sqlalchemy.orm import Session
from app.db.models.audit_log import AuditLog
from app.db.models.user import User
from typing import Optional, Dict, Any

def log_audit(
    db: Session,
    user: Optional[User],
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    request: Optional[Request] = None,
    details: Optional[Dict[str, Any]] = None,
):
    """
    Create an audit log entry in the database.
    
    Args:
        db: Database session
        user: User performing the action (can be None)
        action: Action name (e.g., 'user.delete')
        resource_type: Type of resource (e.g., 'User')
        resource_id: ID of the resource
        request: FastAPI Request object to extract IP and User-Agent
        details: Additional context/metadata
    """
    audit_log = AuditLog(
        user_id=str(user.id) if user else None,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=request.client.host if request else "0.0.0.0",
        user_agent=request.headers.get("user-agent") if request else None,
        details=details
    )
    
    db.add(audit_log)
    db.commit()
    
    return audit_log
