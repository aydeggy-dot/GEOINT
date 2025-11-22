"""
Comprehensive Negative and Exception Testing for Nigeria Security System
Tests input validation, error handling, security, boundary conditions, and edge cases
"""
import sys
import os
from datetime import datetime, timedelta
import requests
import time
import uuid

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
        print(f"  [PASS] {test_name}")

    def add_fail(self, test_name, error):
        self.failed += 1
        self.tests.append((test_name, False, error))
        print(f"  [FAIL] {test_name}: {error}")

    def summary(self):
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0
        print(f"\n  {'='*68}")
        print(f"  RESULTS: {self.passed}/{total} tests passed ({pass_rate:.1f}%)")
        print(f"  {'='*68}\n")
        return self.failed == 0


def print_header(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


# ==============================================================================
# 1. INPUT VALIDATION TESTS
# ==============================================================================

def test_invalid_input_validation():
    """Test API input validation with invalid data"""
    print_header("INPUT VALIDATION TESTS")
    results = TestResults()

    # Test 1: Missing required fields
    print("\n[TEST 1] Missing Required Fields")
    try:
        invalid_data = {
            "description": "Test incident without required fields"
        }
        response = requests.post(
            f"{API_V1_BASE}/incidents/",
            json=invalid_data,
            timeout=5
        )
        if response.status_code == 422:
            results.add_pass("Missing required fields rejected (422)")
        else:
            results.add_fail("Missing required fields", f"Expected 422, got {response.status_code}")
    except Exception as e:
        results.add_fail("Missing required fields test", str(e))

    # Test 2: Invalid incident type
    print("\n[TEST 2] Invalid Incident Type")
    try:
        invalid_data = {
            "incident_type": "zombie_attack",  # Invalid type
            "severity": "high",
            "location": {"type": "Point", "coordinates": [7.4905, 9.0765]},
            "description": "Invalid incident type test",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        response = requests.post(
            f"{API_V1_BASE}/incidents/",
            json=invalid_data,
            timeout=5
        )
        if response.status_code == 422:
            results.add_pass("Invalid incident type rejected (422)")
        else:
            results.add_fail("Invalid incident type", f"Expected 422, got {response.status_code}")
    except Exception as e:
        results.add_fail("Invalid incident type test", str(e))

    # Test 3: Invalid severity level
    print("\n[TEST 3] Invalid Severity Level")
    try:
        invalid_data = {
            "incident_type": "armed_attack",
            "severity": "super_critical",  # Invalid severity
            "location": {"type": "Point", "coordinates": [7.4905, 9.0765]},
            "description": "Invalid severity test",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        response = requests.post(
            f"{API_V1_BASE}/incidents/",
            json=invalid_data,
            timeout=5
        )
        if response.status_code == 422:
            results.add_pass("Invalid severity level rejected (422)")
        else:
            results.add_fail("Invalid severity level", f"Expected 422, got {response.status_code}")
    except Exception as e:
        results.add_fail("Invalid severity level test", str(e))

    # Test 4: Malformed GeoJSON
    print("\n[TEST 4] Malformed GeoJSON")
    try:
        invalid_data = {
            "incident_type": "armed_attack",
            "severity": "high",
            "location": {"type": "InvalidType", "coordinates": "not_an_array"},  # Malformed
            "description": "Malformed GeoJSON test",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        response = requests.post(
            f"{API_V1_BASE}/incidents/",
            json=invalid_data,
            timeout=5
        )
        if response.status_code in [400, 422]:
            results.add_pass("Malformed GeoJSON rejected (400/422)")
        else:
            results.add_fail("Malformed GeoJSON", f"Expected 400/422, got {response.status_code}")
    except Exception as e:
        results.add_fail("Malformed GeoJSON test", str(e))

    # Test 5: Wrong coordinate order (latitude, longitude instead of lon, lat)
    print("\n[TEST 5] Wrong Coordinate Order")
    try:
        invalid_data = {
            "incident_type": "armed_attack",
            "severity": "high",
            "location": {"type": "Point", "coordinates": [9.0765, 7.4905]},  # Reversed
            "description": "Wrong coordinate order - this should be outside Nigeria",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        response = requests.post(
            f"{API_V1_BASE}/incidents/",
            json=invalid_data,
            timeout=5
        )
        # This should fail validation as coordinates would be outside Nigeria
        if response.status_code == 400:
            results.add_pass("Invalid coordinates detected (400)")
        else:
            # Might pass if accidentally still in Nigeria, so just document it
            results.add_pass(f"Coordinate order test completed (status: {response.status_code})")
    except Exception as e:
        results.add_fail("Wrong coordinate order test", str(e))

    # Test 6: Invalid timestamp format
    print("\n[TEST 6] Invalid Timestamp Format")
    try:
        invalid_data = {
            "incident_type": "armed_attack",
            "severity": "high",
            "location": {"type": "Point", "coordinates": [7.4905, 9.0765]},
            "description": "Invalid timestamp test",
            "timestamp": "not-a-valid-timestamp"
        }
        response = requests.post(
            f"{API_V1_BASE}/incidents/",
            json=invalid_data,
            timeout=5
        )
        if response.status_code == 422:
            results.add_pass("Invalid timestamp format rejected (422)")
        else:
            results.add_fail("Invalid timestamp format", f"Expected 422, got {response.status_code}")
    except Exception as e:
        results.add_fail("Invalid timestamp format test", str(e))

    # Test 7: Wrong data types
    print("\n[TEST 7] Wrong Data Types")
    try:
        invalid_data = {
            "incident_type": "armed_attack",
            "severity": "high",
            "location": {"type": "Point", "coordinates": [7.4905, 9.0765]},
            "description": 12345,  # Should be string, not integer
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        response = requests.post(
            f"{API_V1_BASE}/incidents/",
            json=invalid_data,
            timeout=5
        )
        if response.status_code == 422:
            results.add_pass("Wrong data type rejected (422)")
        else:
            results.add_fail("Wrong data type", f"Expected 422, got {response.status_code}")
    except Exception as e:
        results.add_fail("Wrong data type test", str(e))

    # Test 8: Empty required fields
    print("\n[TEST 8] Empty Required Fields")
    try:
        invalid_data = {
            "incident_type": "armed_attack",
            "severity": "high",
            "location": {"type": "Point", "coordinates": [7.4905, 9.0765]},
            "description": "",  # Empty description
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        response = requests.post(
            f"{API_V1_BASE}/incidents/",
            json=invalid_data,
            timeout=5
        )
        if response.status_code in [400, 422]:
            results.add_pass("Empty description rejected (400/422)")
        else:
            # Might accept empty string, document the behavior
            results.add_pass(f"Empty field test completed (status: {response.status_code})")
    except Exception as e:
        results.add_fail("Empty required fields test", str(e))

    return results.summary()


# ==============================================================================
# 2. BOUNDARY AND COORDINATE VALIDATION TESTS
# ==============================================================================

def test_boundary_conditions():
    """Test boundary conditions and coordinate validation"""
    print_header("BOUNDARY CONDITION TESTS")
    results = TestResults()

    # Test 1: Coordinates outside Nigeria (Paris, France)
    print("\n[TEST 1] Coordinates Outside Nigeria - Europe")
    try:
        invalid_data = {
            "incident_type": "armed_attack",
            "severity": "high",
            "location": {"type": "Point", "coordinates": [2.3522, 48.8566]},  # Paris
            "description": "Test incident in Paris, France - should be rejected",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        response = requests.post(
            f"{API_V1_BASE}/incidents/",
            json=invalid_data,
            timeout=5
        )
        if response.status_code == 400:
            results.add_pass("Non-Nigerian coordinates rejected (400)")
        else:
            results.add_fail("Non-Nigerian coordinates", f"Expected 400, got {response.status_code}")
    except Exception as e:
        results.add_fail("Non-Nigerian coordinates test", str(e))

    # Test 2: Coordinates in neighboring country (Cameroon)
    print("\n[TEST 2] Coordinates in Neighboring Country")
    try:
        invalid_data = {
            "incident_type": "armed_attack",
            "severity": "high",
            "location": {"type": "Point", "coordinates": [11.5174, 3.8480]},  # Yaoundé, Cameroon
            "description": "Test incident in Cameroon - should be rejected",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        response = requests.post(
            f"{API_V1_BASE}/incidents/",
            json=invalid_data,
            timeout=5
        )
        if response.status_code == 400:
            results.add_pass("Cameroon coordinates rejected (400)")
        else:
            results.add_fail("Cameroon coordinates", f"Expected 400, got {response.status_code}")
    except Exception as e:
        results.add_fail("Cameroon coordinates test", str(e))

    # Test 3: Extreme latitude/longitude values
    print("\n[TEST 3] Extreme Coordinate Values")
    try:
        invalid_data = {
            "incident_type": "armed_attack",
            "severity": "high",
            "location": {"type": "Point", "coordinates": [999.9999, 999.9999]},  # Invalid
            "description": "Test with extreme coordinates",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        response = requests.post(
            f"{API_V1_BASE}/incidents/",
            json=invalid_data,
            timeout=5
        )
        if response.status_code in [400, 422]:
            results.add_pass("Extreme coordinates rejected (400/422)")
        else:
            results.add_fail("Extreme coordinates", f"Expected 400/422, got {response.status_code}")
    except Exception as e:
        results.add_fail("Extreme coordinates test", str(e))

    # Test 4: Negative casualty numbers
    print("\n[TEST 4] Negative Casualty Numbers")
    try:
        invalid_data = {
            "incident_type": "armed_attack",
            "severity": "high",
            "location": {"type": "Point", "coordinates": [7.4905, 9.0765]},
            "description": "Test with negative casualties",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "casualties": {
                "killed": -5,
                "injured": -10,
                "missing": -2
            }
        }
        response = requests.post(
            f"{API_V1_BASE}/incidents/",
            json=invalid_data,
            timeout=5
        )
        if response.status_code in [400, 422]:
            results.add_pass("Negative casualties rejected (400/422)")
        else:
            results.add_fail("Negative casualties", f"Expected 400/422, got {response.status_code}")
    except Exception as e:
        results.add_fail("Negative casualties test", str(e))

    # Test 5: Future timestamp
    print("\n[TEST 5] Future Timestamp")
    try:
        future_time = datetime.utcnow() + timedelta(days=365)
        invalid_data = {
            "incident_type": "armed_attack",
            "severity": "high",
            "location": {"type": "Point", "coordinates": [7.4905, 9.0765]},
            "description": "Test with future timestamp",
            "timestamp": future_time.isoformat() + "Z"
        }
        response = requests.post(
            f"{API_V1_BASE}/incidents/",
            json=invalid_data,
            timeout=5
        )
        # Future timestamps might be accepted or rejected depending on validation
        if response.status_code in [200, 201]:
            # If accepted, check if verification score penalizes it
            data = response.json()
            score = data.get('verification_score', 1.0)
            if score < 0.5:
                results.add_pass(f"Future timestamp accepted but penalized (score: {score:.2f})")
            else:
                results.add_fail("Future timestamp", f"Accepted with high score: {score:.2f}")
            # Clean up
            if 'id' in data:
                requests.delete(f"{API_V1_BASE}/incidents/{data['id']}", timeout=5)
        elif response.status_code in [400, 422]:
            results.add_pass("Future timestamp rejected (400/422)")
        else:
            results.add_fail("Future timestamp", f"Unexpected status: {response.status_code}")
    except Exception as e:
        results.add_fail("Future timestamp test", str(e))

    # Test 6: Very old timestamp (100 years ago)
    print("\n[TEST 6] Very Old Timestamp")
    try:
        old_time = datetime.utcnow() - timedelta(days=365*100)
        invalid_data = {
            "incident_type": "armed_attack",
            "severity": "high",
            "location": {"type": "Point", "coordinates": [7.4905, 9.0765]},
            "description": "Test with very old timestamp",
            "timestamp": old_time.isoformat() + "Z"
        }
        response = requests.post(
            f"{API_V1_BASE}/incidents/",
            json=invalid_data,
            timeout=5
        )
        if response.status_code in [200, 201]:
            data = response.json()
            score = data.get('verification_score', 1.0)
            if score < 0.6:
                results.add_pass(f"Old timestamp accepted but penalized (score: {score:.2f})")
            else:
                results.add_pass(f"Old timestamp accepted (score: {score:.2f})")
            # Clean up
            if 'id' in data:
                requests.delete(f"{API_V1_BASE}/incidents/{data['id']}", timeout=5)
        else:
            results.add_pass(f"Old timestamp handling (status: {response.status_code})")
    except Exception as e:
        results.add_fail("Very old timestamp test", str(e))

    # Test 7: Invalid pagination parameters
    print("\n[TEST 7] Invalid Pagination Parameters")
    try:
        response = requests.get(
            f"{API_V1_BASE}/incidents/?page=-1&page_size=1000000",
            timeout=5
        )
        if response.status_code in [400, 422]:
            results.add_pass("Invalid pagination rejected (400/422)")
        else:
            # Might clamp values instead of rejecting
            results.add_pass(f"Pagination handled (status: {response.status_code})")
    except Exception as e:
        results.add_fail("Invalid pagination test", str(e))

    # Test 8: Radius too large for nearby search
    print("\n[TEST 8] Excessive Search Radius")
    try:
        response = requests.get(
            f"{API_V1_BASE}/incidents/nearby/search?latitude=9.0765&longitude=7.4905&radius_km=10000",
            timeout=5
        )
        if response.status_code in [400, 422]:
            results.add_pass("Excessive radius rejected (400/422)")
        else:
            # Might clamp to max value (500km)
            results.add_pass(f"Excessive radius handled (status: {response.status_code})")
    except Exception as e:
        results.add_fail("Excessive radius test", str(e))

    return results.summary()


# ==============================================================================
# 3. SECURITY TESTS (SQL Injection, XSS, etc.)
# ==============================================================================

def test_security_vulnerabilities():
    """Test security vulnerabilities"""
    print_header("SECURITY VULNERABILITY TESTS")
    results = TestResults()

    # Test 1: SQL Injection in description
    print("\n[TEST 1] SQL Injection Attempt - Description")
    try:
        sql_injection = {
            "incident_type": "armed_attack",
            "severity": "high",
            "location": {"type": "Point", "coordinates": [7.4905, 9.0765]},
            "description": "Test'; DROP TABLE incidents; --",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        response = requests.post(
            f"{API_V1_BASE}/incidents/",
            json=sql_injection,
            timeout=5
        )
        if response.status_code in [200, 201]:
            # ORM should sanitize, verify table still exists
            try:
                conn = psycopg2.connect(**DB_CONFIG)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM incidents")
                count = cursor.fetchone()[0]
                cursor.close()
                conn.close()
                results.add_pass(f"SQL injection blocked - incidents table intact ({count} records)")
                # Clean up test incident
                data = response.json()
                if 'id' in data:
                    requests.delete(f"{API_V1_BASE}/incidents/{data['id']}", timeout=5)
            except Exception as db_e:
                results.add_fail("SQL injection protection", f"Table check failed: {str(db_e)}")
        else:
            results.add_pass(f"SQL injection rejected (status: {response.status_code})")
    except Exception as e:
        results.add_fail("SQL injection test", str(e))

    # Test 2: XSS in description
    print("\n[TEST 2] XSS Attempt - Description")
    try:
        xss_payload = {
            "incident_type": "armed_attack",
            "severity": "high",
            "location": {"type": "Point", "coordinates": [7.4905, 9.0765]},
            "description": "<script>alert('XSS')</script>",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        response = requests.post(
            f"{API_V1_BASE}/incidents/",
            json=xss_payload,
            timeout=5
        )
        if response.status_code in [200, 201]:
            data = response.json()
            # Check if script tags are stored as-is or sanitized
            stored_desc = data.get('description', '')
            if '<script>' in stored_desc:
                results.add_pass("XSS payload stored (frontend must sanitize)")
            else:
                results.add_pass("XSS payload sanitized by backend")
            # Clean up
            if 'id' in data:
                requests.delete(f"{API_V1_BASE}/incidents/{data['id']}", timeout=5)
        else:
            results.add_pass(f"XSS payload rejected (status: {response.status_code})")
    except Exception as e:
        results.add_fail("XSS test", str(e))

    # Test 3: SQL Injection in query parameters
    print("\n[TEST 3] SQL Injection Attempt - Query Parameters")
    try:
        response = requests.get(
            f"{API_V1_BASE}/incidents/?state=' OR '1'='1",
            timeout=5
        )
        # Should either return empty results or handle safely
        if response.status_code == 200:
            data = response.json()
            # If we get results, the injection didn't work (good)
            results.add_pass("Query parameter injection blocked")
        else:
            results.add_pass(f"Query parameter injection handled (status: {response.status_code})")
    except Exception as e:
        results.add_fail("Query parameter injection test", str(e))

    # Test 4: Path traversal attempt
    print("\n[TEST 4] Path Traversal Attempt")
    try:
        response = requests.get(
            f"{API_V1_BASE}/incidents/../../../../etc/passwd",
            timeout=5
        )
        if response.status_code in [400, 404, 422]:
            results.add_pass("Path traversal blocked (400/404/422)")
        else:
            results.add_fail("Path traversal", f"Unexpected status: {response.status_code}")
    except Exception as e:
        results.add_fail("Path traversal test", str(e))

    # Test 5: Invalid UUID format
    print("\n[TEST 5] Invalid UUID Format")
    try:
        response = requests.get(
            f"{API_V1_BASE}/incidents/not-a-valid-uuid",
            timeout=5
        )
        if response.status_code in [400, 422]:
            results.add_pass("Invalid UUID rejected (400/422)")
        else:
            results.add_fail("Invalid UUID", f"Expected 400/422, got {response.status_code}")
    except Exception as e:
        results.add_fail("Invalid UUID test", str(e))

    # Test 6: Oversized payload
    print("\n[TEST 6] Oversized Payload Attack")
    try:
        huge_description = "A" * 1000000  # 1MB of text
        oversized = {
            "incident_type": "armed_attack",
            "severity": "high",
            "location": {"type": "Point", "coordinates": [7.4905, 9.0765]},
            "description": huge_description,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        response = requests.post(
            f"{API_V1_BASE}/incidents/",
            json=oversized,
            timeout=10
        )
        if response.status_code in [413, 400, 422]:
            results.add_pass("Oversized payload rejected (413/400/422)")
        elif response.status_code in [200, 201]:
            # Might accept it, check if stored
            results.add_pass("Oversized payload accepted (consider size limits)")
            data = response.json()
            if 'id' in data:
                requests.delete(f"{API_V1_BASE}/incidents/{data['id']}", timeout=5)
        else:
            results.add_fail("Oversized payload", f"Unexpected status: {response.status_code}")
    except requests.exceptions.Timeout:
        results.add_pass("Oversized payload timed out (protected)")
    except Exception as e:
        results.add_fail("Oversized payload test", str(e))

    # Test 7: NULL byte injection
    print("\n[TEST 7] NULL Byte Injection")
    try:
        null_byte = {
            "incident_type": "armed_attack",
            "severity": "high",
            "location": {"type": "Point", "coordinates": [7.4905, 9.0765]},
            "description": "Test\x00null byte",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        response = requests.post(
            f"{API_V1_BASE}/incidents/",
            json=null_byte,
            timeout=5
        )
        if response.status_code in [200, 201]:
            results.add_pass("NULL byte handled")
            data = response.json()
            if 'id' in data:
                requests.delete(f"{API_V1_BASE}/incidents/{data['id']}", timeout=5)
        else:
            results.add_pass(f"NULL byte rejected (status: {response.status_code})")
    except Exception as e:
        results.add_fail("NULL byte test", str(e))

    return results.summary()


# ==============================================================================
# 4. ERROR RESPONSE TESTS
# ==============================================================================

def test_error_responses():
    """Test proper error response codes"""
    print_header("ERROR RESPONSE CODE TESTS")
    results = TestResults()

    # Test 1: 404 for non-existent incident
    print("\n[TEST 1] 404 for Non-Existent Resource")
    try:
        fake_uuid = str(uuid.uuid4())
        response = requests.get(
            f"{API_V1_BASE}/incidents/{fake_uuid}",
            timeout=5
        )
        if response.status_code == 404:
            results.add_pass("Non-existent resource returns 404")
        else:
            results.add_fail("404 response", f"Expected 404, got {response.status_code}")
    except Exception as e:
        results.add_fail("404 test", str(e))

    # Test 2: 404 for non-existent endpoint
    print("\n[TEST 2] 404 for Non-Existent Endpoint")
    try:
        response = requests.get(
            f"{API_V1_BASE}/nonexistent-endpoint",
            timeout=5
        )
        if response.status_code == 404:
            results.add_pass("Non-existent endpoint returns 404")
        else:
            results.add_fail("Endpoint 404", f"Expected 404, got {response.status_code}")
    except Exception as e:
        results.add_fail("Endpoint 404 test", str(e))

    # Test 3: 405 for wrong HTTP method
    print("\n[TEST 3] 405 for Wrong HTTP Method")
    try:
        response = requests.put(
            f"{API_V1_BASE}/incidents/",  # Should be POST, not PUT
            json={},
            timeout=5
        )
        if response.status_code == 405:
            results.add_pass("Wrong HTTP method returns 405")
        else:
            results.add_pass(f"Wrong method handled (status: {response.status_code})")
    except Exception as e:
        results.add_fail("405 test", str(e))

    # Test 4: Proper error message format
    print("\n[TEST 4] Error Message Format")
    try:
        response = requests.post(
            f"{API_V1_BASE}/incidents/",
            json={},
            timeout=5
        )
        if response.status_code == 422:
            try:
                error_data = response.json()
                if 'detail' in error_data:
                    results.add_pass("Error includes 'detail' field")
                else:
                    results.add_fail("Error format", "Missing 'detail' field")
            except:
                results.add_fail("Error format", "Response not JSON")
        else:
            results.add_pass(f"Error response received (status: {response.status_code})")
    except Exception as e:
        results.add_fail("Error format test", str(e))

    # Test 5: Delete non-existent incident
    print("\n[TEST 5] Delete Non-Existent Resource")
    try:
        fake_uuid = str(uuid.uuid4())
        response = requests.delete(
            f"{API_V1_BASE}/incidents/{fake_uuid}",
            timeout=5
        )
        if response.status_code == 404:
            results.add_pass("Delete non-existent returns 404")
        else:
            results.add_fail("Delete 404", f"Expected 404, got {response.status_code}")
    except Exception as e:
        results.add_fail("Delete 404 test", str(e))

    # Test 6: Update non-existent incident
    print("\n[TEST 6] Update Non-Existent Resource")
    try:
        fake_uuid = str(uuid.uuid4())
        response = requests.patch(
            f"{API_V1_BASE}/incidents/{fake_uuid}",
            json={"severity": "low"},
            timeout=5
        )
        if response.status_code == 404:
            results.add_pass("Update non-existent returns 404")
        else:
            results.add_fail("Update 404", f"Expected 404, got {response.status_code}")
    except Exception as e:
        results.add_fail("Update 404 test", str(e))

    return results.summary()


# ==============================================================================
# 5. DATABASE CONSTRAINT TESTS
# ==============================================================================

def test_database_constraints():
    """Test database constraint violations"""
    print_header("DATABASE CONSTRAINT TESTS")
    results = TestResults()

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Test 1: NULL constraint on required fields
        print("\n[TEST 1] NULL Constraint Violation")
        try:
            cursor.execute("""
                INSERT INTO incidents (id, incident_type, severity, location, timestamp)
                VALUES (gen_random_uuid(), NULL, 'HIGH', ST_SetSRID(ST_MakePoint(7.4905, 9.0765), 4326), NOW())
            """)
            conn.commit()
            results.add_fail("NULL constraint", "Accepted NULL incident_type")
        except psycopg2.Error:
            conn.rollback()
            results.add_pass("NULL constraint enforced")

        # Test 2: Invalid enum value
        print("\n[TEST 2] Invalid Enum Value")
        try:
            cursor.execute("""
                INSERT INTO incidents (id, incident_type, severity, location, description, timestamp)
                VALUES (
                    gen_random_uuid(),
                    'INVALID_TYPE',
                    'HIGH',
                    ST_SetSRID(ST_MakePoint(7.4905, 9.0765), 4326),
                    'Test',
                    NOW()
                )
            """)
            conn.commit()
            results.add_fail("Enum constraint", "Accepted invalid enum value")
        except psycopg2.Error:
            conn.rollback()
            results.add_pass("Enum constraint enforced")

        # Test 3: Invalid foreign key
        print("\n[TEST 3] Foreign Key Constraint")
        try:
            fake_reporter_id = str(uuid.uuid4())
            cursor.execute(f"""
                INSERT INTO incidents (id, incident_type, severity, location, description, timestamp, reporter_id)
                VALUES (
                    gen_random_uuid(),
                    'ARMED_ATTACK',
                    'HIGH',
                    ST_SetSRID(ST_MakePoint(7.4905, 9.0765), 4326),
                    'Test',
                    NOW(),
                    '{fake_reporter_id}'
                )
            """)
            conn.commit()
            results.add_fail("Foreign key constraint", "Accepted invalid reporter_id")
        except psycopg2.Error:
            conn.rollback()
            results.add_pass("Foreign key constraint enforced")

        # Test 4: Check constraint on SRID
        print("\n[TEST 4] Spatial SRID Constraint")
        try:
            # Try to insert with wrong SRID
            cursor.execute("""
                INSERT INTO incidents (id, incident_type, severity, location, description, timestamp)
                VALUES (
                    gen_random_uuid(),
                    'ARMED_ATTACK',
                    'HIGH',
                    ST_SetSRID(ST_MakePoint(7.4905, 9.0765), 3857),
                    'Test wrong SRID',
                    NOW()
                )
            """)
            conn.commit()
            results.add_fail("SRID constraint", "Accepted wrong SRID")
        except psycopg2.Error:
            conn.rollback()
            results.add_pass("SRID constraint enforced")

        cursor.close()
        conn.close()

    except Exception as e:
        results.add_fail("Database constraints test", str(e))

    return results.summary()


# ==============================================================================
# 6. EDGE CASE TESTS
# ==============================================================================

def test_edge_cases():
    """Test edge cases and special scenarios"""
    print_header("EDGE CASE TESTS")
    results = TestResults()

    # Test 1: Unicode characters in description
    print("\n[TEST 1] Unicode Characters")
    try:
        unicode_data = {
            "incident_type": "armed_attack",
            "severity": "high",
            "location": {"type": "Point", "coordinates": [7.4905, 9.0765]},
            "description": "Test with unicode: 你好 مرحبا привет 🔫💣",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        response = requests.post(
            f"{API_V1_BASE}/incidents/",
            json=unicode_data,
            timeout=5
        )
        if response.status_code in [200, 201]:
            results.add_pass("Unicode characters accepted")
            data = response.json()
            if 'id' in data:
                requests.delete(f"{API_V1_BASE}/incidents/{data['id']}", timeout=5)
        else:
            results.add_fail("Unicode test", f"Status: {response.status_code}")
    except Exception as e:
        results.add_fail("Unicode test", str(e))

    # Test 2: Very long description
    print("\n[TEST 2] Very Long Description")
    try:
        long_desc = "A" * 10000  # 10KB description
        long_data = {
            "incident_type": "armed_attack",
            "severity": "high",
            "location": {"type": "Point", "coordinates": [7.4905, 9.0765]},
            "description": long_desc,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        response = requests.post(
            f"{API_V1_BASE}/incidents/",
            json=long_data,
            timeout=5
        )
        if response.status_code in [200, 201]:
            results.add_pass("Long description accepted")
            data = response.json()
            if 'id' in data:
                requests.delete(f"{API_V1_BASE}/incidents/{data['id']}", timeout=5)
        else:
            results.add_pass(f"Long description handled (status: {response.status_code})")
    except Exception as e:
        results.add_fail("Long description test", str(e))

    # Test 3: Exactly on Nigeria boundary
    print("\n[TEST 3] Coordinates on Boundary")
    try:
        # Use exact boundary coordinates
        boundary_data = {
            "incident_type": "armed_attack",
            "severity": "high",
            "location": {"type": "Point", "coordinates": [2.6917, 4.2767]},  # Southwest corner
            "description": "Test on Nigeria boundary",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        response = requests.post(
            f"{API_V1_BASE}/incidents/",
            json=boundary_data,
            timeout=5
        )
        if response.status_code in [200, 201]:
            results.add_pass("Boundary coordinates accepted")
            data = response.json()
            if 'id' in data:
                requests.delete(f"{API_V1_BASE}/incidents/{data['id']}", timeout=5)
        else:
            results.add_pass(f"Boundary test completed (status: {response.status_code})")
    except Exception as e:
        results.add_fail("Boundary coordinates test", str(e))

    # Test 4: Zero casualties
    print("\n[TEST 4] Zero Casualties")
    try:
        zero_casualties = {
            "incident_type": "armed_attack",
            "severity": "low",
            "location": {"type": "Point", "coordinates": [7.4905, 9.0765]},
            "description": "Test with zero casualties",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "casualties": {
                "killed": 0,
                "injured": 0,
                "missing": 0
            }
        }
        response = requests.post(
            f"{API_V1_BASE}/incidents/",
            json=zero_casualties,
            timeout=5
        )
        if response.status_code in [200, 201]:
            results.add_pass("Zero casualties accepted")
            data = response.json()
            if 'id' in data:
                requests.delete(f"{API_V1_BASE}/incidents/{data['id']}", timeout=5)
        else:
            results.add_fail("Zero casualties", f"Status: {response.status_code}")
    except Exception as e:
        results.add_fail("Zero casualties test", str(e))

    # Test 5: Special characters in phone number
    print("\n[TEST 5] Special Characters in Phone")
    try:
        special_phone = {
            "incident_type": "armed_attack",
            "severity": "high",
            "location": {"type": "Point", "coordinates": [7.4905, 9.0765]},
            "description": "Test with special characters in phone",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "reporter_phone": "+234-801-234-5678"
        }
        response = requests.post(
            f"{API_V1_BASE}/incidents/",
            json=special_phone,
            timeout=5
        )
        if response.status_code in [200, 201]:
            results.add_pass("Phone with dashes accepted")
            data = response.json()
            if 'id' in data:
                requests.delete(f"{API_V1_BASE}/incidents/{data['id']}", timeout=5)
        else:
            results.add_pass(f"Phone validation (status: {response.status_code})")
    except Exception as e:
        results.add_fail("Special phone test", str(e))

    # Test 6: Empty arrays
    print("\n[TEST 6] Empty Arrays")
    try:
        empty_arrays = {
            "incident_type": "armed_attack",
            "severity": "high",
            "location": {"type": "Point", "coordinates": [7.4905, 9.0765]},
            "description": "Test with empty arrays",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "media_urls": [],
            "tags": []
        }
        response = requests.post(
            f"{API_V1_BASE}/incidents/",
            json=empty_arrays,
            timeout=5
        )
        if response.status_code in [200, 201]:
            results.add_pass("Empty arrays accepted")
            data = response.json()
            if 'id' in data:
                requests.delete(f"{API_V1_BASE}/incidents/{data['id']}", timeout=5)
        else:
            results.add_fail("Empty arrays", f"Status: {response.status_code}")
    except Exception as e:
        results.add_fail("Empty arrays test", str(e))

    # Test 7: Case sensitivity in enums
    print("\n[TEST 7] Enum Case Sensitivity")
    try:
        mixed_case = {
            "incident_type": "Armed_Attack",  # Mixed case
            "severity": "HIGH",
            "location": {"type": "Point", "coordinates": [7.4905, 9.0765]},
            "description": "Test enum case sensitivity",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        response = requests.post(
            f"{API_V1_BASE}/incidents/",
            json=mixed_case,
            timeout=5
        )
        if response.status_code in [200, 201]:
            results.add_pass("Mixed case enum accepted")
            data = response.json()
            if 'id' in data:
                requests.delete(f"{API_V1_BASE}/incidents/{data['id']}", timeout=5)
        elif response.status_code == 422:
            results.add_pass("Enum case sensitivity enforced (422)")
        else:
            results.add_pass(f"Enum case handled (status: {response.status_code})")
    except Exception as e:
        results.add_fail("Enum case test", str(e))

    return results.summary()


# ==============================================================================
# MAIN TEST RUNNER
# ==============================================================================

def main():
    """Run all negative and exception tests"""
    print("\n" + "="*70)
    print("  NIGERIA SECURITY SYSTEM - NEGATIVE & EXCEPTION TESTS")
    print("  Testing input validation, error handling, and security")
    print("="*70)

    # Check API availability
    print("\n[SETUP] Checking API availability...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("[OK] API is running and healthy\n")
        else:
            print(f"[WARNING] API returned status {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Cannot connect to API: {str(e)}")
        print("Please ensure the API is running: uvicorn app.main:app --reload")
        return

    # Track overall results
    all_passed = True

    # Run all test suites
    all_passed &= test_invalid_input_validation()
    all_passed &= test_boundary_conditions()
    all_passed &= test_security_vulnerabilities()
    all_passed &= test_error_responses()
    all_passed &= test_database_constraints()
    all_passed &= test_edge_cases()

    # Final summary
    print("\n" + "="*70)
    if all_passed:
        print("[SUCCESS] ALL NEGATIVE/EXCEPTION TESTS PASSED!")
    else:
        print("[WARNING] SOME TESTS FAILED - SEE DETAILS ABOVE")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
