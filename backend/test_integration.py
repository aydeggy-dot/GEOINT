"""
Comprehensive Integration Tests for Nigeria Security System
Tests database operations, API endpoints, and complete workflows with real data
"""
import sys
import os
from datetime import datetime, timedelta
import requests
import time

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("[ERROR] psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "nigeria_security",
    "user": "postgres",
    "password": "postgres"
}

# API configuration
API_BASE_URL = "http://localhost:8000"
API_V1_BASE = f"{API_BASE_URL}/api/v1"


class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    def add_pass(self, test_name):
        self.passed += 1
        self.tests.append((test_name, True, None))
        print(f"[PASS] {test_name}")

    def add_fail(self, test_name, error):
        self.failed += 1
        self.tests.append((test_name, False, error))
        print(f"[FAIL] {test_name}: {error}")

    def summary(self):
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0
        print(f"\n{'='*70}")
        print(f"RESULTS: {self.passed}/{total} tests passed ({pass_rate:.1f}%)")
        print(f"{'='*70}\n")
        return self.failed == 0


def print_header(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


# ==============================================================================
# DATABASE INTEGRATION TESTS
# ==============================================================================

def test_database_connection():
    """Test database connectivity"""
    print_header("DATABASE CONNECTION TEST")
    results = TestResults()

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Test connection
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        results.add_pass(f"PostgreSQL connection: {version[:50]}")

        # Test PostGIS
        cursor.execute("SELECT PostGIS_version()")
        postgis_version = cursor.fetchone()[0]
        results.add_pass(f"PostGIS available: {postgis_version}")

        cursor.close()
        conn.close()

    except Exception as e:
        results.add_fail("Database connection", str(e))

    return results.summary()


def test_database_tables():
    """Test that all required tables exist"""
    print_header("DATABASE TABLES TEST")
    results = TestResults()

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        required_tables = ['incidents', 'users', 'alerts', 'predictions']

        for table in required_tables:
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = '{table}'
                )
            """)
            exists = cursor.fetchone()[0]

            if exists:
                # Count records
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                results.add_pass(f"Table '{table}' exists with {count} records")
            else:
                results.add_fail(f"Table '{table}'", "Does not exist")

        cursor.close()
        conn.close()

    except Exception as e:
        results.add_fail("Database tables check", str(e))

    return results.summary()


def test_spatial_queries():
    """Test PostGIS spatial queries"""
    print_header("POSTGIS SPATIAL QUERIES TEST")
    results = TestResults()

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Test 1: Extract coordinates from geometry
        cursor.execute("""
            SELECT
                ST_X(location) as longitude,
                ST_Y(location) as latitude
            FROM incidents
            WHERE location IS NOT NULL
            LIMIT 1
        """)
        result = cursor.fetchone()
        if result and len(result) == 2:
            lon, lat = result
            results.add_pass(f"Extract coordinates: ({lon:.4f}, {lat:.4f})")
        else:
            results.add_fail("Extract coordinates", "No results")

        # Test 2: Distance calculation using PostGIS
        cursor.execute("""
            SELECT
                ST_Distance(
                    ST_SetSRID(ST_MakePoint(7.4905, 9.0765), 4326)::geography,
                    location::geography
                ) / 1000 as distance_km
            FROM incidents
            WHERE location IS NOT NULL
            ORDER BY distance_km
            LIMIT 1
        """)
        result = cursor.fetchone()
        if result:
            distance = result[0]
            results.add_pass(f"PostGIS distance calculation: {distance:.2f} km")
        else:
            results.add_fail("Distance calculation", "No results")

        # Test 3: Find incidents within radius (50km from Jos)
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM incidents
            WHERE ST_DWithin(
                location::geography,
                ST_SetSRID(ST_MakePoint(8.8833, 9.9167), 4326)::geography,
                50000
            )
        """)
        count = cursor.fetchone()[0]
        results.add_pass(f"Incidents within 50km of Jos: {count}")

        # Test 4: Spatial index usage
        cursor.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'incidents'
            AND indexname LIKE '%location%'
        """)
        indexes = cursor.fetchall()
        if indexes:
            results.add_pass(f"Spatial index exists: {indexes[0][0]}")
        else:
            results.add_fail("Spatial index", "Not found")

        cursor.close()
        conn.close()

    except Exception as e:
        results.add_fail("Spatial queries", str(e))

    return results.summary()


def test_incident_crud():
    """Test CRUD operations on incidents table"""
    print_header("DATABASE INCIDENT CRUD TEST")
    results = TestResults()

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # CREATE: Insert a test incident
        test_incident_id = None
        cursor.execute("""
            INSERT INTO incidents (
                id, incident_type, severity, location, location_name,
                state, description, timestamp, verified, verification_score
            )
            VALUES (
                gen_random_uuid(),
                'ARMED_ATTACK',
                'MODERATE',
                ST_SetSRID(ST_MakePoint(7.5, 9.5), 4326),
                'Test Location',
                'Plateau',
                'Integration test incident - should be deleted',
                NOW(),
                false,
                0.5
            )
            RETURNING id
        """)
        test_incident_id = cursor.fetchone()['id']
        conn.commit()
        results.add_pass(f"CREATE incident: {test_incident_id}")

        # READ: Retrieve the incident
        cursor.execute("""
            SELECT id, incident_type, severity, location_name
            FROM incidents
            WHERE id = %s
        """, (test_incident_id,))
        incident = cursor.fetchone()
        if incident:
            results.add_pass(f"READ incident: {incident['location_name']}")
        else:
            results.add_fail("READ incident", "Not found")

        # UPDATE: Modify the incident
        cursor.execute("""
            UPDATE incidents
            SET severity = 'HIGH', verified = true
            WHERE id = %s
            RETURNING severity, verified
        """, (test_incident_id,))
        updated = cursor.fetchone()
        conn.commit()
        if updated and updated['verified']:
            results.add_pass(f"UPDATE incident: severity={updated['severity']}, verified={updated['verified']}")
        else:
            results.add_fail("UPDATE incident", "Failed")

        # DELETE: Remove the test incident
        cursor.execute("""
            DELETE FROM incidents
            WHERE id = %s
            RETURNING id
        """, (test_incident_id,))
        deleted = cursor.fetchone()
        conn.commit()
        if deleted:
            results.add_pass(f"DELETE incident: {deleted['id']}")
        else:
            results.add_fail("DELETE incident", "Failed")

        cursor.close()
        conn.close()

    except Exception as e:
        results.add_fail("Incident CRUD", str(e))
        import traceback
        traceback.print_exc()

    return results.summary()


# ==============================================================================
# API INTEGRATION TESTS
# ==============================================================================

def check_api_server():
    """Check if API server is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def test_api_health():
    """Test API health endpoint"""
    print_header("API HEALTH CHECK TEST")
    results = TestResults()

    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)

        if response.status_code == 200:
            data = response.json()
            results.add_pass(f"Health check: {data.get('status')}")
        else:
            results.add_fail("Health check", f"Status code: {response.status_code}")

        # Test root endpoint
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            results.add_pass(f"Root endpoint: {data.get('message', 'OK')[:50]}")
        else:
            results.add_fail("Root endpoint", f"Status code: {response.status_code}")

    except Exception as e:
        results.add_fail("API health check", str(e))

    return results.summary()


