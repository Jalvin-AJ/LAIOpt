# MASTER_PROJECT_CONTEXT.md

---

## Project Overview

LAIOpt (AI-Assisted Chip Layout Optimization) is a software system intended to demonstrate a **correct, explainable, early-stage VLSI macro floorplanning workflow**. The target users are students, researchers, and reviewers who need to understand *how macro placement optimization works*, not a production-grade EDA tool. The system takes realistic physical inputs (macro sizes, connectivity, die dimensions) and produces **legal, deterministic macro placements** using optimization logic (primarily Simulated Annealing). A browser-based UI visualizes baseline versus optimized layouts and reports quantitative metrics. The core objective is **correctness, physical plausibility, and stability**, not visual flair or artificial “AI” claims.

---

## Final Feature Set

### Core Features (Must Exist)

- CSV-based input for:
  - Macro blocks (ID, width, height, power level, heat level)
  - Connectivity (nets with weights)
- Explicit die definition (width, height)
- Deterministic baseline placement:
  - No overlaps
  - Respects die boundaries
  - Uses real block dimensions
- Optimization engine based on Simulated Annealing:
  - Legal move generation
  - Acceptance based on cost comparison
  - Deterministic behavior aside from controlled randomness
- Cost function including:
  - Wirelength (Manhattan / HPWL-style)
  - Overlap penalty (hard constraint)
  - Boundary violation penalty (hard constraint)
- Stable results:
  - Same input produces comparable output
  - No artificial forced “improvement”
- Streamlit browser UI:
  - Editable input tables
  - Run optimization button
  - Side-by-side baseline vs optimized visualization
  - Quantitative metric comparison
- Clear separation between UI and backend logic
- Modular backend with unit tests for:
  - Models
  - Baseline placement
  - Cost computation
  - Simulated Annealing engine

---

### Deferred or Discarded Ideas (Do NOT implement)

- Reinforcement Learning / Q-Learning agents
- Claims of trained ML models without training data
- Forcing positive improvement in every run
- Randomized grid placement unrelated to macro size
- Fake thermal or power optimization results
- Arbitrary normalization affecting metrics
- Overlapping macros in final output
- Negative or misleading “improvement” metrics
- Real thermal simulation
- Timing-aware placement
- Detailed routing or congestion modeling
- GDSII / DEF export
- React + FastAPI frontend (postponed)
- Database persistence

---

## System Architecture

LAIOpt follows a **strict layered architecture**:

- **Frontend (Streamlit UI)**  
  Responsible only for:
  - Loading input CSVs
  - Allowing user edits
  - Triggering optimization
  - Displaying plots and metrics  
  The frontend must never alter optimization logic or results.

- **Backend Core Engine**  
  Contains all placement intelligence:
  - Physical models
  - Baseline placement
  - Cost functions
  - Simulated Annealing optimizer  
  This layer is fully testable without the UI.

- **Data Layer (Files only)**  
  - CSV files for input
  - Optional CSV/JSON outputs for results  
  No database is used.

There are **no external service integrations** and **no cloud components**.

---

## Folder Structure and Responsibilities

```

laiopt/
│
├── frontend/
│   ├── app.py
│   │   Streamlit UI entry point. Handles user interaction and visualization only.
│   ├── visualization.py
│   │   Safe plotting utilities (bounded figure size, no normalization affecting metrics).
│   └── ui_config.py
│       UI constants and presentation settings.
│
├── backend/
│   ├── core/
│   │   ├── models.py
│   │   │   Defines Block, Net, Die data structures.
│   │   ├── baseline.py
│   │   │   Deterministic initial placement logic.
│   │   ├── cost.py
│   │   │   Cost functions: wirelength, overlap, boundary penalties.
│   │   └── sa_engine.py
│   │       Simulated Annealing optimizer using the cost functions.
│   │
│   └── adapters/
│       ├── csv_loader.py
│       │   Converts CSV input into internal models.
│       └── serializer.py
│           Converts placements into UI-friendly output.
│
├── data/
│   ├── FINAL_blocks.csv
│   ├── FINAL_connections.csv
│   └── outputs/
│
├── tests/
│   ├── test_models.py
│   ├── test_baseline.py
│   ├── test_cost.py
│   └── test_sa.py
│
└── MASTER_PROJECT_CONTEXT.md

```

---

## Data Flow and State Management

1. User edits CSV data in the UI.
2. CSV files are saved to disk.
3. Backend loads CSVs into Block, Net, and Die models.
4. Baseline placement generates a legal starting layout.
5. Simulated Annealing iteratively proposes moves and evaluates cost.
6. Best placement and cost are returned.
7. UI computes metrics from placements and renders plots.

**State management rules:**
- All authoritative state lives in memory during execution.
- CSV files are the only persistent storage.
- UI holds no hidden or duplicated state.
- Visualization normalization (if any) is strictly display-only.

---

## API Contracts and Interfaces

### Placement Definition

A Placement is defined as:
- A dictionary mapping block_id → (x, y)
- Coordinates represent the bottom-left corner of the macro
- Units are consistent with input dimensions
- Placement must represent a fully legal configuration unless explicitly stated otherwise

### Backend Interfaces (Internal)

- `baseline_placement(blocks, die) -> Placement`
  - Input: list of Block objects, Die
  - Output: dict `{block_id: (x, y)}`

- `total_cost(placement, blocks, nets, die) -> float`
  - Input: placement dict, blocks list, nets list, die
  - Output: scalar cost

- `simulated_annealing(blocks, nets, die) -> (Placement, cost)`
  - Input: blocks, nets, die
  - Output: optimized placement and its cost

### Frontend ↔ Backend

- Frontend calls backend functions directly (same process).
- No HTTP APIs are used in the current build.

---

## Constraints and Non-Negotiable Rules

- No overlapping macros in final placement.
- All macros must fit entirely within the die.
- Macro dimensions must affect placement geometry.
- Metrics must reflect true physical distances.
- UI must never modify backend results.
- Normalization must not affect cost computation.
- Same input must not yield arbitrary, unjustified randomness.
- No “AI” claims without real optimization logic.
- Backend must be testable independently of UI.
- Plots must stay within safe image size limits.
- All stochastic behavior (e.g., simulated annealing moves) must be governed by an explicit, user-controllable random seed.
- Random seed defaults must be documented and reproducible.
- No hidden randomness is allowed.
---

## Known Risks, Gaps, and Inconsistencies

- Early conversation explored RL/Q-learning, later discarded.
- Initial Streamlit versions mixed visualization normalization with metrics (corrected later).
- Some intermediate code versions produced random or unstable outputs (now stabilized).
- Thermal and power concepts exist in data but are not yet enforced as optimization pressure.
- Small test cases may show no improvement, which is correct but can be misinterpreted.
- Folder structure evolved during development, causing temporary import errors.
- Users may expect “AI” behavior beyond current deterministic SA logic.

---

## Future Extensions (Not Part of Current Build)

- Thermal-aware cost terms using real models
- Power delivery proximity constraints
- Timing-aware placement
- Macro clustering / hierarchy
- MILP or force-directed solvers
- JSON input/output support
- React + FastAPI frontend
- Persistent storage or experiment tracking
- DEF/GDSII export

---

**This document is the SINGLE SOURCE OF TRUTH.  
All future development must conform to it.**
```
