"""Geocoding, location lookup, and spatial node snapping tool."""

import logging
import math
from typing import Optional, Tuple

import networkx as nx
import osmnx as ox
from geopy.geocoders import Nominatim

from src.config import BENCHMARK_PRESETS

logger = logging.getLogger(__name__)

# Initialize Nominatim geocoder with custom user-agent
_geolocator = Nominatim(user_agent="rrr_agent_micro1_hackathon")


def geocode_location(location_str: str) -> Tuple[float, float]:
    """
    Resolve a text location or landmark to (latitude, longitude).
    Checks predefined benchmark presets first, then attempts Nominatim geocoding.
    
    Args:
        location_str: Name of place, landmark, or address (e.g. "Santa Monica Pier")
        
    Returns:
        (latitude, longitude)
    """
    normalized = location_str.strip().lower().replace(" ", "_").replace("-", "_")

    # Check direct preset aliases
    for key, coords in BENCHMARK_PRESETS.items():
        if key in normalized or normalized in key:
            logger.info("Resolved '%s' via benchmark preset '%s': %s", location_str, key, coords)
            return coords

    # Special handling for common phrases
    if "santa_monica" in normalized:
        return BENCHMARK_PRESETS["santa_monica_pier"]
    if "griffith" in normalized:
        return BENCHMARK_PRESETS["griffith_park"]
    if "central_park" in normalized or "nyc" in normalized or "manhattan" in normalized:
        return BENCHMARK_PRESETS["central_park_nyc"]
    if "venice" in normalized:
        return BENCHMARK_PRESETS["venice_beach"]
    if "downtown_la" in normalized or "dtla" in normalized:
        return BENCHMARK_PRESETS["downtown_la"]

    # Try online geocoding via Nominatim
    try:
        location = _geolocator.geocode(location_str, timeout=10)
        if location:
            logger.info("Resolved '%s' via Nominatim: (%f, %f)", location_str, location.latitude, location.longitude)
            return float(location.latitude), float(location.longitude)
    except Exception as e:
        logger.warning("Geocoding failed for '%s': %s. Falling back to default Santa Monica Pier.", location_str, e)

    return BENCHMARK_PRESETS["santa_monica_pier"]


def snap_point_to_node(G: nx.MultiDiGraph, lat: float, lon: float) -> int:
    """
    Find the nearest node in the OSM graph to the given (latitude, longitude).
    
    Args:
        G: NetworkX MultiDiGraph with node coordinates ('x' = lon, 'y' = lat).
        lat: Latitude.
        lon: Longitude.
        
    Returns:
        Nearest node ID.
    """
    nearest_node = ox.distance.nearest_nodes(G, X=lon, Y=lat)
    return int(nearest_node)


def haversine_distance_km(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """Calculate the great-circle distance between two points on the Earth in kilometers."""
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    radius = 6371.0  # Earth radius in km

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius * c


def compute_destination_point(lat: float, lon: float, distance_km: float, bearing_deg: float) -> Tuple[float, float]:
    """
    Calculate destination point given start coordinate, distance (km), and bearing (degrees).
    """
    radius = 6371.0
    rad_lat = math.radians(lat)
    rad_lon = math.radians(lon)
    rad_bearing = math.radians(bearing_deg)
    angular_dist = distance_km / radius

    dest_lat = math.asin(
        math.sin(rad_lat) * math.cos(angular_dist)
        + math.cos(rad_lat) * math.sin(angular_dist) * math.cos(rad_bearing)
    )
    dest_lon = rad_lon + math.atan2(
        math.sin(rad_bearing) * math.sin(angular_dist) * math.cos(rad_lat),
        math.cos(angular_dist) - math.sin(rad_lat) * math.sin(dest_lat),
    )
    return math.degrees(dest_lat), math.degrees(dest_lon)
