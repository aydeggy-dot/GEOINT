"""
Pydantic schemas for user API validation
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserCreate(BaseModel):
    """Schema for creating a new user"""
    phone_number: str = Field(..., max_length=20)
    email: Optional[str] = None
    receive_alerts: bool = True
    alert_radius_km: float = Field(default=50.0, ge=1.0, le=500.0)


class UserResponse(BaseModel):
    """Schema for user response"""
    id: UUID
    phone_number: str
    email: Optional[str] = None
    trust_score: float
    reports_submitted: int
    reports_verified: int
    reports_rejected: int
    receive_alerts: bool
    alert_radius_km: float
    is_active: bool
    is_verified_reporter: bool
    created_at: datetime

    class Config:
        from_attributes = True
