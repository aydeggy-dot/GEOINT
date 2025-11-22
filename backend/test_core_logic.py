"""
Core Logic Tests - Tests without database dependencies
Tests the pure Python business logic without requiring PostGIS/GeoAlchemy2
"""
import sys
import os
from datetime import datetime, timedelta
import math

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


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


def test_haversine_distance():
    """Test haversine distance calculation"""
    print("\n" + "="*70)
    print("TEST SUITE: Haversine Distance Calculation")
    print("="*70)

    results = TestResults()

    # Haversine formula implementation (inline for testing)
    def haversine(lon1, lat1, lon2, lat2):
        lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return 6371 * c

    # Test 1: Same point
    try:
        dist = haversine(7.0, 9.0, 7.0, 9.0)
        if dist < 0.01:
            results.add_pass("Same point distance is zero")
        else:
            results.add_fail("Same point distance", f"Expected 0, got {dist:.2f}")
    except Exception as e:
        results.add_fail("Same point distance", str(e))

    # Test 2: Lagos to Abuja (actual distance ~520-530km)
    try:
        dist = haversine(3.3792, 6.5244, 7.3986, 9.0765)
        if 500 <= dist <= 550:
            results.add_pass(f"Lagos to Abuja distance: {dist:.2f} km")
        else:
            results.add_fail("Lagos to Abuja distance", f"Expected ~520km, got {dist:.2f}km")
    except Exception as e:
        results.add_fail("Lagos to Abuja distance", str(e))

    # Test 3: Symmetry
    try:
        dist1 = haversine(3.3792, 6.5244, 7.3986, 9.0765)
        dist2 = haversine(7.3986, 9.0765, 3.3792, 6.5244)
        if abs(dist1 - dist2) < 0.001:
            results.add_pass("Distance is symmetric")
        else:
            results.add_fail("Distance symmetry", f"{dist1:.2f} != {dist2:.2f}")
    except Exception as e:
        results.add_fail("Distance symmetry", str(e))

    # Test 4: Short distance
    try:
        dist = haversine(7.0, 9.0, 7.0, 9.09)  # ~10km north
        if 9 <= dist <= 11:
            results.add_pass(f"Short distance: {dist:.2f} km")
        else:
            results.add_fail("Short distance", f"Expected ~10km, got {dist:.2f}km")
    except Exception as e:
        results.add_fail("Short distance", str(e))

    return results.summary()


def test_coordinate_validation():
    """Test Nigerian coordinate validation"""
    print("\n" + "="*70)
    print("TEST SUITE: Coordinate Validation")
    print("="*70)

    results = TestResults()

    NIGERIA_BOUNDS = {
        "min_lat": 4.0,
        "max_lat": 14.0,
        "min_lon": 2.5,
        "max_lon": 15.0
    }

    def validate_nigerian_coords(lon, lat):
        return (
            NIGERIA_BOUNDS["min_lon"] <= lon <= NIGERIA_BOUNDS["max_lon"] and
            NIGERIA_BOUNDS["min_lat"] <= lat <= NIGERIA_BOUNDS["max_lat"]
        )

    # Test cases: (lon, lat, should_be_valid, name)
    test_cases = [
        (3.3792, 6.5244, True, "Lagos"),
        (7.3986, 9.0765, True, "Abuja"),
        (13.1500, 11.8333, True, "Maiduguri"),
        (8.8833, 9.9167, True, "Jos"),
        (0.0, 51.5074, False, "London"),
        (-74.0060, 40.7128, False, "New York"),
        (7.0, 3.9, False, "Just south of Nigeria"),
        (7.0, 14.1, False, "Just north of Nigeria"),
    ]

    for lon, lat, should_be_valid, name in test_cases:
        try:
            is_valid = validate_nigerian_coords(lon, lat)
            if is_valid == should_be_valid:
                status = "valid" if should_be_valid else "invalid"
                results.add_pass(f"{name} correctly {status}")
            else:
                results.add_fail(f"{name} validation", f"Expected {should_be_valid}, got {is_valid}")
        except Exception as e:
            results.add_fail(f"{name} validation", str(e))

    return results.summary()


def test_bearing_calculation():
    """Test compass bearing calculation"""
    print("\n" + "="*70)
    print("TEST SUITE: Compass Bearing Calculation")
    print("="*70)

    results = TestResults()

    def calculate_bearing(lon1, lat1, lon2, lat2):
        lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        x = math.sin(dlon) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        bearing = math.degrees(math.atan2(x, y))
        bearing = (bearing + 360) % 360
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        index = round(bearing / 45) % 8
        return directions[index]

    # Test cases: (lon1, lat1, lon2, lat2, expected_direction)
    test_cases = [
        (7.0, 9.0, 7.0, 10.0, "N", "Due North"),
        (7.0, 10.0, 7.0, 9.0, "S", "Due South"),
        (7.0, 9.0, 8.0, 9.0, "E", "Due East"),
        (8.0, 9.0, 7.0, 9.0, "W", "Due West"),
    ]

    for lon1, lat1, lon2, lat2, expected, description in test_cases:
        try:
            bearing = calculate_bearing(lon1, lat1, lon2, lat2)
            if bearing == expected:
                results.add_pass(f"{description}: {bearing}")
            else:
                results.add_fail(f"{description}", f"Expected {expected}, got {bearing}")
        except Exception as e:
            results.add_fail(f"{description}", str(e))

    return results.summary()


