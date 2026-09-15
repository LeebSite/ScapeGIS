from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.schemas.auth_schema import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    UpdateUserRoleRequest,
    GoogleOAuthRequest,
    RefreshTokenRequest,
    LogoutRequest,
    MagicLinkRequest,
    SignupInitRequest,
    SignupInitResponse,
    SignupPasswordRequest,
    SignupPasswordResponse,
    SignupVerifyRequest,
    SignupVerifyResponse,
    SignupCompleteRequest,
    AdminMagicLinkRequest,
    AdminMagicLinkResponse
)
from app.services import auth_service, oauth_service, magic_link_service, email_verification_service
from app.api.deps import get_db, get_current_user, require_admin
from app.db.models.user import User
from app.db.models.email_verification import EmailVerification  # ✅ ADD THIS
from app.core.security import create_access_token, create_refresh_token
from app.core.rate_limit import limiter

router = APIRouter(prefix="/auth", tags=["Auth"])


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]
    return request.client.host if request.client else "0.0.0.0"


@router.post("/register", response_model=TokenResponse)
@limiter.limit("3/hour")
def register(
    request: Request,
    payload: RegisterRequest,
    db: Session = Depends(get_db)
):
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("User-Agent")
    return auth_service.register(db, payload, ip_address, user_agent)


from fastapi import Response

from typing import List
from app.core.session import create_session
from app.db.models.session import Session as UserSession
from app.schemas.auth_schema import SessionResponse

@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(
    request: Request,
    response: Response,
    payload: LoginRequest,
    db: Session = Depends(get_db)
):
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("User-Agent")
    
    # Authenticate and get tokens
    token_data = auth_service.login(db, payload, ip_address, user_agent)
    
    # Create or update session
    # We need user_id, but login service returns tokens. 
    # Let's inspect auth_service.login. It creates refresh token. 
    # For now, let's just get user from token payload or modify service.
    # Actually, auth_service.login creates a refresh token row. 
    # We should ideally link session to that refresh token or user. 
    # For this implementation, I will just create a new session here.
    # To get user_id, decode access token or refetch user.
    from app.core.security import decode_token
    user_data = decode_token(token_data.access_token)
    user_id = user_data["sub"]
    
    # Extract JTI from refresh token (assuming it's JWT or we use the string itself)
    # Our refresh tokens are opaque strings stored in DB. We can use the token string itself as JTI key.
    create_session(db, user_id, token_data.refresh_token, request)
    
    # Set HttpOnly cookies
    response.set_cookie(
        key="access_token",
        value=token_data.access_token,
        httponly=True,
        secure=False,  # Set True in production
        samesite="lax",
        max_age=60 * 60,  # 1 hour
        path="/"
    )
    
    if token_data.refresh_token:
        response.set_cookie(
            key="refresh_token",
            value=token_data.refresh_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=60 * 60 * 24 * 7,  # 7 days
            path="/"
        )
            
    return token_data


@router.post("/login/request-otp", response_model=dict)
@limiter.limit("10/hour")
def login_request_otp(
    request: Request,
    payload: dict,  # {"email": "..."}
    db: Session = Depends(get_db)
):
    """
    Passwordless login - Step 1: Request OTP
    For returning users who want to login with OTP instead of password.
    """
    from app.services.otp_login_service import otp_login_service
    from app.core.email import send_verification_code_email
    
    email = payload.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    try:
        # Generate and store OTP
        code = otp_login_service.request_otp(db, email)
        
        # Send OTP via email
        success = send_verification_code_email(email, code)
        
        if not success:
            print(f"WARNING: Failed to send OTP email to {email}")
            print(f"===========================================")
            print(f"LOGIN OTP FOR {email}: {code}")
            print(f"===========================================")
        
        return {
            "status": "otp_sent",
            "email": email,
            "message": "OTP sent to your email"
        }
        
    except ValueError as e:
        # User not found
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"ERROR in login_request_otp: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to send OTP")


