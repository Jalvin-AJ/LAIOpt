"""
Cost functions for placement evaluation.

This module implements:
- Wirelength calculation (HPWL / Manhattan distance)
- Overlap penalty (hard constraint)
- Die boundary violation penalty (hard constraint)

Cost functions are used by the optimization engine to evaluate placement quality.
"""

from typing import Dict, Tuple, List
from laiopt.backend.core.models import Block, Net, Die

# Hard-constraint penalties (must dominate wirelength)
OVERLAP_PENALTY = 1e9
BOUNDARY_PENALTY = 1e9
MISSING_BLOCK_PENALTY = 1e9


def compute_hpwl_wirelength(
    placement: Dict[str, Tuple[float, float]],
    blocks: List[Block],
    nets: List[Net],
) -> float:
    """
    Compute total wirelength using HPWL (Manhattan bounding box),
    weighted by net weights.

    Block centers are used for HPWL computation.

    Raises a large penalty if a net references a missing block.
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

        if xs and ys:
            hpwl = (max(xs) - min(xs)) + (max(ys) - min(ys))
            total_length += hpwl * net.weight

    return total_length


def compute_overlap_penalty(
    placement: Dict[str, Tuple[float, float]],
    blocks: List[Block],
) -> float:
    """
    Compute hard penalty for overlapping blocks.

    Any positive overlap area incurs a fixed penalty.
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
                penalty += OVERLAP_PENALTY

    return penalty


def compute_boundary_penalty(
    placement: Dict[str, Tuple[float, float]],
    blocks: List[Block],
    die: Die,
) -> float:
    """
    Compute hard penalty for blocks exceeding die boundaries.

    Any boundary violation incurs one fixed penalty per block.
    """
    penalty = 0.0

    for block in blocks:
        if block.id not in placement:
            continue

        x, y = placement[block.id]
        violates = (
            x < 0.0 or
            y < 0.0 or
            (x + block.width) > die.width or
            (y + block.height) > die.height
        )

        if violates:
            penalty += BOUNDARY_PENALTY

    return penalty


def total_cost(
    placement: Dict[str, Tuple[float, float]],
    blocks: List[Block],
    nets: List[Net],
    die: Die,
) -> float:
    """
    Compute total placement cost as the sum of:
    - HPWL wirelength
    - Overlap penalty (hard constraint)
    - Boundary violation penalty (hard constraint)
    """
    wirelength = compute_hpwl_wirelength(placement, blocks, nets)
    overlap = compute_overlap_penalty(placement, blocks)
    boundary = compute_boundary_penalty(placement, blocks, die)

    return wirelength + overlap + boundary
