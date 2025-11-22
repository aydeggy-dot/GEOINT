"""
Authentication and authorization models
Roles, permissions, sessions, 2FA, and audit logging
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, ForeignKey, Table, JSON
from sqlalchemy.dialects.postgresql import UUID, INET, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database import Base


# Many-to-many association table for role-permissions
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('permission_id', UUID(as_uuid=True), ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True)
)


# Many-to-many association table for user-roles
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('assigned_by', UUID(as_uuid=True), ForeignKey('users.id'), nullable=True),
    Column('assigned_at', DateTime(timezone=True), server_default=func.now()),
    Column('expires_at', DateTime(timezone=True), nullable=True)
)


class Role(Base):
    """
    Roles for role-based access control (RBAC)
    Examples: admin, moderator, analyst, verified_reporter, user
    """
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False, index=True)  # e.g., 'admin', 'moderator'
    display_name = Column(String(100), nullable=False)  # e.g., 'Administrator'
    description = Column(Text, nullable=True)
    is_system_role = Column(Boolean, default=False)  # System roles cannot be deleted
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")

    def __repr__(self):
        return f"<Role {self.name}>"


class Permission(Base):
    """
    Granular permissions for fine-grained access control
    Format: resource.action (e.g., 'incident.verify', 'user.delete')
    """
    __tablename__ = "permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)  # e.g., 'incident.verify'
    resource = Column(String(50), nullable=False)  # e.g., 'incident', 'user', 'setting'
    action = Column(String(50), nullable=False)  # e.g., 'create', 'read', 'update', 'delete', 'verify'
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

    def __repr__(self):
        return f"<Permission {self.name}>"


class UserSession(Base):
    """
    Track user sessions for security and logout-all-devices functionality
    Stores refresh tokens and session metadata
    """
    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    refresh_token_hash = Column(String(255), unique=True, nullable=False, index=True)

    # Session metadata
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    device_info = Column(JSON, nullable=True)  # Browser, OS, device type

    # Session lifecycle
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)  # For manual logout

    def __repr__(self):
        return f"<UserSession {self.id} for user {self.user_id}>"


class TwoFactorAuth(Base):
    """
    Two-factor authentication settings for users
    Supports TOTP (authenticator apps) and email-based 2FA
    """
    __tablename__ = "two_factor_auth"

    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    method = Column(String(20), nullable=False)  # 'totp' or 'email'
    secret = Column(String(255), nullable=True)  # TOTP secret (base32 encoded, encrypted)
    backup_codes = Column(ARRAY(String), nullable=True)  # Hashed backup codes
    enabled = Column(Boolean, default=False)
    enabled_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<TwoFactorAuth user={self.user_id} method={self.method}>"


class VerificationCode(Base):
    """
    Store verification codes for email verification, 2FA, and password reset
    Single-use codes with expiration
    """
    __tablename__ = "verification_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=True, index=True)
    code = Column(String(10), nullable=False)  # 6-digit code or JWT token
    type = Column(String(50), nullable=False, index=True)  # 'email_verification', '2fa_email', 'password_reset'
    email = Column(String(255), nullable=False, index=True)  # Email where code was sent

    # Security
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)

    # Lifecycle
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<VerificationCode {self.type} for {self.email}>"


class AuditLog(Base):
    """
    Comprehensive audit logging for security and compliance
    Tracks all significant actions in the system
    """
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)

    # Action details
    action = Column(String(100), nullable=False, index=True)  # e.g., 'user.login', 'incident.verify'
    resource_type = Column(String(50), nullable=True, index=True)  # 'user', 'incident', 'setting'
    resource_id = Column(UUID(as_uuid=True), nullable=True)  # ID of affected resource

    # Changes (before/after values in JSON)
    changes = Column(JSON, nullable=True)

    # Request metadata
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)

    # Result
    status = Column(String(20), nullable=False)  # 'success', 'failure'
    error_message = Column(Text, nullable=True)

    # Timestamp (immutable)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    def __repr__(self):
        return f"<AuditLog {self.action} by user {self.user_id}>"


class Alert(Base):
    """
    System alerts sent to users (email/SMS)
    Tracks delivery status and engagement
    """
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)

    # Alert configuration
    type = Column(String(20), nullable=False)  # 'sms', 'email', 'push'
    severity = Column(String(20), nullable=False)  # 'info', 'warning', 'critical'

    # Sender and recipients
    sent_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    recipient_filter = Column(JSON, nullable=True)  # Criteria for selecting recipients

    # Scheduling
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)

    # Delivery tracking
    recipient_count = Column(Integer, default=0)
    delivery_status = Column(JSON, nullable=True)  # {"sent": 100, "delivered": 95, "failed": 5}

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Alert {self.title} type={self.type}>"
