"""
Database seeding script with sample incident data for testing
Run this to populate the database with realistic Nigerian security incidents
"""
import sys
import os
from datetime import datetime, timedelta
import random

# Add backend directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.database import SessionLocal, init_db, create_spatial_indexes
from app.models.incident import Incident, IncidentType, SeverityLevel
from app.models.user import User
from app.utils.spatial_utils import create_point_geometry


# Sample locations in Nigeria (major cities and conflict zones)
SAMPLE_LOCATIONS = [
    # Northeast (High insurgent activity)
    {"name": "Maiduguri, Borno", "lat": 11.8333, "lon": 13.1500, "state": "Borno"},
    {"name": "Damaturu, Yobe", "lat": 11.7500, "lon": 11.9667, "state": "Yobe"},
    {"name": "Yola, Adamawa", "lat": 9.2094, "lon": 12.4818, "state": "Adamawa"},
    {"name": "Monguno, Borno", "lat": 12.6667, "lon": 13.6167, "state": "Borno"},
    {"name": "Biu, Borno", "lat": 10.6136, "lon": 12.1944, "state": "Borno"},

    # Northwest (Banditry zones)
    {"name": "Gusau, Zamfara", "lat": 12.1704, "lon": 6.6642, "state": "Zamfara"},
    {"name": "Katsina, Katsina", "lat": 12.9908, "lon": 7.6008, "state": "Katsina"},
    {"name": "Sokoto, Sokoto", "lat": 13.0622, "lon": 5.2339, "state": "Sokoto"},
    {"name": "Kaduna, Kaduna", "lat": 10.5222, "lon": 7.4383, "state": "Kaduna"},
    {"name": "Birnin Gwari, Kaduna", "lat": 10.7500, "lon": 6.5000, "state": "Kaduna"},

    # Middle Belt (Farmer-herder conflicts)
    {"name": "Jos, Plateau", "lat": 9.9167, "lon": 8.8833, "state": "Plateau"},
    {"name": "Makurdi, Benue", "lat": 7.7333, "lon": 8.5333, "state": "Benue"},
    {"name": "Lafia, Nasarawa", "lat": 8.4833, "lon": 8.5167, "state": "Nasarawa"},
    {"name": "Wukari, Taraba", "lat": 7.8500, "lon": 9.7833, "state": "Taraba"},

    # Relatively peaceful areas (baseline)
    {"name": "Lagos, Lagos", "lat": 6.5244, "lon": 3.3792, "state": "Lagos"},
    {"name": "Abuja, FCT", "lat": 9.0765, "lon": 7.3986, "state": "Federal Capital Territory"},
    {"name": "Port Harcourt, Rivers", "lat": 4.8156, "lon": 7.0498, "state": "Rivers"},
    {"name": "Enugu, Enugu", "lat": 6.4411, "lon": 7.4919, "state": "Enugu"},
    {"name": "Ibadan, Oyo", "lat": 7.3775, "lon": 3.9470, "state": "Oyo"},
    {"name": "Kano, Kano", "lat": 12.0022, "lon": 8.5920, "state": "Kano"},
]

# Incident templates with realistic descriptions
INCIDENT_TEMPLATES = {
    IncidentType.INSURGENT_ATTACK: [
        "Suspected insurgents attacked {location} in the early hours, targeting military base",
        "Boko Haram fighters raided {location}, setting houses ablaze",
        "ISWAP militants ambushed security convoy near {location}",
        "Insurgents attacked {location}, residents fled to neighboring towns",
    ],
    IncidentType.ARMED_ATTACK: [
        "Armed men attacked {location}, killing {killed} and injuring {injured}",
        "Gunmen invaded {location} village at night, casualties reported",
        "Armed attackers targeted {location}, multiple casualties",
        "Heavily armed men stormed {location}, shooting sporadically",
    ],
    IncidentType.KIDNAPPING: [
        "Gunmen kidnapped {missing} people along {location} road",
        "Bandits abducted travelers near {location}",
        "{missing} students kidnapped from school in {location}",
        "Kidnappers struck at {location}, taking {missing} hostages",
    ],
    IncidentType.BANDITRY: [
        "Bandits attacked {location}, rustling cattle and looting homes",
        "Armed bandits invaded {location}, killing {killed} villagers",
        "Bandits on motorcycles raided {location}, shooting residents",
        "Village of {location} attacked by bandits, {injured} wounded",
    ],
    IncidentType.FARMER_HERDER_CLASH: [
        "Clashes between farmers and herders in {location} left {killed} dead",
        "Violent confrontation in {location} over grazing rights, {injured} injured",
        "Farmers and herders clashed in {location} over farmland destruction",
        "Deadly clash in {location} between farming and herding communities",
    ],
    IncidentType.CATTLE_RUSTLING: [
        "Cattle rustlers attacked {location}, stealing over 100 cows",
        "Armed rustlers raided {location}, making away with livestock",
        "Herders in {location} lost cattle to armed rustlers",
        "Cattle rustling incident in {location}, vigilantes in pursuit",
    ],
    IncidentType.BOMB_BLAST: [
        "IED explosion in {location} market, {killed} killed, {injured} injured",
        "Suicide bomber detonated explosives in {location}",
        "Bomb blast at {location} motor park, casualties evacuated",
        "Explosive device detonated in {location}, multiple casualties",
    ],
}

