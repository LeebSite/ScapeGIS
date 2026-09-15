from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from app.core.config import settings
from app.db.models.user import User, UserRole
from app.db.models.oauth_account import OAuthAccount
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def verify_google_token(id_token_str: str) -> dict:
    """
    Verify Google ID token and extract user information
    
    Returns:
        dict with keys: sub, email, name, picture
    """
    try:
        # Verify the token
        idinfo = id_token.verify_oauth2_token(
            id_token_str,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )
        
        # Verify the issuer
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
        
        # Extract user info
        return {
            'sub': idinfo['sub'],  # Google user ID
            'email': idinfo['email'],
            'name': idinfo.get('name', idinfo['email'].split('@')[0]),
            'picture': idinfo.get('picture'),
            'email_verified': idinfo.get('email_verified', False)
        }
        
    except ValueError as e:
        logger.error(f"Google token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token"
        )


def get_or_create_oauth_user(db: Session, provider: str, provider_data: dict) -> User:
    """
    Get existing OAuth user or create new one
    
    Args:
        provider: 'google', 'github', etc.
        provider_data: dict with sub, email, name, picture
    
    Returns:
        User object
    """
    provider_id = provider_data['sub']
    email = provider_data['email']
    
    # Check if OAuth account exists
    oauth_account = db.query(OAuthAccount).filter(
        OAuthAccount.provider == provider,
        OAuthAccount.provider_id == provider_id
    ).first()
    
    if oauth_account:
        # User exists, update last login
        user = oauth_account.user
        user.last_login_at = datetime.utcnow()
        
        # Update avatar if changed
        if provider_data.get('picture'):
            user.avatar_url = provider_data['picture']
        
        db.commit()
        db.refresh(user)
        return user
    
    # Check if user with this email exists (local account)
    existing_user = db.query(User).filter(User.email == email).first()
    
    if existing_user:
        # Link OAuth account to existing user
        new_oauth_account = OAuthAccount(
            user_id=existing_user.id,
            provider=provider,
            provider_id=provider_id
        )
        db.add(new_oauth_account)
        
        # Update user info
        existing_user.auth_provider = provider
        existing_user.provider_id = provider_id
        existing_user.avatar_url = provider_data.get('picture')
        existing_user.is_verified = provider_data.get('email_verified', False)
        existing_user.last_login_at = datetime.utcnow()
        
        db.commit()
        db.refresh(existing_user)
        return existing_user
    
    # Create new user
    new_user = User(
        email=email,
        name=provider_data['name'],
        auth_provider=provider,
        provider_id=provider_id,
        avatar_url=provider_data.get('picture'),
        is_verified=provider_data.get('email_verified', False),
        hashed_password=None,  # No password for OAuth users
        role=UserRole.DEVELOPER,  # Default role
        last_login_at=datetime.utcnow()
    )
    db.add(new_user)
    db.flush()  # Get the user ID
    
    # Create OAuth account record
    oauth_account = OAuthAccount(
        user_id=new_user.id,
        provider=provider,
        provider_id=provider_id
    )
    db.add(oauth_account)
    
    db.commit()
    db.refresh(new_user)
    
    logger.info(f"Created new OAuth user: {email} via {provider}")
    return new_user


def link_oauth_account(db: Session, user_id: str, provider: str, provider_data: dict):
    """
    Link an OAuth account to an existing user
    """
    # Check if OAuth account already linked
    existing = db.query(OAuthAccount).filter(
        OAuthAccount.provider == provider,
        OAuthAccount.provider_id == provider_data['sub']
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This OAuth account is already linked to another user"
        )
    
    # Create new OAuth account
    oauth_account = OAuthAccount(
        user_id=user_id,
        provider=provider,
        provider_id=provider_data['sub']
    )
    db.add(oauth_account)
    db.commit()
