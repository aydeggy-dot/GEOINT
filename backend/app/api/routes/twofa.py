"""
Two-Factor Authentication API Routes
Setup, enable, disable, and verify 2FA
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.database import get_db
from app.models.user import User
from app.models.auth import TwoFactorAuth
from app.schemas.twofa import (
    TwoFASetupResponse, TwoFAEnableRequest, TwoFAVerifyRequest,
    TwoFADisableRequest, TwoFAStatusResponse, TwoFARegenerateCodesResponse
)
from app.api.dependencies.auth import get_current_user
from app.utils.twofa import (
    generate_totp_secret, generate_totp_uri, generate_qr_code,
    verify_totp_code, generate_backup_codes, hash_backup_code,
    verify_backup_code
)
from app.utils.auth import verify_password

router = APIRouter(prefix="/2fa", tags=["2FA"])


@router.post("/setup", response_model=TwoFASetupResponse)
async def setup_2fa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initialize 2FA setup - generate secret and QR code

    Returns QR code and backup codes for user to save
    """
    # Check if 2FA already enabled
    existing_2fa = db.query(TwoFactorAuth).filter(
        TwoFactorAuth.user_id == current_user.id
    ).first()

    if existing_2fa and existing_2fa.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is already enabled. Disable it first to set up again."
        )

    # Generate TOTP secret
    secret = generate_totp_secret()

    # Generate QR code
    uri = generate_totp_uri(secret, current_user.email)
    qr_code = generate_qr_code(uri)

    # Generate backup codes
    backup_codes = generate_backup_codes(10)
    hashed_codes = [hash_backup_code(code) for code in backup_codes]

    # Store in database (not enabled yet)
    if existing_2fa:
        # Update existing
        existing_2fa.secret = secret
        existing_2fa.backup_codes = hashed_codes
        existing_2fa.enabled = False
        existing_2fa.updated_at = datetime.now(timezone.utc)
    else:
        # Create new
        new_2fa = TwoFactorAuth(
            user_id=current_user.id,
            method="totp",
            secret=secret,
            backup_codes=hashed_codes,
            enabled=False,
            created_at=datetime.now(timezone.utc)
        )
        db.add(new_2fa)

    db.commit()

    return TwoFASetupResponse(
        secret=secret,
        qr_code=qr_code,
        backup_codes=backup_codes,
        message="Scan the QR code with your authenticator app, then verify with a code to enable 2FA"
    )


@router.post("/enable")
async def enable_2fa(
    request: TwoFAEnableRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Enable 2FA after setup by verifying a code

    User must provide a valid TOTP code to confirm setup
    """
    twofa = db.query(TwoFactorAuth).filter(
        TwoFactorAuth.user_id == current_user.id
    ).first()

    if not twofa or not twofa.secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA not set up. Please call /2fa/setup first."
        )

    if twofa.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is already enabled"
        )

    # Verify the code
    if not verify_totp_code(twofa.secret, request.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )

    # Enable 2FA
    twofa.enabled = True
    twofa.enabled_at = datetime.now(timezone.utc)
    twofa.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "message": "2FA enabled successfully",
        "enabled": True,
        "backup_codes_count": len(twofa.backup_codes) if twofa.backup_codes else 0
    }


@router.post("/verify")
async def verify_2fa_code(
    request: TwoFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verify a 2FA code (TOTP or backup code)

    Used during login or for testing
    """
    twofa = db.query(TwoFactorAuth).filter(
        TwoFactorAuth.user_id == current_user.id,
        TwoFactorAuth.enabled == True
    ).first()

    if not twofa:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is not enabled for this account"
        )

    # Try TOTP code first (6 digits)
    if len(request.code) == 6 and request.code.isdigit():
        if verify_totp_code(twofa.secret, request.code):
            return {"message": "Code verified successfully", "valid": True}

    # Try backup code (format: XXXX-XXXX)
    if len(request.code) == 9 and '-' in request.code:
        is_valid, matched_hash = verify_backup_code(request.code, twofa.backup_codes or [])

        if is_valid:
            # Remove used backup code (reassign array for SQLAlchemy to detect change)
            twofa.backup_codes = [code for code in twofa.backup_codes if code != matched_hash]
            twofa.updated_at = datetime.now(timezone.utc)
            db.commit()

            return {
                "message": "Backup code verified successfully",
                "valid": True,
                "backup_codes_remaining": len(twofa.backup_codes)
            }

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid 2FA code"
    )


@router.post("/disable")
async def disable_2fa(
    request: TwoFADisableRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Disable 2FA

    Requires password confirmation
    """
    # Verify password
    if not verify_password(request.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )

    twofa = db.query(TwoFactorAuth).filter(
        TwoFactorAuth.user_id == current_user.id
    ).first()

    if not twofa or not twofa.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is not enabled"
        )

    # Disable 2FA
    twofa.enabled = False
    twofa.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": "2FA disabled successfully", "enabled": False}


@router.get("/status", response_model=TwoFAStatusResponse)
async def get_2fa_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get 2FA status for current user
    """
    twofa = db.query(TwoFactorAuth).filter(
        TwoFactorAuth.user_id == current_user.id
    ).first()

    if not twofa:
        return TwoFAStatusResponse(
            enabled=False,
            backup_codes_remaining=0
        )

    return TwoFAStatusResponse(
        enabled=twofa.enabled,
        method=twofa.method if twofa.enabled else None,
        backup_codes_remaining=len(twofa.backup_codes) if twofa.backup_codes else 0
    )


@router.post("/regenerate-codes", response_model=TwoFARegenerateCodesResponse)
async def regenerate_backup_codes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Regenerate backup codes

    Replaces all existing backup codes with new ones
    """
    twofa = db.query(TwoFactorAuth).filter(
        TwoFactorAuth.user_id == current_user.id,
        TwoFactorAuth.enabled == True
    ).first()

    if not twofa:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is not enabled"
        )

    # Generate new backup codes
    backup_codes = generate_backup_codes(10)
    hashed_codes = [hash_backup_code(code) for code in backup_codes]

    # Replace existing codes
    twofa.backup_codes = hashed_codes
    twofa.updated_at = datetime.now(timezone.utc)
    db.commit()

    return TwoFARegenerateCodesResponse(
        backup_codes=backup_codes,
        message="Save these new backup codes in a secure location. Old codes are no longer valid."
    )
