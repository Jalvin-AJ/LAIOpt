"""
Deterministic initial placement logic.

This module generates a legal baseline placement that:
- Ensures no macro overlaps
- Respects die boundaries
- Uses real block dimensions
- Produces deterministic, repeatable results

The baseline placement serves as the starting point for optimization.
"""
from typing import List, Dict, Tuple
from laiopt.backend.core.models import Block, Die


def baseline_place(blocks: List[Block], die: Die) -> Dict[str, Tuple[float, float]]:
    """
    Deterministically place macros (blocks) within the die using
    a simple row-wise, left-to-right strategy.

    This placement serves as a legal, explainable baseline and
    is not intended to be optimal.

    Args:
        blocks (List[Block]): List of Block objects to place.
        die (Die): Die object specifying chip area.

    Returns:
        Dict[str, Tuple[float, float]]:
            Mapping of block ID to (x, y) bottom-left placement coordinates.

    Raises:
        ValueError:
            - If a block cannot fit within die boundaries.
            - If duplicate block IDs are detected.
    """
    # Sort blocks by ID to ensure deterministic placement order
    blocks_sorted = sorted(blocks, key=lambda b: b.id)

    placement: Dict[str, Tuple[float, float]] = {}

    current_x: float = 0.0     # Current x-position in the row
    current_y: float = 0.0     # Current y-position (row base)
    row_height: float = 0.0    # Max height of blocks in the current row

    for block in blocks_sorted:
        # Prevent silent overwriting due to duplicate block IDs
        if block.id in placement:
            raise ValueError(f"Duplicate block ID detected: '{block.id}'")

        # Move to next row if block does not fit horizontally
        if current_x + block.width > die.width:
            current_x = 0.0
            current_y += row_height
            row_height = 0.0

        # Check vertical fit within die
        if current_y + block.height > die.height:
            raise ValueError(
                f"Cannot place block '{block.id}': exceeds die height at y={current_y}."
            )

        # Place block at current location (bottom-left corner)
        placement[block.id] = (current_x, current_y)

        # Advance position for next block
        current_x += block.width
        row_height = max(row_height, block.height)

    return placement


