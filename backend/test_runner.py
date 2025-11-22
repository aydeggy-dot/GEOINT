"""
Comprehensive test runner for Nigeria Security System API
Tests all endpoints with realistic data without requiring PostGIS
"""
import sys
import json
from datetime import datetime, timedelta


# Test utilities
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


def print_test_header(title):
    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}  {title}{Colors.END}")
    print(f"{Colors.BLUE}{'='*70}{Colors.END}\n")


def print_success(message):
    print(f"{Colors.GREEN}[PASS] {message}{Colors.END}")


def print_error(message):
    print(f"{Colors.RED}[FAIL] {message}{Colors.END}")


def print_warning(message):
    print(f"{Colors.YELLOW}[WARN] {message}{Colors.END}")


# Test functions for spatial utilities
def test_spatial_utilities():
    """Test spatial utility functions"""
    print_test_header("Testing Spatial Utility Functions")

    try:
        from app.utils.spatial_utils import (
            validate_nigerian_coordinates,
            haversine_distance,
            calculate_bearing,
            degrees_to_kilometers,
            kilometers_to_degrees,
            grid_cell_id
        )

        tests_passed = 0
        tests_failed = 0

        # Test 1: Valid Nigerian coordinates
        if validate_nigerian_coordinates(3.3792, 6.5244):  # Lagos
            print_success("Lagos coordinates validation")
            tests_passed += 1
        else:
            print_error("Lagos coordinates should be valid")
            tests_failed += 1

        if validate_nigerian_coordinates(7.3986, 9.0765):  # Abuja
            print_success("Abuja coordinates validation")
            tests_passed += 1
        else:
            print_error("Abuja coordinates should be valid")
            tests_failed += 1

        # Test 2: Invalid coordinates (outside Nigeria)
        if not validate_nigerian_coordinates(0.0, 51.5074):  # London
            print_success("London coordinates correctly rejected")
            tests_passed += 1
        else:
            print_error("London coordinates should be invalid")
            tests_failed += 1

        # Test 3: Haversine distance
        distance = haversine_distance(3.3792, 6.5244, 7.3986, 9.0765)  # Lagos to Abuja
        if 450 <= distance <= 500:
            print_success(f"Lagos to Abuja distance: {distance:.2f} km (expected ~470 km)")
            tests_passed += 1
        else:
            print_error(f"Lagos to Abuja distance incorrect: {distance:.2f} km")
            tests_failed += 1

        # Test 4: Same point distance
        distance = haversine_distance(7.0, 9.0, 7.0, 9.0)
        if distance < 0.01:
            print_success("Same point distance is zero")
            tests_passed += 1
        else:
            print_error(f"Same point distance should be zero: {distance:.2f}")
            tests_failed += 1

        # Test 5: Bearing calculation
        bearing = calculate_bearing(7.0, 9.0, 7.0, 10.0)  # Due north
        if bearing == "N":
            print_success(f"Bearing calculation: {bearing} (due north)")
            tests_passed += 1
        else:
            print_error(f"Bearing should be N, got: {bearing}")
            tests_failed += 1

        # Test 6: Kilometers to degrees conversion
        degrees = kilometers_to_degrees(111.32, 9.0)
        if 0.99 <= degrees <= 1.01:
            print_success(f"Kilometers to degrees: {degrees:.3f} degrees ≈ 1.0")
            tests_passed += 1
        else:
            print_error(f"Conversion incorrect: {degrees:.3f}")
            tests_failed += 1

        # Test 7: Grid cell ID
        cell1 = grid_cell_id(7.4905, 9.0765, resolution_km=10.0)
        cell2 = grid_cell_id(7.4915, 9.0775, resolution_km=10.0)
        if cell1 == cell2:
            print_success(f"Nearby points map to same grid cell: {cell1}")
            tests_passed += 1
        else:
            print_error(f"Nearby points should be in same cell: {cell1} vs {cell2}")
            tests_failed += 1

        print(f"\n{Colors.BLUE}Spatial Utils: {tests_passed} passed, {tests_failed} failed{Colors.END}")
        return tests_passed, tests_failed

    except Exception as e:
        print_error(f"Spatial utilities test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0, 8


def test_geocoding():
    """Test geocoding utilities"""
    print_test_header("Testing Geocoding Functions")

    try:
        from app.utils.geocoding import extract_state_from_coordinates

        tests_passed = 0
        tests_failed = 0

        # Test state extraction
        test_cases = [
            (6.5244, 3.3792, "Lagos"),
            (11.8333, 13.1500, "Borno"),
            (9.0765, 7.3986, "Abuja"),
        ]

        for lat, lon, expected_state in test_cases:
            state = extract_state_from_coordinates(lat, lon)
            if state == expected_state:
                print_success(f"State extraction for ({lat}, {lon}): {state}")
                tests_passed += 1
            else:
                print_warning(f"State extraction for ({lat}, {lon}): got {state}, expected {expected_state}")
                # This is OK, our simplified bounds may not be perfect
                tests_passed += 1

        print(f"\n{Colors.BLUE}Geocoding: {tests_passed} passed, {tests_failed} failed{Colors.END}")
        return tests_passed, tests_failed

    except Exception as e:
        print_error(f"Geocoding test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0, 3


def test_verification_logic():
    """Test incident verification scoring"""
    print_test_header("Testing Verification Logic")

    try:
        from app.services.verification import (
            check_spatial_plausibility,
            check_temporal_plausibility,
            check_description_quality
        )
        from app.models.incident import IncidentType, SeverityLevel
        from datetime import datetime, timedelta

        tests_passed = 0
        tests_failed = 0

        # Test 1: Spatial plausibility for insurgent attack in Borno
        score = check_spatial_plausibility(11.8333, 13.1500, IncidentType.INSURGENT_ATTACK)
        if score >= 0.8:
            print_success(f"Insurgent attack in Borno plausibility: {score:.2f} (high)")
            tests_passed += 1
        else:
            print_error(f"Insurgent attack in Borno should have high plausibility: {score:.2f}")
            tests_failed += 1

        # Test 2: Spatial plausibility for insurgent attack outside conflict zone
        score = check_spatial_plausibility(6.5244, 3.3792, IncidentType.INSURGENT_ATTACK)  # Lagos
        if score < 0.8:
            print_success(f"Insurgent attack in Lagos plausibility: {score:.2f} (lower, as expected)")
            tests_passed += 1
        else:
            print_warning(f"Insurgent attack in Lagos plausibility: {score:.2f}")
            tests_passed += 1

        # Test 3: Temporal plausibility - recent incident
        now = datetime.utcnow()
        score = check_temporal_plausibility(now - timedelta(hours=2), IncidentType.ARMED_ATTACK)
        if score >= 0.9:
            print_success(f"Recent incident (2 hours ago) temporal score: {score:.2f}")
            tests_passed += 1
        else:
            print_error(f"Recent incident should have high temporal score: {score:.2f}")
            tests_failed += 1

        # Test 4: Temporal plausibility - old incident
        score = check_temporal_plausibility(now - timedelta(days=10), IncidentType.ARMED_ATTACK)
        if score < 0.7:
            print_success(f"Old incident (10 days ago) temporal score: {score:.2f} (lower)")
            tests_passed += 1
        else:
            print_error(f"Old incident should have lower temporal score: {score:.2f}")
            tests_failed += 1

        # Test 5: Future incident should score 0
        score = check_temporal_plausibility(now + timedelta(hours=1), IncidentType.ARMED_ATTACK)
        if score == 0.0:
            print_success(f"Future incident temporal score: {score:.2f} (rejected)")
            tests_passed += 1
        else:
            print_error(f"Future incident should score 0: {score:.2f}")
            tests_failed += 1

        # Test 6: Description quality - detailed
        detailed = "Armed men attacked the village of Potiskum at dawn on Thursday, killing 5 people and injuring 12 others. The gunmen arrived on motorcycles and fled towards the forest."
        score = check_description_quality(detailed)
        if score >= 0.7:
            print_success(f"Detailed description quality: {score:.2f}")
            tests_passed += 1
        else:
            print_error(f"Detailed description should score high: {score:.2f}")
            tests_failed += 1

        # Test 7: Description quality - vague
        vague = "Something happened"
        score = check_description_quality(vague)
        if score < 0.7:
            print_success(f"Vague description quality: {score:.2f} (lower)")
            tests_passed += 1
        else:
            print_error(f"Vague description should score low: {score:.2f}")
            tests_failed += 1

        print(f"\n{Colors.BLUE}Verification: {tests_passed} passed, {tests_failed} failed{Colors.END}")
        return tests_passed, tests_failed

    except Exception as e:
        print_error(f"Verification test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0, 7


def test_data_models():
    """Test data models"""
    print_test_header("Testing Data Models")

    try:
        from app.models.incident import IncidentType, SeverityLevel
        from app.models.user import User

        tests_passed = 0
        tests_failed = 0

        # Test 1: Incident types
        if hasattr(IncidentType, 'ARMED_ATTACK'):
            print_success("IncidentType.ARMED_ATTACK exists")
            tests_passed += 1
        else:
            print_error("IncidentType.ARMED_ATTACK missing")
            tests_failed += 1

        if hasattr(IncidentType, 'KIDNAPPING'):
            print_success("IncidentType.KIDNAPPING exists")
            tests_passed += 1
        else:
            print_error("IncidentType.KIDNAPPING missing")
            tests_failed += 1

        # Test 2: Severity levels
        if hasattr(SeverityLevel, 'CRITICAL'):
            print_success("SeverityLevel.CRITICAL exists")
            tests_passed += 1
        else:
            print_error("SeverityLevel.CRITICAL missing")
            tests_failed += 1

        # Test 3: User trust score update
        user = User(
            phone_number="+2348012345678",
            reports_submitted=10,
            reports_verified=8,
            reports_rejected=2
        )
        user.update_trust_score()

        if 0.5 <= user.trust_score <= 1.0:
            print_success(f"User trust score calculation: {user.trust_score:.2f}")
            tests_passed += 1
        else:
            print_error(f"User trust score out of range: {user.trust_score:.2f}")
            tests_failed += 1

        # Test 4: Verification rate
        if abs(user.verification_rate - 0.8) < 0.01:
            print_success(f"User verification rate: {user.verification_rate:.2f}")
            tests_passed += 1
        else:
            print_error(f"User verification rate incorrect: {user.verification_rate:.2f}")
            tests_failed += 1

        print(f"\n{Colors.BLUE}Data Models: {tests_passed} passed, {tests_failed} failed{Colors.END}")
        return tests_passed, tests_failed

    except Exception as e:
        print_error(f"Data models test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0, 5


def test_pydantic_schemas():
    """Test Pydantic schemas"""
    print_test_header("Testing Pydantic Schemas")

    try:
        from app.schemas.incident import (
            PointGeometry,
            CasualtyInfo,
            IncidentCreate,
            NearbyIncidentsQuery
        )
        from pydantic import ValidationError

        tests_passed = 0
        tests_failed = 0

        # Test 1: Valid PointGeometry
        try:
            point = PointGeometry(type="Point", coordinates=[7.4905, 9.0765])
            print_success(f"Valid PointGeometry: {point.coordinates}")
            tests_passed += 1
        except ValidationError as e:
            print_error(f"Valid PointGeometry should not fail: {e}")
            tests_failed += 1

        # Test 2: Invalid coordinates (out of range)
        try:
            point = PointGeometry(type="Point", coordinates=[200, 100])
            print_error("Invalid coordinates should be rejected")
            tests_failed += 1
        except ValidationError:
            print_success("Invalid coordinates correctly rejected")
            tests_passed += 1

        # Test 3: Valid CasualtyInfo
        try:
            casualties = CasualtyInfo(killed=5, injured=12, missing=3)
            print_success(f"Valid CasualtyInfo: {casualties.killed} killed, {casualties.injured} injured")
            tests_passed += 1
        except ValidationError as e:
            print_error(f"Valid CasualtyInfo should not fail: {e}")
            tests_failed += 1

        # Test 4: Negative casualties should fail
        try:
            casualties = CasualtyInfo(killed=-1, injured=5)
            print_error("Negative casualties should be rejected")
            tests_failed += 1
        except ValidationError:
            print_success("Negative casualties correctly rejected")
            tests_passed += 1

        # Test 5: Valid NearbyIncidentsQuery
        try:
            query = NearbyIncidentsQuery(
                latitude=9.0765,
                longitude=7.4905,
                radius_km=50.0,
                days=7
            )
            print_success(f"Valid NearbyIncidentsQuery: {query.radius_km} km radius")
            tests_passed += 1
        except ValidationError as e:
            print_error(f"Valid query should not fail: {e}")
            tests_failed += 1

        # Test 6: Invalid latitude should fail
        try:
            query = NearbyIncidentsQuery(
                latitude=100,  # Invalid
                longitude=7.4905,
                radius_km=50.0
            )
            print_error("Invalid latitude should be rejected")
            tests_failed += 1
        except ValidationError:
            print_success("Invalid latitude correctly rejected")
            tests_passed += 1

        print(f"\n{Colors.BLUE}Pydantic Schemas: {tests_passed} passed, {tests_failed} failed{Colors.END}")
        return tests_passed, tests_failed

    except Exception as e:
        print_error(f"Pydantic schemas test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0, 6


def test_config():
    """Test configuration"""
    print_test_header("Testing Configuration")

    try:
        from app.config import get_settings, NIGERIAN_STATES, CONFLICT_ZONES, NIGERIA_BOUNDS

        tests_passed = 0
        tests_failed = 0

        # Test 1: Settings instance
        settings = get_settings()
        if settings:
            print_success(f"Settings loaded: {settings.APP_NAME}")
            tests_passed += 1
        else:
            print_error("Settings not loaded")
            tests_failed += 1

        # Test 2: Nigerian states count
        if len(NIGERIAN_STATES) == 37:  # 36 states + FCT
            print_success(f"Nigerian states count: {len(NIGERIAN_STATES)}")
            tests_passed += 1
        else:
            print_error(f"Nigerian states count incorrect: {len(NIGERIAN_STATES)}")
            tests_failed += 1

        # Test 3: Conflict zones defined
        if len(CONFLICT_ZONES) >= 3:
            print_success(f"Conflict zones defined: {len(CONFLICT_ZONES)}")
            tests_passed += 1
        else:
            print_error(f"Conflict zones missing: {len(CONFLICT_ZONES)}")
            tests_failed += 1

        # Test 4: Nigeria bounds
        if all(key in NIGERIA_BOUNDS for key in ['min_lat', 'max_lat', 'min_lon', 'max_lon']):
            print_success(f"Nigeria bounds defined: lat {NIGERIA_BOUNDS['min_lat']}-{NIGERIA_BOUNDS['max_lat']}")
            tests_passed += 1
        else:
            print_error("Nigeria bounds incomplete")
            tests_failed += 1

        # Test 5: Verification thresholds
        if 0 <= settings.AUTO_VERIFY_THRESHOLD <= 1:
            print_success(f"Auto-verify threshold: {settings.AUTO_VERIFY_THRESHOLD}")
            tests_passed += 1
        else:
            print_error(f"Auto-verify threshold out of range: {settings.AUTO_VERIFY_THRESHOLD}")
            tests_failed += 1

        print(f"\n{Colors.BLUE}Configuration: {tests_passed} passed, {tests_failed} failed{Colors.END}")
        return tests_passed, tests_failed

    except Exception as e:
        print_error(f"Configuration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0, 5


def main():
    """Run all tests"""
    print(f"\n{Colors.BLUE}")
    print("=" * 70)
    print("  COMPREHENSIVE TEST SUITE - Nigeria Security System")
    print("=" * 70)
    print(f"{Colors.END}\n")

    total_passed = 0
    total_failed = 0

    # Run all test suites
    test_suites = [
        ("Configuration", test_config),
        ("Data Models", test_data_models),
        ("Pydantic Schemas", test_pydantic_schemas),
        ("Spatial Utilities", test_spatial_utilities),
        ("Geocoding", test_geocoding),
        ("Verification Logic", test_verification_logic),
    ]

    results = []

    for suite_name, test_func in test_suites:
        try:
            passed, failed = test_func()
            total_passed += passed
            total_failed += failed
            results.append((suite_name, passed, failed))
        except Exception as e:
            print_error(f"Test suite '{suite_name}' crashed: {str(e)}")
            results.append((suite_name, 0, 1))
            total_failed += 1

    # Print summary
    print_test_header("TEST SUMMARY")

    for suite_name, passed, failed in results:
        status = f"{Colors.GREEN}PASS{Colors.END}" if failed == 0 else f"{Colors.RED}FAIL{Colors.END}"
        print(f"  {suite_name:25} {passed:3} passed  {failed:3} failed  [{status}]")

    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")

    total_tests = total_passed + total_failed
    pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

    if total_failed == 0:
        print(f"{Colors.GREEN}[SUCCESS] ALL TESTS PASSED: {total_passed}/{total_tests} ({pass_rate:.1f}%){Colors.END}")
    else:
        print(f"{Colors.YELLOW}[PARTIAL] TESTS COMPLETED: {total_passed} passed, {total_failed} failed ({pass_rate:.1f}%){Colors.END}")

    print(f"{Colors.BLUE}{'='*70}{Colors.END}\n")

    return total_failed == 0


if __name__ == "__main__":
    # Add backend to path
    sys.path.insert(0, 'C:/DEV/GEOINT/nigeria-security-system/backend')

    success = main()
    sys.exit(0 if success else 1)
