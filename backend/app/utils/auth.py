"""
Authentication utilities
JWT token management, password hashing, and security helpers
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
import secrets
import hashlib
from app.config import get_settings

settings = get_settings()

# Password hashing context
# Configure bcrypt to not raise errors on password length
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__truncate_error=False
)


# ==================== Password Hashing ====================

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt

    Note: bcrypt has a 72-byte limit. Passwords are truncated to 72 bytes
    before hashing as bcrypt only uses the first 72 bytes anyway.

    Args:
        password: Plain text password

    Returns:
        str: Hashed password
    """
    # Truncate to 72 bytes (bcrypt limitation)
    password_bytes = password.encode('utf-8')[:72]
    return pwd_context.hash(password_bytes)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash

    Note: bcrypt has a 72-byte limit. Passwords are truncated to 72 bytes
    before verification to match the hashing behavior.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored hash to verify against

    Returns:
        bool: True if password matches
    """
    # Truncate to 72 bytes (bcrypt limitation)
    password_bytes = plain_password.encode('utf-8')[:72]
    return pwd_context.verify(password_bytes, hashed_password)


def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate password meets security requirements

    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character

    Args:
        password: Password to validate

    Returns:
        tuple: (is_valid, error_message)
    """
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long"

    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"

    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"

    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"

    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?/~`" for c in password):
        return False, "Password must contain at least one special character"

    # Check against common passwords (basic check)
    common_passwords = [
        "password", "12345678", "password123", "admin123", "qwerty123",
        "letmein", "welcome", "monkey", "dragon", "master"
    ]
    if password.lower() in common_passwords:
        return False, "Password is too common. Please choose a stronger password"

    return True, None


# ==================== JWT Token Management ====================

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token

    Args:
        data: Payload data to encode in token
        expires_delta: Token expiration time (default: 15 minutes)

    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create JWT refresh token (longer-lived)

    Args:
        data: Payload data to encode in token

    Returns:
        str: Encoded JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh"
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate JWT token

    Args:
        token: JWT token string

    Returns:
        dict: Decoded payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def create_email_verification_token(email: str) -> str:
    """
    Create token for email verification

    Args:
        email: User's email address

    Returns:
        str: Verification token
    """
    data = {"email": email, "purpose": "email_verification"}
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS)

    to_encode = data.copy()
    to_encode.update({"exp": expire})

    token = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return token


def verify_email_token(token: str) -> Optional[str]:
    """
    Verify email verification token and extract email

    Args:
        token: Verification token

    Returns:
        str: Email if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        if payload.get("purpose") != "email_verification":
            return None

        return payload.get("email")
    except JWTError:
        return None


def create_password_reset_token(email: str) -> str:
    """
    Create token for password reset

    Args:
        email: User's email address

    Returns:
        str: Reset token
    """
    data = {"email": email, "purpose": "password_reset"}
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS)

    to_encode = data.copy()
    to_encode.update({"exp": expire})

    token = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return token


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Verify password reset token and extract email

    Args:
        token: Reset token

    Returns:
        str: Email if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        if payload.get("purpose") != "password_reset":
            return None

        return payload.get("email")
    except JWTError:
        return None


# ==================== Security Helpers ====================

def generate_verification_code(length: int = 6) -> str:
    """
    Generate random numeric verification code

    Args:
        length: Code length (default: 6)

    Returns:
        str: Random numeric code
    """
    return ''.join([str(secrets.randbelow(10)) for _ in range(length)])


def hash_refresh_token(token: str) -> str:
    """
    Hash refresh token for secure storage

    Args:
        token: Refresh token string

    Returns:
        str: Hashed token
    """
    return hashlib.sha256(token.encode()).hexdigest()


def generate_backup_codes(count: int = 10) -> list[str]:
    """
    Generate backup codes for 2FA

    Args:
        count: Number of codes to generate (default: 10)

    Returns:
        list: List of backup codes
    """
    codes = []
    for _ in range(count):
        # Generate 8-character alphanumeric code
        code = secrets.token_hex(4).upper()
        codes.append(f"{code[:4]}-{code[4:]}")
    return codes


def hash_backup_code(code: str) -> str:
    """
    Hash backup code for secure storage

    Args:
        code: Backup code

    Returns:
        str: Hashed code
    """
    return hashlib.sha256(code.encode()).hexdigest()


def verify_backup_code(plain_code: str, hashed_code: str) -> bool:
    """
    Verify backup code against hash

    Args:
        plain_code: Plain backup code
        hashed_code: Stored hash

    Returns:
        bool: True if code matches
    """
    return hash_backup_code(plain_code) == hashed_code
