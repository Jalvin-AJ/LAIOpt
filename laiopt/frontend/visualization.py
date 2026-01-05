"""
Visualization utilities for macro placement.

This module provides safe, geometry-accurate plotting functions
for baseline and optimized placements.
"""

from typing import Dict, Tuple, List
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.patches import Patch

from laiopt.backend.core.models import Block, Die

Placement = Dict[str, Tuple[float, float]]


def _get_heat_color(heat: float) -> str:
    """
    Get color based on heat attribute.
    
    Args:
        heat (float): Heat value
        
    Returns:
        str: Color name
    """
    if heat <= 1:
        return "blue"
    elif heat == 2:
        return "yellow"
    else:  # heat >= 3
        return "red"


def plot_placement(
    placement: Placement,
    blocks: List[Block],
    die: Die,
    title: str = "Placement"
):
    """
    Plot a macro placement within the die.

    Args:
        placement (Placement): Block ID -> (x, y)
        blocks (List[Block]): Block definitions
        die (Die): Die dimensions
        title (str): Plot title
    """
    fig, ax = plt.subplots(figsize=(6, 6))

    # Calculate core region margin (uniform on all sides)
    margin = 0.08 * min(die.width, die.height)
    
    # Draw die outline (thick black rectangle) from (0, 0) to (die.width, die.height)
    ax.add_patch(
        Rectangle(
            (0, 0),
            die.width,
            die.height,
            fill=False,
            edgecolor="black",
            linewidth=2
        )
    )
    
    # Draw core region (inset uniformly on all sides)
    core_x = margin
    core_y = margin
    core_width = die.width - 2 * margin
    core_height = die.height - 2 * margin
    
    ax.add_patch(
        Rectangle(
            (core_x, core_y),
            core_width,
            core_height,
            fill=True,
            facecolor="lightgray",
            alpha=0.2,
            edgecolor="gray",
            linestyle="--",
            linewidth=1.5
        )
    )

    # Draw blocks (visually offset by core margin)
    block_dict = {b.id: b for b in blocks}
    for block_id, (x, y) in placement.items():
        block = block_dict[block_id]
        color = _get_heat_color(block.heat)
        
        # Apply visual offset: draw at (x + margin, y + margin)
        visual_x = x + margin
        visual_y = y + margin
        
        rect = Rectangle(
            (visual_x, visual_y),
            block.width,
            block.height,
            fill=True,
            facecolor=color,
            edgecolor="black",
            linewidth=1.5,
            alpha=0.6
        )
        ax.add_patch(rect)
        
        # Add text label with outline for readability (also offset)
        ax.text(
            visual_x + block.width / 2,
            visual_y + block.height / 2,
            block_id,
            ha="center",
            va="center",
            fontsize=8,
            color="black",
            weight="bold",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7, edgecolor="none")
        )
    
    # Add legend
    legend_elements = [
        Patch(facecolor="blue", alpha=0.6, edgecolor="black", label="Low heat (≤1)"),
        Patch(facecolor="yellow", alpha=0.6, edgecolor="black", label="Medium heat (=2)"),
        Patch(facecolor="red", alpha=0.6, edgecolor="black", label="High heat (≥3)")
    ]
    ax.legend(handles=legend_elements, loc="upper right", framealpha=0.9)

    ax.set_xlim(0, die.width)
    ax.set_ylim(0, die.height)
    ax.set_aspect("equal", adjustable="box")
    ax.set_title(title)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.grid(True, linestyle="--", alpha=0.3)

    return fig
