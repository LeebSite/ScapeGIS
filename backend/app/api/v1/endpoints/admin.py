from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from app.api.deps import get_db, require_admin
from app.services import admin_service
from app.db.models.user import User
from app.core.audit import log_audit
from app.db.models.audit_log import AuditLog
from app.schemas.audit_schema import AuditLogListResponse
from app.schemas.admin_schema import (
    UserListResponse,
    UserDetailResponse,
    UpdateUserStatusRequest,
    UpdateUserRoleRequest,
    UserStatisticsResponse
)

from app.core.permissions import require_permissions

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users", response_model=List[UserListResponse])
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("users.read"))
):
    """
    Get all users with summary information.
    Requires users.read permission.
    """
    return admin_service.get_all_users_with_details(db)


@router.get("/users/statistics", response_model=UserStatisticsResponse)
def get_user_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("users.read"))
):
    """
    Get user statistics for admin dashboard.
    Requires users.read endpoint.
    """
    return admin_service.get_user_statistics(db)


@router.get("/users/{user_id}", response_model=UserDetailResponse)
def get_user_detail(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("users.read"))
):
    """
    Get detailed information for a specific user.
    Requires users.read permission.
    """
    return admin_service.get_user_detail_by_id(db, user_id)


@router.put("/users/{user_id}/status")
def update_user_status(
    user_id: str,
    payload: UpdateUserStatusRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("users.update_status"))
):
    """
    Update user active status.
    Requires users.update_status permission.
    """
    result = admin_service.update_user_status(db, user_id, payload.is_active)
    
    # Audit log
    log_audit(
        db=db,
        user=current_user,
        action="user.update_status",
        resource_type="User",
        resource_id=user_id,
        request=request,
        details={"is_active": payload.is_active}
    )
    
    return result


@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: str,
    payload: UpdateUserRoleRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("users.update_role"))
):
    """
    Update user role.
    Requires users.update_role permission.
    """
    result = admin_service.update_user_role(db, user_id, payload.role)
    
    # Audit log
    log_audit(
        db=db,
        user=current_user,
        action="user.update_role",
        resource_type="User",
        resource_id=user_id,
        request=request,
        details={"new_role": payload.role}
    )
    
    return result


@router.delete("/users/{user_id}")
def delete_user(
    user_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("users.delete"))
):
    """
    Delete user from the system.
    Requires users.delete permission.
    """
    result = admin_service.delete_user(db, user_id)
    
    # Audit log
    log_audit(
        db=db,
        user=current_user,
        action="user.delete",
        resource_type="User",
        resource_id=user_id,
        request=request
    )
    
    return result


@router.get("/audit-logs", response_model=AuditLogListResponse)
def get_audit_logs(
    limit: int = 100,
    offset: int = 0,
    action: Optional[str] = None,
    user_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("audit.read"))
):
    """
    Get audit logs.
    Requires audit.read permission.
    """
    query = db.query(AuditLog)
    
    if action:
        query = query.filter(AuditLog.action == action)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    
    total = query.count()
    logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "logs": logs
    }

