"""
Tests for incident API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.incident import IncidentType, SeverityLevel

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop after"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestIncidentCreation:
    """Tests for creating incidents"""

    def test_create_valid_incident(self):
        """Test creating a valid incident report"""
        incident_data = {
            "incident_type": "armed_attack",
            "severity": "high",
            "location": {
                "type": "Point",
                "coordinates": [7.4905, 9.0765]  # Jos, Plateau
            },
            "description": "Armed men attacked village at dawn, multiple casualties reported",
            "timestamp": datetime.utcnow().isoformat(),
            "casualties": {
                "killed": 5,
                "injured": 12,
                "missing": 0
            },
            "reporter_phone": "+2348012345678",
            "is_anonymous": False
        }

        response = client.post("/api/v1/incidents/", json=incident_data)

        assert response.status_code == 201
        data = response.json()

        assert "id" in data
        assert data["incident_type"] == "armed_attack"
        assert data["severity"] == "high"
        assert data["verified"] in [True, False]
        assert 0 <= data["verification_score"] <= 1
        assert data["state"] is not None  # Should be geocoded
        assert data["latitude"] is not None
        assert data["longitude"] is not None

    def test_create_incident_outside_nigeria(self):
        """Test that incidents outside Nigeria are rejected"""
        incident_data = {
            "incident_type": "armed_attack",
            "severity": "high",
            "location": {
                "type": "Point",
                "coordinates": [0.0, 51.5074]  # London coordinates
            },
            "description": "This should be rejected",
            "timestamp": datetime.utcnow().isoformat()
        }

        response = client.post("/api/v1/incidents/", json=incident_data)

        assert response.status_code == 400
        assert "outside Nigerian boundaries" in response.json()["detail"]

    def test_create_incident_invalid_coordinates(self):
        """Test validation of invalid coordinates"""
        incident_data = {
            "incident_type": "armed_attack",
            "severity": "high",
            "location": {
                "type": "Point",
                "coordinates": [200, 100]  # Invalid coordinates
            },
            "description": "Test incident",
            "timestamp": datetime.utcnow().isoformat()
        }

        response = client.post("/api/v1/incidents/", json=incident_data)

        assert response.status_code == 422  # Validation error

    def test_create_incident_short_description(self):
        """Test that short descriptions are rejected"""
        incident_data = {
            "incident_type": "armed_attack",
            "severity": "high",
            "location": {
                "type": "Point",
                "coordinates": [7.4905, 9.0765]
            },
            "description": "Too short",  # Less than 10 characters
            "timestamp": datetime.utcnow().isoformat()
        }

        response = client.post("/api/v1/incidents/", json=incident_data)

        assert response.status_code == 422

    def test_create_anonymous_incident(self):
        """Test creating an anonymous incident report"""
        incident_data = {
            "incident_type": "kidnapping",
            "severity": "critical",
            "location": {
                "type": "Point",
                "coordinates": [6.6642, 12.1704]  # Zamfara
            },
            "description": "Gunmen kidnapped travelers along the highway near Gusau",
            "timestamp": datetime.utcnow().isoformat(),
            "is_anonymous": True
        }

        response = client.post("/api/v1/incidents/", json=incident_data)

        assert response.status_code == 201
        data = response.json()
        assert data["incident_type"] == "kidnapping"


class TestIncidentRetrieval:
    """Tests for retrieving incidents"""

    def test_get_incident_by_id(self):
        """Test retrieving a specific incident by ID"""
        # First create an incident
        incident_data = {
            "incident_type": "banditry",
            "severity": "high",
            "location": {
                "type": "Point",
                "coordinates": [6.6642, 12.1704]
            },
            "description": "Bandits attacked village, rustling cattle and looting homes",
            "timestamp": datetime.utcnow().isoformat()
        }

        create_response = client.post("/api/v1/incidents/", json=incident_data)
        incident_id = create_response.json()["id"]

        # Retrieve it
        get_response = client.get(f"/api/v1/incidents/{incident_id}")

        assert get_response.status_code == 200
        data = get_response.json()
        assert data["id"] == incident_id
        assert data["incident_type"] == "banditry"

    def test_get_nonexistent_incident(self):
        """Test retrieving a non-existent incident returns 404"""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/incidents/{fake_uuid}")

        assert response.status_code == 404

    def test_list_incidents_with_pagination(self):
        """Test listing incidents with pagination"""
        # Create multiple incidents
        for i in range(5):
            incident_data = {
                "incident_type": "armed_attack",
                "severity": "moderate",
                "location": {
                    "type": "Point",
                    "coordinates": [7.4905, 9.0765]
                },
                "description": f"Test incident number {i} with enough description",
                "timestamp": datetime.utcnow().isoformat()
            }
            client.post("/api/v1/incidents/", json=incident_data)

        # Get page 1
        response = client.get("/api/v1/incidents/?page=1&page_size=3")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["page_size"] == 3
        assert len(data["incidents"]) == 3

    def test_list_incidents_filter_by_type(self):
        """Test filtering incidents by type"""
        # Create incidents of different types
        types = ["armed_attack", "kidnapping", "banditry"]
        for incident_type in types:
            incident_data = {
                "incident_type": incident_type,
                "severity": "moderate",
                "location": {
                    "type": "Point",
                    "coordinates": [7.4905, 9.0765]
                },
                "description": f"Test {incident_type} incident with description",
                "timestamp": datetime.utcnow().isoformat()
            }
            client.post("/api/v1/incidents/", json=incident_data)

        # Filter by kidnapping
        response = client.get("/api/v1/incidents/?incident_type=kidnapping")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["incidents"][0]["incident_type"] == "kidnapping"


class TestNearbyIncidents:
    """Tests for nearby incidents search"""

    def test_search_nearby_incidents(self):
        """Test finding incidents within a radius"""
        # Create incident in Jos
        incident_data = {
            "incident_type": "farmer_herder_clash",
            "severity": "high",
            "location": {
                "type": "Point",
                "coordinates": [8.8833, 9.9167]  # Jos coordinates
            },
            "description": "Clashes between farmers and herders in Jos, casualties reported",
            "timestamp": datetime.utcnow().isoformat()
        }
        client.post("/api/v1/incidents/", json=incident_data)

        # Search within 100km of Jos
        response = client.get(
            "/api/v1/incidents/nearby/search?"
            "latitude=9.9167&longitude=8.8833&radius_km=100&days=7"
        )

        assert response.status_code == 200
        incidents = response.json()
        assert len(incidents) >= 1
        assert incidents[0]["incident_type"] == "farmer_herder_clash"

    def test_nearby_search_outside_nigeria(self):
        """Test that search outside Nigeria is rejected"""
        response = client.get(
            "/api/v1/incidents/nearby/search?"
            "latitude=51.5074&longitude=0.0&radius_km=50"
        )

        assert response.status_code == 400


class TestIncidentStatistics:
    """Tests for incident statistics"""

    def test_get_statistics(self):
        """Test retrieving incident statistics"""
        # Create a few incidents
        incidents = [
            ("armed_attack", "high"),
            ("kidnapping", "critical"),
            ("armed_attack", "moderate"),
        ]

        for incident_type, severity in incidents:
            incident_data = {
                "incident_type": incident_type,
                "severity": severity,
                "location": {
                    "type": "Point",
                    "coordinates": [7.4905, 9.0765]
                },
                "description": "Test incident for statistics with proper length",
                "timestamp": datetime.utcnow().isoformat(),
                "casualties": {"killed": 2, "injured": 5, "missing": 0}
            }
            client.post("/api/v1/incidents/", json=incident_data)

        # Get statistics
        response = client.get("/api/v1/incidents/stats/summary?days=30")

        assert response.status_code == 200
        data = response.json()
        assert data["total_incidents"] == 3
        assert "by_type" in data
        assert "by_severity" in data
        assert "casualties_total" in data
        assert data["casualties_total"]["killed"] == 6  # 2 * 3 incidents


class TestGeoJSON:
    """Tests for GeoJSON export"""

    def test_get_geojson_featurecollection(self):
        """Test exporting incidents as GeoJSON"""
        # Create an incident
        incident_data = {
            "incident_type": "bomb_blast",
            "severity": "critical",
            "location": {
                "type": "Point",
                "coordinates": [13.1500, 11.8333]  # Maiduguri
            },
            "description": "IED explosion in market, multiple casualties reported",
            "timestamp": datetime.utcnow().isoformat()
        }
        client.post("/api/v1/incidents/", json=incident_data)

        # Get GeoJSON
        response = client.get("/api/v1/incidents/geojson/all?days=30")

        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "FeatureCollection"
        assert "features" in data
        assert len(data["features"]) >= 1

        feature = data["features"][0]
        assert feature["type"] == "Feature"
        assert feature["geometry"]["type"] == "Point"
        assert "properties" in feature
        assert feature["properties"]["incident_type"] == "bomb_blast"
