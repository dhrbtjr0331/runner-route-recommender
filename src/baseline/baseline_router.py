"""Baseline router implementation using unguided geometric polygon waypoint selection."""

import logging
from typing import Dict, List, Optional, Tuple

import networkx as nx

from src.tools.elevation_tool import calculate_path_elevation_gain
from src.tools.geocoding_tool import compute_destination_point, snap_point_to_node

logger = logging.getLogger(__name__)


class BaselineRouter:
    """
    Unguided Baseline Route Generator.
    
    Uses identical OSMnx graph data as the agent, but selects loops purely based on
    geometric bearing rotation and standard unweighted distance shortest paths.
    Completely ignores elevation profile, POIs, and negative avoid constraints.
    """

    def __init__(self, bearings_count: int = 8):
        """
        Args:
            bearings_count: Number of radial candidate bearings to test (default 8: 0, 45, 90, ...).
        """
        self.bearings_count = bearings_count

    def generate_route(
        self,
        G: nx.MultiDiGraph,
        start_coords: Tuple[float, float],
        target_distance_km: float,
    ) -> Optional[Dict]:
        """
        Generate a candidate closed loop route near the target distance.
        
        Args:
            G: OSMnx walk graph.
            start_coords: (latitude, longitude) of origin.
            target_distance_km: Target distance in kilometers.
            
        Returns:
            Dictionary with route details, or None if no valid loop found.
        """
        if len(G) == 0:
            return None

        start_lat, start_lon = start_coords
        start_node = snap_point_to_node(G, start_lat, start_lon)

        candidates: List[Dict] = []
        angles = [i * (360.0 / self.bearings_count) for i in range(self.bearings_count)]

        # Test both 3-waypoint triangle loops and 4-waypoint diamond loops
        for n_points in [3, 4]:
            scale_factor = 1.35 if n_points == 3 else 1.25
            radius_km = target_distance_km / (n_points * scale_factor)

            for base_bearing in angles:
                waypoint_nodes: List[int] = []
                valid_waypoints = True

                for step in range(1, n_points):
                    bearing = (base_bearing + step * (360.0 / n_points)) % 360.0
                    w_lat, w_lon = compute_destination_point(start_lat, start_lon, radius_km, bearing)
                    try:
                        w_node = snap_point_to_node(G, w_lat, w_lon)
                        waypoint_nodes.append(w_node)
                    except Exception:
                        valid_waypoints = False
                        break

                if not valid_waypoints:
                    continue

                # Form full loop sequence: Start -> W1 -> W2 -> ... -> Start
                node_sequence = [start_node] + waypoint_nodes + [start_node]
                full_path: List[int] = []
                route_possible = True

                for i in range(len(node_sequence) - 1):
                    u = node_sequence[i]
                    v = node_sequence[i + 1]
                    try:
                        # Baseline shortest path based solely on edge length
                        leg_path = nx.shortest_path(G, source=u, target=v, weight="length")
                        if full_path:
                            full_path.extend(leg_path[1:])
                        else:
                            full_path.extend(leg_path)
                    except (nx.NetworkXNoPath, nx.NodeNotFound):
                        route_possible = False
                        break

                if not route_possible or len(full_path) < 3:
                    continue

                gain_m, loss_m, dist_m = calculate_path_elevation_gain(G, full_path)
                dist_km = dist_m / 1000.0

                candidates.append({
                    "path_nodes": full_path,
                    "actual_distance_km": dist_km,
                    "elevation_gain_m": gain_m,
                    "elevation_loss_m": loss_m,
                    "waypoints": waypoint_nodes,
                    "distance_error_km": abs(dist_km - target_distance_km),
                    "n_points": n_points,
                    "base_bearing": base_bearing,
                })

        if not candidates:
            return None

        # Naive baseline selection: Pick candidate with minimum absolute distance error
        candidates.sort(key=lambda c: c["distance_error_km"])
        best_candidate = candidates[0]
        return best_candidate