@router.post("/login/verify-otp", response_model=TokenResponse)
@limiter.limit("20/hour")
def login_verify_otp(
    request: Request,
    response: Response,
    payload: dict,  # {"email": "...", "code": "..."}
    db: Session = Depends(get_db)
):
    """
    Passwordless login - Step 2: Verify OTP and login
    """
    from app.services.otp_login_service import otp_login_service
    
    email = payload.get("email")
    code = payload.get("code")
    
    if not email or not code:
        raise HTTPException(status_code=400, detail="Email and code are required")
    
    try:
        # Verify OTP and get user
        user = otp_login_service.verify_otp(db, email, code)
        
        # Generate tokens
        access_token = create_access_token(
            data={"sub": str(user.id), "role": user.role.value}
        )
        refresh_token = create_refresh_token(str(user.id), db)
        
        # Create session
        from app.core.session import create_session
        create_session(db, str(user.id), refresh_token, request)
        
        # Set cookies
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=60 * 60,
            path="/"
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=60 * 60 * 24 * 7,
            path="/"
        )
        
        print(f"DEBUG: User logged in successfully via OTP: {email}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"ERROR in login_verify_otp: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Login failed")


@router.post("/oauth/google", response_model=TokenResponse)
@limiter.limit("10/minute")
def google_oauth(
    request: Request,
    response: Response,
    payload: GoogleOAuthRequest,
    db: Session = Depends(get_db)
):
    """
    Google OAuth2 login/register
    """
    # Verify Google token and get user info
    google_user_data = oauth_service.verify_google_token(payload.id_token)
    
    # Get or create user
    user = oauth_service.get_or_create_oauth_user(db, "google", google_user_data)
    
    # Create tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value}
    )
    refresh_token = create_refresh_token(str(user.id), db)
    
    # Create audit log
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("User-Agent")
    auth_service.create_audit_log(db, str(user.id), "user.oauth.google", ip_address, user_agent)
    
    # Create session
    create_session(db, str(user.id), refresh_token, request)
    
    # Set HttpOnly cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # Set True in production
        samesite="lax",
        max_age=60 * 60,  # 1 hour
        path="/"
    )
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,  # 7 days
        path="/"
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
def read_users_me(
    current_user: User = Depends(get_current_user)
):
    """Get current user details"""
    return {
        "id": str(current_user.id),
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role, 
        "avatar_url": current_user.avatar_url
    }


