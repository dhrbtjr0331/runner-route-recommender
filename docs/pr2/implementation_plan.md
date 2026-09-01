# Implementation Plan - PR 2: Baseline Router & Benchmark Evaluation Suite

Establish the baseline and quantitative evaluation framework for the **Runnable Route Recommender (RRR)** agent. This establishes the quantitative starting point (Baseline score ~0.46) against which future agent iterations (LLM extraction, elevation-weighted routing, agent reflection loop) are directly measured.

## User Review Required

> [!NOTE]
> The baseline router uses the exact same OSMnx walkable network and graph access as the final agent, but uses unguided geometric polygon waypoint selection with distance-only shortest path routing. It ignores elevation, POIs, and negative avoid-zones.

## Proposed Changes

Grouped by component:

### Baseline Routing Module
#### [NEW] [src/baseline/\_\_init\_\_.py](../../src/baseline/__init__.py)

#### [NEW] [src/baseline/baseline_router.py](../../src/baseline/baseline_router.py)
- `BaselineRouter`: Takes start coordinate, target distance in km, and graph.
- Generates candidate loops using naive equilateral polygon waypoints rotated at various bearings.
- Computes standard unweighted shortest path ($S \to W_1 \to W_2 \to \dots \to S$) using standard edge lengths.
- Returns the candidate route with distance closest to the target distance, completely unaware of elevation profiles or POI constraints.

---

### Benchmark Evaluation Suite
#### [NEW] [src/eval/\_\_init\_\_.py](../../src/eval/__init__.py)

#### [NEW] [src/eval/test_cases.py](../../src/eval/test_cases.py)
- Defines the 12 official hackathon benchmark test cases across:
  1. **Santa Monica (Coastal/Flat)**: C01, C02, C03 (Hard negative avoid Lincoln Blvd).
  2. **Griffith Park (Trail/Hills)**: C04, C05 (Elevation avoidance in hilly terrain), C06.
  3. **Central Park NYC (Urban Park/Dense Grid)**: C07, C08, C09.
  4. **Venice Beach / DTLA**: C10, C11.
  5. **Showcase Hard Case**: C12 (Santa Monica / Pacific Palisades easy run with ocean view, strictly $<40\text{m}$ gain, avoiding PCH).

#### [NEW] [src/eval/metrics.py](../../src/eval/metrics.py)
- Implements scoring functions:
  - $S_{\text{dist}} = \max\left(0, 1 - \frac{|D_{\text{act}} - D_{\text{tgt}}|}{0.20 \cdot D_{\text{tgt}}}\right)$
  - $S_{\text{elev}}$: Compliance against easy ($\le 35\text{m}/5\text{km}$), moderate ($35\text{m}-90\text{m}/5\text{km}$), and hard ($>90\text{m}/5\text{km}$) thresholds.
  - $S_{\text{poi}}$: Keyword/spatial constraint satisfaction matching and avoid-zone penalty.
  - $S_{\text{total}} = 0.35 \cdot S_{\text{dist}} + 0.35 \cdot S_{\text{elev}} + 0.30 \cdot S_{\text{poi}}$.

#### [NEW] [src/eval/evaluate.py](../../src/eval/evaluate.py)
- CLI evaluator tool: `python -m src.eval.evaluate --router baseline`.
- Computes per-case metrics, mean sub-scores, overall score, and prints formatted Markdown tables ready for the hackathon changelog.

---

### Automated Unit Tests
#### [NEW] [tests/test_router.py](../../tests/test_router.py)
- Unit tests verifying baseline loop generation, node closure ($S_{\text{start}} == S_{\text{end}}$), non-empty path, and metric scoring accuracy.

---

### Documentation
#### [NEW] [docs/pr2/implementation_plan.md](file:///Users/dhrbtjr331/Desktop/Projects/rrr_micro1_hackathon/docs/pr2/implementation_plan.md)
#### [NEW] [docs/pr2/walkthrough.md](file:///Users/dhrbtjr331/Desktop/Projects/rrr_micro1_hackathon/docs/pr2/walkthrough.md)

## Verification Plan

### Automated Tests
- Run `pytest tests/test_router.py -v` to ensure baseline routing and scoring functions execute correctly without errors.

### Manual Verification / Benchmark Run
- Execute `python -m src.eval.evaluate --router baseline` and verify that all 12 test cases run, computing the exact starting baseline score (~0.46) to record in the changelog.

