"""
Cost functions for placement evaluation.

This module implements a simplified but industry-aligned
floorplanning cost model with explicit breakdowns for explainability.

Cost components:
- Wirelength (HPWL)
- Overlap penalty (soft, area-based)
- Die boundary violation penalty (hard constraint)
"""

from typing import Dict, Tuple, List
from laiopt.backend.core.models import Block, Net, Die

# Penalty weights
OVERLAP_WEIGHT = 1e4          # Soft penalty per unit overlap area
BOUNDARY_PENALTY = 1e9        # Hard constraint
MISSING_BLOCK_PENALTY = 1e9   # Hard constraint


Placement = Dict[str, Tuple[float, float]]


def compute_hpwl_wirelength(
    placement: Placement,
    blocks: List[Block],
    nets: List[Net],
) -> float:
    """
    Compute total HPWL (Half-Perimeter Wirelength),
    weighted by net weights.
    """
    block_dict = {b.id: b for b in blocks}
    total_length = 0.0

    for net in nets:
        xs: List[float] = []
        ys: List[float] = []

        for block_id in net.blocks:
            if block_id not in placement or block_id not in block_dict:
                total_length += MISSING_BLOCK_PENALTY
                continue

            block = block_dict[block_id]
            x, y = placement[block_id]
            cx = x + block.width / 2.0
            cy = y + block.height / 2.0
            xs.append(cx)
            ys.append(cy)

        if len(xs) > 1:
            hpwl = (max(xs) - min(xs)) + (max(ys) - min(ys))
            total_length += hpwl * net.weight

    return total_length


def compute_overlap_penalty(
    placement: Placement,
    blocks: List[Block],
) -> float:
    """
    Compute soft overlap penalty based on overlapping area.

    Allows temporary overlaps during optimization but
    strongly discourages them in the final solution.
    """
    penalty = 0.0

    for i, block_a in enumerate(blocks):
        if block_a.id not in placement:
            continue

        ax, ay = placement[block_a.id]
        ax2 = ax + block_a.width
        ay2 = ay + block_a.height

        for block_b in blocks[i + 1:]:
            if block_b.id not in placement:
                continue

            bx, by = placement[block_b.id]
            bx2 = bx + block_b.width
            by2 = by + block_b.height

            overlap_w = min(ax2, bx2) - max(ax, bx)
            overlap_h = min(ay2, by2) - max(ay, by)

            if overlap_w > 0.0 and overlap_h > 0.0:
                penalty += overlap_w * overlap_h * OVERLAP_WEIGHT

    return penalty


def compute_boundary_penalty(
    placement: Placement,
    blocks: List[Block],
    die: Die,
) -> float:
    """
    Compute hard penalty for blocks exceeding die boundaries.
    """
    penalty = 0.0

    for block in blocks:
        if block.id not in placement:
            continue

        x, y = placement[block.id]
        if (
            x < 0.0 or
            y < 0.0 or
            (x + block.width) > die.width or
            (y + block.height) > die.height
        ):
            penalty += BOUNDARY_PENALTY

    return penalty


def total_cost(
    placement: Placement,
    blocks: List[Block],
    nets: List[Net],
    die: Die,
) -> float:
    """
    Compute total placement cost.
    """
    wl = compute_hpwl_wirelength(placement, blocks, nets)
    ov = compute_overlap_penalty(placement, blocks)
    bd = compute_boundary_penalty(placement, blocks, die)

    return wl + ov + bd


def cost_breakdown(
    placement: Placement,
    blocks: List[Block],
    nets: List[Net],
    die: Die,
) -> Dict[str, float]:
    """
    Return detailed cost breakdown for explainability and debugging.
    """
    return {
        "wirelength": compute_hpwl_wirelength(placement, blocks, nets),
        "overlap_penalty": compute_overlap_penalty(placement, blocks),
        "boundary_penalty": compute_boundary_penalty(placement, blocks, die),
    }
