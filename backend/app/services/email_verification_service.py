import random
import string
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.models.email_verification import EmailVerification
from app.core.security import hash_password

class EmailVerificationService:
    def generate_code(self) -> str:
        """Generate 6-digit verification code"""
        return ''.join(random.choices(string.digits, k=6))
    
    def create_verification(self, db: Session, email: str, temp_password: str) -> str:
        """
        Create verification entry with 10-minute expiry.
        Returns the verification code.
        """
        from sqlalchemy import text
        
        code = self.generate_code()
        temp_password_hash = hash_password(temp_password)
        
        # Delete old verification if exists
        db.query(EmailVerification).filter_by(email=email).delete()
        db.commit()
        
        # Use database server time for consistency
        verification = EmailVerification(
            email=email,
            code=code,
            temp_password_hash=temp_password_hash,
            expires_at=text("NOW() + INTERVAL '10 minutes'")
        )
        db.add(verification)
        db.commit()
        db.refresh(verification)  # Get actual values from DB
        
        print(f"DEBUG: Created verification code for {email}")
        print(f"DEBUG: Code: {code}")
        print(f"DEBUG: Expires at: {verification.expires_at}")
        
        return code
    
    def verify_code(self, db: Session, email: str, code: str) -> EmailVerification:
        """
        Verify code and return verification entry.
        Raises ValueError if invalid.
        """
        from datetime import timezone
        
        # Trim input code
        clean_code = code.strip()
        
        # Debug logging
        print(f"DEBUG: Verifying code for email: {email}")
        print(f"DEBUG: Code received: '{clean_code}' (length: {len(clean_code)})")
        
        # Get LATEST verification record for this email
        from sqlalchemy import text
        
        verification = db.query(EmailVerification).filter_by(
            email=email
        ).order_by(EmailVerification.created_at.desc()).first()
        
        if not verification:
            print(f"DEBUG: No verification found for email: {email}")
            raise ValueError("Invalid verification code")
        
        # Debug info
        print(f"DEBUG: Verification record found")
        print(f"DEBUG: Expected code: '{verification.code}'")
        print(f"DEBUG: Received code: '{clean_code}'")
        print(f"DEBUG: Expires at: {verification.expires_at}")
        
        # Check if already used
        if verification.verified:
            print(f"DEBUG: Code already used")
            raise ValueError("Code already used")
        
        # Check expiry using database time (more reliable)
        is_expired = db.execute(
            text("SELECT :expires_at < NOW()"),
            {"expires_at": verification.expires_at}
        ).scalar()
        
        if is_expired:
            print(f"DEBUG: Code expired")
            raise ValueError("Code expired. Please request a new one")
        
        # Compare codes (simple string comparison after trim)
        if clean_code != verification.code:
            print(f"DEBUG: Code mismatch!")
            raise ValueError("Invalid verification code")
        
        print(f"DEBUG: Code verified successfully!")
        return verification
    
    def mark_as_verified(self, db: Session, verification: EmailVerification):
        """Mark verification as used and delete it"""
        verification.verified = True
        db.commit()
        
        # Delete after verified to prevent reuse
        db.delete(verification)
        db.commit()
        print(f"DEBUG: Verification record deleted")
    
    def send_verification_email(self, email: str, code: str):
        """
        Send verification code via email using SMTP.
        """
        from app.core.email import send_verification_code_email
        
        success = send_verification_code_email(email, code)
        
        if not success:
            # Log error but don't fail the entire flow
            print(f"WARNING: Failed to send email to {email}")
            print(f"===========================================")
            print(f"VERIFICATION CODE FOR {email}:")
            print(f"{code}")
            print(f"This code expires in 10 minutes.")
            print(f"===========================================")

# Create singleton instance
email_verification_service = EmailVerificationService()
