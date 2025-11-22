"""
Pydantic schemas for alert API validation
"""
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime
from uuid import UUID
from app.models.alert import AlertType, AlertStatus


class AlertCreate(BaseModel):
    """Schema for creating a new alert"""
    incident_id: UUID
    alert_type: AlertType
    message: str
    title: Optional[str] = None
    radius_km: float


class AlertResponse(BaseModel):
    """Schema for alert response"""
    id: UUID
    incident_id: UUID
    alert_type: AlertType
    message: str
    title: Optional[str] = None
    status: AlertStatus
    radius_km: Optional[float] = None
    recipients_count: int
    delivery_status: Optional[Dict] = None
    created_at: datetime
    sent_at: Optional[datetime] = None

    class Config:
        from_attributes = True
