from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.db.models.user import UserRole

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str  # Frontend sends 'name'


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    name: str
    role: str
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True


class MagicLinkRequest(BaseModel):
    email: EmailStr


class UpdateUserRoleRequest(BaseModel):
    user_id: str
    role: UserRole


class GoogleOAuthRequest(BaseModel):
    id_token: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class SessionResponse(BaseModel):
    id: UUID
    device_name: Optional[str]
    ip_address: Optional[str]
    last_active: datetime
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class LogoutRequest(BaseModel):
    refresh_token: str


# ===== SIGNUP SCHEMAS (Multi-step) =====

class SignupInitRequest(BaseModel):
    email: EmailStr

class SignupInitResponse(BaseModel):
    status: str = "password_required"
    email: EmailStr

class SignupPasswordRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)

class SignupPasswordResponse(BaseModel):
    status: str = "verification_sent"
    email: EmailStr
    message: str = "Verification code sent to your email"

class SignupVerifyRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)

class SignupVerifyResponse(BaseModel):
    status: str = "profile_required"
    email: EmailStr
    temp_token: str  # Temporary token to proceed to profile completion

class SignupCompleteRequest(BaseModel):
    email: EmailStr
    temp_token: str
    name: str
    birthday: str  # Format: YYYY-MM-DD

# Response is TokenResponse (auto-login)


# ===== ADMIN SCHEMAS =====

# Admin Magic Link
class AdminMagicLinkRequest(BaseModel):
    email: EmailStr

class AdminMagicLinkResponse(BaseModel):
    status: str = "magic_link_sent"
    message: str = "If this is an admin account, a magic link has been sent"

# Passwordless OTP Login (for returning users)
class LoginOTPRequest(BaseModel):
    email: EmailStr

class LoginOTPResponse(BaseModel):
    status: str = "otp_sent"
    email: EmailStr
    message: str = "OTP sent to your email"

class LoginOTPVerifyRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)

# Response is TokenResponse

# Admin verify returns TokenResponse
