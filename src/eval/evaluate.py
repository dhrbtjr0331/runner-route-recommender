"""Benchmark evaluation runner to benchmark baseline and agent route recommenders."""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional
import networkx as nx

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.baseline.baseline_router import BaselineRouter
from src.config import BENCHMARK_PRESETS
from src.eval.metrics import calculate_case_score, calculate_overall_score
from src.eval.test_cases import BENCHMARK_CASES, TestCase
from src.tools.elevation_tool import enrich_graph_elevations
from src.tools.osm_tool import generate_cache_key, get_walk_graph

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("evaluator")


# Regional Graph Hubs (maps city presets to primary regional graphs)
CITY_GRAPH_MAPPING: Dict[str, str] = {
    "santa_monica_pier": "santa_monica_pier",
    "venice_beach": "santa_monica_pier",      # Venice Beach is within Santa Monica 3.5km graph
    "griffith_park": "griffith_park",
    "downtown_la": "griffith_park",          # DTLA / East LA regional coverage
    "central_park_nyc": "central_park_nyc",
}

CITY_RADII: Dict[str, int] = {
    "santa_monica_pier": 3500,
    "griffith_park": 4000,
    "central_park_nyc": 3500,
    "venice_beach": 3000,
    "downtown_la": 3000,
}

_IN_MEMORY_GRAPHS: Dict[str, nx.MultiDiGraph] = {}


def load_graph_for_case(test_case: TestCase, radius_padding_factor: float = 1.35):
    """Load or extract the enriched OSM graph for the test case (cached in memory)."""
    hub_key = CITY_GRAPH_MAPPING.get(test_case.city_key, test_case.city_key)
    coords = BENCHMARK_PRESETS.get(hub_key, (34.0099, -118.4965))
    start_coords = BENCHMARK_PRESETS.get(test_case.city_key, coords)
    base_radius = CITY_RADII.get(hub_key, 3500)
    estimated_radius_m = base_radius
    
    cache_key = generate_cache_key(coords[0], coords[1], estimated_radius_m, "walk")
    if cache_key in _IN_MEMORY_GRAPHS:
        return _IN_MEMORY_GRAPHS[cache_key], start_coords

    G = get_walk_graph(coords, dist_m=estimated_radius_m, network_type="walk", strongly_connected_only=True)
    G = enrich_graph_elevations(G, cache_key=cache_key)
    _IN_MEMORY_GRAPHS[cache_key] = G
    return G, start_coords


def run_evaluation(router_type: str = "baseline", export_path: Optional[str] = None) -> Dict:
    """
    Run evaluation suite across all 12 benchmark test cases.
    
    Args:
        router_type: 'baseline' or 'agent'
        export_path: Optional path to save JSON results.
        
    Returns:
        Dictionary containing case-by-case results and aggregate scores.
    """
    logger.info("Starting benchmark evaluation for router: %s", router_type.upper())

    if router_type == "baseline":
        router = BaselineRouter()
    else:
        raise NotImplementedError(f"Router type '{router_type}' will be integrated in PR 3.")

    results: List[Dict] = []

    print("\n" + "=" * 90)
    print(f"  RUNNABLE ROUTE RECOMMENDER — BENCHMARK EVALUATION [{router_type.upper()}]")
    print("=" * 90)
    print(f"{'Case':<5} | {'Location':<18} | {'Tgt(km)':<7} | {'Act(km)':<7} | {'Diff':<8} | {'Gain(m)':<7} | {'S_dist':<6} | {'S_elev':<6} | {'S_poi':<6} | {'S_total':<6}")
    print("-" * 90)

    for case in BENCHMARK_CASES:
        try:
            G, coords = load_graph_for_case(case)
            route_data = router.generate_route(
                G=G,
                start_coords=coords,
                target_distance_km=case.target_distance_km,
            )
            score_dict = calculate_case_score(G, route_data, case)
        except Exception as e:
            logger.error("Error evaluating %s: %s", case.id, e)
            score_dict = {
                "score_dist": 0.0,
                "score_elev": 0.0,
                "score_poi": 0.0,
                "score_total": 0.0,
                "actual_distance_km": 0.0,
                "elevation_gain_m": 0.0,
            }

        res_entry = {
            "case_id": case.id,
            "name": case.name,
            "city_key": case.city_key,
            "target_distance_km": case.target_distance_km,
            "difficulty": case.difficulty,
            "user_prompt": case.user_prompt,
            **score_dict,
        }
        results.append(res_entry)

        loc_label = case.city_key[:18]
        print(
            f"{case.id:<5} | {loc_label:<18} | {case.target_distance_km:<7.1f} | "
            f"{res_entry['actual_distance_km']:<7.1f} | {case.difficulty:<8} | "
            f"{res_entry['elevation_gain_m']:<7.0f} | {res_entry['score_dist']:<6.2f} | "
            f"{res_entry['score_elev']:<6.2f} | {res_entry['score_poi']:<6.2f} | "
            f"{res_entry['score_total']:<6.2f}"
        )

    summary = calculate_overall_score(results)

    print("-" * 90)
    print(f"{'OVERALL MEAN SCORES':<48} | {'':<7} | {summary['mean_dist']:<6.2f} | {summary['mean_elev']:<6.2f} | {summary['mean_poi']:<6.2f} | {summary['mean_total']:<6.2f}")
    print("=" * 90 + "\n")

    output_payload = {
        "router_type": router_type,
        "summary": summary,
        "cases": results,
    }

    if export_path:
        out_p = Path(export_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(output_payload, f, indent=2)
        logger.info("Exported evaluation results to %s", out_p)

    return output_payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate route recommenders on benchmark dataset.")
    parser.add_argument("--router", type=str, default="baseline", choices=["baseline", "agent"], help="Router type to evaluate.")
    parser.add_argument("--export", type=str, default="data/eval_baseline.json", help="Path to export JSON evaluation results.")
    args = parser.parse_args()

    run_evaluation(router_type=args.router, export_path=args.export)
