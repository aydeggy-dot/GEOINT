"""
Quick Database Viewer for Nigeria Security System
View incidents, users, and statistics from the database
"""
import sys
import os

# Check if psycopg2 is installed
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("ERROR: psycopg2 not installed")
    print("\nPlease install it with:")
    print("  pip install psycopg2-binary")
    sys.exit(1)

# Database connection details
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "nigeria_security",
    "user": "postgres",
    "password": "postgres"
}


def print_header(title):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def connect_to_database():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✓ Connected to database successfully")
        return conn
    except psycopg2.OperationalError as e:
        print("✗ Could not connect to database")
        print(f"\nError: {e}")
        print("\nMake sure PostgreSQL is running:")
        print("  docker-compose up -d postgres")
        print("\nOr check if credentials are correct in docker-compose.yml")
        sys.exit(1)


def get_table_counts(cursor):
    """Get count of records in each table"""
    print_header("DATABASE OVERVIEW")

    tables = ['incidents', 'users', 'alerts', 'predictions']

    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"{table.capitalize():15} {count:>6} records")
        except Exception as e:
            print(f"{table.capitalize():15} Error: {e}")


def view_recent_incidents(cursor, limit=10):
    """View recent incidents"""
    print_header(f"RECENT {limit} INCIDENTS")

    cursor.execute("""
        SELECT
            incident_type,
            severity,
            location_name,
            state,
            verified,
            verification_score,
            timestamp,
            casualties
        FROM incidents
        ORDER BY timestamp DESC
        LIMIT %s
    """, (limit,))

    incidents = cursor.fetchall()

    if not incidents:
        print("No incidents found. Run the seeding script:")
        print("  python scripts/seed_database.py")
        return

    for inc in incidents:
        inc_type, severity, location, state, verified, score, timestamp, casualties = inc
        status = "✓" if verified else "✗"
        score_str = f"{score:.2f}" if score else "N/A"

        # Extract casualties
        killed = casualties.get('killed', 0) if casualties else 0
        injured = casualties.get('injured', 0) if casualties else 0

        print(f"{status} [{severity:8}] {inc_type:25} | {location:25} | {state:10} | Score: {score_str} | K:{killed} I:{injured} | {timestamp.strftime('%Y-%m-%d %H:%M')}")


def view_incidents_by_state(cursor):
    """View incidents grouped by state"""
    print_header("INCIDENTS BY STATE (Top 10)")

    cursor.execute("""
        SELECT state, COUNT(*) as count
        FROM incidents
        WHERE state IS NOT NULL
        GROUP BY state
        ORDER BY count DESC
        LIMIT 10
    """)

    states = cursor.fetchall()

    if not states:
        print("No incidents found")
        return

    max_count = max(s[1] for s in states)

    for state, count in states:
        # Create bar chart
        bar_length = int((count / max_count) * 40) if max_count > 0 else 0
        bar = "█" * bar_length
        print(f"{state:30} {count:4} {bar}")


def view_incidents_by_type(cursor):
    """View incidents grouped by type"""
    print_header("INCIDENTS BY TYPE")

    cursor.execute("""
        SELECT incident_type, COUNT(*) as count
        FROM incidents
        GROUP BY incident_type
        ORDER BY count DESC
    """)

    types = cursor.fetchall()

    if not types:
        print("No incidents found")
        return

    max_count = max(t[1] for t in types)

    for inc_type, count in types:
        bar_length = int((count / max_count) * 40) if max_count > 0 else 0
        bar = "█" * bar_length
        print(f"{inc_type:25} {count:4} {bar}")


def view_incidents_by_severity(cursor):
    """View incidents grouped by severity"""
    print_header("INCIDENTS BY SEVERITY")

    cursor.execute("""
        SELECT severity, COUNT(*) as count
        FROM incidents
        GROUP BY severity
        ORDER BY
            CASE severity
                WHEN 'critical' THEN 1
                WHEN 'high' THEN 2
                WHEN 'moderate' THEN 3
                WHEN 'low' THEN 4
            END
    """)

    severities = cursor.fetchall()

    if not severities:
        print("No incidents found")
        return

    max_count = max(s[1] for s in severities)

    for severity, count in severities:
        bar_length = int((count / max_count) * 40) if max_count > 0 else 0
        bar = "█" * bar_length
        print(f"{severity:10} {count:4} {bar}")


def view_casualty_statistics(cursor):
    """View total casualties"""
    print_header("CASUALTY STATISTICS")

    cursor.execute("""
        SELECT
            COUNT(*) as incident_count,
            SUM((casualties->>'killed')::int) as total_killed,
            SUM((casualties->>'injured')::int) as total_injured,
            SUM((casualties->>'missing')::int) as total_missing
        FROM incidents
        WHERE casualties IS NOT NULL
    """)

    result = cursor.fetchone()

    if result:
        incident_count, killed, injured, missing = result
        print(f"Incidents with casualties:  {incident_count or 0}")
        print(f"Total killed:               {killed or 0}")
        print(f"Total injured:              {injured or 0}")
        print(f"Total missing:              {missing or 0}")
        print(f"\nTotal affected:             {(killed or 0) + (injured or 0) + (missing or 0)}")


