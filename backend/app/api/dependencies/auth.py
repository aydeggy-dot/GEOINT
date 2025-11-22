"""
Authentication dependencies for FastAPI
Extract and validate JWT tokens, get current user, check permissions
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timezone

from app.database import get_db
from app.models.user import User
from app.models.auth import Role, Permission, UserSession, user_roles, role_permissions
from app.utils.auth import decode_token
from app.config import get_settings

settings = get_settings()

# Security scheme for JWT bearer token
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token

    Args:
        credentials: Bearer token from Authorization header
        db: Database session

    Returns:
        User: Current authenticated user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials

    # Decode and validate token
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user ID from token
    user_id: str = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch user from database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active or user.status != 'active':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive or suspended"
        )

    # Check if email is verified
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email address"
        )

    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is temporarily locked due to multiple failed login attempts"
        )

    # Update last seen
    user.last_seen = datetime.now(timezone.utc)
    db.commit()

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (alias for get_current_user)

    Args:
        current_user: Current user from token

    Returns:
        User: Current active user
    """
    return current_user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if token provided, otherwise None
    Useful for endpoints that work with or without authentication

    Args:
        credentials: Optional bearer token
        db: Database session

    Returns:
        Optional[User]: User if authenticated, None otherwise
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


def require_roles(*role_names: str):
    """
    Dependency factory to require specific roles

    Usage:
        @router.get("/admin", dependencies=[Depends(require_roles("admin", "super_admin"))])

    Args:
        *role_names: Required role names (user must have at least one)

    Returns:
        Dependency function
    """
    async def check_roles(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        # Get user's roles
        user_role_names = db.query(Role.name).join(
            user_roles, Role.id == user_roles.c.role_id
        ).filter(
            user_roles.c.user_id == current_user.id
        ).all()

        user_role_names = [r[0] for r in user_role_names]

        # Check if user has any of the required roles
        if not any(role in user_role_names for role in role_names):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(role_names)}"
            )

        return current_user

    return check_roles


def require_permissions(*permission_names: str):
    """
    Dependency factory to require specific permissions

    Usage:
        @router.post("/incidents/verify", dependencies=[Depends(require_permissions("incident.verify"))])

    Args:
        *permission_names: Required permission names (user must have all)

    Returns:
        Dependency function
    """
    async def check_permissions(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        # Get user's permissions through their roles
        user_permissions = db.query(Permission.name).join(
            role_permissions, Permission.id == role_permissions.c.permission_id
        ).join(
            Role, Role.id == role_permissions.c.role_id
        ).join(
            user_roles, Role.id == user_roles.c.role_id
        ).filter(
            user_roles.c.user_id == current_user.id
        ).all()

        user_permission_names = [p[0] for p in user_permissions]

        # Check if user has all required permissions
        missing_permissions = [p for p in permission_names if p not in user_permission_names]
        if missing_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Missing: {', '.join(missing_permissions)}"
            )

        return current_user

    return check_permissions


def require_admin(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Dependency to require admin role

    Usage:
        @router.get("/admin/users", dependencies=[Depends(require_admin)])

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        User: Current user if admin

    Raises:
        HTTPException: If user is not admin
    """
    # Check legacy admin flag
    if current_user.is_admin:
        return current_user

    # Check for admin role
    user_roles_query = db.query(Role.name).join(
        user_roles, Role.id == user_roles.c.role_id
    ).filter(
        user_roles.c.user_id == current_user.id
    ).all()

    user_role_names = [r[0] for r in user_roles_query]

    if "admin" not in user_role_names and "super_admin" not in user_role_names:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return current_user


def require_verified_email(
    current_user: User = Depends(get_current_user)
):
    """
    Dependency to ensure user has verified email

    Args:
        current_user: Current user

    Returns:
        User: Current user if email verified

    Raises:
        HTTPException: If email not verified
    """
    if not current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required. Please check your inbox."
        )
    return current_user


async def get_request_ip(request: Request) -> str:
    """
    Get client IP address from request

    Args:
        request: FastAPI request object

    Returns:
        str: Client IP address
    """
    # Check for forwarded IP (behind proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()

    # Check for real IP
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fall back to direct client
    return request.client.host if request.client else "unknown"


async def get_user_agent(request: Request) -> str:
    """
    Get user agent from request

    Args:
        request: FastAPI request object

    Returns:
        str: User agent string
    """
    return request.headers.get("User-Agent", "unknown")


def has_permission(user: User, permission_name: str, db: Session) -> bool:
    """
    Check if user has a specific permission

    Args:
        user: User to check
        permission_name: Permission name (e.g., "incident.verify")
        db: Database session

    Returns:
        bool: True if user has permission
    """
    # Check if user has permission through their roles
    result = db.query(Permission).join(
        role_permissions, Permission.id == role_permissions.c.permission_id
    ).join(
        Role, Role.id == role_permissions.c.role_id
    ).join(
        user_roles, Role.id == user_roles.c.role_id
    ).filter(
        user_roles.c.user_id == user.id,
        Permission.name == permission_name
    ).first()

    return result is not None


def get_user_roles(user: User, db: Session) -> list[str]:
    """
    Get list of role names for a user

    Args:
        user: User to check
        db: Database session

    Returns:
        list: List of role names
    """
    roles = db.query(Role.name).join(
        user_roles, Role.id == user_roles.c.role_id
    ).filter(
        user_roles.c.user_id == user.id
    ).all()

    return [r[0] for r in roles]


def get_user_permissions(user: User, db: Session) -> list[str]:
    """
    Get list of permission names for a user

    Args:
        user: User to check
        db: Database session

    Returns:
        list: List of permission names
    """
    permissions = db.query(Permission.name).join(
        role_permissions, Permission.id == role_permissions.c.permission_id
    ).join(
        Role, Role.id == role_permissions.c.role_id
    ).join(
        user_roles, Role.id == user_roles.c.role_id
    ).filter(
        user_roles.c.user_id == user.id
    ).distinct().all()

    return [p[0] for p in permissions]
