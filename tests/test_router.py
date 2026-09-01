"""Unit tests for baseline router and evaluation scoring metrics."""

import networkx as nx
import pytest

from src.baseline.baseline_router import BaselineRouter
from src.eval.metrics import (
    calculate_case_score,
    calculate_overall_score,
    score_constraint_satisfaction,
    score_distance_accuracy,
    score_elevation_compliance,
)
from src.eval.test_cases import BENCHMARK_CASES, TestCase


def test_benchmark_cases_count():
    """Verify all 12 benchmark test cases are defined properly."""
    assert len(BENCHMARK_CASES) == 12
    case_ids = [c.id for c in BENCHMARK_CASES]
    assert case_ids == [f"C{i:02d}" for i in range(1, 13)]
    
    # Check showcase hard case
    hard_cases = [c for c in BENCHMARK_CASES if c.is_showcase_hard_case]
    assert len(hard_cases) == 1
    assert hard_cases[0].id == "C12"


def test_distance_accuracy_metric():
    """Test distance scoring with tolerance decay."""
    # Target 5.0km, exact match
    assert score_distance_accuracy(5.0, 5.0) == 1.0
    # Target 5.0km, 5.5km actual (10% error, max tolerance is 20%) -> 0.5 score
    assert pytest.approx(score_distance_accuracy(5.5, 5.0), abs=0.01) == 0.50
    # Target 5.0km, 6.0km actual (20% error) -> 0.0 score
    assert score_distance_accuracy(6.0, 5.0) == 0.0
    # Target 5.0km, 7.0km actual (>20% error) -> 0.0 score
    assert score_distance_accuracy(7.0, 5.0) == 0.0


def test_elevation_compliance_metric():
    """Test easy, moderate, and hard elevation scoring."""
    # Easy run (5km): ceiling is 35m
    assert score_elevation_compliance(20.0, "easy", 5.0) == 1.0
    assert score_elevation_compliance(35.0, "easy", 5.0) == 1.0
    # 70m on easy run (100% overshoot) -> 0.0 score
    assert score_elevation_compliance(70.0, "easy", 5.0) == 0.0

    # Hard run (5km): floor is 90m
    assert score_elevation_compliance(120.0, "hard", 5.0) == 1.0
    assert score_elevation_compliance(90.0, "hard", 5.0) == 1.0
    # 45m on hard run (half of floor) -> 0.5 score
    assert pytest.approx(score_elevation_compliance(45.0, "hard", 5.0), abs=0.01) == 0.50


def test_constraint_scoring():
    """Test positive keyword traversal and negative avoid penalty."""
    G = nx.MultiDiGraph()
    G.add_node(1, x=0, y=0, elevation=0)
    G.add_node(2, x=0, y=0.01, elevation=10)
    G.add_node(3, x=0.01, y=0, elevation=0)

    # Edge 1->2 has name 'Ocean Ave' (avoid keyword)
    G.add_edge(1, 2, length=1000, name="Ocean Ave", highway="footway")
    # Edge 2->3 has name 'Beach Boardwalk' (positive POI)
    G.add_edge(2, 3, length=1000, name="Beach Boardwalk", highway="path")

    tc = TestCase(
        id="C99",
        name="Synthetic Test Case",
        city_key="santa_monica_pier",
        location_query="Santa Monica, CA",
        target_distance_km=2.0,
        difficulty="easy",
        user_prompt="Run by the beach, avoid Ocean Ave",
        poi_keywords=["beach", "boardwalk"],
        avoid_keywords=["ocean_ave"],
    )

    # Path [1, 2, 3] hits 2/2 POIs (1.0) but triggers avoid penalty (-0.4) -> 0.60
    score = score_constraint_satisfaction(G, [1, 2, 3], tc)
    assert pytest.approx(score, abs=0.01) == 0.60


def test_baseline_router_synthetic_graph():
    """Test that baseline router finds a valid closed loop on a synthetic polygon grid."""
    G = nx.MultiDiGraph()
    G.graph["crs"] = "epsg:4326"
    # Create an 4-node diamond graph around (34.0, -118.4)
    nodes = [
        (1, 34.000, -118.400),
        (2, 34.005, -118.405),
        (3, 34.010, -118.400),
        (4, 34.005, -118.395),
    ]
    for n_id, lat, lon in nodes:
        G.add_node(n_id, x=lon, y=lat, elevation=10.0)

    # Add bidirectional edges with lengths
    edges = [(1, 2), (2, 3), (3, 4), (4, 1)]
    for u, v in edges:
        G.add_edge(u, v, length=1000.0)
        G.add_edge(v, u, length=1000.0)

    router = BaselineRouter(bearings_count=4)
    route = router.generate_route(G, (34.000, -118.400), target_distance_km=4.0)

    assert route is not None
    assert route["path_nodes"][0] == route["path_nodes"][-1]
    assert len(route["path_nodes"]) >= 3
    assert route["actual_distance_km"] > 0
