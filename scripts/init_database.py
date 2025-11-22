"""
Initialize database - Create all tables and spatial indexes
Run this before seeding data
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

print("\n" + "="*70)
print("  DATABASE INITIALIZATION")
print("="*70 + "\n")

print("Importing database modules...")
try:
    from app.database import init_db, create_spatial_indexes, engine
    from sqlalchemy import text
    print("[OK] Modules imported successfully")
except Exception as e:
    print(f"[ERROR] Error importing modules: {e}")
    print("\nMake sure you're in the project directory and dependencies are installed:")
    print("  cd C:\\DEV\\GEOINT\\nigeria-security-system")
    print("  pip install sqlalchemy geoalchemy2 shapely")
    sys.exit(1)

print("\n" + "-"*70)
print("Step 1: Enabling PostGIS Extension")
print("-"*70)

try:
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        conn.commit()
    print("[OK] PostGIS extension enabled")
except Exception as e:
    print(f"[ERROR] Error enabling PostGIS: {e}")
    sys.exit(1)

print("\n" + "-"*70)
print("Step 2: Creating Database Tables")
print("-"*70)

try:
    from app.database import Base

    # Import all models so they're registered with Base
    print("  - Importing models...")
    from app.models import incident, user, alert, prediction

    print("  - Creating tables...")
    Base.metadata.create_all(bind=engine)

    print("[OK] All tables created successfully")

    # List created tables
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            AND table_name IN ('incidents', 'users', 'alerts', 'predictions')
            ORDER BY table_name
        """))

        tables = [row[0] for row in result]

        if tables:
            print("\n  Created tables:")
            for table in tables:
                print(f"    - {table}")
        else:
            print("\n  [WARN] Warning: Tables may not have been created")

except Exception as e:
    print(f"[ERROR] Error creating tables: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "-"*70)
print("Step 3: Creating Spatial Indexes")
print("-"*70)

try:
    create_spatial_indexes()
    print("[OK] Spatial indexes created")
except Exception as e:
    print(f"[ERROR] Error creating spatial indexes: {e}")
    print("  (This is OK - indexes may already exist)")

print("\n" + "-"*70)
print("Step 4: Verifying Database")
print("-"*70)

try:
    with engine.connect() as conn:
        # Check PostGIS version
        result = conn.execute(text("SELECT PostGIS_version()"))
        postgis_version = result.fetchone()[0]
        print(f"[OK] PostGIS version: {postgis_version}")

        # Count tables
        result = conn.execute(text("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('incidents', 'users', 'alerts', 'predictions')
        """))
        table_count = result.fetchone()[0]
        print(f"[OK] Application tables created: {table_count}/4")

        if table_count < 4:
            print("\n[WARN] Warning: Not all tables were created")
            print("  Expected: 4 (incidents, users, alerts, predictions)")
            print(f"  Found: {table_count}")

except Exception as e:
    print(f"[ERROR] Error verifying database: {e}")

print("\n" + "="*70)
print("  DATABASE INITIALIZATION COMPLETE")
print("="*70)

print("\nNext steps:")
print("  1. Verify tables exist:")
print("     docker exec -it nigeria-security-postgres psql -U postgres -d nigeria_security -c '\\dt'")
print("\n  2. Load sample data:")
print("     python scripts/seed_database.py")
print("\n  3. View data:")
print("     python scripts/view_database.py")
print()
