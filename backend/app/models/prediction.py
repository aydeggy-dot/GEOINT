"""
Risk prediction data model for forecasting security incidents
"""
from sqlalchemy import Column, String, Float, DateTime, Date, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
import uuid
from app.database import Base


class Prediction(Base):
    """
    Risk prediction table storing ML-based forecasts
    """
    __tablename__ = "predictions"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Spatial grid cell
    location = Column(
        Geometry(geometry_type='POINT', srid=4326),
        nullable=False
    )
    grid_cell_id = Column(String(50), index=True)  # e.g., "9.5_7.5" for 10km grid
    state = Column(String(100), index=True)

    # Prediction
    risk_score = Column(Float, nullable=False)  # 0-100 scale
    confidence = Column(Float)  # 0-1 confidence interval
    prediction_date = Column(Date, nullable=False, index=True)  # Date this prediction is for
    forecast_horizon_days = Column(Integer, default=7)  # How many days ahead

    # Model information
    model_version = Column(String(50))
    model_type = Column(String(50))  # "random_forest", "xgboost", etc.

    # Contributing factors
    factors = Column(JSONB)  # {"historical_7d": 5, "distance_to_conflict": 25.5, etc.}
    feature_importance = Column(JSONB)  # Which features drove this prediction

    # Actual outcome (for accuracy tracking)
    actual_incidents = Column(Integer, nullable=True)  # How many incidents actually occurred
    prediction_error = Column(Float, nullable=True)  # Difference from prediction

    # Timing
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Prediction {self.grid_cell_id} on {self.prediction_date} - Risk: {self.risk_score:.1f}>"

    @property
    def risk_level(self):
        """Convert numeric risk score to categorical level"""
        if self.risk_score >= 75:
            return "critical"
        elif self.risk_score >= 50:
            return "high"
        elif self.risk_score >= 25:
            return "moderate"
        else:
            return "low"

    def to_geojson_feature(self):
        """Convert prediction to GeoJSON feature format"""
        return {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [self.location.longitude, self.location.latitude]
            },
            "properties": {
                "id": str(self.id),
                "grid_cell_id": self.grid_cell_id,
                "risk_score": self.risk_score,
                "risk_level": self.risk_level,
                "confidence": self.confidence,
                "prediction_date": self.prediction_date.isoformat() if self.prediction_date else None,
                "state": self.state,
                "factors": self.factors
            }
        }
