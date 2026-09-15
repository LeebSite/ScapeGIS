import secrets
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.models.magic_link import MagicLink
from app.db.models.user import User

class MagicLinkService:
    def create_magic_link(self, db: Session, user: User, expires_in_minutes: int = 10) -> str:
        """
        Generate a secure token, save it to DB, and return it.
        """
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
        
        magic_link = MagicLink(
            user_id=user.id,
            token=token,
            expires_at=expires_at
        )
        
        db.add(magic_link)
        db.commit()
        
        return token

    def verify_token(self, db: Session, token: str) -> MagicLink:
        """
        Verify if the token is valid, unused, and not expired.
        Raises ValueError if invalid.
        """
        magic_link = db.query(MagicLink).filter(MagicLink.token == token).first()
        
        if not magic_link:
            raise ValueError("Invalid token")
        
        if magic_link.used:
            raise ValueError("Token already used")
            
        if magic_link.expires_at < datetime.utcnow():
            raise ValueError("Token expired")
            
        return magic_link

    def mark_as_used(self, db: Session, magic_link: MagicLink):
        """
        Mark token as used.
        """
        magic_link.used = True
        db.commit()

    def send_magic_link_email(self, email: str, token: str):
        """Send magic link email via SMTP"""
        from app.core.email import send_magic_link_email
        
        success = send_magic_link_email(email, token)
        
        if not success:
            # Fallback to console print if email fails
            magic_link = f"http://localhost:3000/admin/verify?token={token}"
            print(f"===========================================")
            print(f"MAGIC LINK FOR {email}:")
            print(f"{magic_link}")
            print(f"===========================================")

# Create singleton instance
magic_link_service = MagicLinkService()
