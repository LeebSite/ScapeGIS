from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from app.db.models.user import User
from datetime import datetime, timedelta, timezone


def get_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def get_by_id(db: Session, user_id: str):
    return db.query(User).filter(User.id == user_id).first()


def get_all_users(db: Session):
    """Get all users for admin dashboard"""
    return db.query(User).all()

def get_user_by_id_with_relations(db: Session, user_id: str):
    """Get user with all auth-related relations for detailed view"""
    return db.query(User).options(
        joinedload(User.oauth_accounts),
        joinedload(User.refresh_tokens),
        joinedload(User.audit_logs)
    ).filter(User.id == user_id).first()



def create(db: Session, user: User):
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_role(db: Session, user_id: str, new_role):
    user = get_by_id(db, user_id)
    if user:
        user.role = new_role
        db.commit()
        db.refresh(user)
    return user


def update_status(db: Session, user_id: str, is_active: bool):
    user = get_by_id(db, user_id)
    if user:
        user.is_active = is_active
        db.commit()
        db.refresh(user)
    return user


def delete(db: Session, user_id: str):
    user = get_by_id(db, user_id)
    if user:
        db.delete(user)
        db.commit()
    return user


# Statistics functions for admin dashboard
def get_total_users(db: Session) -> int:
    return db.query(func.count(User.id)).scalar()


def get_active_users_count(db: Session) -> int:
    return db.query(func.count(User.id)).filter(User.is_active == True).scalar()


def get_verified_users_count(db: Session) -> int:
    return db.query(func.count(User.id)).filter(User.is_verified == True).scalar()


def get_user_count_by_role(db: Session) -> dict:
    """Get count of users grouped by role"""
    result = db.query(User.role, func.count(User.id)).group_by(User.role).all()
    return {str(role): count for role, count in result}


def get_user_count_by_auth_provider(db: Session) -> dict:
    """Get count of users grouped by auth provider"""
    result = db.query(User.auth_provider, func.count(User.id)).group_by(User.auth_provider).all()
    return {provider: count for provider, count in result}


def get_new_users_count(db: Session, days: int = 30) -> int:
    """Get count of users created in the last N days"""
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    return db.query(func.count(User.id)).filter(User.created_at >= cutoff_date).scalar()

