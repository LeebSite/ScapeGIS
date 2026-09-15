"""
OTP Login Service - Passwordless login for returning users
"""
import random
import string
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.models.user import User
from app.db.models.email_verification import EmailVerification

class OTPLoginService:
    def generate_code(self) -> str:
        """Generate 6-digit OTP code"""
        return ''.join(random.choices(string.digits, k=6))
    
    def request_otp(self, db: Session, email: str) -> str:
        """
        Generate and send OTP for login.
        Returns the OTP code (to be sent via email).
        """
        # Check if user exists
        user = db.query(User).filter_by(email=email).first()
        if not user:
            raise ValueError("User not found")
        
        # Generate OTP
        code = self.generate_code()
        
        # Delete old OTP if exists
        db.query(EmailVerification).filter_by(email=email).delete()
        db.commit()
        
        # Store OTP (reuse email_verifications table)
        from sqlalchemy import text
        verification = EmailVerification(
            email=email,
            code=code,
            temp_password_hash="",  # Not needed for login OTP
            expires_at=text("NOW() + INTERVAL '10 minutes'")
        )
        db.add(verification)
        db.commit()
        db.refresh(verification)
        
        print(f"DEBUG: Login OTP created for {email}: {code}")
        print(f"DEBUG: Expires at: {verification.expires_at}")
        
        return code
    
    def verify_otp(self, db: Session, email: str, code: str) -> User:
        """
        Verify OTP and return user if valid.
        Raises ValueError if invalid.
        """
        clean_code = code.strip()
        
        print(f"DEBUG: Verifying login OTP for {email}, code: {clean_code}")
        
        # Get latest verification
        verification = db.query(EmailVerification).filter_by(
            email=email
        ).order_by(EmailVerification.created_at.desc()).first()
        
        if not verification:
            print(f"DEBUG: No OTP found for {email}")
            raise ValueError("Invalid or expired OTP")
        
        # Check if already used
        if verification.verified:
            print(f"DEBUG: OTP already used")
            raise ValueError("OTP already used")
        
        # Check expiry using database time
        is_expired = db.execute(
            text("SELECT :expires_at < NOW()"),
            {"expires_at": verification.expires_at}
        ).scalar()
        
        if is_expired:
            print(f"DEBUG: OTP expired")
            raise ValueError("OTP expired. Please request a new one")
        
        # Verify code
        if clean_code != verification.code:
            print(f"DEBUG: OTP mismatch")
            raise ValueError("Invalid OTP")
        
        # Get user
        user = db.query(User).filter_by(email=email).first()
        if not user:
            raise ValueError("User not found")
        
        # Mark as used and delete
        verification.verified = True
        db.commit()
        db.delete(verification)
        db.commit()
        
        print(f"DEBUG: Login OTP verified successfully for {email}")
        
        return user

# Singleton instance
otp_login_service = OTPLoginService()
