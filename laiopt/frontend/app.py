"""
LAIOpt Frontend — Explainable AI-Assisted Floorplanning
Professional UI with Wall Attraction & Thermal Physics support.
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
# Compilers
# -----------------------------

def compile_blocks(block_df: pd.DataFrame) -> io.StringIO:
    rows = []
    for _, r in block_df.iterrows():
        rows.append({
            "id": str(r["block_id"]),
            "width": float(r["width"]),
            "height": float(r["height"]),
            "power": int(r["power"]),
            "heat": int(r["heat"]),
            "role": str(r["role"]) 
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
# Streamlit UI Configuration
# -----------------------------

st.set_page_config(layout="wide", page_title="LAIOpt")

# --- Header Section ---
st.title("LAIOpt — Explainable AI-Assisted Floorplanning")
st.caption("Professional-grade UI with strict backend guarantees | Physics: Wall Attraction & Thermal Spreading")

with st.expander("ℹ️ How does the optimization work?", expanded=False):
    st.markdown("""
    **1. Smart Wall-Aware Baseline:** Instead of a random start, the system generates a deterministic, legal initial placement using a **Less Flexibility First (LFF)** heuristic. It prioritizes placing high-power blocks on the periphery (walls/corners) to satisfy power integrity constraints immediately.

    **2. Simulated Annealing Exploration:** The optimizer refines this layout by exploring the solution space stochastically. It accepts "worse" moves early on (High Temp) to escape local optima, then converges to a precise solution (Low Temp) using three move types:
    * **Displacement (50%):** Moving a single block to a new coordinate.
    * **Swap (35%):** Exchanging positions of two blocks.
    * **Rotation (15%):** Rotating a block 90 degrees.

    **3. Multi-Objective Cost Function:** The engine minimizes a weighted sum of **Wirelength (HPWL)**, **Overlap Penalty**, **Thermal Spreading** (preventing hotspots), and **Boundary Attraction** (forcing heavy blocks to the edge).
    """)

st.sidebar.header("Die Parameters")
die_width = st.sidebar.number_input("Die Width", min_value=50.0, value=100.0)
die_height = st.sidebar.number_input("Die Height", min_value=50.0, value=100.0)
run_button = st.sidebar.button("Run Optimization")


# -----------------------------

# Block Table (20-Block Config for Wall Attraction)

# -----------------------------



st.subheader("Blocks (20-Block Config)")



block_df = st.data_editor(

    pd.DataFrame([

        # --- THE HEAVYWEIGHTS (High Heat/Power) ---

        {"block_id": "S7",  "role": "CPU_Cluster", "width": 28.0, "height": 28.0, "power": 3, "heat": 3},

        {"block_id": "S4",  "role": "GPU_Core",    "width": 28.0, "height": 28.0, "power": 3, "heat": 3},

        {"block_id": "S13", "role": "PCIe_Root",   "width": 25.0, "height": 25.0, "power": 3, "heat": 3},

        {"block_id": "S14", "role": "NPU_Engine",  "width": 25.0, "height": 25.0, "power": 3, "heat": 3},



        # --- THE MEMORY BACKBONE (Victims) ---

        {"block_id": "S2",  "role": "L3_Cache",    "width": 20.0, "height": 20.0, "power": 1, "heat": 1},

        {"block_id": "S15", "role": "Sys_SRAM",    "width": 30.0, "height": 10.0, "power": 1, "heat": 1},



        # --- THE PERIPHERAL WALLS (Long & Thin) ---

        {"block_id": "S6",  "role": "NoC_Left",    "width": 8.0,  "height": 70.0, "power": 1, "heat": 1},

        {"block_id": "S12", "role": "NoC_Right",   "width": 8.0,  "height": 70.0, "power": 1, "heat": 1},

        {"block_id": "S8",  "role": "DDR_Top",     "width": 60.0, "height": 8.0,  "power": 2, "heat": 2},

        {"block_id": "S11", "role": "DDR_Bot",     "width": 60.0, "height": 8.0,  "power": 2, "heat": 2},



        # --- MEDIUM LOGIC BLOCKS ---

        {"block_id": "S5",  "role": "DSP_Unit",    "width": 15.0, "height": 15.0, "power": 2, "heat": 2},

        {"block_id": "S10", "role": "Video_Enc",   "width": 15.0, "height": 15.0, "power": 2, "heat": 2},

        {"block_id": "S16", "role": "Modem_5G",    "width": 18.0, "height": 12.0, "power": 2, "heat": 2},

        {"block_id": "S17", "role": "ISP_Cam",     "width": 12.0, "height": 18.0, "power": 2, "heat": 2},



        # --- SMALL CONTROLLERS (Fillers) ---

        {"block_id": "S3",  "role": "Power_Mgt",   "width": 10.0, "height": 10.0, "power": 1, "heat": 1},

        {"block_id": "S1",  "role": "Sensors",     "width": 10.0, "height": 10.0, "power": 1, "heat": 1},

        {"block_id": "S9",  "role": "Security",    "width": 12.0, "height": 12.0, "power": 1, "heat": 1},

        {"block_id": "S18", "role": "Audio_Sub",   "width": 10.0, "height": 10.0, "power": 1, "heat": 1},

        {"block_id": "S19", "role": "USB_Ctrl",    "width": 10.0, "height": 10.0, "power": 1, "heat": 1},

        {"block_id": "S20", "role": "GPIO_Mux",    "width": 15.0, "height": 5.0,  "power": 1, "heat": 1},

    ]),

    num_rows="dynamic",

    use_container_width=True,

    column_config={

        "width": st.column_config.NumberColumn("Width", min_value=1.0, required=True),

        "height": st.column_config.NumberColumn("Height", min_value=1.0, required=True),

        "power": st.column_config.NumberColumn("Power", min_value=0, max_value=3),

        "heat": st.column_config.NumberColumn("Heat", min_value=0, max_value=3),

    }

)



# -----------------------------

# Net Table (20-Block Config)

# -----------------------------



st.subheader("Nets (20-Block Config)")



net_df = st.data_editor(

    pd.DataFrame([

        # --- CRITICAL BUS (The "Gravity" pulling inward) ---

        {"net_id": "N1", "block_a": "S7",  "block_b": "S2", "weight": 20.0},

        {"net_id": "N2", "block_a": "S4",  "block_b": "S2", "weight": 20.0},

        {"net_id": "N3", "block_a": "S14", "block_b": "S2", "weight": 20.0},

        {"net_id": "N4", "block_a": "S13", "block_b": "S15","weight": 15.0},



        # --- PERIPHERAL ANCHORS (Helping the "Wall Attraction") ---

        {"net_id": "N5", "block_a": "S7",  "block_b": "S8", "weight": 12.0},

        {"net_id": "N6", "block_a": "S4",  "block_b": "S11","weight": 12.0},

        {"net_id": "N7", "block_a": "S6",  "block_b": "S7", "weight": 10.0},

        {"net_id": "N8", "block_a": "S12", "block_b": "S4", "weight": 10.0},

       

        # --- MEDIA CLUSTER ---

        {"net_id": "N9", "block_a": "S10", "block_b": "S17", "weight": 8.0},

        {"net_id": "N10","block_a": "S17", "block_b": "S15", "weight": 8.0},

        {"net_id": "N11","block_a": "S5",  "block_b": "S18", "weight": 5.0},



        # --- COMMS CLUSTER ---

        {"net_id": "N12","block_a": "S16", "block_b": "S9",  "weight": 8.0},

        {"net_id": "N13","block_a": "S16", "block_b": "S6",  "weight": 8.0},



        # --- LOW SPEED CONTROL ---

        {"net_id": "N14","block_a": "S1",  "block_b": "S3",  "weight": 3.0},

        {"net_id": "N15","block_a": "S19", "block_b": "S13", "weight": 5.0},

        {"net_id": "N16","block_a": "S20", "block_b": "S3",  "weight": 3.0},

    ]),

    num_rows="dynamic",

    use_container_width=True

)

# -----------------------------
# Execution Logic
# -----------------------------

if run_button:
    die = Die(die_width, die_height)
    blocks = load_blocks_csv(compile_blocks(block_df))
    nets = load_nets_csv(compile_nets(net_df))

    # --- 1. Smart Baseline ---
    # We pass 'nets' so the baseline can use connectivity scoring
    baseline = baseline_place(blocks, die, nets)
    
    # Calculate baseline cost for comparison
    base_orient = {b.id: False for b in blocks}
    base_cost = total_cost(baseline, base_orient, blocks, nets, die)

    # --- 2. Batch Optimization (3 Targeted Runs) ---
    temperatures = [500.0, 1000.0, 2000.0]
    
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    st.write("### Optimization Batch Results")
    
    for i, temp in enumerate(temperatures):
        status_text.text(f"Running Strategy {i+1}/3: Initial Temp = {temp}...")
        
        r_place, r_cost, r_hist, r_orient = simulated_annealing(
            blocks, nets, die,
            initial_temperature=temp,
            alpha=0.99,   
            k_steps=50,   
            random_seed=42 + i
        )
        
        results.append({
            "run_id": f"Run {i+1}",
            "temp": temp,
            "cost": r_cost,
            "placement": r_place,
            "orientation": r_orient
        })
        progress_bar.progress((i + 1) / len(temperatures))

    status_text.text("Optimization Complete.")
    
    # --- 3. Pick the Winner ---
    results.sort(key=lambda x: x["cost"])
    winner = results[0]
    
    # Display Result Summary Table (Hidden History)
    res_df = pd.DataFrame([{k: v for k, v in r.items() if k not in ["placement", "orientation"]} for r in results])
    st.dataframe(res_df, use_container_width=True)

    # --- 4. Visualization ---
    st.subheader(f"Winner: {winner['run_id']} (Temp {winner['temp']})")
    
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**Smart Baseline** (Cost: {base_cost:.2f})")
        st.pyplot(plot_placement(
            baseline, blocks, die, 
            "Baseline (Smart LFF)", 
            orientations=base_orient
        ))

    with col2:
        st.markdown(f"**Optimized Result** (Cost: {winner['cost']:.2f})")
        st.pyplot(plot_placement(
            winner["placement"], blocks, die, 
            f"Best Run (T={winner['temp']})", 
            orientations=winner["orientation"]
        ))

    # --- Metrics ---
    opt_cost = winner["cost"]
    improvement = base_cost - opt_cost
    imp_percent = (improvement / base_cost) * 100 if base_cost > 0 else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Baseline Cost", f"{base_cost:.2f}")
    c2.metric("Optimized Cost", f"{opt_cost:.2f}")
    c3.metric("Improvement", f"{improvement:.2f}", f"{imp_percent:.1f}%")
    
    # --- 5. Final Coordinates Table ---
    st.subheader("Final Layout Coordinates")
    
    layout_data = []
    for block in blocks:
        if block.id in winner["placement"]:
            bx, by = winner["placement"][block.id]
            # No Role, No Rotated columns as requested
            layout_data.append({
                "Block ID": block.id,
                "X (Bottom-Left)": f"{bx:.2f}",
                "Y (Bottom-Left)": f"{by:.2f}",
                "Width": block.width,
                "Height": block.height
            })
            
    st.dataframe(
        pd.DataFrame(layout_data).sort_values(by="Block ID"),
        use_container_width=True,
        hide_index=True
    )