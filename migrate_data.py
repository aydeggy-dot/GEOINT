"""
Script to migrate data from local database to production
"""
import os
import json
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Database URLs
LOCAL_DB = os.getenv('LOCAL_DATABASE_URL', "postgresql://postgres:postgres@localhost:5432/nigeria_security")
PROD_DB = os.getenv('DATABASE_URL', os.getenv('PROD_DATABASE_URL', ''))

def migrate_data():
    print("Connecting to databases...")
    local_engine = create_engine(LOCAL_DB)
    prod_engine = create_engine(PROD_DB)

    with local_engine.connect() as local_conn, prod_engine.connect() as prod_conn:
        # Start transaction
        trans = prod_conn.begin()

        try:
            # 1. Migrate Users
            print("\n1. Migrating users...")
            users = local_conn.execute(text("SELECT * FROM users")).fetchall()
            print(f"Found {len(users)} users to migrate")

            for user in users:
                # Check if user exists
                existing = prod_conn.execute(
                    text("SELECT id FROM users WHERE email = :email"),
                    {"email": user.email}
                ).fetchone()

                if not existing:
                    prod_conn.execute(text("""
                        INSERT INTO users (
                            id, email, password_hash, name, phone_number,
                            is_active, is_admin, is_verified_reporter,
                            trust_score, reports_submitted, reports_verified, reports_rejected,
                            email_verified, phone_verified, receive_alerts, receive_sms_alerts,
                            alert_radius_km, status, created_at, updated_at, registered_at
                        ) VALUES (
                            :id, :email, :password_hash, :name, :phone_number,
                            :is_active, :is_admin, :is_verified_reporter,
                            :trust_score, :reports_submitted, :reports_verified, :reports_rejected,
                            :email_verified, :phone_verified, :receive_alerts, :receive_sms_alerts,
                            :alert_radius_km, :status, :created_at, :updated_at, :registered_at
                        )
                    """), {
                        "id": user.id,
                        "email": user.email,
                        "password_hash": user.password_hash,
                        "name": user.name,
                        "phone_number": user.phone_number,
                        "is_active": user.is_active,
                        "is_admin": user.is_admin,
                        "is_verified_reporter": user.is_verified_reporter,
                        "trust_score": user.trust_score,
                        "reports_submitted": user.reports_submitted,
                        "reports_verified": user.reports_verified,
                        "reports_rejected": user.reports_rejected,
                        "email_verified": user.email_verified,
                        "phone_verified": user.phone_verified,
                        "receive_alerts": user.receive_alerts,
                        "receive_sms_alerts": user.receive_sms_alerts,
                        "alert_radius_km": user.alert_radius_km,
                        "status": user.status,
                        "created_at": user.created_at,
                        "updated_at": user.updated_at,
                        "registered_at": user.registered_at
                    })
                    print(f"  - Migrated user: {user.email}")
                else:
                    print(f"  - User already exists: {user.email}")

            # 2. Migrate Incidents
            print("\n2. Migrating incidents...")
            incidents = local_conn.execute(text("SELECT * FROM incidents")).fetchall()
            print(f"Found {len(incidents)} incidents to migrate")

            for incident in incidents:
                # Check if incident exists
                existing = prod_conn.execute(
                    text("SELECT id FROM incidents WHERE id = :id"),
                    {"id": incident.id}
                ).fetchone()

                if not existing:
                    # Convert dict fields to JSON strings for JSONB columns
                    casualties_json = json.dumps(incident.casualties) if isinstance(incident.casualties, dict) else incident.casualties
                    additional_data_json = json.dumps(incident.additional_data) if isinstance(incident.additional_data, dict) else incident.additional_data

                    # Handle array fields - convert string to list if needed
                    if isinstance(incident.media_urls, str):
                        try:
                            media_urls_array = json.loads(incident.media_urls) if incident.media_urls else None
                        except:
                            media_urls_array = None
                    elif isinstance(incident.media_urls, list):
                        media_urls_array = incident.media_urls
                    else:
                        media_urls_array = None

                    if isinstance(incident.tags, str):
                        try:
                            tags_array = json.loads(incident.tags) if incident.tags else None
                        except:
                            tags_array = None
                    elif isinstance(incident.tags, list):
                        tags_array = incident.tags
                    else:
                        tags_array = None

                    prod_conn.execute(text("""
                        INSERT INTO incidents (
                            id, incident_type, severity, description,
                            location, location_name, state, lga,
                            verified, verification_score, verified_by, verification_notes,
                            reporter_id, reporter_phone, is_anonymous,
                            media_urls, casualties, timestamp,
                            created_at, updated_at, additional_data, tags
                        ) VALUES (
                            :id, :incident_type, :severity, :description,
                            :location, :location_name, :state, :lga,
                            :verified, :verification_score, :verified_by, :verification_notes,
                            :reporter_id, :reporter_phone, :is_anonymous,
                            :media_urls, :casualties, :timestamp,
                            :created_at, :updated_at, :additional_data, :tags
                        )
                    """), {
                        "id": incident.id,
                        "incident_type": incident.incident_type,
                        "severity": incident.severity,
                        "description": incident.description,
                        "location": incident.location,
                        "location_name": incident.location_name,
                        "state": incident.state,
                        "lga": incident.lga,
                        "verified": incident.verified,
                        "verification_score": incident.verification_score,
                        "verified_by": incident.verified_by,
                        "verification_notes": incident.verification_notes,
                        "reporter_id": incident.reporter_id,
                        "reporter_phone": incident.reporter_phone,
                        "is_anonymous": incident.is_anonymous,
                        "media_urls": media_urls_array,
                        "casualties": casualties_json,
                        "timestamp": incident.timestamp,
                        "created_at": incident.created_at,
                        "updated_at": incident.updated_at,
                        "additional_data": additional_data_json,
                        "tags": tags_array
                    })
                    print(f"  - Migrated incident: {incident.description[:50] if incident.description else 'No description'}...")
                else:
                    print(f"  - Incident already exists: {incident.id}")

            # Commit transaction
            trans.commit()
            print("\nData migration completed successfully!")

        except Exception as e:
            trans.rollback()
            print(f"\nError during migration: {e}")
            raise

if __name__ == "__main__":
    migrate_data()
