"""OpenStreetMap graph extraction, cleaning, and caching utility using OSMnx and NetworkX."""

import hashlib
import logging
from pathlib import Path
from typing import Optional, Tuple

import networkx as nx
import osmnx as ox

from src.config import OSM_CACHE_DIR, DEFAULT_WALK_NETWORK_TYPE

logger = logging.getLogger(__name__)

# Configure OSMnx settings
ox.settings.use_cache = True
ox.settings.log_console = False


def generate_cache_key(lat: float, lon: float, dist_m: int, network_type: str = DEFAULT_WALK_NETWORK_TYPE) -> str:
    """Generate a deterministic filename key based on query location and radius."""
    raw = f"{round(lat, 4)}_{round(lon, 4)}_{int(dist_m)}_{network_type}"
    h = hashlib.md5(raw.encode("utf-8")).hexdigest()[:10]
    return f"osm_{round(lat, 4)}_{round(lon, 4)}_{int(dist_m)}m_{h}"


def get_cached_graph_path(cache_key: str) -> Path:
    """Return the filesystem path for a cached GraphML file."""
    return OSM_CACHE_DIR / f"{cache_key}.graphml"


def get_cached_graph(cache_key: str) -> Optional[nx.MultiDiGraph]:
    """Load graph from local cache if it exists."""
    path = get_cached_graph_path(cache_key)
    if path.exists():
        try:
            logger.info("Loading cached OSM graph from %s", path)
            G = ox.load_graphml(path)
            return G
        except Exception as e:
            logger.warning("Failed to load cached graph %s: %s", path, e)
    return None


def save_graph_to_cache(G: nx.MultiDiGraph, cache_key: str) -> Path:
    """Save graph to local cache in GraphML format."""
    path = get_cached_graph_path(cache_key)
    try:
        ox.save_graphml(G, path)
        logger.info("Saved OSM graph to cache at %s", path)
    except Exception as e:
        logger.warning("Failed to save graph to cache %s: %s", path, e)
    return path


def get_walk_graph(
    center_point: Tuple[float, float],
    dist_m: int = 3000,
    network_type: str = DEFAULT_WALK_NETWORK_TYPE,
    force_refresh: bool = False,
    strongly_connected_only: bool = True,
) -> nx.MultiDiGraph:
    """
    Download or load a walkable network graph centered around a coordinate.
    
    Args:
        center_point: (latitude, longitude)
        dist_m: Radial distance in meters from center
        network_type: OSMnx network type ('walk', 'all', etc.)
        force_refresh: If True, bypass cache and re-download from OSM Overpass
        strongly_connected_only: If True, keep only the largest strongly connected component
        
    Returns:
        nx.MultiDiGraph with node attributes 'x', 'y' and edge attributes 'length', 'highway', etc.
    """
    lat, lon = center_point
    cache_key = generate_cache_key(lat, lon, dist_m, network_type)

    if not force_refresh:
        cached_G = get_cached_graph(cache_key)
        if cached_G is not None:
            return cached_G

    logger.info("Downloading OSM walk graph for (%f, %f) with radius %dm...", lat, lon, dist_m)
    try:
        G = ox.graph_from_point(
            (lat, lon),
            dist=dist_m,
            network_type=network_type,
            simplify=True,
            retain_all=False,
            truncate_by_edge=True,
        )
    except Exception as e:
        logger.error("Error downloading graph from OSM: %s", e)
        raise

    if strongly_connected_only and len(G) > 0:
        G = ox.truncate.largest_component(G, strongly=True)

    # Ensure edge attributes have numerical lengths
    for u, v, k, data in G.edges(keys=True, data=True):
        if "length" not in data:
            data["length"] = 1.0

    save_graph_to_cache(G, cache_key)
    return G
