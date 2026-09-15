from fastapi import HTTPException, Depends, status
from sqlalchemy.orm import Session
from app.db.models.user import User
from app.db.models.permission import Permission, RolePermission, UserPermission
from app.api.deps import get_current_user, get_db
from typing import List, Set

def get_user_permissions(user: User, db: Session) -> Set[str]:
    """
    Get all permissions for a user (role-based + user-specific)
    """
    # Get role-based permissions
    role_perms = db.query(Permission.name).join(
        RolePermission, Permission.id == RolePermission.permission_id
    ).filter(
        RolePermission.role == user.role
    ).all()
    
    permissions = {perm[0] for perm in role_perms}
    
    # Get user-specific permission overrides
    user_perms = db.query(Permission.name, UserPermission.granted).join(
        UserPermission, Permission.id == UserPermission.permission_id
    ).filter(
        UserPermission.user_id == user.id
    ).all()
    
    for perm_name, granted in user_perms:
        if granted:
            permissions.add(perm_name)
        else:
            permissions.discard(perm_name)
    
    return permissions


class PermissionChecker:
    def __init__(self, required_permissions: List[str]):
        self.required_permissions = required_permissions
    
    def __call__(
        self,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        # Admin always has full access (optional bypass, but good for safety)
        if current_user.role == "admin":
             # Optimization: Return immediately for admin role if desired
             pass 

        user_permissions = get_user_permissions(current_user, db)
        
        for perm in self.required_permissions:
            if perm not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied. Required: {perm}"
                )
        
        return current_user


def require_permissions(*permissions: str):
    """
    Decorator dependency to require specific permissions.
    Example: @router.get("/", dependencies=[Depends(require_permissions("users.read"))])
    """
    return PermissionChecker(list(permissions))
