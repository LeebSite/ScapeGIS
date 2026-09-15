import hashlib
from user_agents import parse as parse_user_agent
from fastapi import Request
from sqlalchemy.orm import Session
from app.db.models.session import Session as UserSession
from app.db.models.user import User
from datetime import datetime, timedelta
import uuid

def generate_device_fingerprint(user_agent: str, ip_address: str) -> str:
    """Generate a consistent fingerprint for the device"""
    fingerprint_data = f"{user_agent}{ip_address}"
    return hashlib.sha256(fingerprint_data.encode()).hexdigest()

def get_device_name(user_agent_string: str) -> str:
    """Extract friendly device name from user agent"""
    if not user_agent_string:
        return "Unknown Device"
        
    try:
        ua = parse_user_agent(user_agent_string)
        browser = ua.browser.family
        os = ua.os.family
        device = ua.device.family
        
        if device != "Other":
            return f"{browser} on {device} ({os})"
        return f"{browser} on {os}"
    except Exception:
        return "Unknown Device"

def create_session(
    db: Session,
    user_id: str,
    refresh_token_jti: str,
    request: Request,
    expires_in_days: int = 7
) -> UserSession:
    """Create a new session record"""
    user_agent = request.headers.get("user-agent", "")
    ip_address = request.client.host if request.client else "0.0.0.0"
    
    session = UserSession(
        user_id=user_id,
        refresh_token_jti=refresh_token_jti,
        device_name=get_device_name(user_agent),
        device_fingerprint=generate_device_fingerprint(user_agent, ip_address),
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=datetime.utcnow() + timedelta(days=expires_in_days)
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    return session
