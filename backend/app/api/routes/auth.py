"""
Authentication API endpoints
Registration, login, email verification, password reset, 2FA
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import List
import logging

from app.database import get_db
from app.models.user import User
from app.models.auth import VerificationCode, UserSession, AuditLog, TwoFactorAuth
from app.schemas.auth import (
    UserRegister, UserRegisterResponse,
    UserLogin, TokenResponse,
    ResendVerificationRequest, EmailVerificationResponse,
    ForgotPasswordRequest, ForgotPasswordResponse,
    ResetPasswordRequest, ResetPasswordResponse,
    ChangePasswordRequest,
    RefreshTokenRequest,
    UserResponse, SessionResponse, LogoutResponse
)
from app.utils.auth import (
    hash_password, verify_password, validate_password_strength,
    create_access_token, create_refresh_token,
    create_email_verification_token, verify_email_token,
    create_password_reset_token, verify_password_reset_token,
    hash_refresh_token, decode_token
)
from app.utils.email import email_service
from app.utils.twofa import verify_totp_code, verify_backup_code
from app.api.dependencies.auth import (
    get_current_user, get_request_ip, get_user_agent, get_user_roles
)
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ==================== Helper Functions ====================

def create_audit_log(
    db: Session,
    user_id: str = None,
    action: str = "",
    resource_type: str = None,
    resource_id: str = None,
    changes: dict = None,
    ip_address: str = None,
    user_agent: str = None,
    status: str = "success",
    error_message: str = None
):
    """Helper to create audit log entry"""
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        changes=changes,
        ip_address=ip_address,
        user_agent=user_agent,
        status=status,
        error_message=error_message
    )
    db.add(log)
    db.commit()


async def get_frontend_url() -> str:
    """Get frontend URL for email links"""
    # In production, this should come from environment variable
    return settings.ALLOWED_ORIGINS[0] if settings.ALLOWED_ORIGINS else "http://localhost:3000"


# ==================== Registration ====================

@router.post("/register", response_model=UserRegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Register a new user

    - **email**: Valid email address (will be verified)
    - **password**: Strong password (min 8 chars, uppercase, lowercase, digit, special char)
    - **name**: Optional display name

    Returns registration confirmation and sends verification email
    """
    ip_address = await get_request_ip(request)
    user_agent = await get_user_agent(request)

    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        create_audit_log(
            db, None, "user.register.failed", "user", None,
            {"email": user_data.email, "reason": "email_exists"},
            ip_address, user_agent, "failure", "Email already registered"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address already registered"
        )

    # Validate password strength
    is_valid, error_msg = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    # Hash password
    password_hash = hash_password(user_data.password)

    # Create user
    new_user = User(
        email=user_data.email,
        password_hash=password_hash,
        name=user_data.name,
        email_verified=False,
        is_active=True,
        status='active',
        registered_at=datetime.now(timezone.utc)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create email verification token
    verification_token = create_email_verification_token(new_user.email)
    frontend_url = await get_frontend_url()
    verification_link = f"{frontend_url}/verify-email?token={verification_token}"

    # Send verification email
    email_sent = email_service.send_verification_email(
        to_email=new_user.email,
        to_name=new_user.name,
        verification_link=verification_link
    )

    if not email_sent:
        logger.error(f"Failed to send verification email to {new_user.email}")

    # Audit log
    create_audit_log(
        db, str(new_user.id), "user.register", "user", str(new_user.id),
        {"email": new_user.email, "name": new_user.name},
        ip_address, user_agent, "success"
    )

    return UserRegisterResponse(
        message="Registration successful. Please check your email to verify your account.",
        email=new_user.email,
        verification_required=True
    )


# ==================== Email Verification ====================

@router.get("/verify-email", response_model=EmailVerificationResponse)
async def verify_email(
    token: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Verify email address with token from email link

    - **token**: Verification token from email

    Activates user account after successful verification
    """
    ip_address = await get_request_ip(request)
    user_agent = await get_user_agent(request)

    # Verify token and extract email
    email = verify_email_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )

    # Find user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if already verified
    if user.email_verified:
        return EmailVerificationResponse(
            message="Email already verified",
            email_verified=True
        )

    # Mark email as verified
    user.email_verified = True
    db.commit()

    # Audit log
    create_audit_log(
        db, str(user.id), "user.email_verified", "user", str(user.id),
        None, ip_address, user_agent, "success"
    )

    logger.info(f"Email verified for user {user.email}")

    return EmailVerificationResponse(
        message="Email verified successfully. You can now log in.",
        email_verified=True
    )


@router.post("/resend-verification", status_code=status.HTTP_200_OK)
async def resend_verification(
    data: ResendVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Resend verification email

    - **email**: Email address to resend verification to

    Rate limited to prevent abuse
    """
    # Find user
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        # Don't reveal if email exists or not (security)
        return {"message": "If the email exists, a verification link has been sent."}

    # Check if already verified
    if user.email_verified:
        return {"message": "Email already verified."}

    # Create new verification token
    verification_token = create_email_verification_token(user.email)
    frontend_url = await get_frontend_url()
    verification_link = f"{frontend_url}/verify-email?token={verification_token}"

    # Send verification email
    email_sent = email_service.send_verification_email(
        to_email=user.email,
        to_name=user.name,
        verification_link=verification_link
    )

    if not email_sent:
        logger.error(f"Failed to resend verification email to {user.email}")

    return {"message": "If the email exists, a verification link has been sent."}


# ==================== Login ====================

@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Login with email and password

    - **email**: User's email address
    - **password**: User's password
    - **remember_me**: Extend session duration (optional)

    Returns JWT access token and refresh token
    """
    ip_address = await get_request_ip(request)
    user_agent = await get_user_agent(request)

    # Find user by email
    user = db.query(User).filter(User.email == credentials.email).first()

    # Generic error message to prevent user enumeration
    invalid_credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password"
    )

    if not user:
        create_audit_log(
            db, None, "user.login.failed", None, None,
            {"email": credentials.email, "reason": "user_not_found"},
            ip_address, user_agent, "failure", "User not found"
        )
        raise invalid_credentials_error

    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account temporarily locked due to multiple failed login attempts. Please try again later."
        )

    # Verify password
    if not verify_password(credentials.password, user.password_hash):
        # Increment failed login attempts
        user.failed_login_attempts += 1

        # Lock account after max attempts
        if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCOUNT_LOCKOUT_MINUTES)
            logger.warning(f"Account locked for user {user.email} due to {user.failed_login_attempts} failed attempts")

        db.commit()

        create_audit_log(
            db, str(user.id), "user.login.failed", "user", str(user.id),
            {"reason": "invalid_password", "failed_attempts": user.failed_login_attempts},
            ip_address, user_agent, "failure", "Invalid password"
        )
        raise invalid_credentials_error

    # Check if user is active
    if not user.is_active or user.status != 'active':
        create_audit_log(
            db, str(user.id), "user.login.failed", "user", str(user.id),
            {"reason": "account_inactive"},
            ip_address, user_agent, "failure", "Account inactive"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive or suspended"
        )

    # Check if email is verified
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email address before logging in"
        )

    # Reset failed login attempts on successful login
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = datetime.now(timezone.utc)
    user.last_login_ip = ip_address

    # Check if 2FA is enabled
    twofa = db.query(TwoFactorAuth).filter(
        TwoFactorAuth.user_id == user.id,
        TwoFactorAuth.enabled == True
    ).first()

    if twofa:
        # 2FA is enabled - require verification
        if not credentials.two_factor_code:
            # No 2FA code provided
            db.commit()  # Save last_login_at update
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Two-factor authentication code required",
                headers={"X-Requires-2FA": "true"}
            )

        # Verify 2FA code (TOTP or backup code)
        code_verified = False

        # Try TOTP code first (6 digits)
        if len(credentials.two_factor_code) == 6 and credentials.two_factor_code.isdigit():
            if verify_totp_code(twofa.secret, credentials.two_factor_code):
                code_verified = True
                logger.info(f"User {user.email} verified with TOTP code")

        # Try backup code (XXXX-XXXX format)
        elif len(credentials.two_factor_code) == 9 and '-' in credentials.two_factor_code:
            is_valid, matched_hash = verify_backup_code(credentials.two_factor_code, twofa.backup_codes or [])
            if is_valid:
                # Remove used backup code
                twofa.backup_codes = [code for code in twofa.backup_codes if code != matched_hash]
                twofa.updated_at = datetime.now(timezone.utc)
                code_verified = True
                logger.info(f"User {user.email} verified with backup code. {len(twofa.backup_codes)} codes remaining")

        if not code_verified:
            # Invalid 2FA code
            db.commit()  # Save updates
            create_audit_log(
                db, str(user.id), "user.login.2fa_failed", "user", str(user.id),
                {"reason": "invalid_2fa_code"},
                ip_address, user_agent, "failure", "Invalid 2FA code"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid two-factor authentication code"
            )

        # 2FA verified successfully
        logger.info(f"User {user.email} passed 2FA verification")

    # Get user roles
    user_role_names = get_user_roles(user, db)

    # Create tokens
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "roles": user_role_names
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Store refresh token in database (hashed)
    session = UserSession(
        user_id=user.id,
        refresh_token_hash=hash_refresh_token(refresh_token),
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(session)
    db.commit()

    # Audit log
    create_audit_log(
        db, str(user.id), "user.login", "user", str(user.id),
        None, ip_address, user_agent, "success"
    )

    # Send security alert email for new device login
    # (Could check if IP/device is new and send email)

    logger.info(f"User {user.email} logged in successfully")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            email_verified=user.email_verified,
            phone_number=user.phone_number,
            phone_verified=user.phone_verified,
            is_active=user.is_active,
            status=user.status,
            trust_score=user.trust_score,
            is_verified_reporter=user.is_verified_reporter,
            roles=user_role_names,
            created_at=user.created_at,
            last_login_at=user.last_login_at
        )
    )


# ==================== Token Refresh ====================

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token

    - **refresh_token**: Valid refresh token from login

    Returns new access token and refresh token
    """
    ip_address = await get_request_ip(request)
    user_agent = await get_user_agent(request)

    # Decode refresh token
    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    # Check if refresh token exists in database
    token_hash = hash_refresh_token(data.refresh_token)
    session = db.query(UserSession).filter(
        UserSession.refresh_token_hash == token_hash,
        UserSession.user_id == user_id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found or already used"
        )

    # Check if token is expired or revoked
    # Ensure timezone-aware comparison
    expires_at = session.expires_at if session.expires_at.tzinfo else session.expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc) or session.revoked_at:
        db.delete(session)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired or revoked"
        )

    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Get user roles
    user_role_names = get_user_roles(user, db)

    # Create new tokens
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "roles": user_role_names
    }

    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    # Delete old session and create new one
    db.delete(session)
    new_session = UserSession(
        user_id=user.id,
        refresh_token_hash=hash_refresh_token(new_refresh_token),
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(new_session)
    db.commit()

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            email_verified=user.email_verified,
            phone_number=user.phone_number,
            phone_verified=user.phone_verified,
            is_active=user.is_active,
            status=user.status,
            trust_score=user.trust_score,
            is_verified_reporter=user.is_verified_reporter,
            roles=user_role_names,
            created_at=user.created_at,
            last_login_at=user.last_login_at
        )
    )


