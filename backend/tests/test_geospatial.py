"""
Tests for geospatial utility functions
"""
import pytest
from app.utils.spatial_utils import (
    validate_nigerian_coordinates,
    haversine_distance,
    calculate_bearing,
    degrees_to_kilometers,
    kilometers_to_degrees,
    grid_cell_id
)
from app.utils.geocoding import extract_state_from_coordinates


class TestCoordinateValidation:
    """Tests for Nigerian coordinate validation"""

    def test_valid_nigerian_coordinates(self):
        """Test coordinates within Nigeria are valid"""
        # Lagos
        assert validate_nigerian_coordinates(3.3792, 6.5244) == True

        # Abuja
        assert validate_nigerian_coordinates(7.3986, 9.0765) == True

        # Maiduguri (Borno)
        assert validate_nigerian_coordinates(13.1500, 11.8333) == True

        # Calabar (Cross River)
        assert validate_nigerian_coordinates(8.3417, 4.9517) == True

    def test_invalid_coordinates_outside_nigeria(self):
        """Test coordinates outside Nigeria are invalid"""
        # London
        assert validate_nigerian_coordinates(0.0, 51.5074) == False

        # New York
        assert validate_nigerian_coordinates(-74.0060, 40.7128) == False

        # Tokyo
        assert validate_nigerian_coordinates(139.6917, 35.6895) == False

    def test_boundary_coordinates(self):
        """Test coordinates at Nigeria's boundaries"""
        # Just inside southern boundary
        assert validate_nigerian_coordinates(7.0, 4.1) == True

        # Just outside southern boundary
        assert validate_nigerian_coordinates(7.0, 3.9) == False

        # Just inside northern boundary
        assert validate_nigerian_coordinates(7.0, 13.9) == True

        # Just outside northern boundary
        assert validate_nigerian_coordinates(7.0, 14.1) == False


class TestDistanceCalculations:
    """Tests for distance calculation functions"""

    def test_haversine_distance_same_point(self):
        """Test distance between same point is zero"""
        distance = haversine_distance(7.4905, 9.0765, 7.4905, 9.0765)
        assert distance < 0.01  # Should be essentially zero

    def test_haversine_distance_lagos_to_abuja(self):
        """Test distance from Lagos to Abuja"""
        # Lagos: 3.3792, 6.5244
        # Abuja: 7.3986, 9.0765
        distance = haversine_distance(3.3792, 6.5244, 7.3986, 9.0765)

        # Actual distance is approximately 470 km
        assert 450 <= distance <= 500

    def test_haversine_distance_symmetry(self):
        """Test that distance is symmetric (A to B = B to A)"""
        dist1 = haversine_distance(3.3792, 6.5244, 7.3986, 9.0765)
        dist2 = haversine_distance(7.3986, 9.0765, 3.3792, 6.5244)

        assert abs(dist1 - dist2) < 0.001

    def test_haversine_short_distance(self):
        """Test short distance calculation accuracy"""
        # Two points about 10km apart
        lon1, lat1 = 7.4905, 9.0765
        lon2, lat2 = 7.4905, 9.17  # ~10km north

        distance = haversine_distance(lon1, lat1, lon2, lat2)

        assert 9 <= distance <= 11  # Should be approximately 10km


class TestBearingCalculation:
    """Tests for compass bearing calculations"""

    def test_bearing_due_north(self):
        """Test bearing when destination is due north"""
        bearing = calculate_bearing(7.0, 9.0, 7.0, 10.0)
        assert bearing == "N"

    def test_bearing_due_south(self):
        """Test bearing when destination is due south"""
        bearing = calculate_bearing(7.0, 10.0, 7.0, 9.0)
        assert bearing == "S"

    def test_bearing_due_east(self):
        """Test bearing when destination is due east"""
        bearing = calculate_bearing(7.0, 9.0, 8.0, 9.0)
        assert bearing == "E"

    def test_bearing_due_west(self):
        """Test bearing when destination is due west"""
        bearing = calculate_bearing(8.0, 9.0, 7.0, 9.0)
        assert bearing == "W"

    def test_bearing_northeast(self):
        """Test bearing when destination is northeast"""
        bearing = calculate_bearing(7.0, 9.0, 8.0, 10.0)
        assert bearing in ["NE", "N", "E"]  # Should be approximately NE


