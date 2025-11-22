"""
Seed sample incident data for testing and demonstration
"""
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta, timezone
import random
import uuid

# Sample Nigerian locations with coordinates
NIGERIAN_LOCATIONS = [
    # Lagos
    {"state": "Lagos", "city": "Lagos Island", "lat": 6.4541, "lng": 3.3947},
    {"state": "Lagos", "city": "Ikeja", "lat": 6.6018, "lng": 3.3515},
    {"state": "Lagos", "city": "Lekki", "lat": 6.4698, "lng": 3.5852},

    # Abuja
    {"state": "FCT", "city": "Garki", "lat": 9.0579, "lng": 7.4951},
    {"state": "FCT", "city": "Wuse", "lat": 9.0643, "lng": 7.4892},
    {"state": "FCT", "city": "Maitama", "lat": 9.0820, "lng": 7.4910},

    # Kano
    {"state": "Kano", "city": "Kano City", "lat": 12.0022, "lng": 8.5920},
    {"state": "Kano", "city": "Fagge", "lat": 11.9950, "lng": 8.5211},

    # Port Harcourt
    {"state": "Rivers", "city": "Port Harcourt", "lat": 4.8156, "lng": 7.0498},
    {"state": "Rivers", "city": "Eleme", "lat": 4.7861, "lng": 7.1564},

    # Kaduna
    {"state": "Kaduna", "city": "Kaduna", "lat": 10.5105, "lng": 7.4165},
    {"state": "Kaduna", "city": "Zaria", "lat": 11.0757, "lng": 7.7044},

    # Enugu
    {"state": "Enugu", "city": "Enugu", "lat": 6.4403, "lng": 7.4940},

    # Ibadan
    {"state": "Oyo", "city": "Ibadan", "lat": 7.3775, "lng": 3.9470},
]

INCIDENT_TYPES = [
    "ARMED_ATTACK",
    "KIDNAPPING",
    "BANDITRY",
    "INSURGENT_ATTACK",
    "FARMER_HERDER_CLASH",
    "ROBBERY",
    "COMMUNAL_CLASH",
    "CATTLE_RUSTLING",
    "BOMB_BLAST",
    "SHOOTING",
    "OTHER"
]

SEVERITY_LEVELS = ["LOW", "MODERATE", "HIGH", "CRITICAL"]

INCIDENT_TEMPLATES = {
    "ARMED_ATTACK": [
        "Armed attack in {location}",
        "Gunmen attack {location}",
        "Armed assault reported at {location}",
    ],
    "KIDNAPPING": [
        "Kidnapping reported in {location}",
        "Abduction incident at {location}",
        "Hostage situation in {location}",
    ],
    "BANDITRY": [
        "Bandit attack in {location}",
        "Armed bandits active near {location}",
        "Banditry incident at {location}",
    ],
    "INSURGENT_ATTACK": [
        "Insurgent attack in {location}",
        "Militant activity reported near {location}",
        "Terrorist incident at {location}",
    ],
    "FARMER_HERDER_CLASH": [
        "Farmer-herder clash in {location}",
        "Herder conflict at {location}",
        "Pastoral clash reported in {location}",
    ],
    "ROBBERY": [
        "Robbery incident at {location}",
        "Armed robbery in {location}",
        "Theft reported at {location}",
    ],
    "COMMUNAL_CLASH": [
        "Communal clash in {location}",
        "Inter-communal violence at {location}",
        "Community conflict in {location}",
    ],
    "CATTLE_RUSTLING": [
        "Cattle rustling in {location}",
        "Livestock theft near {location}",
        "Rustlers active in {location}",
    ],
    "BOMB_BLAST": [
        "Explosion in {location}",
        "Bomb blast at {location}",
        "IED detonated in {location}",
    ],
    "SHOOTING": [
        "Shooting incident in {location}",
        "Gunfire reported at {location}",
        "Armed confrontation in {location}",
    ],
    "OTHER": [
        "Security incident in {location}",
        "Suspicious activity in {location}",
    ]
}

