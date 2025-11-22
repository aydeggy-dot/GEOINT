"""
Geocoding utilities for converting coordinates to location names
Uses Nominatim (OpenStreetMap) for reverse geocoding
"""
from typing import Optional, Dict
import httpx
from app.config import NIGERIAN_STATES


async def reverse_geocode(latitude: float, longitude: float) -> Optional[Dict[str, str]]:
    """
    Convert coordinates to location name using Nominatim API

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate

    Returns:
        Dictionary with location information or None if failed
        {
            "location_name": "Full address",
            "state": "State name",
            "lga": "Local Government Area",
            "city": "City name"
        }
    """
    try:
        # Use Nominatim API (OpenStreetMap)
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "lat": latitude,
            "lon": longitude,
            "format": "json",
            "addressdetails": 1,
            "zoom": 18
        }
        headers = {
            "User-Agent": "NigeriaSecuritySystem/1.0"  # Required by Nominatim
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers, timeout=10.0)

            if response.status_code != 200:
                return None

            data = response.json()

            if "error" in data:
                return None

            address = data.get("address", {})

            # Extract state (try multiple fields)
            state = (
                address.get("state") or
                address.get("region") or
                address.get("province")
            )

            # Validate state is in Nigeria
            if state and state not in NIGERIAN_STATES:
                # Try to find matching state
                state_lower = state.lower()
                for nigerian_state in NIGERIAN_STATES:
                    if nigerian_state.lower() in state_lower or state_lower in nigerian_state.lower():
                        state = nigerian_state
                        break

            # Extract LGA (Local Government Area)
            lga = (
                address.get("county") or
                address.get("municipality") or
                address.get("local_government_area")
            )

            # Extract city/town/village
            city = (
                address.get("city") or
                address.get("town") or
                address.get("village") or
                address.get("hamlet")
            )

            # Build full location name
            location_parts = []
            if city:
                location_parts.append(city)
            if lga and lga != city:
                location_parts.append(lga)
            if state:
                location_parts.append(state)

            location_name = ", ".join(location_parts) if location_parts else data.get("display_name", "Unknown Location")

            return {
                "location_name": location_name,
                "state": state,
                "lga": lga,
                "city": city
            }

    except Exception as e:
        print(f"Reverse geocoding error: {str(e)}")
        return None


def extract_state_from_coordinates(latitude: float, longitude: float) -> Optional[str]:
    """
    Determine Nigerian state from coordinates using simple bounding box lookup
    This is a fallback if reverse geocoding fails

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate

    Returns:
        State name or None
    """
    # Simplified state boundaries (approximate bounding boxes)
    # In production, use actual state polygon boundaries from GeoJSON
    state_bounds = {
        "Lagos": {"lat": (6.4, 6.7), "lon": (2.8, 4.0)},
        "Kano": {"lat": (10.5, 13.0), "lon": (7.5, 9.5)},
        "Kaduna": {"lat": (9.0, 11.3), "lon": (6.5, 8.5)},
        "Abuja": {"lat": (8.7, 9.3), "lon": (6.9, 7.7)},
        "Rivers": {"lat": (4.5, 5.2), "lon": (6.5, 7.5)},
        "Borno": {"lat": (10.5, 13.9), "lon": (11.5, 14.5)},
        "Yobe": {"lat": (11.0, 13.2), "lon": (10.5, 12.5)},
        "Adamawa": {"lat": (7.5, 10.5), "lon": (11.0, 13.5)},
        "Zamfara": {"lat": (11.0, 13.0), "lon": (5.0, 7.0)},
        "Katsina": {"lat": (11.5, 13.5), "lon": (7.0, 9.0)},
        "Sokoto": {"lat": (12.0, 14.0), "lon": (4.0, 6.5)},
        "Plateau": {"lat": (8.5, 10.0), "lon": (8.5, 10.0)},
        "Benue": {"lat": (6.5, 8.5), "lon": (7.5, 10.0)},
        "Nasarawa": {"lat": (7.5, 9.5), "lon": (7.0, 9.0)},
    }

    for state, bounds in state_bounds.items():
        lat_min, lat_max = bounds["lat"]
        lon_min, lon_max = bounds["lon"]

        if lat_min <= latitude <= lat_max and lon_min <= longitude <= lon_max:
            return state

    return None
