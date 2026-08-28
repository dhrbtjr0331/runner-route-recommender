"""Pre-download and cache benchmark graphs and elevation data for Santa Monica, Griffith Park, and Central Park."""

import logging
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import BENCHMARK_PRESETS
from src.tools.osm_tool import generate_cache_key, get_walk_graph
from src.tools.elevation_tool import enrich_graph_elevations

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("cache_benchmarks")


def cache_all_benchmark_data():
    """Download and cache graphs + 3D node elevations for all benchmark cities."""
    benchmark_configs = [
        ("santa_monica_pier", 3500),   # 3.5km radius
        ("griffith_park", 4000),        # 4.0km radius
        ("central_park_nyc", 3500),     # 3.5km radius
        ("venice_beach", 3000),         # 3.0km radius
    ]

    for name, radius_m in benchmark_configs:
        coords = BENCHMARK_PRESETS[name]
        print(f"=== Caching {name} ({coords}, radius={radius_m}m) ===")
        
        # 1. Download/load walk graph
        cache_key = generate_cache_key(coords[0], coords[1], radius_m, "walk")
        G = get_walk_graph(coords, dist_m=radius_m, network_type="walk", strongly_connected_only=True)
        print(f"Graph '{name}' loaded: {len(G.nodes)} nodes, {len(G.edges)} edges")
        
        # 2. Enrich with elevation
        G = enrich_graph_elevations(G, cache_key=cache_key)
        print(f"Graph '{name}' enriched with elevations successfully.\n")


if __name__ == "__main__":
    cache_all_benchmark_data()
