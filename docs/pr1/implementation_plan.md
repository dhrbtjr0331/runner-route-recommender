# Implementation Plan - PR 1: Core Foundation & Spatial Graph Infrastructure

Build the spatial data foundation for the **Runnable Route Recommender (RRR)** agent. This includes project configuration, pinned dependencies, OpenStreetMap (OSM) walkable graph extraction and local caching, elevation enrichment via the Open-Meteo elevation API, geocoding utilities, and automated unit tests.

## User Review Required

> [!NOTE]
> Open-Meteo provides a free, keyless elevation API that allows batch queries of coordinate pairs. We implement local caching of OSM graphs and elevation data to ensure fast, deterministic offline execution for the benchmark test cases.

## Proposed Changes

Grouped by component:

### Project Packaging & Dependencies
#### [NEW] [requirements.txt](../../requirements.txt)
- Pin core dependencies: `osmnx`, `networkx`, `shapely`, `geopandas`, `requests`, `geopy`, `pydantic`, `folium`, `matplotlib`, `gpxpy`, `python-dotenv`, `pytest`.

#### [NEW] [pyproject.toml](../../pyproject.toml)
- Standard Python packaging file for editable installs (`pip install -e .`).

#### [NEW] [.gitignore](../../.gitignore)
- Ignore `.venv`, `__pycache__`, `.pytest_cache`, `.env`, `data/cache/`, etc.

---

### Core Configuration & Data Tooling
#### [NEW] [src/\_\_init\_\_.py](../../src/__init__.py)

#### [NEW] [src/config.py](../../src/config.py)
- Configuration parameters: cache directories (`data/cache/osm`, `data/cache/elevation`), default coordinates for fixed benchmark cities (Santa Monica, Griffith Park, Central Park), Open-Meteo API URL, logging settings.

#### [NEW] [src/tools/\_\_init\_\_.py](../../src/tools/__init__.py)

#### [NEW] [src/tools/osm_tool.py](../../src/tools/osm_tool.py)
- Graph extraction using `osmnx.graph_from_point` (network_type='walk').
- Largest strongly connected component extraction (`ox.truncate.largest_component`).
- Graph cleaning, edge bearing computation, and GraphML/pickle disk caching for instant offline reuse.

#### [NEW] [src/tools/elevation_tool.py](../../src/tools/elevation_tool.py)
- Batch node elevation fetching from Open-Meteo Elevation API in chunks of $\le 100$ nodes with rate-limiting throttling.
- Node elevation attribution (`node['elevation']`) and edge grade calculation: $\text{grade} = \frac{\text{elev}_v - \text{elev}_u}{\text{length}_{u,v}}$.
- Cumulative elevation gain calculation along any path sequence.
- Local cache persistence for elevation data.

#### [NEW] [src/tools/geocoding_tool.py](../../src/tools/geocoding_tool.py)
- Geocoding start location addresses/landmarks to `(lat, lon)` using `geopy.geocoders.Nominatim` with offline fallbacks for benchmark cities.
- Snapping coordinates to nearest graph nodes via `ox.distance.nearest_nodes`.

---

### Automated Unit Tests
#### [NEW] [tests/\_\_init\_\_.py](../../tests/__init__.py)

#### [NEW] [tests/test_graph.py](../../tests/test_graph.py)
- Test OSM graph loading and caching.
- Test Open-Meteo elevation fetching and edge grade attribution.
- Test cumulative ascent calculation.
- Test geocoding tool and node snapping.

## Verification Plan

### Automated Tests
- Run `pytest tests/test_graph.py -v` to ensure all graph extraction, elevation calculation, and caching components pass.

### Manual Verification
- Run a standalone cache script that fetches graphs around Santa Monica Pier and Griffith Park, enriches them with elevations, and verifies cache creation in `data/cache/`.

