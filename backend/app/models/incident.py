"""
Incident data model with PostGIS spatial support
"""
from sqlalchemy import Column, String, Text, Boolean, Float, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
import uuid
import enum
from app.database import Base


class IncidentType(str, enum.Enum):
    """Types of security incidents in Nigeria"""
    ARMED_ATTACK = "armed_attack"
    KIDNAPPING = "kidnapping"
    BANDITRY = "banditry"
    INSURGENT_ATTACK = "insurgent_attack"
    FARMER_HERDER_CLASH = "farmer_herder_clash"
    ROBBERY = "robbery"
    COMMUNAL_CLASH = "communal_clash"
    CATTLE_RUSTLING = "cattle_rustling"
    BOMB_BLAST = "bomb_blast"
    SHOOTING = "shooting"
    OTHER = "other"


class SeverityLevel(str, enum.Enum):
    """Severity levels for incidents"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class Incident(Base):
    """
    Main incident table storing security incidents with geospatial data
    """
    __tablename__ = "incidents"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Incident details
    incident_type = Column(Enum(IncidentType), nullable=False, index=True)
    severity = Column(Enum(SeverityLevel), nullable=False, index=True)
    description = Column(Text, nullable=False)

    # Geospatial data (SRID 4326 = WGS84)
    location = Column(
        Geometry(geometry_type='POINT', srid=4326),
        nullable=False
    )
    location_name = Column(String(255))  # Human-readable location
    state = Column(String(100), index=True)  # Nigerian state
    lga = Column(String(100))  # Local Government Area

    # Verification
    verified = Column(Boolean, default=False, index=True)
    verification_score = Column(Float, default=0.0)  # 0-1 score
    verified_by = Column(UUID(as_uuid=True), nullable=True)  # Admin user ID
    verification_notes = Column(Text)

    # Reporter information
    reporter_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    reporter_phone = Column(String(20))  # Hashed or encrypted in production
    is_anonymous = Column(Boolean, default=False)

    # Media evidence
    media_urls = Column(ARRAY(Text))  # URLs to photos/videos

    # Casualties
    casualties = Column(JSONB)  # {"killed": int, "injured": int, "missing": int}

    # Temporal data
    timestamp = Column(DateTime(timezone=True), nullable=False)  # When incident occurred
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Additional metadata
    additional_data = Column(JSONB)  # Flexible field for additional data (renamed from 'metadata' to avoid SQLAlchemy conflict)
    tags = Column(ARRAY(String))  # For categorization

    def __repr__(self):
        return f"<Incident {self.id} - {self.incident_type.value} at {self.location_name}>"

    @property
    def latitude(self):
        """Extract latitude from geometry"""
        if self.location:
            return self.location.latitude
        return None

    @property
    def longitude(self):
        """Extract longitude from geometry"""
        if self.location:
            return self.location.longitude
        return None

    @property
    def severity_score(self):
        """Convert severity to numeric score for calculations"""
        scores = {
            SeverityLevel.LOW: 25,
            SeverityLevel.MODERATE: 50,
            SeverityLevel.HIGH: 75,
            SeverityLevel.CRITICAL: 100
        }
        return scores.get(self.severity, 0)

    def to_geojson_feature(self):
        """Convert incident to GeoJSON feature format"""
        return {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [self.longitude, self.latitude]
            },
            "properties": {
                "id": str(self.id),
                "incident_type": self.incident_type.value,
                "severity": self.severity.value,
                "severity_score": self.severity_score,
                "description": self.description,
                "location_name": self.location_name,
                "state": self.state,
                "verified": self.verified,
                "verification_score": self.verification_score,
                "casualties": self.casualties,
                "timestamp": self.timestamp.isoformat() if self.timestamp else None,
                "created_at": self.created_at.isoformat() if self.created_at else None
            }
        }
