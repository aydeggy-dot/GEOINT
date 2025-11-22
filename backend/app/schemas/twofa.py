"""
Two-Factor Authentication Schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class TwoFASetupResponse(BaseModel):
    """Response for 2FA setup initiation"""
    secret: str
    qr_code: str  # Base64 encoded QR code image
    backup_codes: List[str]
    message: str = "Scan the QR code with your authenticator app"


class TwoFAEnableRequest(BaseModel):
    """Request to enable 2FA after setup"""
    code: str = Field(..., min_length=6, max_length=6, description="6-digit TOTP code")


class TwoFAVerifyRequest(BaseModel):
    """Request to verify 2FA code during login"""
    code: str = Field(..., min_length=6, max_length=9, description="6-digit TOTP code or backup code (XXXX-XXXX)")


class TwoFADisableRequest(BaseModel):
    """Request to disable 2FA"""
    password: str = Field(..., description="User password for confirmation")


class TwoFAStatusResponse(BaseModel):
    """Response showing 2FA status"""
    enabled: bool
    method: Optional[str] = None  # 'totp' or 'email'
    backup_codes_remaining: int = 0


class TwoFARegenerateCodesResponse(BaseModel):
    """Response for backup code regeneration"""
    backup_codes: List[str]
    message: str = "Save these backup codes in a secure location"