@router.get("/sessions", response_model=List[SessionResponse])
def get_user_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get active sessions for current user"""
    return db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_active == True
    ).all()


@router.delete("/sessions/{session_id}")
def revoke_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Revoke a specific session"""
    session = db.query(UserSession).filter(
        UserSession.id == session_id,
        UserSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session.is_active = False
    # Also revoke the associated refresh token?
    # Ideally yes. We stored refresh_token string in refresh_token_jti column.
    # Let's revoke it if we can find it.
    from app.db.models.refresh_token import RefreshToken
    token = db.query(RefreshToken).filter(RefreshToken.token == session.refresh_token_jti).first()
    if token:
        db.delete(token)
    
    db.commit()
    return {"message": "Session revoked"}


@router.delete("/sessions")
def revoke_all_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Revoke all sessions except current one (optional complexity, for now revoke all)"""
    # To keep current session, we'd need to know which one matches current refresh token.
    # For now, let's revoke all OTHER sessions.
    # But checking current session is hard without passing session_id in header.
    # Let's just revoke all for security.
    sessions = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_active == True
    ).all()
    
    for session in sessions:
        session.is_active = False
        
    db.commit()
    return {"message": "All sessions revoked"}


@router.put("/users/role", dependencies=[Depends(require_admin)])
def update_user_role(
    payload: UpdateUserRoleRequest,
    db: Session = Depends(get_db)
):
    user = auth_service.update_user_role(db, payload.user_id, payload.role)
    return {"message": f"User role updated to {payload.role.value}"}


@router.delete("/users/{user_id}", dependencies=[Depends(require_admin)])
def delete_user(
    user_id: str,
    db: Session = Depends(get_db)
):
    return auth_service.delete_user(db, user_id)


@router.post("/magic-link")
@limiter.limit("5/hour")
def request_magic_link(
    request: Request,
    payload: MagicLinkRequest,
    db: Session = Depends(get_db)
):
    """
    Generate magic link and send to email.
    Always returns success to prevent email enumeration.
    """
    # Check if user exists, if not create
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        user = User(
            email=payload.email,
            name=payload.email.split("@")[0],  # Default name from email
            role="property_developer",
            auth_provider="magic_link",
            is_active=True,
            is_verified=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Generate token
    token = magic_link_service.create_magic_link(db, user)
    
    # Send email (mock)
    link = magic_link_service.send_magic_link_email(payload.email, token)
    
    return {"message": "If the email exists, a magic link has been sent", "dev_link": link}


@router.get("/verify", response_model=TokenResponse)
def verify_magic_link(
    token: str,
    request: Request,
    response: Response,
    db: Session = Depends(get_db) 
):
    """
    Verify magic link token and log user in.
    """
    try:
        magic_link_entry = magic_link_service.verify_token(db, token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    user = magic_link_entry.user
    
    # Mark user as verified
    if not user.is_verified:
        user.is_verified = True
        
    # Update last login
    from datetime import datetime
    user.last_login_at = datetime.utcnow()
    
    # Mark token as used
    magic_link_service.mark_as_used(db, magic_link_entry)
    db.commit()
    
    # Create tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role}
    )
    refresh_token = create_refresh_token(str(user.id), db)
    
    # Create audit log
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("User-Agent")
    auth_service.create_audit_log(db, str(user.id), "user.login.magic_link", ip_address, user_agent)
    
    # Create session
    create_session(db, str(user.id), refresh_token, request)
    
    # Set HttpOnly cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # Set True in production
        samesite="lax",
        max_age=60 * 60,  # 1 hour
        path="/"
    )
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,  # 7 days
        path="/"
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


# ===== DEVELOPER SIGNUP ENDPOINTS (Multi-step) =====

@router.post("/signup/init", response_model=SignupInitResponse)
@limiter.limit("10/hour")
def signup_init(
    request: Request,
    payload: SignupInitRequest,
    db: Session = Depends(get_db)
):
    """Step 1: Email input - Check if email already registered"""
    existing = db.query(User).filter_by(email=payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    return SignupInitResponse(email=payload.email)


@router.post("/signup/password", response_model=SignupPasswordResponse)
@limiter.limit("30/hour")  # Increased for development/testing
def signup_password(
    request: Request,
    payload: SignupPasswordRequest,
    db: Session = Depends(get_db)
):
    """Step 2: Password creation - Generate and send verification code"""
    # Generate verification code and store with temp password
    code = email_verification_service.create_verification(
        db, payload.email, payload.password
    )
    
    # Send code via email
    email_verification_service.send_verification_email(payload.email, code)
    
    return SignupPasswordResponse(email=payload.email)


@router.post("/signup/verify", response_model=SignupVerifyResponse)
@limiter.limit("20/hour")
def signup_verify(
    request: Request,
    payload: SignupVerifyRequest,
    db: Session = Depends(get_db)
):
    """Step 3: Code verification - Validate code"""
    try:
        verification = email_verification_service.verify_code(
            db, payload.email, payload.code
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Generate temp token for profile completion
    # Using email as temp token (simple approach)
    import base64
    temp_token = base64.b64encode(payload.email.encode()).decode()
    
    return SignupVerifyResponse(email=payload.email, temp_token=temp_token)


@router.post("/signup/complete", response_model=TokenResponse)
def signup_complete(
    request: Request,
    response: Response,
    payload: SignupCompleteRequest,
    db: Session = Depends(get_db)
):
    """Step 4: Profile completion - Create account and auto-login"""
    try:
        # Verify temp token
        import base64
        try:
            decoded_email = base64.b64decode(payload.temp_token).decode()
            if decoded_email != payload.email:
                raise ValueError("Invalid token")
        except Exception as e:
            print(f"ERROR: Token validation failed: {e}")
            raise HTTPException(status_code=400, detail="Invalid temp token")
        
        # Get LATEST verification that's verified (from previous step)
        verification = db.query(EmailVerification).filter_by(
            email=payload.email,
            verified=False  # Not yet consumed
        ).order_by(EmailVerification.created_at.desc()).first()
        
        if not verification:
            print(f"ERROR: No verification found for {payload.email}")
            raise HTTPException(status_code=400, detail="Verification not found or already used. Please start signup again.")
        
        print(f"DEBUG: Verification found for {payload.email}")
        
        # Check if user already exists
        existing_user = db.query(User).filter_by(email=payload.email).first()
        if existing_user:
            print(f"ERROR: User already exists: {payload.email}")
            raise HTTPException(status_code=400, detail="User already exists")
        
        # Parse birthday
        from datetime import datetime as dt
        try:
            birthday_date = dt.strptime(payload.birthday, "%Y-%m-%d").date()
            print(f"DEBUG: Birthday parsed: {birthday_date}")
        except ValueError as e:
            print(f"ERROR: Birthday parse failed: {e}")
            raise HTTPException(status_code=400, detail="Invalid birthday format. Use YYYY-MM-DD")
        
        # Create user
        from app.db.models.user import UserRole
        print(f"DEBUG: Creating user with email={payload.email}, name={payload.name}")
        
        new_user = User(
            email=payload.email,
            name=payload.name,
            birthday=birthday_date,
            hashed_password=verification.temp_password_hash,
            role=UserRole.DEVELOPER,
            auth_provider="local",
            is_verified=True,
            is_active=True
        )
        db.add(new_user)
        db.flush()  # Get user ID before committing
        
        print(f"DEBUG: User added to session, ID: {new_user.id}")
        
        # Mark verification as used and delete
        email_verification_service.mark_as_verified(db, verification)
        
        db.commit()
        db.refresh(new_user)
        
        print(f"DEBUG: User created successfully: {new_user.email}")
        
        # Generate tokens
        print(f"DEBUG: Generating tokens...")
        access_token = create_access_token(
            data={"sub": str(new_user.id), "role": new_user.role.value}
        )
        refresh_token = create_refresh_token(str(new_user.id), db)
        
        print(f"DEBUG: Tokens generated")
        
        # Create session
        from app.core.session import create_session
        print(f"DEBUG: Creating session...")
        create_session(db, str(new_user.id), refresh_token, request)
        
        print(f"DEBUG: Session created")
        
        # Set cookies
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=60 * 60,
            path="/"
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=60 * 60 * 24 * 7,
            path="/"
        )
        
        print(f"DEBUG: Signup complete successful for {payload.email}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"CRITICAL ERROR in signup_complete: {type(e).__name__}: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


# ===== ADMIN ENDPOINTS =====

@router.post("/admin/request-link", response_model=AdminMagicLinkResponse)
@limiter.limit("5/hour")
def admin_request_magic_link(
    request: Request,
    payload: AdminMagicLinkRequest,
    db: Session = Depends(get_db)
):
    """Admin login - Request magic link"""
    from app.db.models.user import UserRole
    
    # Check if user is admin
    user = db.query(User).filter_by(email=payload.email).first()
    if not user or user.role != UserRole.ADMIN:
        # Don't reveal if user exists for security
        return AdminMagicLinkResponse()
    
    # Generate magic link
    token = magic_link_service.create_magic_link(db, user)
    
    # Send email
    magic_link_service.send_magic_link_email(payload.email, token)
    
    return AdminMagicLinkResponse()


@router.get("/admin/verify", response_model=TokenResponse)
def admin_verify_magic_link(
    token: str,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Admin login - Verify magic link and login"""
    from app.db.models.user import UserRole
    
    try:
        magic_link_entry = magic_link_service.verify_token(db, token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    user = magic_link_entry.user
    
    # Verify user is admin
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access only")
    
    # Mark user as verified
    user.is_verified = True
    
    # Update last login
    from datetime import datetime
    user.last_login_at = datetime.utcnow()
    
    # Mark token as used
    magic_link_service.mark_as_used(db, magic_link_entry)
    db.commit()
    
    # Generate tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value}
    )
    refresh_token = create_refresh_token(str(user.id), db)
    
    # Create audit log
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("User-Agent")
    auth_service.create_audit_log(db, str(user.id), "admin.login.magic_link", ip_address, user_agent)
    
    # Create session
    from app.core.session import create_session
    create_session(db, str(user.id), refresh_token, request)
    
    # Set cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60,
        path="/"
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
        path="/"
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

