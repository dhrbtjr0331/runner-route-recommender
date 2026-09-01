"""Quantitative evaluation metrics for route recommendation quality."""

from typing import Dict, List, Optional
import networkx as nx

from src.eval.test_cases import TestCase


def score_distance_accuracy(actual_distance_km: float, target_distance_km: float, tolerance: float = 0.20) -> float:
    """
    Score how accurately the actual distance matches the target.
    
    Formula:
        S_dist = max(0.0, 1.0 - |D_actual - D_target| / (D_target * tolerance))
    """
    if target_distance_km <= 0:
        return 0.0
    err = abs(actual_distance_km - target_distance_km)
    max_err = target_distance_km * tolerance
    score = 1.0 - (err / max_err)
    return max(0.0, min(1.0, score))


def score_elevation_compliance(
    elevation_gain_m: float,
    difficulty: str,
    target_distance_km: float,
    max_gain_ceiling_m: Optional[float] = None,
    min_gain_floor_m: Optional[float] = None,
) -> float:
    """
    Score how well the route's elevation profile matches the requested difficulty.
    
    - 'easy': penalizes excessive hill climbs beyond ceiling.
    - 'hard': penalizes flat routes below minimum climbing floor.
    - 'moderate': rewards rolling hills within an acceptable middle band.
    """
    dist_scale = max(0.5, target_distance_km / 5.0)

    if difficulty == "easy":
        ceiling = max_gain_ceiling_m if max_gain_ceiling_m is not None else (35.0 * dist_scale)
        if elevation_gain_m <= ceiling:
            return 1.0
        overshoot = elevation_gain_m - ceiling
        score = 1.0 - (overshoot / ceiling)
        return max(0.0, min(1.0, score))

    elif difficulty == "hard":
        floor = min_gain_floor_m if min_gain_floor_m is not None else (90.0 * dist_scale)
        if elevation_gain_m >= floor:
            return 1.0
        score = elevation_gain_m / floor
        return max(0.0, min(1.0, score))

    else:  # "moderate"
        floor = min_gain_floor_m if min_gain_floor_m is not None else (30.0 * dist_scale)
        ceiling = max_gain_ceiling_m if max_gain_ceiling_m is not None else (90.0 * dist_scale)
        if floor <= elevation_gain_m <= ceiling:
            return 1.0
        elif elevation_gain_m < floor:
            return max(0.0, min(1.0, elevation_gain_m / max(1.0, floor)))
        else:
            overshoot = elevation_gain_m - ceiling
            return max(0.0, min(1.0, 1.0 - (overshoot / max(1.0, ceiling))))


def score_constraint_satisfaction(
    G: nx.MultiDiGraph,
    path_nodes: List[int],
    test_case: TestCase,
) -> float:
    """
    Score whether positive POI preferences were traversed and negative avoid areas were avoided.
    """
    if not path_nodes or len(path_nodes) < 2:
        return 0.0

    traversed_names = set()
    for i in range(len(path_nodes) - 1):
        u = path_nodes[i]
        v = path_nodes[i + 1]
        if G.has_edge(u, v):
            edge_dict = G.get_edge_data(u, v)
            for k, data in edge_dict.items():
                name = data.get("name", "")
                highway = data.get("highway", "")
                if isinstance(name, list):
                    traversed_names.update(str(n).lower() for n in name)
                elif name:
                    traversed_names.add(str(name).lower())
                if isinstance(highway, list):
                    traversed_names.update(str(h).lower() for h in highway)
                elif highway:
                    traversed_names.add(str(highway).lower())

    joined_text = " ".join(traversed_names)

    # 1. Positive POI matching
    poi_matches = 0
    total_pois = len(test_case.poi_keywords)
    if total_pois > 0:
        for kw in test_case.poi_keywords:
            clean_kw = kw.lower().replace("_", " ")
            if any(clean_kw in name for name in traversed_names) or clean_kw in joined_text:
                poi_matches += 1
        poi_score = poi_matches / total_pois
    else:
        poi_score = 1.0

    # 2. Negative Avoid checking
    avoid_penalty = 0.0
    for avoid in test_case.avoid_keywords:
        clean_avoid = avoid.lower().replace("_", " ")
        if any(clean_avoid in name for name in traversed_names) or clean_avoid in joined_text:
            avoid_penalty += 0.40

    final_poi_score = max(0.0, min(1.0, poi_score - avoid_penalty))
    return final_poi_score


def calculate_case_score(
    G: nx.MultiDiGraph,
    route_data: Optional[Dict],
    test_case: TestCase,
) -> Dict[str, float]:
    """
    Calculate the 3 sub-scores and the combined total score for a test case.
    
    Formula:
        S_total = 0.35 * S_dist + 0.35 * S_elev + 0.30 * S_poi
    """
    if not route_data or not route_data.get("path_nodes"):
        return {
            "score_dist": 0.0,
            "score_elev": 0.0,
            "score_poi": 0.0,
            "score_total": 0.0,
            "actual_distance_km": 0.0,
            "elevation_gain_m": 0.0,
        }

    act_dist = route_data["actual_distance_km"]
    act_gain = route_data["elevation_gain_m"]
    path_nodes = route_data["path_nodes"]

    s_dist = score_distance_accuracy(act_dist, test_case.target_distance_km)
    s_elev = score_elevation_compliance(
        elevation_gain_m=act_gain,
        difficulty=test_case.difficulty,
        target_distance_km=test_case.target_distance_km,
        max_gain_ceiling_m=test_case.max_gain_ceiling_m,
        min_gain_floor_m=test_case.min_gain_floor_m,
    )
    s_poi = score_constraint_satisfaction(G, path_nodes, test_case)

    s_total = (0.35 * s_dist) + (0.35 * s_elev) + (0.30 * s_poi)

    return {
        "score_dist": round(s_dist, 4),
        "score_elev": round(s_elev, 4),
        "score_poi": round(s_poi, 4),
        "score_total": round(s_total, 4),
        "actual_distance_km": round(act_dist, 2),
        "elevation_gain_m": round(act_gain, 1),
    }


def calculate_overall_score(case_results: List[Dict]) -> Dict[str, float]:
    """Aggregate per-case metrics across all benchmark cases."""
    if not case_results:
        return {"mean_dist": 0.0, "mean_elev": 0.0, "mean_poi": 0.0, "mean_total": 0.0}

    n = len(case_results)
    mean_dist = sum(r["score_dist"] for r in case_results) / n
    mean_elev = sum(r["score_elev"] for r in case_results) / n
    mean_poi = sum(r["score_poi"] for r in case_results) / n
    mean_total = sum(r["score_total"] for r in case_results) / n

    return {
        "mean_dist": round(mean_dist, 4),
        "mean_elev": round(mean_elev, 4),
        "mean_poi": round(mean_poi, 4),
        "mean_total": round(mean_total, 4),
    }
