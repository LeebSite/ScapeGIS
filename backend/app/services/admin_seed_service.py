from sqlalchemy.orm import Session
from app.db.models.user import User, UserRole

def seed_admin(db: Session) -> User:
    """
    Seed admin account for mhd.ghalibpradipa@gmail.com.
    Returns existing admin or creates new one.
    """
    admin_email = "mhd.ghalibpradipa@gmail.com"
    
    # Check if already exists
    existing = db.query(User).filter_by(email=admin_email).first()
    if existing:
        print(f"Admin account already exists: {admin_email}")
        return existing
    
    # Create admin
    admin = User(
        email=admin_email,
        name="Admin",
        role=UserRole.ADMIN,
        auth_provider="local",
        is_verified=False,  # Must verify via magic link on first login
        is_active=True,
        hashed_password=None  # No password - admin uses magic link
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    
    print(f"✅ Admin account created: {admin_email}")
    print(f"Admin must use magic link to login")
    
    return admin
