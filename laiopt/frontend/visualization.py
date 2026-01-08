"""
Visualization utilities for macro placement.
Now supports custom text labels (e.g., Role names).
"""

from typing import Dict, Tuple, List, Optional
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch

from laiopt.backend.core.models import Block, Die

Placement = Dict[str, Tuple[float, float]]
Orientations = Dict[str, bool]

def _get_heat_color(heat: float) -> str:
    """Get color based on heat attribute."""
    if heat <= 1:
        return "#add8e6"  # Light Blue (Cool)
    elif heat == 2:
        return "#ffd700"  # Gold (Warm)
    else:
        return "#ff6b6b"  # Light Red (Hot)

def plot_placement(
    placement: Placement,
    blocks: List[Block],
    die: Die,
    title: str = "Placement",
    orientations: Optional[Orientations] = None,
    labels: Optional[Dict[str, str]] = None  # <--- NEW ARGUMENT
):
    """
    Plot a macro placement within the die.
    """
    fig, ax = plt.subplots(figsize=(6, 6))

    # Margin and Outline
    margin = 0.05 * min(die.width, die.height)
    ax.add_patch(
        Rectangle((0, 0), die.width, die.height, fill=False, edgecolor="black", linewidth=2)
    )
    
    block_dict = {b.id: b for b in blocks}
    
    for block_id, (x, y) in placement.items():
        if block_id not in block_dict:
            continue
            
        block = block_dict[block_id]
        color = _get_heat_color(block.heat)
        
        # Rotation Logic
        is_rotated = orientations.get(block_id, False) if orientations else False
        current_w = block.height if is_rotated else block.width
        current_h = block.width if is_rotated else block.height

        # Draw Block
        rect = Rectangle(
            (x, y), current_w, current_h,
            fill=True, facecolor=color, edgecolor="black", linewidth=1.0, alpha=0.8
        )
        ax.add_patch(rect)
        
        # --- NEW LABEL LOGIC ---
        # Use the Role Name if provided, otherwise use ID
        display_text = labels.get(block_id, block_id) if labels else block_id
        
        # Determine text color (Black for light blocks, White for dark blocks if needed)
        # For our colors, black text works best.
        ax.text(
            x + current_w / 2,
            y + current_h / 2,
            display_text,
            ha="center", va="center", fontsize=7,
            color="black", weight="bold",
            clip_on=True
        )

    # Legend
    legend_elements = [
        Patch(facecolor="#add8e6", label="Low Heat (1)"),
        Patch(facecolor="#ffd700", label="Med Heat (2)"),
        Patch(facecolor="#ff6b6b", label="High Heat (3)")
    ]
    ax.legend(handles=legend_elements, loc="upper right", fontsize=8)

    ax.set_xlim(0, die.width)
    ax.set_ylim(0, die.height)
    ax.set_aspect("equal")
    ax.set_title(title)
    ax.grid(True, linestyle="--", alpha=0.3)

    return fig