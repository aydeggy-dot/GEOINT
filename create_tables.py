"""
Create database tables in production
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import create_engine
from app.database import Base
# Import all models to ensure they're registered
from app.models import user, incident, auth

# Production database - use DATABASE_URL from environment
import os
PROD_DB = os.getenv('DATABASE_URL', os.getenv('PROD_DATABASE_URL', ''))

print("Creating tables in production database...")
engine = create_engine(PROD_DB)

# Create all tables
Base.metadata.create_all(bind=engine)

print("Tables created successfully!")