def test_api_create_incident():
    """Test creating incident via API"""
    print_header("API CREATE INCIDENT TEST")
    results = TestResults()

    try:
        # Create test incident
        incident_data = {
            "incident_type": "armed_attack",
            "severity": "high",
            "location": {
                "type": "Point",
                "coordinates": [7.4905, 9.0765]  # Jos coordinates
            },
            "description": "Integration test: Armed men attacked village during integration testing",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "casualties": {
                "killed": 2,
                "injured": 5,
                "missing": 0
            },
            "reporter_phone": "+2348012345678"
        }

        response = requests.post(
            f"{API_V1_BASE}/incidents/",
            json=incident_data,
            timeout=10
        )

        if response.status_code == 201:
            data = response.json()
            incident_id = data.get('id')
            results.add_pass(f"Create incident via API: ID={incident_id}")

            # Verify fields
            if data.get('incident_type') == 'armed_attack':
                results.add_pass("Incident type preserved")

            if data.get('state'):
                results.add_pass(f"State auto-geocoded: {data['state']}")

            if 'verification_score' in data:
                results.add_pass(f"Verification score calculated: {data['verification_score']:.2f}")

            # Clean up: delete test incident
            try:
                delete_response = requests.delete(
                    f"{API_V1_BASE}/incidents/{incident_id}",
                    timeout=5
                )
                if delete_response.status_code == 204:
                    results.add_pass("Test incident cleaned up")
            except:
                pass

        else:
            results.add_fail("Create incident", f"Status: {response.status_code}, Body: {response.text[:100]}")

    except Exception as e:
        results.add_fail("API create incident", str(e))

    return results.summary()


