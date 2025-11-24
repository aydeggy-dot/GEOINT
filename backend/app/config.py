"""
Configuration management for Nigeria Security System
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "Nigeria Security Early Warning System"
    API_VERSION: str = "v1"
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-change-in-production"

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/nigeria_security"
    POSTGIS_VERSION: str = "3.3"

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:5173"
    FRONTEND_URL: str = "http://localhost:5173"  # Frontend URL for email links

    @property
    def ALLOWED_ORIGINS_LIST(self) -> List[str]:
        """Parse ALLOWED_ORIGINS as a list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    # Geospatial Settings
    DEFAULT_SRID: int = 4326  # WGS84
    DISTANCE_THRESHOLD_KM: float = 50.0
    RISK_GRID_RESOLUTION_KM: float = 10.0

    # API Keys (to be set in production)
    MAPBOX_ACCESS_TOKEN: str = ""
    AFRICASTALKING_USERNAME: str = ""
    AFRICASTALKING_API_KEY: str = ""

    # Authentication & JWT
    JWT_SECRET_KEY: str = "your-jwt-secret-key-change-in-production-use-openssl-rand-hex-32"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # Short-lived access tokens
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # Refresh tokens valid for 7 days

    # Email Service (Brevo or Gmail)
    USE_GMAIL: bool = False  # Set to True to use Gmail instead of Brevo
    BREVO_API_KEY: str = ""  # Get from https://app.brevo.com/settings/keys/api
    GMAIL_EMAIL: str = ""  # Your Gmail address
    GMAIL_APP_PASSWORD: str = ""  # Gmail App Password (not regular password!)
    EMAIL_FROM_ADDRESS: str = "noreply@nigeriasecurity.gov.ng"
    EMAIL_FROM_NAME: str = "Nigeria Security EWS"

    # Email Verification
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 1

    # Security
    PASSWORD_MIN_LENGTH: int = 8
    MAX_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_MINUTES: int = 15
    RATE_LIMIT_PER_MINUTE: int = 60

    # Alert Zones (in kilometers)
    IMMEDIATE_ZONE_KM: float = 5.0
    WARNING_ZONE_KM: float = 20.0
    WATCH_ZONE_KM: float = 50.0

    # Verification Thresholds
    AUTO_VERIFY_THRESHOLD: float = 0.8
    MANUAL_REVIEW_THRESHOLD: float = 0.5

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Nigerian States for validation
NIGERIAN_STATES = [
    "Abia", "Adamawa", "Akwa Ibom", "Anambra", "Bauchi", "Bayelsa",
    "Benue", "Borno", "Cross River", "Delta", "Ebonyi", "Edo",
    "Ekiti", "Enugu", "Gombe", "Imo", "Jigawa", "Kaduna",
    "Kano", "Katsina", "Kebbi", "Kogi", "Kwara", "Lagos",
    "Nasarawa", "Niger", "Ogun", "Ondo", "Osun", "Oyo",
    "Plateau", "Rivers", "Sokoto", "Taraba", "Yobe", "Zamfara",
    "Federal Capital Territory"
]

# High-risk conflict zones
CONFLICT_ZONES = {
    "northeast_insurgency": ["Borno", "Yobe", "Adamawa"],
    "northwest_banditry": ["Zamfara", "Katsina", "Sokoto", "Kaduna"],
    "middle_belt_clashes": ["Plateau", "Benue", "Nasarawa"]
}

# Nigerian boundary (approximate bounding box)
NIGERIA_BOUNDS = {
    "min_lat": 4.0,
    "max_lat": 14.0,
    "min_lon": 2.5,
    "max_lon": 15.0
}
