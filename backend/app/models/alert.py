"""
Alert data model for security warnings
"""
from sqlalchemy import Column, String, Text, DateTime, Enum, ForeignKey, Integer, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
import uuid
import enum
from app.database import Base


class AlertType(str, enum.Enum):
    """Alert priority levels"""
    CRITICAL = "critical"  # Immediate danger - evacuate
    HIGH = "high"  # Serious threat - take precautions
    MEDIUM = "medium"  # Elevated risk - stay alert
    LOW = "low"  # General awareness


class AlertStatus(str, enum.Enum):
    """Alert delivery status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"


class Alert(Base):
    """
    Alert table for security warnings sent to users
    """
    __tablename__ = "alerts"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Related incident
    incident_id = Column(UUID(as_uuid=True), ForeignKey('incidents.id'), nullable=False, index=True)

    # Alert details
    alert_type = Column(Enum(AlertType), nullable=False, index=True)
    message = Column(Text, nullable=False)
    title = Column(String(255))

    # Affected area (polygon or buffer around incident)
    target_area = Column(
        Geometry(geometry_type='POLYGON', srid=4326),
        nullable=True
    )
    radius_km = Column(Float)  # Radius of impact zone

    # Delivery tracking
    status = Column(Enum(AlertStatus), default=AlertStatus.PENDING, index=True)
    delivery_status = Column(JSONB)  # {"sms": 150, "push": 200, "failed": 10}
    recipients_count = Column(Integer, default=0)

    # Timing
    sent_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))  # When alert is no longer relevant

    # Additional data
    additional_data = Column(JSONB)  # Extra information (safe routes, assembly points, etc.) - renamed from 'metadata' to avoid SQLAlchemy conflict

    def __repr__(self):
        return f"<Alert {self.id} - {self.alert_type.value} for incident {self.incident_id}>"
