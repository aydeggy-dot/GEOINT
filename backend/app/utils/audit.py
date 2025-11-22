"""
Audit Logging Utilities
Track admin actions and security events for compliance and security monitoring
"""
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import uuid

from app.models.auth import AuditLog


def log_admin_action(
    db: Session,
    user_id: Optional[uuid.UUID],
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    changes: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    status: str = "success",
    error_message: Optional[str] = None
) -> AuditLog:
    """
    Log an admin action to the audit log

    Args:
        db: Database session
        user_id: ID of user performing the action
        action: Action performed (e.g., 'create_user', 'delete_incident')
        resource_type: Type of resource (e.g., 'user', 'incident', 'alert')
        resource_id: ID of the resource
        changes: Dictionary of changes made
        ip_address: IP address of the request
        user_agent: User agent string
        status: Status of the action ('success' or 'failure')
        error_message: Error message if action failed

    Returns:
        AuditLog: Created audit log entry
    """
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        changes=changes,
        ip_address=ip_address,
        user_agent=user_agent,
        status=status,
        error_message=error_message,
        created_at=datetime.now(timezone.utc)
    )

    db.add(audit_log)
    db.commit()

    return audit_log


def log_security_event(
    db: Session,
    user_id: Optional[uuid.UUID],
    event_type: str,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> AuditLog:
    """
    Log a security-related event

    Args:
        db: Database session
        user_id: ID of user involved (if applicable)
        event_type: Type of security event (e.g., 'failed_login', 'account_locked')
        details: Additional details about the event
        ip_address: IP address
        user_agent: User agent string

    Returns:
        AuditLog: Created audit log entry
    """
    return log_admin_action(
        db=db,
        user_id=user_id,
        action=f"security_{event_type}",
        resource_type="security",
        changes=details,
        ip_address=ip_address,
        user_agent=user_agent,
        status="success"
    )


def log_authentication_event(
    db: Session,
    user_id: Optional[uuid.UUID],
    event: str,
    success: bool,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> AuditLog:
    """
    Log an authentication event (login, logout, etc.)

    Args:
        db: Database session
        user_id: ID of user
        event: Event type ('login', 'logout', 'token_refresh')
        success: Whether the event was successful
        ip_address: IP address
        user_agent: User agent string
        details: Additional details

    Returns:
        AuditLog: Created audit log entry
    """
    return log_admin_action(
        db=db,
        user_id=user_id,
        action=f"auth_{event}",
        resource_type="authentication",
        changes=details,
        ip_address=ip_address,
        user_agent=user_agent,
        status="success" if success else "failure"
    )
