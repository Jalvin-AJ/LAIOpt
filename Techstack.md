Project Identity

Project Name: LAIOpt (Layout AI Optimizer)

Domain: Electronic Design Automation (EDA) / VLSI Physical Design

Problem Area: Early-Stage Macro Floorplanning

Core Function:
Deterministic and explainable macro placement optimization using a physics-aware Simulated Annealing framework.

1. Core Language & Runtime
Language

Python 3.10+

Why Python?

Python is the de facto standard for:

Academic EDA research

Algorithmic prototyping

Optimization experimentation

It enables rapid iteration, strong readability, and modular design—critical for demonstrating correctness and explainability, which is the core objective of LAIOpt.

2. User Interface & Visualization (Frontend)
Framework: Streamlit

Why Streamlit?

Enables fast creation of interactive engineering tools

No frontend framework overhead (React/Vue not required)

Ideal for hackathon timelines

Keeps focus on algorithmic correctness rather than UI plumbing

Role in LAIOpt

Allows users to edit block and netlist data

Triggers backend optimization

Displays baseline vs optimized layouts

Reports quantitative metrics (cost, wirelength)

Important architectural rule:
Streamlit never modifies optimization logic or results.
It is a pure presentation and control layer.

Visualization Engine: Matplotlib

Why Matplotlib?

Precise, coordinate-accurate plotting

Full control over geometry (rectangles, boundaries)

Deterministic rendering (critical for physical design)

Used to visualize:

Die boundary

Macro blocks with true physical dimensions

Relative thermal/heat indicators (color-coded)

Baseline vs optimized placement comparison

No visual normalization affects backend metrics.

3. Backend Logic & Optimization Engine
Optimization Algorithm: Custom Simulated Annealing (SA)
Why Simulated Annealing?

Macro floorplanning is:

NP-Hard

Highly non-convex

Sensitive to initial placement

Simulated Annealing is a classical and well-accepted solution for such problems because:

It escapes local minima

It does not require training data

It works immediately on unseen designs

This makes LAIOpt a zero-shot optimizer, suitable for arbitrary inputs.

Deterministic Baseline Placement

Before optimization begins, LAIOpt constructs a legal baseline placement:

No overlaps

No boundary violations

Uses real block dimensions

Deterministic ordering

Why this matters

Prevents undefined or misleading starting states

Enables fair baseline vs optimized comparison

Mirrors professional EDA workflows

4. Cost Function Design (Physics-Aware but Honest)

The cost function is the heart of the optimizer and reflects real physical considerations—without fake claims.

Implemented Cost Terms
1. Wirelength (HPWL)

Manhattan (Half-Perimeter Wirelength)

Computed from block centers

Weighted by net importance

Industry relevance:
HPWL is the standard early-stage wirelength proxy.

2. Overlap Penalty (Soft, Area-Based)

Penalizes overlapping macro area

Allows temporary overlaps during search

Strongly discourages overlaps in final solution

Why soft instead of hard?

Enables exploration

Improves convergence

Final result still converges to legal placement

3. Boundary Violation Penalty (Hard)

Any macro exceeding the die incurs a massive penalty

Reason:
Blocks outside the die are physically illegal—no compromise allowed.

About Power and Heat Columns

Power and heat are explicitly modeled as metadata

Used for:

Visualization

Future extensibility

Not falsely claimed as optimized parameters

This design choice avoids misleading claims while keeping the system extensible.

5. Data Handling & Processing
CSV-Based Input Pipeline

Why CSV?

Simple

Transparent

Editable by non-programmers

Matches common EDA data interchange practices

Used for:

Block definitions

Connectivity (netlists)

Data Models (Typed, Validated)

Core data structures:

Block

Net

Die

Each model enforces:

Physical validity

Positive dimensions

Non-negative attributes

6. System Architecture

LAIOpt follows a strict layered architecture:

User Input (CSV / UI)
        ↓
Typed Physical Models
        ↓
Deterministic Baseline Placement
        ↓
Simulated Annealing Optimization
        ↓
Cost Evaluation Loop
        ↓
Final Legal Placement
        ↓
Visualization & Metrics

Architectural Principles

UI and backend are fully decoupled

No hidden state

No silent normalization

Fully testable backend

7. Folder-Level Technology Mapping
Folder	Role
frontend/	Streamlit UI and plotting
backend/core/	Models, baseline, cost, SA engine
backend/adapters/	CSV loaders and serializers
data/	Input CSVs and optional outputs
tests/	Unit tests validating correctness

Even minimal or empty files exist to demonstrate professional structure and extensibility.

8. Dependencies
Runtime Dependencies (requirements.txt)
streamlit>=1.20.0
pandas>=1.5.0
matplotlib>=3.7.0
numpy>=1.24.0

Why These Libraries?
Library	Purpose
Streamlit	Interactive UI
Pandas	Structured data handling
NumPy	Numerical operations
Matplotlib	Geometry-accurate visualization
9. Key Engineering Decisions
Why Not Reinforcement Learning?

RL requires massive datasets

Long training times

Hard to explain

Not suitable for hackathon constraints

Simulated Annealing:

No training

Immediate results

Explainable

Industry-accepted

Deterministic + Stochastic Hybrid

Deterministic baseline ensures legality

Stochastic SA refines solution

This hybrid approach:

Improves convergence

Reduces randomness

Produces stable, defensible results

10. What Makes This Project Strong

No fake AI claims

No misleading optimization metrics

Correct abstraction level

Physically meaningful outputs

Clean separation of concerns

Future-ready architecture

11. Forward Compatibility (Not Implemented Yet)

LAIOpt is intentionally designed to later support:

Thermal-aware optimization

Power delivery constraints

Hierarchical floorplanning

Alternative solvers

DEF/GDSII export

These are future extensions, not falsely claimed features.

12. Final One-Line Summary

LAIOpt is an explainable, deterministic macro floorplanner that demonstrates how physical constraints and connectivity drive early-stage VLSI layout optimization.