# Incident probabilities by region type
REGION_INCIDENT_WEIGHTS = {
    "northeast": {
        IncidentType.INSURGENT_ATTACK: 0.5,
        IncidentType.BOMB_BLAST: 0.2,
        IncidentType.ARMED_ATTACK: 0.2,
        IncidentType.KIDNAPPING: 0.1,
    },
    "northwest": {
        IncidentType.BANDITRY: 0.4,
        IncidentType.KIDNAPPING: 0.3,
        IncidentType.ARMED_ATTACK: 0.2,
        IncidentType.CATTLE_RUSTLING: 0.1,
    },
    "middle_belt": {
        IncidentType.FARMER_HERDER_CLASH: 0.5,
        IncidentType.ARMED_ATTACK: 0.3,
        IncidentType.KIDNAPPING: 0.2,
    },
    "peaceful": {
        IncidentType.ARMED_ATTACK: 0.4,
        IncidentType.KIDNAPPING: 0.3,
        IncidentType.ROBBERY: 0.3,
    }
}

def classify_region(state):
    """Classify state into region type for incident weighting"""
    northeast = ["Borno", "Yobe", "Adamawa"]
    northwest = ["Zamfara", "Katsina", "Sokoto", "Kaduna"]
    middle_belt = ["Plateau", "Benue", "Nasarawa", "Taraba"]

    if state in northeast:
        return "northeast"
    elif state in northwest:
        return "northwest"
    elif state in middle_belt:
        return "middle_belt"
    else:
        return "peaceful"


def generate_casualties(severity, incident_type):
    """Generate realistic casualty numbers based on severity and type"""
    if incident_type in [IncidentType.CATTLE_RUSTLING, IncidentType.ROBBERY]:
        # These typically have lower casualties
        casualty_ranges = {
            SeverityLevel.CRITICAL: (3, 8, 5, 15),
            SeverityLevel.HIGH: (1, 5, 2, 10),
            SeverityLevel.MODERATE: (0, 2, 1, 5),
            SeverityLevel.LOW: (0, 1, 0, 3),
        }
    else:
        casualty_ranges = {
            SeverityLevel.CRITICAL: (10, 30, 15, 50),
            SeverityLevel.HIGH: (3, 12, 5, 25),
            SeverityLevel.MODERATE: (1, 5, 2, 10),
            SeverityLevel.LOW: (0, 2, 0, 5),
        }

    min_killed, max_killed, min_injured, max_injured = casualty_ranges.get(
        severity, (0, 1, 0, 3)
    )

    killed = random.randint(min_killed, max_killed)
    injured = random.randint(min_injured, max_injured)
    missing = random.randint(0, 5) if incident_type == IncidentType.KIDNAPPING else 0

    return {"killed": killed, "injured": injured, "missing": missing}


def create_sample_users(db, num_users=20):
    """Create sample reporter users"""
    users = []
    for i in range(num_users):
        user = User(
            phone_number=f"+234{8000000000 + i}",
            trust_score=random.uniform(0.3, 0.9),
            reports_submitted=random.randint(0, 20),
            reports_verified=random.randint(0, 15),
            reports_rejected=random.randint(0, 5),
        )
        users.append(user)
        db.add(user)

    db.commit()
    print(f"Created {num_users} sample users")
    return users