def seed_incidents(num_incidents=50):
    """Seed sample incidents into the database"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="nigeria_security",
            user="postgres",
            password="postgres"
        )
        cur = conn.cursor()

        # Get user ID (use the first user in the database)
        cur.execute("SELECT id FROM users LIMIT 1")
        user_result = cur.fetchone()
        if not user_result:
            print("[ERROR] No users found in database. Please create a user first.")
            return False

        user_id = user_result[0]
        print(f"[INFO] Using user ID: {user_id}")

        # Generate incidents over the last 60 days
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=60)

        incidents_created = 0

        for i in range(num_incidents):
            # Random date within the range
            days_ago = random.randint(0, 60)
            incident_date = end_date - timedelta(
                days=days_ago,
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )

            # Random location
            location = random.choice(NIGERIAN_LOCATIONS)

            # Add some random variation to coordinates (within ~1km)
            lat = location["lat"] + random.uniform(-0.01, 0.01)
            lng = location["lng"] + random.uniform(-0.01, 0.01)

            # Random incident type and severity
            incident_type = random.choice(INCIDENT_TYPES)
            severity = random.choice(SEVERITY_LEVELS)

            # Generate description with title-like first sentence
            templates = INCIDENT_TEMPLATES[incident_type]
            title_template = random.choice(templates)
            title_part = title_template.format(location=location["city"])

            detail_parts = [
                f"Incident occurred at approximately {incident_date.strftime('%H:%M')}. Local authorities have been notified.",
                f"Security forces are responding to the situation. Residents are advised to stay indoors.",
                f"Investigation is ongoing. Multiple witnesses have come forward.",
                f"Emergency services deployed to the area. Situation under control.",
                f"Community leaders working with security agencies to address the situation.",
            ]
            description = f"{title_part}. {random.choice(detail_parts)}"

            # Location name
            location_name = f"{location['city']}, {location['state']}"

            # Verification score (random but realistic)
            verification_score = random.uniform(0.3, 0.9)
            is_verified = verification_score > 0.6

            # Casualties (some incidents)
            casualties = None
            if random.random() < 0.3:  # 30% have casualties
                casualties = {
                    "killed": random.randint(0, 5),
                    "injured": random.randint(0, 10),
                    "missing": random.randint(0, 3)
                }

            # Insert incident
            incident_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO incidents (
                    id, description, incident_type, severity,
                    location, location_name, state,
                    reporter_id, verification_score, verified,
                    casualties, timestamp, created_at, updated_at
                )
                VALUES (
                    %s, %s, %s, %s,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s
                )
            """, (
                incident_id,
                description,
                incident_type,
                severity,
                lng,  # PostGIS uses (lng, lat) order
                lat,
                location_name,
                location["state"],
                user_id,
                verification_score,
                is_verified,
                None if casualties is None else psycopg2.extras.Json(casualties),
                incident_date,
                incident_date,
                incident_date
            ))

            incidents_created += 1

        conn.commit()
        print(f"[SUCCESS] Created {incidents_created} sample incidents")
        print(f"   Date range: {start_date.date()} to {end_date.date()}")
        print(f"   Locations: {len(NIGERIAN_LOCATIONS)} cities across Nigeria")
        print(f"   Incident types: {len(INCIDENT_TYPES)} types")

        # Show summary statistics
        cur.execute("SELECT incident_type, COUNT(*) FROM incidents GROUP BY incident_type")
        print("\n[STATISTICS] Incidents by type:")
        for row in cur.fetchall():
            print(f"   {row[0]}: {row[1]}")

        cur.execute("SELECT severity, COUNT(*) FROM incidents GROUP BY severity")
        print("\n[STATISTICS] Incidents by severity:")
        for row in cur.fetchall():
            print(f"   {row[0]}: {row[1]}")

        cur.close()
        conn.close()
        return True

    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("Nigeria Security System - Sample Data Seeder")
    print("="*60)
    print("\nThis will create 50 sample security incidents across Nigeria")
    print("with realistic dates, locations, and severity levels.\n")

    seed_incidents(50)

    print("\n[INFO] You can now view the populated dashboard!")
    print("[INFO] Frontend: http://localhost:3000")
    print("="*60)
