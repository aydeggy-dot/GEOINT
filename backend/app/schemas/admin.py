"""
Admin API Schemas
Pydantic models for admin user management, role management, and audit logs
"""
from pydantic import BaseModel, EmailStr, UUID4, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ==================== User Status Enum ====================

class UserStatus(str, Enum):
    """User account status options"""
    active = "active"
    suspended = "suspended"
    banned = "banned"
    pending = "pending"


# ==================== User Management Schemas ====================

class UserListItem(BaseModel):
    """User list item for admin user listing"""
    id: UUID4
    email: EmailStr
    name: str
    status: str
    email_verified: bool
    is_admin: bool
    trust_score: float
    created_at: datetime
    last_login_at: Optional[datetime] = None
    roles: List[str] = []

    class Config:
        from_attributes = True


class UserDetailResponse(BaseModel):
    """Detailed user information for admin"""
    id: UUID4
    email: EmailStr
    name: str
    status: str
    email_verified: bool
    is_admin: bool
    trust_score: float
    failed_login_attempts: int
    locked_until: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    password_changed_at: Optional[datetime] = None
    roles: List[str] = []
    permissions: List[str] = []

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    """Request to update user information"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    status: Optional[UserStatus] = None
    trust_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    is_admin: Optional[bool] = None


class UserStatusUpdateRequest(BaseModel):
    """Request to update user status"""
    status: UserStatus
    reason: Optional[str] = Field(None, max_length=500)


class UserListResponse(BaseModel):
    """Paginated user list response"""
    users: List[UserListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


# ==================== Role Management Schemas ====================

class PermissionSchema(BaseModel):
    """Permission schema"""
    id: UUID4
    name: str
    resource: str
    action: str
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RoleSchema(BaseModel):
    """Role schema without permissions"""
    id: UUID4
    name: str
    display_name: str
    description: Optional[str] = None
    is_system_role: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RoleDetailResponse(BaseModel):
    """Detailed role information with permissions"""
    id: UUID4
    name: str
    display_name: str
    description: Optional[str] = None
    is_system_role: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    permissions: List[PermissionSchema] = []

    class Config:
        from_attributes = True


class AssignRoleRequest(BaseModel):
    """Request to assign role to user"""
    role_name: str
    expires_at: Optional[datetime] = None


class RemoveRoleRequest(BaseModel):
    """Request to remove role from user"""
    role_name: str


# ==================== Audit Log Schemas ====================

class AuditLogSchema(BaseModel):
    """Audit log entry schema"""
    id: UUID4
    user_id: Optional[UUID4] = None
    user_email: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    changes: Optional[dict] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Paginated audit log list response"""
    logs: List[AuditLogSchema]
    total: int
    page: int
    page_size: int
    total_pages: int


# ==================== Statistics Schemas ====================

class UserStatistics(BaseModel):
    """User statistics for admin dashboard"""
    total_users: int
    active_users: int
    suspended_users: int
    banned_users: int
    pending_users: int
    verified_users: int
    unverified_users: int
    users_with_2fa: int
    new_users_today: int
    new_users_this_week: int
    new_users_this_month: int


class RoleStatistics(BaseModel):
    """Role distribution statistics"""
    role_name: str
    display_name: str
    user_count: int


class SystemStatistics(BaseModel):
    """Overall system statistics"""
    user_stats: UserStatistics
    role_distribution: List[RoleStatistics]
    total_sessions: int
    active_sessions: int


# ==================== Bulk Operations ====================

class BulkUserActionRequest(BaseModel):
    """Request for bulk user actions"""
    user_ids: List[UUID4]
    action: str  # 'suspend', 'activate', 'verify', 'delete'
    reason: Optional[str] = None


class BulkActionResponse(BaseModel):
    """Response from bulk user action"""
    success_count: int
    failed_count: int
    errors: List[dict] = []
