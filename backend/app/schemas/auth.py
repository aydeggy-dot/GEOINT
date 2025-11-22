"""
Pydantic schemas for authentication and authorization
Request/response models for auth endpoints
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# ==================== Registration ====================

class UserRegister(BaseModel):
    """User registration request"""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    name: Optional[str] = Field(None, max_length=255, description="Optional display name")

    @field_validator('email')
    @classmethod
    def email_lowercase(cls, v):
        """Convert email to lowercase"""
        return v.lower().strip()


class UserRegisterResponse(BaseModel):
    """User registration response"""
    message: str
    email: str
    verification_required: bool = True


# ==================== Login ====================

class UserLogin(BaseModel):
    """User login request"""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")
    remember_me: bool = Field(False, description="Extend session duration")
    two_factor_code: Optional[str] = Field(None, description="2FA code (if 2FA is enabled)")

    @field_validator('email')
    @classmethod
    def email_lowercase(cls, v):
        """Convert email to lowercase"""
        return v.lower().strip()


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: "UserResponse"


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


# ==================== User Response ====================

class UserResponse(BaseModel):
    """User profile response"""
    id: UUID
    email: str
    name: Optional[str]
    email_verified: bool
    phone_number: Optional[str]
    phone_verified: bool
    is_active: bool
    status: str
    trust_score: float
    is_verified_reporter: bool
    roles: List[str] = []  # Role names
    created_at: datetime
    last_login_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== Email Verification ====================

class ResendVerificationRequest(BaseModel):
    """Resend verification email request"""
    email: EmailStr

    @field_validator('email')
    @classmethod
    def email_lowercase(cls, v):
        """Convert email to lowercase"""
        return v.lower().strip()


class EmailVerificationResponse(BaseModel):
    """Email verification response"""
    message: str
    email_verified: bool


# ==================== Password Reset ====================

class ForgotPasswordRequest(BaseModel):
    """Forgot password request"""
    email: EmailStr

    @field_validator('email')
    @classmethod
    def email_lowercase(cls, v):
        """Convert email to lowercase"""
        return v.lower().strip()


class ForgotPasswordResponse(BaseModel):
    """Forgot password response"""
    message: str


class ResetPasswordRequest(BaseModel):
    """Reset password with token"""
    token: str = Field(..., description="Password reset token from email")
    new_password: str = Field(..., min_length=8, description="New password")


class ResetPasswordResponse(BaseModel):
    """Reset password response"""
    message: str


class ChangePasswordRequest(BaseModel):
    """Change password (authenticated user)"""
    current_password: str
    new_password: str = Field(..., min_length=8)


# ==================== 2FA ====================

class TwoFactorEnableRequest(BaseModel):
    """Enable 2FA request"""
    method: str = Field(..., description="2FA method: 'totp' or 'email'")
    password: str = Field(..., description="Current password for confirmation")


class TwoFactorEnableResponse(BaseModel):
    """Enable 2FA response"""
    message: str
    method: str
    secret: Optional[str] = None  # TOTP secret for QR code
    qr_code_url: Optional[str] = None  # Data URL for QR code image
    backup_codes: Optional[List[str]] = None  # One-time backup codes


class TwoFactorVerifyRequest(BaseModel):
    """Verify 2FA code"""
    code: str = Field(..., description="6-digit verification code or backup code")


class TwoFactorVerifyResponse(BaseModel):
    """2FA verification response"""
    verified: bool
    message: str


class TwoFactorDisableRequest(BaseModel):
    """Disable 2FA request"""
    password: str = Field(..., description="Current password for confirmation")


# ==================== Session Management ====================

class SessionResponse(BaseModel):
    """Active session information"""
    id: UUID
    device_info: Optional[dict]
    ip_address: Optional[str]
    last_activity: datetime
    created_at: datetime
    is_current: bool = False

    class Config:
        from_attributes = True


class LogoutResponse(BaseModel):
    """Logout response"""
    message: str


# ==================== Profile ====================

class UserProfileUpdate(BaseModel):
    """Update user profile"""
    name: Optional[str] = Field(None, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=20)
    receive_alerts: Optional[bool] = None
    receive_sms_alerts: Optional[bool] = None
    alert_radius_km: Optional[float] = Field(None, ge=1, le=500)


# ==================== Error Response ====================

class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: str
    error_code: Optional[str] = None


# ==================== Role & Permission (Admin) ====================

class RoleResponse(BaseModel):
    """Role information"""
    id: UUID
    name: str
    display_name: str
    description: Optional[str]
    permissions: List[str] = []  # Permission names

    class Config:
        from_attributes = True


class PermissionResponse(BaseModel):
    """Permission information"""
    id: UUID
    name: str
    resource: str
    action: str
    description: Optional[str]

    class Config:
        from_attributes = True


class AssignRoleRequest(BaseModel):
    """Assign role to user"""
    user_id: UUID
    role_name: str
    expires_at: Optional[datetime] = None


# ==================== Audit Log ====================

class AuditLogResponse(BaseModel):
    """Audit log entry"""
    id: UUID
    user_id: Optional[UUID]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[UUID]
    changes: Optional[dict]
    ip_address: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