class TestUnitConversions:
    """Tests for unit conversion functions"""

    def test_degrees_to_kilometers_equator(self):
        """Test degree to km conversion at equator"""
        # At equator, 1 degree ≈ 111 km
        km = degrees_to_kilometers(1.0, 0.0)
        assert 110 <= km <= 112

    def test_kilometers_to_degrees(self):
        """Test km to degree conversion"""
        degrees = kilometers_to_degrees(111.32, 9.0)
        assert 0.99 <= degrees <= 1.01  # Should be approximately 1 degree

    def test_conversion_roundtrip(self):
        """Test that conversions are reversible"""
        original_km = 50.0
        degrees = kilometers_to_degrees(original_km, 9.0)
        back_to_km = degrees_to_kilometers(degrees, 9.0)

        assert abs(original_km - back_to_km) < 1.0  # Within 1km


class TestGridCellID:
    """Tests for spatial grid cell identification"""

    def test_grid_cell_same_point(self):
        """Test that nearby points map to same grid cell"""
        cell1 = grid_cell_id(7.4905, 9.0765, resolution_km=10.0)
        cell2 = grid_cell_id(7.4915, 9.0775, resolution_km=10.0)  # Very close

        # Should be in same grid cell
        assert cell1 == cell2

    def test_grid_cell_different_points(self):
        """Test that far apart points map to different grid cells"""
        cell1 = grid_cell_id(7.0, 9.0, resolution_km=10.0)
        cell2 = grid_cell_id(8.0, 10.0, resolution_km=10.0)  # Far apart

        assert cell1 != cell2

    def test_grid_cell_format(self):
        """Test grid cell ID format"""
        cell = grid_cell_id(7.4905, 9.0765, resolution_km=10.0)

        # Should be in format "lat_lon"
        assert "_" in cell
        parts = cell.split("_")
        assert len(parts) == 2

        # Should be parseable as floats
        lat = float(parts[0])
        lon = float(parts[1])
        assert isinstance(lat, float)
        assert isinstance(lon, float)

    def test_grid_cell_different_resolutions(self):
        """Test grid cells with different resolutions"""
        cell_10km = grid_cell_id(7.4905, 9.0765, resolution_km=10.0)
        cell_50km = grid_cell_id(7.4905, 9.0765, resolution_km=50.0)

        # Same point but different resolutions may produce different cells
        # depending on grid alignment
        assert isinstance(cell_10km, str)
        assert isinstance(cell_50km, str)


class TestStateExtraction:
    """Tests for state extraction from coordinates"""

    def test_extract_lagos_state(self):
        """Test extracting Lagos state from coordinates"""
        state = extract_state_from_coordinates(6.5244, 3.3792)
        assert state == "Lagos"

    def test_extract_borno_state(self):
        """Test extracting Borno state from coordinates"""
        state = extract_state_from_coordinates(11.8333, 13.1500)
        assert state == "Borno"

    def test_extract_abuja_state(self):
        """Test extracting FCT/Abuja from coordinates"""
        state = extract_state_from_coordinates(9.0765, 7.3986)
        assert state == "Abuja"

    def test_extract_unknown_state(self):
        """Test extracting state from unrecognized coordinates"""
        # Coordinates in Nigeria but not in our simplified state bounds
        state = extract_state_from_coordinates(7.0, 5.0)
        # Should return None or a valid state
        assert state is None or isinstance(state, str)


class TestEdgeCases:
    """Tests for edge cases and error handling"""

    def test_zero_coordinates(self):
        """Test handling of zero coordinates"""
        # (0, 0) is in the Atlantic Ocean, not Nigeria
        assert validate_nigerian_coordinates(0.0, 0.0) == False

    def test_negative_coordinates(self):
        """Test handling of negative coordinates"""
        # Western hemisphere - not Nigeria
        assert validate_nigerian_coordinates(-10.0, 10.0) == False

    def test_very_large_coordinates(self):
        """Test handling of very large coordinates"""
        assert validate_nigerian_coordinates(500.0, 500.0) == False

    def test_distance_to_self(self):
        """Test distance from point to itself"""
        distance = haversine_distance(7.0, 9.0, 7.0, 9.0)
        assert distance == 0.0

    def test_antipodal_points(self):
        """Test distance between nearly antipodal points"""
        # Points on opposite sides of Earth
        distance = haversine_distance(0.0, 0.0, 180.0, 0.0)

        # Should be approximately half Earth's circumference
        # Earth's circumference ≈ 40,075 km, so half ≈ 20,000 km
        assert 19000 <= distance <= 21000