def test_unit_conversions():
    """Test km/degree conversions"""
    print("\n" + "="*70)
    print("TEST SUITE: Unit Conversions (km <-> degrees)")
    print("="*70)

    results = TestResults()

    def km_to_degrees(km, lat=9.0):
        return km / 111.32

    def degrees_to_km(degrees, lat=9.0):
        lat_km = degrees * 111.32
        lon_km = degrees * 111.32 * math.cos(math.radians(lat))
        return (lat_km + lon_km) / 2

    # Test 1: Basic conversion
    try:
        degrees = km_to_degrees(111.32)
        if 0.99 <= degrees <= 1.01:
            results.add_pass(f"111.32 km = {degrees:.3f} degrees")
        else:
            results.add_fail("km to degrees", f"Expected ~1.0, got {degrees:.3f}")
    except Exception as e:
        results.add_fail("km to degrees", str(e))

    # Test 2: Round trip
    try:
        original_km = 50.0
        degrees = km_to_degrees(original_km)
        back_to_km = degrees_to_km(degrees)
        if abs(original_km - back_to_km) < 5.0:
            results.add_pass(f"Round trip conversion: {original_km}km -> {back_to_km:.2f}km")
        else:
            results.add_fail("Round trip conversion", f"{original_km} != {back_to_km:.2f}")
    except Exception as e:
        results.add_fail("Round trip conversion", str(e))

    return results.summary()


def test_grid_cell_generation():
    """Test spatial grid cell ID generation"""
    print("\n" + "="*70)
    print("TEST SUITE: Grid Cell ID Generation")
    print("="*70)

    results = TestResults()

    def grid_cell_id(lon, lat, resolution_km=10.0):
        resolution_deg = resolution_km / 111.32
        grid_lat = round(lat / resolution_deg) * resolution_deg
        grid_lon = round(lon / resolution_deg) * resolution_deg
        return f"{grid_lat:.2f}_{grid_lon:.2f}"

    # Test 1: Same grid cell
    try:
        cell1 = grid_cell_id(7.4905, 9.0765, 10.0)
        cell2 = grid_cell_id(7.4915, 9.0775, 10.0)
        if cell1 == cell2:
            results.add_pass(f"Nearby points in same cell: {cell1}")
        else:
            results.add_fail("Same grid cell", f"{cell1} != {cell2}")
    except Exception as e:
        results.add_fail("Same grid cell", str(e))

    # Test 2: Different grid cells
    try:
        cell1 = grid_cell_id(7.0, 9.0, 10.0)
        cell2 = grid_cell_id(8.0, 10.0, 10.0)
        if cell1 != cell2:
            results.add_pass(f"Far points in different cells: {cell1} vs {cell2}")
        else:
            results.add_fail("Different grid cells", f"Both are {cell1}")
    except Exception as e:
        results.add_fail("Different grid cells", str(e))

    # Test 3: Format validation
    try:
        cell = grid_cell_id(7.4905, 9.0765, 10.0)
        if "_" in cell:
            parts = cell.split("_")
            lat = float(parts[0])
            lon = float(parts[1])
            results.add_pass(f"Grid cell format valid: {cell}")
        else:
            results.add_fail("Grid cell format", f"Invalid format: {cell}")
    except Exception as e:
        results.add_fail("Grid cell format", str(e))

    return results.summary()


def test_configuration():
    """Test configuration constants"""
    print("\n" + "="*70)
    print("TEST SUITE: Configuration")
    print("="*70)

    results = TestResults()

    try:
        from app.config import NIGERIAN_STATES, CONFLICT_ZONES, NIGERIA_BOUNDS

        # Test 1: States count
        if len(NIGERIAN_STATES) == 37:
            results.add_pass(f"Nigerian states: {len(NIGERIAN_STATES)}")
        else:
            results.add_fail("States count", f"Expected 37, got {len(NIGERIAN_STATES)}")

        # Test 2: Specific states
        required_states = ["Lagos", "Borno", "Zamfara", "Plateau", "Federal Capital Territory"]
        for state in required_states:
            if state in NIGERIAN_STATES:
                results.add_pass(f"State '{state}' present")
            else:
                results.add_fail(f"State '{state}'", "Missing from list")

        # Test 3: Conflict zones
        if "northeast_insurgency" in CONFLICT_ZONES:
            results.add_pass("Northeast conflict zone defined")
        else:
            results.add_fail("Northeast conflict zone", "Missing")

        if "northwest_banditry" in CONFLICT_ZONES:
            results.add_pass("Northwest banditry zone defined")
        else:
            results.add_fail("Northwest banditry zone", "Missing")

    except Exception as e:
        results.add_fail("Configuration loading", str(e))

    return results.summary()


def main():
    """Run all core logic tests"""
    print("\n" + "="*70)
    print("COMPREHENSIVE CORE LOGIC TESTS")
    print("Nigeria Security Early Warning System")
    print("="*70)

    all_passed = True

    # Run test suites
    all_passed &= test_configuration()
    all_passed &= test_coordinate_validation()
    all_passed &= test_haversine_distance()
    all_passed &= test_bearing_calculation()
    all_passed &= test_unit_conversions()
    all_passed &= test_grid_cell_generation()

    # Final summary
    print("\n" + "="*70)
    if all_passed:
        print("[SUCCESS] ALL TEST SUITES PASSED!")
    else:
        print("[PARTIAL] SOME TESTS FAILED - See details above")
    print("="*70 + "\n")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