def view_verification_stats(cursor):
    """View verification statistics"""
    print_header("VERIFICATION STATISTICS")

    cursor.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE verified = true) as verified,
            COUNT(*) FILTER (WHERE verified = false) as unverified,
            AVG(verification_score) as avg_score
        FROM incidents
    """)

    result = cursor.fetchone()

    if result:
        total, verified, unverified, avg_score = result

        verified_pct = (verified / total * 100) if total > 0 else 0

        print(f"Total incidents:            {total}")
        print(f"Verified:                   {verified} ({verified_pct:.1f}%)")
        print(f"Unverified:                 {unverified} ({100-verified_pct:.1f}%)")
        print(f"Average verification score: {avg_score:.3f}" if avg_score else "N/A")


def view_top_reporters(cursor, limit=5):
    """View top reporters by trust score"""
    print_header(f"TOP {limit} REPORTERS")

    cursor.execute("""
        SELECT
            phone_number,
            trust_score,
            reports_submitted,
            reports_verified,
            reports_rejected
        FROM users
        WHERE reports_submitted > 0
        ORDER BY trust_score DESC
        LIMIT %s
    """, (limit,))

    reporters = cursor.fetchall()

    if not reporters:
        print("No reporters found")
        return

    for phone, trust, submitted, verified, rejected in reporters:
        verification_rate = (verified / submitted * 100) if submitted > 0 else 0
        print(f"{phone:20} | Trust: {trust:.2f} | Submitted: {submitted:3} | Verified: {verified:3} ({verification_rate:.0f}%) | Rejected: {rejected:2}")


def view_spatial_stats(cursor):
    """View spatial statistics"""
    print_header("SPATIAL STATISTICS")

    # Check PostGIS version
    cursor.execute("SELECT PostGIS_version()")
    postgis_version = cursor.fetchone()[0]
    print(f"PostGIS Version: {postgis_version}")

    # Spatial extent
    cursor.execute("""
        SELECT
            MIN(ST_Y(location)) as min_lat,
            MAX(ST_Y(location)) as max_lat,
            MIN(ST_X(location)) as min_lon,
            MAX(ST_X(location)) as max_lon
        FROM incidents
        WHERE location IS NOT NULL
    """)

    extent = cursor.fetchone()
    if extent and extent[0]:
        min_lat, max_lat, min_lon, max_lon = extent
        print(f"\nSpatial Extent:")
        print(f"  Latitude:  {min_lat:.4f}° to {max_lat:.4f}°")
        print(f"  Longitude: {min_lon:.4f}° to {max_lon:.4f}°")


def interactive_menu(conn):
    """Interactive menu"""
    cursor = conn.cursor()

    while True:
        print("\n" + "="*70)
        print("  NIGERIA SECURITY SYSTEM - DATABASE VIEWER")
        print("="*70)
        print("\n[1] Overview")
        print("[2] Recent Incidents")
        print("[3] Incidents by State")
        print("[4] Incidents by Type")
        print("[5] Incidents by Severity")
        print("[6] Casualty Statistics")
        print("[7] Verification Statistics")
        print("[8] Top Reporters")
        print("[9] Spatial Statistics")
        print("[0] Exit")

        choice = input("\nSelect option: ").strip()

        if choice == '1':
            get_table_counts(cursor)
        elif choice == '2':
            limit = input("How many incidents? (default 10): ").strip()
            limit = int(limit) if limit.isdigit() else 10
            view_recent_incidents(cursor, limit)
        elif choice == '3':
            view_incidents_by_state(cursor)
        elif choice == '4':
            view_incidents_by_type(cursor)
        elif choice == '5':
            view_incidents_by_severity(cursor)
        elif choice == '6':
            view_casualty_statistics(cursor)
        elif choice == '7':
            view_verification_stats(cursor)
        elif choice == '8':
            limit = input("How many reporters? (default 5): ").strip()
            limit = int(limit) if limit.isdigit() else 5
            view_top_reporters(cursor, limit)
        elif choice == '9':
            view_spatial_stats(cursor)
        elif choice == '0':
            print("\nGoodbye!")
            break
        else:
            print("\nInvalid option")

        input("\nPress Enter to continue...")

    cursor.close()


def main():
    """Main function"""
    print("\n" + "="*70)
    print("  NIGERIA SECURITY SYSTEM - DATABASE VIEWER")
    print("="*70)

    # Connect to database
    conn = connect_to_database()

    try:
        # Show quick overview
        cursor = conn.cursor()
        get_table_counts(cursor)
        view_recent_incidents(cursor, 5)
        view_incidents_by_state(cursor)
        cursor.close()

        # Ask if user wants interactive mode
        print("\n" + "="*70)
        response = input("\nEnter interactive mode? (y/n): ").strip().lower()

        if response == 'y':
            interactive_menu(conn)

    finally:
        conn.close()
        print("\n✓ Database connection closed")


if __name__ == "__main__":
    main()
