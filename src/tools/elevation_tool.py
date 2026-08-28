"""Elevation enrichment tool using Open-Meteo Elevation API and local caching."""

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import networkx as nx
import requests

from src.config import ELEVATION_CACHE_DIR, OPEN_METEO_ELEVATION_URL

logger = logging.getLogger(__name__)


def get_elevation_cache_path(graph_cache_key: str) -> Path:
    """Return cache file path for elevation data associated with a graph."""
    return ELEVATION_CACHE_DIR / f"{graph_cache_key}_elevation.json"


def fetch_elevations_batch(
    coords: List[Tuple[float, float]],
    batch_size: int = 100,
    timeout: int = 15,
    delay_between_requests: float = 0.05,
) -> List[float]:
    """
    Fetch elevations for a list of (latitude, longitude) coordinate pairs from Open-Meteo API.
    
    Args:
        coords: List of (lat, lon) tuples.
        batch_size: Number of coordinates to query per HTTP request (max 100).
        timeout: Request timeout in seconds.
        delay_between_requests: Delay in seconds to avoid rate limiting.
        
    Returns:
        List of elevation values in meters.
    """
    elevations: List[float] = []

    for i in range(0, len(coords), batch_size):
        batch = coords[i : i + batch_size]
        lats = ",".join(f"{c[0]:.5f}" for c in batch)
        lons = ",".join(f"{c[1]:.5f}" for c in batch)
        url = f"{OPEN_METEO_ELEVATION_URL}?latitude={lats}&longitude={lons}"

        success = False
        for attempt in range(3):
            try:
                resp = requests.get(url, timeout=timeout)
                if resp.status_code == 429:
                    time.sleep(1.0 * (attempt + 1))
                    continue
                resp.raise_for_status()
                data = resp.json()
                batch_elev = data.get("elevation", [])
                if len(batch_elev) != len(batch):
                    batch_elev.extend([0.0] * (len(batch) - len(batch_elev)))
                elevations.extend([float(e) for e in batch_elev])
                success = True
                break
            except Exception as e:
                logger.warning("Attempt %d failed to fetch elevations: %s", attempt + 1, e)
                time.sleep(0.5 * (attempt + 1))

        if not success:
            logger.warning("Failed to fetch elevations for batch after retries. Using default 0.0m.")
            elevations.extend([0.0] * len(batch))

        if delay_between_requests > 0:
            time.sleep(delay_between_requests)

    return elevations


def enrich_graph_elevations(
    G: nx.MultiDiGraph,
    cache_key: Optional[str] = None,
    force_refresh: bool = False,
) -> nx.MultiDiGraph:
    """
    Enrich all nodes in the graph with an 'elevation' attribute (in meters) and
    compute 'grade' (rise/run) on all edges.
    
    Args:
        G: NetworkX MultiDiGraph (from OSMnx) with node 'x' (lon) and 'y' (lat).
        cache_key: Optional cache key identifier to persist/load node elevations.
        force_refresh: If True, re-fetch from API even if cached.
        
    Returns:
        The enriched graph with node['elevation'] and edge['grade'].
    """
    if len(G) == 0:
        return G

    cache_path = get_elevation_cache_path(cache_key) if cache_key else None
    node_elevations: Dict[int, float] = {}

    if cache_path and cache_path.exists() and not force_refresh:
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                node_elevations = {int(k): float(v) for k, v in raw_data.items()}
            logger.info("Loaded elevations from cache for %d nodes", len(node_elevations))
        except Exception as e:
            logger.warning("Error reading elevation cache %s: %s", cache_path, e)

    nodes_to_fetch = [n for n in G.nodes if n not in node_elevations]

    if nodes_to_fetch:
        logger.info("Fetching elevations for %d nodes from Open-Meteo...", len(nodes_to_fetch))
        coords = [(G.nodes[n]["y"], G.nodes[n]["x"]) for n in nodes_to_fetch]
        fetched_elevations = fetch_elevations_batch(coords)

        for n, elev in zip(nodes_to_fetch, fetched_elevations):
            node_elevations[n] = float(elev)

        if cache_path:
            try:
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump({str(k): v for k, v in node_elevations.items()}, f)
                logger.info("Cached elevations for %d nodes to %s", len(node_elevations), cache_path)
            except Exception as e:
                logger.warning("Could not write elevation cache: %s", e)

    # Assign elevations to nodes
    for n, data in G.nodes(data=True):
        data["elevation"] = float(node_elevations.get(n, 0.0))

    # Assign grades to edges: grade = (elev_v - elev_u) / length
    for u, v, k, data in G.edges(keys=True, data=True):
        elev_u = G.nodes[u].get("elevation", 0.0)
        elev_v = G.nodes[v].get("elevation", 0.0)
        length = data.get("length", 1.0)
        if length <= 0:
            length = 1.0
        grade = (elev_v - elev_u) / length
        data["grade"] = grade
        data["elev_change"] = elev_v - elev_u

    return G


def calculate_path_elevation_gain(G: nx.MultiDiGraph, path_nodes: List[int]) -> Tuple[float, float, float]:
    """
    Calculate cumulative ascent, cumulative descent, and total distance for a route path.
    
    Args:
        G: Enriched graph with node elevations.
        path_nodes: Sequential list of node IDs along the route.
        
    Returns:
        Tuple of (cumulative_gain_m, cumulative_loss_m, total_distance_m)
    """
    if not path_nodes or len(path_nodes) < 2:
        return 0.0, 0.0, 0.0

    cumulative_gain = 0.0
    cumulative_loss = 0.0
    total_distance = 0.0

    for i in range(len(path_nodes) - 1):
        u = path_nodes[i]
        v = path_nodes[i + 1]

        elev_u = G.nodes[u].get("elevation", 0.0)
        elev_v = G.nodes[v].get("elevation", 0.0)
        diff = elev_v - elev_u

        if diff > 0:
            cumulative_gain += diff
        else:
            cumulative_loss += abs(diff)

        if G.has_edge(u, v):
            edge_data = G.get_edge_data(u, v)
            min_len = min(d.get("length", 0.0) for d in edge_data.values())
            total_distance += min_len

    return cumulative_gain, cumulative_loss, total_distance
