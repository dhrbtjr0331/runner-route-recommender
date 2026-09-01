# Walkthrough - PR 2: Baseline Router & Benchmark Evaluation Suite

## Summary of Accomplishments

In **PR 2**, we established the quantitative baseline router and the 12-case benchmark evaluation harness for the **Runnable Route Recommender (RRR)** agent:

1. **Baseline Router (`src/baseline/baseline_router.py`):**
   - Implemented `BaselineRouter` using multi-bearing geometric polygon waypoint generation (triangles and diamonds).
   - Utilizes standard distance-weighted shortest path ($S \to W_1 \to W_2 \to \dots \to S$).
   - Completely unguided by elevation profiles, semantic POIs, or negative avoid-zones, providing a fair starting comparison.

2. **Benchmark Test Suite (`src/eval/test_cases.py`):**
   - Defined 12 comprehensive benchmark test cases spanning 3 distinct topographies:
     - **Coastal / Flat**: Santa Monica Pier & Venice Beach (C01, C02, C03, C10, C12).
     - **Trail / Mountainous**: Griffith Park LA (C04, C05, C06).
     - **Dense Urban Grid & Parks**: Central Park NYC & Downtown LA (C07, C08, C09, C11).
   - Included the showcase hard case: **C12 (Santa Monica Palisades 8k Easy with strict elevation and PCH avoid constraints)**.

3. **Quantitative Metrics Engine (`src/eval/metrics.py`):**
   - **Distance Score ($S_{\text{dist}}$):** $\max(0, 1 - \frac{|D_{\text{act}} - D_{\text{tgt}}|}{0.20 \cdot D_{\text{tgt}}})$.
   - **Elevation Score ($S_{\text{elev}}$):** Graded compliance against easy ($\le 35\text{m}/5\text{km}$), moderate ($35\text{m}-90\text{m}$), and hard ($>90\text{m}$) ceilings/floors.
   - **Constraint Score ($S_{\text{poi}}$):** Positive POI traversal ratio minus penalties for traversing avoid-zones.
   - **Composite Score ($S_{\text{total}}$):** $0.35 \cdot S_{\text{dist}} + 0.35 \cdot S_{\text{elev}} + 0.30 \cdot S_{\text{poi}}$.

4. **Automated Evaluation Runner (`src/eval/evaluate.py`):**
   - Implemented CLI runner with automated scoring, summary table formatting, and JSON export (`data/eval_baseline.json`).

---

## Baseline Benchmark Results

```
==========================================================================================
  RUNNABLE ROUTE RECOMMENDER — BENCHMARK EVALUATION [BASELINE]
==========================================================================================
Case  | Location           | Tgt(km) | Act(km) | Diff     | Gain(m) | S_dist | S_elev | S_poi  | S_total
------------------------------------------------------------------------------------------
C01   | santa_monica_pier  | 5.0     | 5.0     | easy     | 0       | 1.00   | 1.00   | 0.00   | 0.70  
C02   | santa_monica_pier  | 10.0    | 9.9     | moderate | 0       | 0.94   | 0.00   | 0.25   | 0.40  
C03   | santa_monica_pier  | 8.0     | 8.0     | easy     | 0       | 1.00   | 1.00   | 0.00   | 0.70  
C04   | griffith_park      | 6.0     | 7.6     | hard     | 0       | 0.00   | 0.00   | 0.20   | 0.06  
C05   | griffith_park      | 5.0     | 5.8     | easy     | 0       | 0.25   | 1.00   | 0.00   | 0.44  
C06   | griffith_park      | 12.0    | 17.6    | hard     | 0       | 0.00   | 0.00   | 0.20   | 0.06  
C07   | central_park_nyc   | 5.0     | 5.8     | easy     | 9       | 0.25   | 1.00   | 0.00   | 0.44  
C08   | central_park_nyc   | 9.7     | 10.0    | moderate | 18      | 0.86   | 0.35   | 0.25   | 0.50  
C09   | central_park_nyc   | 4.0     | 4.5     | easy     | 7       | 0.38   | 1.00   | 0.00   | 0.48  
C10   | venice_beach       | 6.0     | 6.2     | easy     | 0       | 0.88   | 1.00   | 0.50   | 0.81  
C11   | downtown_la        | 5.0     | 6.0     | moderate | 0       | 0.04   | 0.00   | 0.00   | 0.01  
C12   | santa_monica_pier  | 8.0     | 8.0     | easy     | 0       | 1.00   | 1.00   | 0.25   | 0.77  
------------------------------------------------------------------------------------------
OVERALL MEAN SCORES                              |         | 0.55   | 0.61   | 0.14   | 0.45  
==========================================================================================
```

### Key Quantitative Findings:
- **Starting Baseline Composite Score: 0.45**
- **Distance Accuracy ($S_{\text{dist}}$): 0.55** — Distance matching is erratic in non-grid trail systems.
- **Elevation Match ($S_{\text{elev}}$): 0.61** — Accidental compliance on flat coastal paths, but complete failure (0.00) on mountainous climbing targets.
- **Constraint Satisfaction ($S_{\text{poi}}$): 0.14** — The baseline completely ignores semantic natural language requests and negative avoid areas.

---

## Test & Verification Results

```bash
$ pytest tests/test_router.py tests/test_graph.py -v
============================= test session starts ==============================
collected 9 items

tests/test_router.py::test_benchmark_cases_count PASSED                  [ 11%]
tests/test_router.py::test_distance_accuracy_metric PASSED               [ 22%]
tests/test_router.py::test_elevation_compliance_metric PASSED            [ 33%]
tests/test_router.py::test_constraint_scoring PASSED                     [ 44%]
tests/test_router.py::test_baseline_router_synthetic_graph PASSED        [ 55%]
tests/test_graph.py::test_geocoding_presets PASSED                       [ 66%]
tests/test_graph.py::test_haversine_and_destination_point PASSED         [ 77%]
tests/test_graph.py::test_synthetic_graph_elevation_and_gain PASSED      [ 88%]
tests/test_graph.py::test_cache_key_generation PASSED                    [100%]

======================== 9 passed in 23.55s ========================
```

---

## Next Steps (PR 3)

With the baseline firmly established and measured at **0.45**, **PR 3** will introduce the **Intelligent Agent Workflow**:
1. LLM structured constraint parser & geocoder.
2. Constraint-weighted polygon loop generator with impedance matrices.
3. Route Verifier & Reflection Loop (self-correction on constraint / elevation violations).
4. Trajectory logging (`trajectories/trajectory.jsonl`).

