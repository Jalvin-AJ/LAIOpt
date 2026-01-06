"""
LAIOpt Frontend — Professional Input Compiler + Visualization UI

This UI provides:
- Editable block table (human-friendly)
- Editable net table (human-friendly)
- Explicit compilation to canonical backend models
- Strict backend execution (baseline + SA)
- Deterministic, explainable results
"""

import io
import pandas as pd
import streamlit as st
from collections import defaultdict

from laiopt.backend.adapters.csv_loader import load_blocks_csv, load_nets_csv
from laiopt.backend.core.baseline import baseline_place
from laiopt.backend.core.sa_engine import simulated_annealing
from laiopt.backend.core.cost import total_cost
from laiopt.frontend.visualization import plot_placement
from laiopt.backend.core.models import Die


# -----------------------------
# UI → Canonical Compilers
# -----------------------------

ROLE_BASE_SIZES = {
    "CPU": (10, 10),
    "Accelerator": (10, 10),
    "Cache": (8, 8),
    "Memory": (8, 8),
    "DSP": (7, 7),
    "Display": (7, 7),
    "IO": (6, 6),
    "Network": (6, 6),
}

def compile_blocks(block_df: pd.DataFrame) -> io.StringIO:
    rows = []
    for _, r in block_df.iterrows():
        base_w, base_h = ROLE_BASE_SIZES.get(str(r["role"]), (6, 6))
        scale = 1.0 + 0.15 * (int(r["connectivity"]) - 1)

        rows.append({
            "id": str(r["block_id"]),
            "width": round(base_w * scale, 2),
            "height": round(base_h * scale, 2),
            "power": int(r["power"]),
            "heat": int(r["heat"]),
        })

    df = pd.DataFrame(rows)
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return buf


def compile_nets(net_df: pd.DataFrame) -> io.StringIO:
    net_map = defaultdict(list)
    weights = {}

    for _, r in net_df.iterrows():
        net = str(r["net_id"])
        net_map[net].append(str(r["block_a"]))
        net_map[net].append(str(r["block_b"]))
        weights[net] = float(r["weight"])

    rows = []
    for net, blocks in net_map.items():
        rows.append({
            "name": net,
            "blocks": ",".join(sorted(set(blocks))),
            "weight": weights[net],
        })

    df = pd.DataFrame(rows)
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return buf


# -----------------------------
# Streamlit UI
# -----------------------------

st.set_page_config(layout="wide", page_title="LAIOpt")
st.title("LAIOpt — Explainable AI-Assisted Floorplanning")
st.caption("Professional-grade UI with strict backend guarantees")

with st.expander("How does the optimization work?", expanded=False):
    st.markdown("""
    **Baseline Placement:** A deterministic, legal initial placement generated using a simple row-wise strategy. 
    This serves as a reference point for comparison and ensures all blocks are placed without overlaps or boundary violations.
    
    **Simulated Annealing Exploration:** The optimizer explores alternative arrangements by randomly selecting between 
    two move types: relocating a single block or swapping two blocks. Each move is evaluated against the cost function, 
    and moves are accepted probabilistically based on temperature and cost improvement.
    
    **Legal Moves and Best-Solution Tracking:** All proposed moves are validated to ensure no overlaps or boundary violations. 
    The algorithm tracks both the current state and the best solution seen, ensuring the final result is the optimal 
    placement discovered during the optimization process.
    """)

st.sidebar.header("Die Parameters")
die_width = st.sidebar.number_input("Die Width", min_value=10.0, value=100.0)
die_height = st.sidebar.number_input("Die Height", min_value=10.0, value=100.0)
run_button = st.sidebar.button("Run Optimization")


# -----------------------------
# Block Table
# -----------------------------

st.subheader("Blocks (Editable)")

block_df = st.data_editor(
    pd.DataFrame([
        {"block_id": "B1", "role": "CPU", "connectivity": 3, "power": 3, "heat": 3},
        {"block_id": "B2", "role": "Cache", "connectivity": 3, "power": 2, "heat": 2},
        {"block_id": "B3", "role": "Memory", "connectivity": 3, "power": 3, "heat": 2},
        {"block_id": "B4", "role": "Accelerator", "connectivity": 3, "power": 3, "heat": 3},
        {"block_id": "B5", "role": "IO", "connectivity": 1, "power": 1, "heat": 1},
    ]),
    num_rows="dynamic",
    use_container_width=True
)


# -----------------------------
# Net Table
# -----------------------------

st.subheader("Nets (Editable)")

net_df = st.data_editor(
    pd.DataFrame([
        {"net_id": "N1", "block_a": "B1", "block_b": "B2", "weight": 1.0},
        {"net_id": "N2", "block_a": "B1", "block_b": "B3", "weight": 2.0},
        {"net_id": "N3", "block_a": "B4", "block_b": "B1", "weight": 1.5},
    ]),
    num_rows="dynamic",
    use_container_width=True
)


# -----------------------------
# Execution
# -----------------------------

if run_button:
    die = Die(die_width, die_height)

    blocks_csv = compile_blocks(block_df)
    nets_csv = compile_nets(net_df)

    blocks = load_blocks_csv(blocks_csv)
    nets = load_nets_csv(nets_csv)

    baseline = baseline_place(blocks, die)
    baseline_cost = total_cost(baseline, blocks, nets, die)

    optimized, opt_cost, cost_history = simulated_annealing(
    blocks, nets, die, random_seed=42
)


    st.subheader("Placement Comparison")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Baseline")
        st.pyplot(plot_placement(baseline, blocks, die, "Baseline"))

    with col2:
        st.markdown("### Optimized")
        st.pyplot(plot_placement(optimized, blocks, die, "Optimized"))

    st.subheader("Metrics")
    st.caption("ℹ️ Total cost = Wirelength + Thermal spreading penalty")
    
    st.metric("Baseline Cost", f"{baseline_cost:.2f}")
    st.metric("Optimized Cost", f"{opt_cost:.2f}")
    st.metric("Improvement", f"{baseline_cost - opt_cost:.2f}")
    
    if abs(opt_cost - baseline_cost) < 1e-6:
        st.info("Baseline is already locally optimal under the current cost model.")
