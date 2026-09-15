from sqlalchemy.orm import Session
from typing import List
from app.repositories import user_repo
from app.db.models.user import User, UserRole
from app.schemas.admin_schema import (
    UserListResponse,
    UserDetailResponse,
    UserStatisticsResponse
)
from fastapi import HTTPException, status


def get_all_users_with_details(db: Session) -> List[UserListResponse]:
    """
    Get all users with summary information for admin dashboard table
    """
    users = user_repo.get_all_users(db)
    
    user_list = []
    for user in users:
        user_list.append(UserListResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            role=user.role,
            auth_provider=user.auth_provider,
            is_active=user.is_active,
            is_verified=user.is_verified,
            last_login_at=user.last_login_at,
            created_at=user.created_at
        ))
    
    return user_list


def get_user_detail_by_id(db: Session, user_id: str) -> UserDetailResponse:
    """
    Get detailed information for a specific user
    """
    user = user_repo.get_user_by_id_with_relations(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    return UserDetailResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        role=user.role,
        auth_provider=user.auth_provider,
        avatar_url=user.avatar_url,
        is_active=user.is_active,
        is_verified=user.is_verified,
        oauth_account_count=len(user.oauth_accounts) if user.oauth_accounts else 0,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


def get_user_statistics(db: Session) -> UserStatisticsResponse:
    """
    Get user statistics for admin dashboard overview
    """
    total_users = user_repo.get_total_users(db)
    active_users = user_repo.get_active_users_count(db)
    verified_users = user_repo.get_verified_users_count(db)
    users_by_role = user_repo.get_user_count_by_role(db)
    users_by_auth_provider = user_repo.get_user_count_by_auth_provider(db)
    new_users_last_30_days = user_repo.get_new_users_count(db, 30)
    
    return UserStatisticsResponse(
        total_users=total_users,
        active_users=active_users,
        inactive_users=total_users - active_users,
        verified_users=verified_users,
        users_by_role=users_by_role,
        users_by_auth_provider=users_by_auth_provider,
        new_users_last_30_days=new_users_last_30_days
    )


def update_user_status(db: Session, user_id: str, is_active: bool):
    """
    Update user active status
    """
    user = user_repo.update_status(db, user_id, is_active)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    return {"message": f"User status updated to {'active' if is_active else 'inactive'}"}


def update_user_role(db: Session, user_id: str, new_role: UserRole):
    """
    Update user role
    """
    user = user_repo.update_role(db, user_id, new_role)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    return {"message": f"User role updated to {new_role}"}


def delete_user(db: Session, user_id: str):
    """
    Delete user from system
    """
    user = user_repo.delete(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    return {"message": f"User {user.email} deleted successfully"}
