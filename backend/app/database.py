"""
Database connection and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from geoalchemy2 import Geometry
from app.config import get_settings

settings = get_settings()

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


def get_db():
    """
    Dependency function to get database session.
    Use with FastAPI Depends.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database with PostGIS extension and create tables
    """
    from sqlalchemy import text

    # Enable PostGIS extension
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        conn.commit()

    # Import all models to ensure they're registered
    from app.models import incident, user, alert, prediction

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully with PostGIS extension")


def create_spatial_indexes():
    """
    Create spatial indexes for better query performance
    """
    from sqlalchemy import text

    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_incidents_location ON incidents USING GIST (location)",
        "CREATE INDEX IF NOT EXISTS idx_users_location ON users USING GIST (location)",
        "CREATE INDEX IF NOT EXISTS idx_alerts_target_area ON alerts USING GIST (target_area)",
        "CREATE INDEX IF NOT EXISTS idx_predictions_location ON predictions USING GIST (location)",
    ]

    with engine.connect() as conn:
        for index_sql in indexes:
            try:
                conn.execute(text(index_sql))
            except Exception as e:
                # Skip if table or column doesn't exist yet
                print(f"Skipping index creation: {e}")
        conn.commit()

    print("Spatial indexes created successfully")
