"""
Admin API Routes
User management, role assignment, audit logs, and system statistics
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
from typing import Optional, List
from datetime import datetime, timezone
import math

from app.database import get_db
from app.models.user import User
from app.models.auth import Role, Permission, UserSession, AuditLog, user_roles, role_permissions
from app.schemas.admin import (
    UserListResponse, UserListItem, UserDetailResponse, UserUpdateRequest,
    UserStatusUpdateRequest, RoleSchema, RoleDetailResponse, PermissionSchema,
    AssignRoleRequest, AuditLogListResponse, AuditLogSchema, SystemStatistics,
    UserStatistics, RoleStatistics, BulkUserActionRequest, BulkActionResponse
)
from app.api.dependencies.auth import get_current_user, require_admin, get_user_roles, get_user_permissions
from app.utils.audit import log_admin_action

router = APIRouter(prefix="/admin", tags=["Admin"])


# ==================== User Management ====================

@router.get("/users", response_model=UserListResponse, dependencies=[Depends(require_admin)])
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    role: Optional[str] = None,
    verified_only: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all users with filtering and pagination

    Requires: admin or super_admin role
    """
    # Base query
    query = db.query(User)

    # Apply filters
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                User.email.ilike(search_pattern),
                User.name.ilike(search_pattern)
            )
        )

    if status:
        query = query.filter(User.status == status)

    if verified_only is not None:
        query = query.filter(User.email_verified == verified_only)

    if role:
        # Filter by role
        query = query.join(user_roles).join(Role).filter(Role.name == role)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    users = query.order_by(User.created_at.desc()).offset(offset).limit(page_size).all()

    # Get roles for each user
    user_list = []
    for user in users:
        roles = get_user_roles(user, db)
        user_list.append(
            UserListItem(
                id=user.id,
                email=user.email,
                name=user.name,
                status=user.status,
                email_verified=user.email_verified,
                is_admin=user.is_admin,
                trust_score=user.trust_score,
                created_at=user.created_at,
                last_login_at=user.last_login_at,
                roles=roles
            )
        )

    # Calculate total pages
    total_pages = math.ceil(total / page_size)

    # Log action
    log_admin_action(
        db=db,
        user_id=current_user.id,
        action="list_users",
        resource_type="user",
        status="success"
    )

    return UserListResponse(
        users=user_list,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/users/{user_id}", response_model=UserDetailResponse, dependencies=[Depends(require_admin)])
async def get_user_details(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed information about a specific user

    Requires: admin or super_admin role
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Get user roles and permissions
    roles = get_user_roles(user, db)
    permissions = get_user_permissions(user, db)

    # Log action
    log_admin_action(
        db=db,
        user_id=current_user.id,
        action="view_user",
        resource_type="user",
        resource_id=str(user_id),
        status="success"
    )

    return UserDetailResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        status=user.status,
        email_verified=user.email_verified,
        is_admin=user.is_admin,
        trust_score=user.trust_score,
        failed_login_attempts=user.failed_login_attempts,
        locked_until=user.locked_until,
        last_login_at=user.last_login_at,
        last_seen=user.last_seen,
        created_at=user.created_at,
        updated_at=user.updated_at,
        password_changed_at=user.password_changed_at,
        roles=roles,
        permissions=permissions
    )


@router.put("/users/{user_id}", response_model=UserDetailResponse, dependencies=[Depends(require_admin)])
async def update_user(
    user_id: str,
    update_data: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update user information

    Requires: admin or super_admin role
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Track changes for audit log
    changes = {}

    # Update fields
    if update_data.name is not None:
        changes["name"] = {"from": user.name, "to": update_data.name}
        user.name = update_data.name

    if update_data.email is not None:
        # Check if email already exists
        existing = db.query(User).filter(
            User.email == update_data.email,
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        changes["email"] = {"from": user.email, "to": update_data.email}
        user.email = update_data.email
        user.email_verified = False  # Require re-verification

    if update_data.status is not None:
        changes["status"] = {"from": user.status, "to": update_data.status.value}
        user.status = update_data.status.value

    if update_data.trust_score is not None:
        changes["trust_score"] = {"from": user.trust_score, "to": update_data.trust_score}
        user.trust_score = update_data.trust_score

    if update_data.is_admin is not None:
        changes["is_admin"] = {"from": user.is_admin, "to": update_data.is_admin}
        user.is_admin = update_data.is_admin

    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    # Get roles and permissions
    roles = get_user_roles(user, db)
    permissions = get_user_permissions(user, db)

    # Log action
    log_admin_action(
        db=db,
        user_id=current_user.id,
        action="update_user",
        resource_type="user",
        resource_id=str(user_id),
        changes=changes,
        status="success"
    )

    return UserDetailResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        status=user.status,
        email_verified=user.email_verified,
        is_admin=user.is_admin,
        trust_score=user.trust_score,
        failed_login_attempts=user.failed_login_attempts,
        locked_until=user.locked_until,
        last_login_at=user.last_login_at,
        last_seen=user.last_seen,
        created_at=user.created_at,
        updated_at=user.updated_at,
        password_changed_at=user.password_changed_at,
        roles=roles,
        permissions=permissions
    )


@router.delete("/users/{user_id}", dependencies=[Depends(require_admin)])
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a user account

    Requires: admin or super_admin role
    """
    # Prevent self-deletion
    if str(current_user.id) == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Store user info for audit log
    user_email = user.email

    # Delete user (cascades to sessions, roles, etc.)
    db.delete(user)
    db.commit()

    # Log action
    log_admin_action(
        db=db,
        user_id=current_user.id,
        action="delete_user",
        resource_type="user",
        resource_id=str(user_id),
        changes={"email": user_email},
        status="success"
    )

    return {"message": f"User {user_email} deleted successfully"}


@router.post("/users/{user_id}/verify", dependencies=[Depends(require_admin)])
async def verify_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually verify a user's email

    Requires: admin or super_admin role
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.email_verified:
        return {"message": "User already verified"}

    user.email_verified = True
    user.updated_at = datetime.now(timezone.utc)
    db.commit()

    # Log action
    log_admin_action(
        db=db,
        user_id=current_user.id,
        action="verify_user",
        resource_type="user",
        resource_id=str(user_id),
        status="success"
    )

    return {"message": f"User {user.email} verified successfully"}


@router.put("/users/{user_id}/status", dependencies=[Depends(require_admin)])
async def update_user_status(
    user_id: str,
    status_update: UserStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update user account status

    Requires: admin or super_admin role
    """
    # Prevent self-suspension/ban
    if str(current_user.id) == user_id and status_update.status in ["suspended", "banned"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot suspend or ban your own account"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    old_status = user.status
    user.status = status_update.status.value
    user.updated_at = datetime.now(timezone.utc)
    db.commit()

    # Log action
    log_admin_action(
        db=db,
        user_id=current_user.id,
        action="update_user_status",
        resource_type="user",
        resource_id=str(user_id),
        changes={
            "status": {"from": old_status, "to": status_update.status.value},
            "reason": status_update.reason
        },
        status="success"
    )

    return {
        "message": f"User status updated to {status_update.status.value}",
        "user_id": user_id,
        "new_status": status_update.status.value
    }


# ==================== Role Management ====================

@router.get("/roles", response_model=List[RoleSchema], dependencies=[Depends(require_admin)])
async def list_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all roles

    Requires: admin or super_admin role
    """
    roles = db.query(Role).order_by(Role.name).all()

    # Log action
    log_admin_action(
        db=db,
        user_id=current_user.id,
        action="list_roles",
        resource_type="role",
        status="success"
    )

    return roles


@router.get("/roles/{role_id}", response_model=RoleDetailResponse, dependencies=[Depends(require_admin)])
async def get_role_details(
    role_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed role information including permissions

    Requires: admin or super_admin role
    """
    role = db.query(Role).filter(Role.id == role_id).first()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    # Log action
    log_admin_action(
        db=db,
        user_id=current_user.id,
        action="view_role",
        resource_type="role",
        resource_id=str(role_id),
        status="success"
    )

    return role


@router.post("/users/{user_id}/roles", dependencies=[Depends(require_admin)])
async def assign_role_to_user(
    user_id: str,
    role_data: AssignRoleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Assign a role to a user

    Requires: admin or super_admin role
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    role = db.query(Role).filter(Role.name == role_data.role_name).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role '{role_data.role_name}' not found"
        )

    # Check if user already has this role
    existing = db.query(user_roles).filter(
        user_roles.c.user_id == user_id,
        user_roles.c.role_id == role.id
    ).first()

    if existing:
        return {"message": f"User already has role '{role_data.role_name}'"}

    # Assign role
    db.execute(
        user_roles.insert().values(
            user_id=user_id,
            role_id=role.id,
            assigned_by=current_user.id,
            assigned_at=datetime.now(timezone.utc),
            expires_at=role_data.expires_at
        )
    )
    db.commit()

    # Log action
    log_admin_action(
        db=db,
        user_id=current_user.id,
        action="assign_role",
        resource_type="user",
        resource_id=str(user_id),
        changes={"role": role_data.role_name, "expires_at": str(role_data.expires_at) if role_data.expires_at else None},
        status="success"
    )

    return {
        "message": f"Role '{role_data.role_name}' assigned to user {user.email}",
        "user_id": user_id,
        "role": role_data.role_name
    }


@router.delete("/users/{user_id}/roles/{role_name}", dependencies=[Depends(require_admin)])
async def remove_role_from_user(
    user_id: str,
    role_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Remove a role from a user

    Requires: admin or super_admin role
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role '{role_name}' not found"
        )

    # Remove role
    result = db.execute(
        user_roles.delete().where(
            and_(
                user_roles.c.user_id == user_id,
                user_roles.c.role_id == role.id
            )
        )
    )
    db.commit()

    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User does not have role '{role_name}'"
        )

    # Log action
    log_admin_action(
        db=db,
        user_id=current_user.id,
        action="remove_role",
        resource_type="user",
        resource_id=str(user_id),
        changes={"role": role_name},
        status="success"
    )

    return {
        "message": f"Role '{role_name}' removed from user {user.email}",
        "user_id": user_id,
        "role": role_name
    }


@router.get("/users/{user_id}/permissions", response_model=List[str], dependencies=[Depends(require_admin)])
async def get_user_permissions_list(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all permissions for a user (through their roles)

    Requires: admin or super_admin role
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    permissions = get_user_permissions(user, db)

    # Log action
    log_admin_action(
        db=db,
        user_id=current_user.id,
        action="view_user_permissions",
        resource_type="user",
        resource_id=str(user_id),
        status="success"
    )

    return permissions


# ==================== Permission Management ====================

@router.get("/permissions", response_model=List[PermissionSchema], dependencies=[Depends(require_admin)])
async def list_permissions(
    resource: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all permissions, optionally filtered by resource

    Requires: admin or super_admin role
    """
    query = db.query(Permission)

    if resource:
        query = query.filter(Permission.resource == resource)

    permissions = query.order_by(Permission.resource, Permission.action).all()

    # Log action
    log_admin_action(
        db=db,
        user_id=current_user.id,
        action="list_permissions",
        resource_type="permission",
        status="success"
    )

    return permissions


# ==================== Audit Logs ====================

@router.get("/audit-logs", response_model=AuditLogListResponse, dependencies=[Depends(require_admin)])
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List audit logs with filtering and pagination

    Requires: admin or super_admin role
    """
    query = db.query(AuditLog)

    # Apply filters
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if status:
        query = query.filter(AuditLog.status == status)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size).all()

    # Enrich with user email
    log_list = []
    for log in logs:
        user_email = None
        if log.user_id:
            user = db.query(User).filter(User.id == log.user_id).first()
            if user:
                user_email = user.email

        log_list.append(
            AuditLogSchema(
                id=log.id,
                user_id=log.user_id,
                user_email=user_email,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=str(log.resource_id) if log.resource_id else None,
                changes=log.changes,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                status=log.status,
                error_message=log.error_message,
                created_at=log.created_at
            )
        )

    # Calculate total pages
    total_pages = math.ceil(total / page_size)

    return AuditLogListResponse(
        logs=log_list,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


# ==================== Statistics ====================

@router.get("/statistics", response_model=SystemStatistics, dependencies=[Depends(require_admin)])
async def get_system_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get system statistics for admin dashboard

    Requires: admin or super_admin role
    """
    # User statistics
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.status == "active").count()
    suspended_users = db.query(User).filter(User.status == "suspended").count()
    banned_users = db.query(User).filter(User.status == "banned").count()
    pending_users = db.query(User).filter(User.status == "pending").count()
    verified_users = db.query(User).filter(User.email_verified == True).count()
    unverified_users = db.query(User).filter(User.email_verified == False).count()

    # Users with 2FA (placeholder - will be implemented when 2FA is built)
    users_with_2fa = 0

    # New users
    now = datetime.now(timezone.utc)
    from datetime import timedelta

    new_users_today = db.query(User).filter(
        User.created_at >= now.replace(hour=0, minute=0, second=0, microsecond=0)
    ).count()

    new_users_this_week = db.query(User).filter(
        User.created_at >= now - timedelta(days=7)
    ).count()

    new_users_this_month = db.query(User).filter(
        User.created_at >= now - timedelta(days=30)
    ).count()

    user_stats = UserStatistics(
        total_users=total_users,
        active_users=active_users,
        suspended_users=suspended_users,
        banned_users=banned_users,
        pending_users=pending_users,
        verified_users=verified_users,
        unverified_users=unverified_users,
        users_with_2fa=users_with_2fa,
        new_users_today=new_users_today,
        new_users_this_week=new_users_this_week,
        new_users_this_month=new_users_this_month
    )

    # Role distribution
    role_distribution = []
    roles = db.query(Role).all()
    for role in roles:
        user_count = db.query(user_roles).filter(user_roles.c.role_id == role.id).count()
        role_distribution.append(
            RoleStatistics(
                role_name=role.name,
                display_name=role.display_name,
                user_count=user_count
            )
        )

    # Session statistics
    total_sessions = db.query(UserSession).count()
    active_sessions = db.query(UserSession).filter(
        UserSession.expires_at > now,
        UserSession.revoked_at == None
    ).count()

    # Log action
    log_admin_action(
        db=db,
        user_id=current_user.id,
        action="view_statistics",
        resource_type="system",
        status="success"
    )

    return SystemStatistics(
        user_stats=user_stats,
        role_distribution=role_distribution,
        total_sessions=total_sessions,
        active_sessions=active_sessions
    )
