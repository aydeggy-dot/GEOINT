"""
Pydantic schemas for incident API validation and serialization
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from app.models.incident import IncidentType, SeverityLevel


class PointGeometry(BaseModel):
    """GeoJSON Point geometry"""
    type: str = "Point"
    coordinates: List[float] = Field(..., min_length=2, max_length=2)

    @field_validator('coordinates')
    @classmethod
    def validate_coordinates(cls, v):
        """Validate longitude and latitude are in valid ranges"""
        if len(v) != 2:
            raise ValueError('Coordinates must be [longitude, latitude]')

        lon, lat = v
        if not (-180 <= lon <= 180):
            raise ValueError(f'Longitude must be between -180 and 180, got {lon}')
        if not (-90 <= lat <= 90):
            raise ValueError(f'Latitude must be between -90 and 90, got {lat}')

        return v


class CasualtyInfo(BaseModel):
    """Casualty information"""
    killed: int = Field(default=0, ge=0)
    injured: int = Field(default=0, ge=0)
    missing: int = Field(default=0, ge=0)


class IncidentCreate(BaseModel):
    """Schema for creating a new incident report"""
    incident_type: IncidentType
    severity: SeverityLevel
    location: PointGeometry
    description: str = Field(..., min_length=10, max_length=2000)
    timestamp: datetime
    casualties: Optional[CasualtyInfo] = None
    reporter_phone: Optional[str] = Field(None, max_length=20)
    is_anonymous: bool = False
    media_urls: Optional[List[str]] = None
    tags: Optional[List[str]] = None

    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        """Ensure description is meaningful"""
        if len(v.strip()) < 10:
            raise ValueError('Description must be at least 10 characters')
        return v.strip()


class IncidentUpdate(BaseModel):
    """Schema for updating an existing incident"""
    incident_type: Optional[IncidentType] = None
    severity: Optional[SeverityLevel] = None
    description: Optional[str] = None
    verified: Optional[bool] = None
    verification_notes: Optional[str] = None
    casualties: Optional[CasualtyInfo] = None
    media_urls: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class IncidentResponse(BaseModel):
    """Schema for incident response"""
    id: UUID
    incident_type: IncidentType
    severity: SeverityLevel
    description: str
    location_name: Optional[str] = None
    state: Optional[str] = None
    lga: Optional[str] = None
    verified: bool
    verification_score: float
    casualties: Optional[Dict[str, int]] = None
    timestamp: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    media_urls: Optional[List[str]] = None
    tags: Optional[List[str]] = None

    class Config:
        from_attributes = True


class IncidentGeoJSON(BaseModel):
    """GeoJSON feature for incident"""
    type: str = "Feature"
    geometry: PointGeometry
    properties: Dict[str, Any]


class IncidentListResponse(BaseModel):
    """Paginated list of incidents"""
    total: int
    page: int
    page_size: int
    incidents: List[IncidentResponse]


class NearbyIncidentsQuery(BaseModel):
    """Query parameters for nearby incidents search"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius_km: float = Field(default=50.0, gt=0, le=500)
    days: int = Field(default=7, gt=0, le=365)
    incident_types: Optional[List[IncidentType]] = None
    severities: Optional[List[SeverityLevel]] = None
    verified_only: bool = False


class IncidentStats(BaseModel):
    """Statistics about incidents"""
    total_incidents: int
    by_type: Dict[str, int]
    by_severity: Dict[str, int]
    by_state: Dict[str, int]
    verified_count: int
    unverified_count: int
    casualties_total: Dict[str, int]
    time_range_start: datetime
    time_range_end: datetime
    # Comparison metrics
    total_incidents_change: Optional[float] = None  # Percentage change from previous period
    verified_count_change: Optional[float] = None
    casualties_change: Optional[float] = None
    previous_period_total: Optional[int] = None
