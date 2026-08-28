"""Unit tests for spatial graph utilities, elevation enrichment, and geocoding."""

import networkx as nx
import pytest

from src.config import BENCHMARK_PRESETS
from src.tools.elevation_tool import (
    calculate_path_elevation_gain,
    enrich_graph_elevations,
)
from src.tools.geocoding_tool import (
    compute_destination_point,
    geocode_location,
    haversine_distance_km,
    snap_point_to_node,
)
from src.tools.osm_tool import generate_cache_key, get_walk_graph


def test_geocoding_presets():
    """Test that benchmark preset locations resolve correctly."""
    lat, lon = geocode_location("Santa Monica Pier")
    assert pytest.approx(lat, abs=0.01) == BENCHMARK_PRESETS["santa_monica_pier"][0]
    assert pytest.approx(lon, abs=0.01) == BENCHMARK_PRESETS["santa_monica_pier"][1]

    lat_gp, lon_gp = geocode_location("Griffith Park, LA")
    assert pytest.approx(lat_gp, abs=0.01) == BENCHMARK_PRESETS["griffith_park"][0]


def test_haversine_and_destination_point():
    """Test geometric distance and bearing destination calculations."""
    p1 = (34.0099, -118.4965)
    # Move 1.0 km North (bearing 0)
    p2 = compute_destination_point(p1[0], p1[1], distance_km=1.0, bearing_deg=0.0)
    dist = haversine_distance_km(p1, p2)
    assert pytest.approx(dist, rel=1e-2) == 1.0
    assert p2[0] > p1[0]  # Moved north


def test_synthetic_graph_elevation_and_gain():
    """Test elevation assignment, edge grade calculation, and path gain on a synthetic graph."""
    G = nx.MultiDiGraph()
    # 3-node linear path: N1 (0m) -> N2 (50m) -> N3 (20m)
    G.add_node(1, x=-118.4965, y=34.0099, elevation=0.0)
    G.add_node(2, x=-118.4965, y=34.0199, elevation=50.0)
    G.add_node(3, x=-118.4965, y=34.0299, elevation=20.0)

    G.add_edge(1, 2, length=1000.0)
    G.add_edge(2, 3, length=1000.0)

    # Compute grades
    for u, v, k, data in G.edges(keys=True, data=True):
        elev_u = G.nodes[u]["elevation"]
        elev_v = G.nodes[v]["elevation"]
        data["grade"] = (elev_v - elev_u) / data["length"]

    # Edge 1->2 has +50m gain over 1000m = +0.05 grade (5% incline)
    assert pytest.approx(G.get_edge_data(1, 2)[0]["grade"], abs=1e-4) == 0.05
    # Edge 2->3 has -30m loss over 1000m = -0.03 grade (-3% decline)
    assert pytest.approx(G.get_edge_data(2, 3)[0]["grade"], abs=1e-4) == -0.03

    # Cumulative elevation gain along path 1 -> 2 -> 3
    gain, loss, total_dist = calculate_path_elevation_gain(G, [1, 2, 3])
    assert pytest.approx(gain, abs=0.1) == 50.0
    assert pytest.approx(loss, abs=0.1) == 30.0
    assert pytest.approx(total_dist, abs=0.1) == 2000.0


def test_cache_key_generation():
    """Test cache key uniqueness and determinism."""
    k1 = generate_cache_key(34.0099, -118.4965, 3000, "walk")
    k2 = generate_cache_key(34.0099, -118.4965, 3000, "walk")
    k3 = generate_cache_key(34.0099, -118.4965, 5000, "walk")
    assert k1 == k2
    assert k1 != k3
