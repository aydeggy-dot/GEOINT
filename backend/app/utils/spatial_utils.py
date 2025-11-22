"""
Spatial utility functions for geospatial operations
"""
from typing import Tuple, Optional
from geoalchemy2.elements import WKTElement
from shapely.geometry import Point, shape
from shapely import wkt
import math
from app.config import NIGERIA_BOUNDS


def create_point_geometry(longitude: float, latitude: float, srid: int = 4326) -> WKTElement:
    """
    Create a PostGIS Point geometry from coordinates

    Args:
        longitude: Longitude coordinate
        latitude: Latitude coordinate
        srid: Spatial Reference System ID (default: 4326 for WGS84)

    Returns:
        WKTElement for use in SQLAlchemy
    """
    point = Point(longitude, latitude)
    return WKTElement(point.wkt, srid=srid)


def validate_nigerian_coordinates(longitude: float, latitude: float) -> bool:
    """
    Validate that coordinates are within Nigerian boundaries

    Args:
        longitude: Longitude coordinate
        latitude: Latitude coordinate

    Returns:
        True if coordinates are within Nigeria's bounding box
    """
    return (
        NIGERIA_BOUNDS["min_lon"] <= longitude <= NIGERIA_BOUNDS["max_lon"] and
        NIGERIA_BOUNDS["min_lat"] <= latitude <= NIGERIA_BOUNDS["max_lat"]
    )


def haversine_distance(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth
    using the Haversine formula

    Args:
        lon1, lat1: First point coordinates
        lon2, lat2: Second point coordinates

    Returns:
        Distance in kilometers
    """
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))

    # Earth's radius in kilometers
    r = 6371

    return c * r


def calculate_bearing(lon1: float, lat1: float, lon2: float, lat2: float) -> str:
    """
    Calculate the compass bearing from point 1 to point 2

    Args:
        lon1, lat1: Origin point coordinates
        lon2, lat2: Destination point coordinates

    Returns:
        Cardinal direction (N, NE, E, SE, S, SW, W, NW)
    """
    # Convert to radians
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])

    dlon = lon2 - lon1

    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)

    # Calculate bearing in degrees
    bearing = math.degrees(math.atan2(x, y))
    bearing = (bearing + 360) % 360

    # Convert to cardinal direction
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    index = round(bearing / 45) % 8
    return directions[index]


def degrees_to_kilometers(degrees: float, latitude: float) -> float:
    """
    Convert degrees to kilometers at a given latitude
    (longitude degrees vary with latitude, latitude degrees are constant)

    Args:
        degrees: Degrees to convert
        latitude: Latitude for longitude calculation

    Returns:
        Approximate distance in kilometers
    """
    # 1 degree of latitude ≈ 111 km everywhere
    lat_km = degrees * 111.32

    # 1 degree of longitude varies with latitude
    lon_km = degrees * 111.32 * math.cos(math.radians(latitude))

    # Return average for simplicity
    return (lat_km + lon_km) / 2


def kilometers_to_degrees(km: float, latitude: float = 9.0) -> float:
    """
    Convert kilometers to approximate degrees
    (uses average latitude for Nigeria ~9°N)

    Args:
        km: Kilometers to convert
        latitude: Latitude for calculation (default: 9.0 for Nigeria center)

    Returns:
        Approximate degrees
    """
    # Average conversion at Nigeria's latitude
    return km / 111.32


def create_buffer_polygon(longitude: float, latitude: float, radius_km: float, srid: int = 4326) -> WKTElement:
    """
    Create a circular polygon buffer around a point

    Args:
        longitude: Center point longitude
        latitude: Center point latitude
        radius_km: Radius in kilometers
        srid: Spatial Reference System ID

    Returns:
        WKTElement polygon for use in SQLAlchemy
    """
    # Convert km to degrees (approximate)
    radius_degrees = kilometers_to_degrees(radius_km, latitude)

    # Create point and buffer
    point = Point(longitude, latitude)
    buffered = point.buffer(radius_degrees)

    return WKTElement(buffered.wkt, srid=srid)


def extract_coordinates_from_geometry(geometry) -> Optional[Tuple[float, float]]:
    """
    Extract longitude and latitude from a GeoAlchemy2 geometry

    Args:
        geometry: GeoAlchemy2 geometry object

    Returns:
        Tuple of (longitude, latitude) or None
    """
    if geometry is None:
        return None

    try:
        # GeoAlchemy2 geometry objects have a desc attribute with coordinates
        # Or we can convert using shapely's wkb module
        from shapely import wkb
        from geoalchemy2.shape import to_shape

        # Convert GeoAlchemy2 element to Shapely geometry
        geom_shape = to_shape(geometry)
        if isinstance(geom_shape, Point):
            return (geom_shape.x, geom_shape.y)
    except Exception as e:
        # Fallback: try direct attribute access
        try:
            if hasattr(geometry, 'coords'):
                coords = list(geometry.coords)
                if coords and len(coords) > 0:
                    return tuple(coords[0])
        except Exception:
            pass

    return None


def grid_cell_id(longitude: float, latitude: float, resolution_km: float = 10.0) -> str:
    """
    Generate a grid cell ID for a coordinate based on resolution
    Used for spatial aggregation and prediction grids

    Args:
        longitude: Longitude coordinate
        latitude: Latitude coordinate
        resolution_km: Grid cell size in kilometers

    Returns:
        Grid cell identifier (e.g., "9.5_7.5")
    """
    # Convert resolution to degrees
    resolution_deg = resolution_km / 111.32

    # Snap to grid
    grid_lat = round(latitude / resolution_deg) * resolution_deg
    grid_lon = round(longitude / resolution_deg) * resolution_deg

    return f"{grid_lat:.2f}_{grid_lon:.2f}"