# ==================== Logout ====================

@router.post("/logout", response_model=LogoutResponse)
async def logout(
    data: RefreshTokenRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout current session

    - **refresh_token**: Refresh token to invalidate

    Revokes the refresh token and logs out user
    """
    token_hash = hash_refresh_token(data.refresh_token)

    # Find and revoke session
    session = db.query(UserSession).filter(
        UserSession.refresh_token_hash == token_hash,
        UserSession.user_id == current_user.id
    ).first()

    if session:
        session.revoked_at = datetime.now(timezone.utc)
        db.commit()

    return LogoutResponse(message="Logged out successfully")


@router.post("/logout-all", response_model=LogoutResponse)
async def logout_all_devices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout from all devices

    Revokes all active sessions for the current user
    """
    # Revoke all user sessions
    db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.revoked_at.is_(None)
    ).update({"revoked_at": datetime.now(timezone.utc)})

    db.commit()

    return LogoutResponse(message="Logged out from all devices successfully")


# ==================== Current User ====================

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user information

    Returns user profile with roles
    """
    user_role_names = get_user_roles(current_user, db)

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        email_verified=current_user.email_verified,
        phone_number=current_user.phone_number,
        phone_verified=current_user.phone_verified,
        is_active=current_user.is_active,
        status=current_user.status,
        trust_score=current_user.trust_score,
        is_verified_reporter=current_user.is_verified_reporter,
        roles=user_role_names,
        created_at=current_user.created_at,
        last_login_at=current_user.last_login_at
    )


# ==================== Password Reset ====================

@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset link

    - **email**: Email address to send reset link to

    Sends password reset email with token
    """
    # Find user (don't reveal if email exists)
    user = db.query(User).filter(User.email == data.email).first()

    if user:
        # Create password reset token
        reset_token = create_password_reset_token(user.email)
        frontend_url = await get_frontend_url()
        reset_link = f"{frontend_url}/reset-password?token={reset_token}"

        # Send password reset email
        email_sent = email_service.send_password_reset_email(
            to_email=user.email,
            to_name=user.name,
            reset_link=reset_link
        )

        if not email_sent:
            logger.error(f"Failed to send password reset email to {user.email}")

    # Always return same message (security - don't reveal if email exists)
    return ForgotPasswordResponse(
        message="If the email exists, a password reset link has been sent."
    )


