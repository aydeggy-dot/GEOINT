"""
Two-Factor Authentication Utilities
TOTP generation, QR codes, and backup codes
"""
import pyotp
import qrcode
import io
import base64
from typing import List, Tuple
import secrets
import hashlib

from app.config import get_settings

settings = get_settings()


def generate_totp_secret() -> str:
    """
    Generate a random TOTP secret (base32 encoded)

    Returns:
        str: Base32 encoded secret
    """
    return pyotp.random_base32()


def generate_totp_uri(secret: str, user_email: str) -> str:
    """
    Generate TOTP provisioning URI for QR code

    Args:
        secret: TOTP secret
        user_email: User's email address

    Returns:
        str: Provisioning URI
    """
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(
        name=user_email,
        issuer_name=settings.APP_NAME
    )


def generate_qr_code(uri: str) -> str:
    """
    Generate QR code image as base64 string

    Args:
        uri: TOTP provisioning URI

    Returns:
        str: Base64 encoded PNG image
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()

    return f"data:image/png;base64,{img_str}"


def verify_totp_code(secret: str, code: str) -> bool:
    """
    Verify TOTP code

    Args:
        secret: TOTP secret
        code: 6-digit code from authenticator app

    Returns:
        bool: True if code is valid
    """
    totp = pyotp.TOTP(secret)
    # Allow 1 time step before and after for clock skew
    return totp.verify(code, valid_window=1)


def generate_backup_codes(count: int = 10) -> List[str]:
    """
    Generate backup codes for 2FA recovery

    Args:
        count: Number of codes to generate

    Returns:
        list: List of backup codes
    """
    codes = []
    for _ in range(count):
        # Generate 8-character alphanumeric code
        code = secrets.token_hex(4).upper()
        # Format as XXXX-XXXX
        formatted = f"{code[:4]}-{code[4:]}"
        codes.append(formatted)
    return codes


def hash_backup_code(code: str) -> str:
    """
    Hash backup code for secure storage

    Args:
        code: Backup code

    Returns:
        str: SHA-256 hash of code
    """
    return hashlib.sha256(code.encode()).hexdigest()


def verify_backup_code(code: str, hashed_codes: List[str]) -> Tuple[bool, str]:
    """
    Verify backup code against list of hashed codes

    Args:
        code: Backup code to verify
        hashed_codes: List of hashed backup codes

    Returns:
        tuple: (is_valid, matched_hash)
    """
    code_hash = hash_backup_code(code)

    if code_hash in hashed_codes:
        return True, code_hash

    return False, None