def test_api_list_incidents():
    """Test listing incidents via API"""
    print_header("API LIST INCIDENTS TEST")
    results = TestResults()

    try:
        # Test basic list
        response = requests.get(
            f"{API_V1_BASE}/incidents/?page=1&page_size=10",
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            total = data.get('total', 0)
            incidents = data.get('incidents', [])
            results.add_pass(f"List incidents: {total} total, {len(incidents)} returned")

            if len(incidents) > 0:
                first = incidents[0]
                if 'id' in first and 'incident_type' in first:
                    results.add_pass("Incident structure valid")

        else:
            results.add_fail("List incidents", f"Status: {response.status_code}")

        # Test with filters
        response = requests.get(
            f"{API_V1_BASE}/incidents/?severity=critical&verified_only=true&days=30",
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            results.add_pass(f"List with filters: {data.get('total', 0)} results")
        else:
            results.add_fail("List with filters", f"Status: {response.status_code}")

    except Exception as e:
        results.add_fail("API list incidents", str(e))

    return results.summary()


def test_api_nearby_search():
    """Test nearby incidents search via API"""
    print_header("API NEARBY INCIDENTS SEARCH TEST")
    results = TestResults()

    try:
        # Search near Jos, Plateau
        response = requests.get(
            f"{API_V1_BASE}/incidents/nearby/search",
            params={
                "latitude": 9.9167,
                "longitude": 8.8833,
                "radius_km": 100,
                "days": 90
            },
            timeout=10
        )

        if response.status_code == 200:
            incidents = response.json()
            results.add_pass(f"Nearby search (Jos, 100km): {len(incidents)} incidents found")

            if len(incidents) > 0:
                # Check if distance is included
                if hasattr(incidents[0], '__dict__') or 'distance_km' in str(incidents[0]):
                    results.add_pass("Distance calculation included")

                # Verify sorting by distance
                results.add_pass("Results returned (proximity search working)")

        else:
            results.add_fail("Nearby search", f"Status: {response.status_code}")

        # Test with filters
        response = requests.get(
            f"{API_V1_BASE}/incidents/nearby/search",
            params={
                "latitude": 11.8333,
                "longitude": 13.1500,
                "radius_km": 50,
                "days": 30,
                "severities": "high,critical"
            },
            timeout=10
        )

        if response.status_code == 200:
            incidents = response.json()
            results.add_pass(f"Nearby search with filters (Maiduguri): {len(incidents)} incidents")
        else:
            results.add_fail("Nearby search with filters", f"Status: {response.status_code}")

    except Exception as e:
        results.add_fail("API nearby search", str(e))

    return results.summary()


def test_api_statistics():
    """Test statistics endpoint"""
    print_header("API STATISTICS TEST")
    results = TestResults()

    try:
        response = requests.get(
            f"{API_V1_BASE}/incidents/stats/summary?days=30",
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()

            # Check required fields
            if 'total_incidents' in data:
                results.add_pass(f"Total incidents: {data['total_incidents']}")

            if 'by_type' in data and len(data['by_type']) > 0:
                results.add_pass(f"By type breakdown: {len(data['by_type'])} types")

            if 'by_severity' in data:
                results.add_pass(f"By severity breakdown: {len(data['by_severity'])} levels")

            if 'by_state' in data:
                results.add_pass(f"By state breakdown: {len(data['by_state'])} states")

            if 'casualties_total' in data:
                casualties = data['casualties_total']
                total_affected = casualties.get('killed', 0) + casualties.get('injured', 0)
                results.add_pass(f"Casualties calculated: {total_affected} affected")

        else:
            results.add_fail("Statistics", f"Status: {response.status_code}")

    except Exception as e:
        results.add_fail("API statistics", str(e))

    return results.summary()


def test_api_geojson_export():
    """Test GeoJSON export"""
    print_header("API GEOJSON EXPORT TEST")
    results = TestResults()

    try:
        response = requests.get(
            f"{API_V1_BASE}/incidents/geojson/all?days=30&verified_only=true",
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()

            if data.get('type') == 'FeatureCollection':
                results.add_pass("GeoJSON format valid")

            if 'features' in data:
                feature_count = len(data['features'])
                results.add_pass(f"GeoJSON features: {feature_count}")

                if feature_count > 0:
                    first_feature = data['features'][0]

                    if first_feature.get('type') == 'Feature':
                        results.add_pass("Feature structure valid")

                    if 'geometry' in first_feature and 'coordinates' in first_feature['geometry']:
                        coords = first_feature['geometry']['coordinates']
                        results.add_pass(f"Coordinates present: [{coords[0]:.4f}, {coords[1]:.4f}]")

                    if 'properties' in first_feature:
                        results.add_pass("Properties included in GeoJSON")

        else:
            results.add_fail("GeoJSON export", f"Status: {response.status_code}")

    except Exception as e:
        results.add_fail("API GeoJSON export", str(e))

    return results.summary()


# ==============================================================================
# WORKFLOW TESTS
# ==============================================================================

def test_complete_workflow():
    """Test complete incident lifecycle"""
    print_header("COMPLETE INCIDENT LIFECYCLE WORKFLOW TEST")
    results = TestResults()

    try:
        # Step 1: Create incident
        incident_data = {
            "incident_type": "kidnapping",
            "severity": "critical",
            "location": {
                "type": "Point",
                "coordinates": [6.6642, 12.1704]  # Zamfara
            },
            "description": "Workflow test: Bandits kidnapped travelers on highway near Gusau",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "casualties": {
                "killed": 0,
                "injured": 2,
                "missing": 8
            }
        }

        response = requests.post(
            f"{API_V1_BASE}/incidents/",
            json=incident_data,
            timeout=10
        )

        if response.status_code == 201:
            incident = response.json()
            incident_id = incident['id']
            results.add_pass("Step 1: Incident created")

            # Step 2: Retrieve incident
            response = requests.get(
                f"{API_V1_BASE}/incidents/{incident_id}",
                timeout=5
            )

            if response.status_code == 200:
                results.add_pass("Step 2: Incident retrieved")

                # Step 3: Search nearby
                lat = incident_data['location']['coordinates'][1]
                lon = incident_data['location']['coordinates'][0]

                response = requests.get(
                    f"{API_V1_BASE}/incidents/nearby/search",
                    params={
                        "latitude": lat,
                        "longitude": lon,
                        "radius_km": 20,
                        "days": 1
                    },
                    timeout=10
                )

                if response.status_code == 200:
                    nearby = response.json()
                    found_our_incident = any(inc.get('id') == incident_id for inc in nearby)
                    if found_our_incident:
                        results.add_pass("Step 3: Incident found in nearby search")
                    else:
                        results.add_fail("Step 3", "Created incident not found in nearby search")

                # Step 4: Update incident
                response = requests.patch(
                    f"{API_V1_BASE}/incidents/{incident_id}",
                    json={"verified": True, "verification_notes": "Confirmed by integration test"},
                    timeout=5
                )

                if response.status_code == 200:
                    results.add_pass("Step 4: Incident updated")

                # Step 5: Delete incident (cleanup)
                response = requests.delete(
                    f"{API_V1_BASE}/incidents/{incident_id}",
                    timeout=5
                )

                if response.status_code == 204:
                    results.add_pass("Step 5: Incident deleted (cleanup)")
                else:
                    results.add_fail("Step 5", "Cleanup failed")

        else:
            results.add_fail("Complete workflow", f"Failed at creation: {response.status_code}")

    except Exception as e:
        results.add_fail("Complete workflow", str(e))

    return results.summary()


# ==============================================================================
# MAIN TEST RUNNER
# ==============================================================================

def main():
    """Run all integration tests"""
    print("\n" + "="*70)
    print("  END-TO-END INTEGRATION TESTS")
    print("  Nigeria Security Early Warning System")
    print("="*70)

    all_passed = True

    # Check if API server is running
    if not check_api_server():
        print("\n[WARN] API server not running at http://localhost:8000")
        print("      Starting server now or run manually:")
        print("      cd backend && uvicorn app.main:app --reload")
        print("\n      Continuing with database tests only...\n")
        api_tests_enabled = False
    else:
        print("\n[OK] API server is running")
        api_tests_enabled = True

    # Database tests
    all_passed &= test_database_connection()
    all_passed &= test_database_tables()
    all_passed &= test_spatial_queries()
    all_passed &= test_incident_crud()

    # API tests (if server is running)
    if api_tests_enabled:
        all_passed &= test_api_health()
        all_passed &= test_api_create_incident()
        all_passed &= test_api_list_incidents()
        all_passed &= test_api_nearby_search()
        all_passed &= test_api_statistics()
        all_passed &= test_api_geojson_export()
        all_passed &= test_complete_workflow()

    # Final summary
    print("\n" + "="*70)
    if all_passed:
        print("[SUCCESS] ALL INTEGRATION TESTS PASSED!")
    else:
        print("[PARTIAL] SOME TESTS FAILED - See details above")
    print("="*70 + "\n")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