def create_sample_incidents(db, num_incidents=500, days_back=90):
    """Create sample incidents across Nigeria"""
    users = db.query(User).all()

    if not users:
        users = create_sample_users(db)

    incidents = []
    now = datetime.utcnow()

    for i in range(num_incidents):
        # Select random location
        location = random.choice(SAMPLE_LOCATIONS)

        # Add small random offset to coordinates (within ~10km)
        lat = location["lat"] + random.uniform(-0.1, 0.1)
        lon = location["lon"] + random.uniform(-0.1, 0.1)

        # Determine region and select appropriate incident type
        region = classify_region(location["state"])
        incident_weights = REGION_INCIDENT_WEIGHTS[region]

        incident_type = random.choices(
            list(incident_weights.keys()),
            weights=list(incident_weights.values())
        )[0]

        # Assign severity (higher conflict zones more likely to have severe incidents)
        if region in ["northeast", "northwest"]:
            severity = random.choices(
                list(SeverityLevel),
                weights=[0.1, 0.2, 0.3, 0.4]  # More critical/high
            )[0]
        else:
            severity = random.choices(
                list(SeverityLevel),
                weights=[0.3, 0.3, 0.25, 0.15]  # More low/moderate
            )[0]

        # Generate casualties
        casualties = generate_casualties(severity, incident_type)

        # Create description
        if incident_type in INCIDENT_TEMPLATES:
            template = random.choice(INCIDENT_TEMPLATES[incident_type])
            description = template.format(
                location=location["name"],
                killed=casualties["killed"],
                injured=casualties["injured"],
                missing=casualties["missing"]
            )
        else:
            description = f"Security incident reported in {location['name']}"

        # Random timestamp within the last N days
        days_ago = random.uniform(0, days_back)
        timestamp = now - timedelta(days=days_ago)

        # Create geometry
        point_geometry = create_point_geometry(lon, lat)

        # Select random reporter
        reporter = random.choice(users)

        # Calculate simple verification score (random with bias toward reporter trust)
        base_score = reporter.trust_score
        verification_score = min(1.0, max(0.0, base_score + random.uniform(-0.2, 0.2)))
        verified = verification_score >= 0.75

        # Create incident
        incident = Incident(
            incident_type=incident_type,
            severity=severity,
            location=point_geometry,
            location_name=location["name"],
            state=location["state"],
            description=description,
            timestamp=timestamp,
            casualties=casualties,
            verified=verified,
            verification_score=verification_score,
            reporter_id=reporter.id,
            is_anonymous=random.choice([True, False]),
        )

        incidents.append(incident)
        db.add(incident)

        # Commit in batches
        if (i + 1) % 50 == 0:
            db.commit()
            print(f"Created {i + 1} incidents...")

    db.commit()
    print(f"\nTotal incidents created: {num_incidents}")

    # Print summary statistics
    print("\nIncidents by type:")
    for inc_type in IncidentType:
        count = sum(1 for inc in incidents if inc.incident_type == inc_type)
        if count > 0:
            print(f"  {inc_type.value}: {count}")

    print("\nIncidents by severity:")
    for sev in SeverityLevel:
        count = sum(1 for inc in incidents if inc.severity == sev)
        print(f"  {sev.value}: {count}")

    print("\nIncidents by state (top 10):")
    from collections import Counter
    state_counts = Counter(inc.state for inc in incidents)
    for state, count in state_counts.most_common(10):
        print(f"  {state}: {count}")

    total_killed = sum(inc.casualties.get("killed", 0) for inc in incidents)
    total_injured = sum(inc.casualties.get("injured", 0) for inc in incidents)
    total_missing = sum(inc.casualties.get("missing", 0) for inc in incidents)
    print(f"\nTotal casualties:")
    print(f"  Killed: {total_killed}")
    print(f"  Injured: {total_injured}")
    print(f"  Missing: {total_missing}")


def main():
    """Main seeding function"""
    print("Initializing database...")
    init_db()
    create_spatial_indexes()

    db = SessionLocal()

    try:
        print("\nCreating sample data...")
        create_sample_users(db, num_users=30)
        create_sample_incidents(db, num_incidents=500, days_back=90)

        print("\n✓ Database seeding completed successfully!")
        print("\nYou can now:")
        print("  1. Start the API: uvicorn app.main:app --reload")
        print("  2. View docs: http://localhost:8000/docs")
        print("  3. Query incidents: http://localhost:8000/api/v1/incidents/")

    except Exception as e:
        print(f"\n✗ Error during seeding: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
