from fastapi import HTTPException, status, Request
from sqlalchemy.orm import Session
from app.repositories import user_repo
from app.db.models.user import User, UserRole
from app.db.models.audit_log import AuditLog
from app.schemas.auth_schema import RegisterRequest, LoginRequest
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_refresh_token
)
from datetime import datetime
import logging
import traceback

logger = logging.getLogger(__name__)


def create_audit_log(db: Session, user_id: str, action: str, ip_address: str, user_agent: str = None, details: dict = None):
    """Helper function to create audit log entries"""
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details
    )
    db.add(audit_log)
    db.commit()


def register(db: Session, payload: RegisterRequest, ip_address: str = "0.0.0.0", user_agent: str = None):
    try:
        existing = user_repo.get_by_email(db, payload.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Determine role - developer for all registrations
        # Admin accounts are created manually via seed
        user_role = UserRole.DEVELOPER

        user = User(
            email=payload.email,
            hashed_password=hash_password(payload.password),
            name=payload.name,  # Use 'name' instead of 'full_name'
            role=user_role,
            auth_provider='local'
        )

        user_repo.create(db, user)

        # Create tokens
        access_token = create_access_token(
            data={"sub": str(user.id), "role": user.role}
        )
        refresh_token = create_refresh_token(str(user.id), db)

        # Create audit log
        create_audit_log(db, str(user.id), "user.register", ip_address, user_agent)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Unhandled exception in register: %s", exc)
        logger.debug(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


def login(db: Session, payload: LoginRequest, ip_address: str = "0.0.0.0", user_agent: str = None):
    # 1. Check if user exists
    user = user_repo.get_by_email(db, payload.email)
    
    if not user:
        # User doesn't exist - frontend will redirect to signup
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 2. Check if admin trying to login with password
    from app.db.models.user import UserRole
    if user.role == UserRole.ADMIN:
        # Admin must use magic link
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin accounts use magic link authentication"
        )
    
    # 3. Verify password
    if not verify_password(payload.password, user.hashed_password):
        # Wrong password - frontend will show error
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Update last login
    user.last_login_at = datetime.utcnow()
    db.commit()

    # Create tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value}
    )
    refresh_token = create_refresh_token(str(user.id), db)

    # Create audit log
    create_audit_log(db, str(user.id), "user.login", ip_address, user_agent)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


def refresh_access_token(refresh_token: str, db: Session):
    """Generate new access token from refresh token"""
    user = verify_refresh_token(refresh_token, db)
    
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


def logout(refresh_token: str, db: Session):
    """Logout by revoking refresh token"""
    from app.core.security import revoke_refresh_token
    
    revoke_refresh_token(refresh_token, db)
    return {"message": "Logged out successfully"}


def update_user_role(db: Session, user_id: str, role: str):
    """Update user role (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.role = role
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: str):
    """Delete user (admin only)"""
    user = user_repo.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user_repo.delete(db, user_id)
    return {"message": "User deleted successfully"}

