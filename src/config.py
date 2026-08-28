"""Configuration settings and constants for Runnable Route Recommender (RRR)."""

import os
from pathlib import Path
from typing import Dict, Tuple

# Base paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
OSM_CACHE_DIR = CACHE_DIR / "osm"
ELEVATION_CACHE_DIR = CACHE_DIR / "elevation"
OUTPUT_DIR = DATA_DIR / "sample_outputs"

# Ensure directories exist
for p in [DATA_DIR, CACHE_DIR, OSM_CACHE_DIR, ELEVATION_CACHE_DIR, OUTPUT_DIR]:
    p.mkdir(parents=True, exist_ok=True)

# APIs
OPEN_METEO_ELEVATION_URL = "https://api.open-meteo.com/v1/elevation"

# Fixed benchmark city presets (lat, lon)
BENCHMARK_PRESETS: Dict[str, Tuple[float, float]] = {
    "santa_monica_pier": (34.0099, -118.4965),
    "griffith_park": (34.1365, -118.2942),
    "central_park_nyc": (40.7829, -73.9654),
    "venice_beach": (33.9850, -118.4695),
    "downtown_la": (34.0537, -118.2427),
}

# Elevation Difficulty Thresholds (cumulative gain in meters per 5km run)
ELEVATION_THRESHOLDS = {
    "easy": {"max_gain_m": 35.0, "description": "Flat or gently rolling (under 35m per 5km)"},
    "moderate": {"min_gain_m": 35.0, "max_gain_m": 90.0, "description": "Moderate hills (35m-90m per 5km)"},
    "hard": {"min_gain_m": 90.0, "description": "Steep hill climbs (>90m per 5km)"},
}

# Routing Defaults
DEFAULT_DISTANCE_TOLERANCE = 0.10  # +/- 10%
DEFAULT_WALK_NETWORK_TYPE = "walk"
DEFAULT_GRAPH_RADIUS_PADDING = 1.35  # Buffer graph download radius relative to loop radius