@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(
    data: ResetPasswordRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Reset password with token from email

    - **token**: Password reset token from email
    - **new_password**: New password

    Updates password and logs out all sessions
    """
    ip_address = await get_request_ip(request)
    user_agent = await get_user_agent(request)

    # Verify reset token
    email = verify_password_reset_token(data.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token"
        )

    # Find user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Validate new password strength
    is_valid, error_msg = validate_password_strength(data.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    # Update password
    user.password_hash = hash_password(data.new_password)
    user.password_changed_at = datetime.now(timezone.utc)

    # Revoke all existing sessions (security measure)
    db.query(UserSession).filter(
        UserSession.user_id == user.id,
        UserSession.revoked_at.is_(None)
    ).update({"revoked_at": datetime.now(timezone.utc)})

    db.commit()

    # Audit log
    create_audit_log(
        db, str(user.id), "user.password_reset", "user", str(user.id),
        None, ip_address, user_agent, "success"
    )

    # Send confirmation email
    email_service.send_security_alert(
        to_email=user.email,
        to_name=user.name,
        event="Password Changed",
        details="Your password has been successfully changed. All active sessions have been logged out."
    )

    logger.info(f"Password reset successful for user {user.email}")

    return ResetPasswordResponse(
        message="Password reset successful. Please log in with your new password."
    )


# ==================== Change Password (Authenticated) ====================

@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Change password (requires current password)

    - **current_password**: Current password for verification
    - **new_password**: New password

    User must be authenticated
    """
    ip_address = await get_request_ip(request)
    user_agent = await get_user_agent(request)

    # Verify current password
    if not verify_password(data.current_password, current_user.password_hash):
        create_audit_log(
            db, str(current_user.id), "user.change_password.failed", "user", str(current_user.id),
            {"reason": "invalid_current_password"},
            ip_address, user_agent, "failure", "Invalid current password"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Validate new password
    is_valid, error_msg = validate_password_strength(data.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    # Update password
    current_user.password_hash = hash_password(data.new_password)
    current_user.password_changed_at = datetime.now(timezone.utc)
    db.commit()

    # Audit log
    create_audit_log(
        db, str(current_user.id), "user.password_changed", "user", str(current_user.id),
        None, ip_address, user_agent, "success"
    )

    # Send confirmation email
    email_service.send_security_alert(
        to_email=current_user.email,
        to_name=current_user.name,
        event="Password Changed",
        details="Your password has been successfully changed."
    )

    return {"message": "Password changed successfully"}


# ==================== Active Sessions ====================

@router.get("/sessions", response_model=List[SessionResponse])
async def get_active_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of active sessions for current user

    Returns all non-revoked sessions
    """
    sessions = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.revoked_at.is_(None),
        UserSession.expires_at > datetime.now(timezone.utc)
    ).all()

    return [
        SessionResponse(
            id=session.id,
            device_info=session.device_info,
            ip_address=str(session.ip_address) if session.ip_address else None,
            last_activity=session.last_activity,
            created_at=session.created_at,
            is_current=False  # TODO: Determine current session
        )
        for session in sessions
    ]


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revoke a specific session

    - **session_id**: Session ID to revoke

    Logs out the specified session
    """
    session = db.query(UserSession).filter(
        UserSession.id == session_id,
        UserSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    session.revoked_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": "Session revoked successfully"}
