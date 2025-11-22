"""
User data model for reporters and system users
"""
from sqlalchemy import Column, String, Float, DateTime, Boolean, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
import uuid
from app.database import Base


class User(Base):
    """
    User/reporter table for tracking reporters and their credibility
    Enhanced with authentication and role management
    """
    __tablename__ = "users"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Authentication - Email is now primary identifier
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email_verified = Column(Boolean, default=False)

    # Contact information
    name = Column(String(255), nullable=True)  # Optional display name
    phone_number = Column(String(20), nullable=True)  # Optional, for SMS alerts
    phone_verified = Column(Boolean, default=False)

    # Trust and credibility
    trust_score = Column(Float, default=0.5)  # 0-1 score, starts at neutral 0.5
    reports_submitted = Column(Float, default=0)
    reports_verified = Column(Float, default=0)
    reports_rejected = Column(Float, default=0)

    # Last known location (for proximity-based alerts)
    location = Column(
        Geometry(geometry_type='POINT', srid=4326),
        nullable=True
    )
    location_updated_at = Column(DateTime(timezone=True))

    # User preferences
    receive_alerts = Column(Boolean, default=True)
    alert_radius_km = Column(Float, default=50.0)  # How far to receive alerts
    receive_sms_alerts = Column(Boolean, default=False)  # Opt-in for SMS

    # Account status
    is_active = Column(Boolean, default=True)
    status = Column(String(20), default='active')  # active, suspended, banned
    suspension_reason = Column(Text, nullable=True)
    suspended_until = Column(DateTime(timezone=True), nullable=True)

    # Legacy admin flag (kept for backwards compatibility)
    is_admin = Column(Boolean, default=False)
    is_verified_reporter = Column(Boolean, default=False)  # Trusted reporter status

    # Security
    password_changed_at = Column(DateTime(timezone=True))
    last_login_at = Column(DateTime(timezone=True))
    last_login_ip = Column(INET, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)

    # Temporal data
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    registered_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_seen = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"<User {self.id} - Trust: {self.trust_score:.2f}>"

    @property
    def verification_rate(self):
        """Calculate percentage of reports that were verified"""
        if self.reports_submitted == 0:
            return 0.0
        return self.reports_verified / self.reports_submitted

    def update_trust_score(self):
        """
        Recalculate trust score based on verification history
        Uses weighted formula: verified reports increase score, rejected decrease it
        """
        if self.reports_submitted == 0:
            self.trust_score = 0.5  # Neutral for new users
            return

        # Calculate verification rate
        verified_rate = self.reports_verified / self.reports_submitted
        rejected_rate = self.reports_rejected / self.reports_submitted

        # Weight by volume (more reports = more reliable score)
        volume_weight = min(self.reports_submitted / 20, 1.0)  # Maxes at 20 reports

        # Calculate score: high verification increases, rejections decrease
        base_score = (verified_rate * 0.8) + 0.2  # Start at 0.2, can reach 1.0
        penalty = rejected_rate * 0.3  # Each rejection reduces score

        self.trust_score = max(0.0, min(1.0, (base_score - penalty) * volume_weight + (0.5 * (1 - volume_weight))))
