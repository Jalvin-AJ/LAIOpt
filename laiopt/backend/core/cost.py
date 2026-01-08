"""
Cost functions for placement evaluation.
TUNED: Rebalanced to allow Wire Attraction to overcome Thermal Repulsion.
"""

import math
from typing import Dict, Tuple, List
from laiopt.backend.core.models import Block, Net, Die

# --- Optimization Weights & Constants ---
OVERLAP_WEIGHT = 1e4           
BOUNDARY_PENALTY = 1e9         

# --- REBALANCED PHYSICS ---
# Old: 50.0 -> New: 5.0 (Make heat penalty less scary)
THERMAL_PENALTY_WEIGHT = 5.0  

# Old: 500.0 -> New: 100.0 (Heat decays faster, allowing closer neighbors)
THERMAL_SPREAD_K = 100.0       

# Threshold
MAX_SAFE_TEMP = 100.0          

Placement = Dict[str, Tuple[float, float]]
Orientations = Dict[str, bool]


def get_effective_dims(block: Block, orientations: Orientations) -> Tuple[float, float]:
    is_rotated = orientations.get(block.id, False)
    if is_rotated:
        return block.height, block.width
    return block.width, block.height


def get_center(
    x: float, y: float, block: Block, orientations: Orientations
) -> Tuple[float, float]:
    w, h = get_effective_dims(block, orientations)
    return x + w / 2.0, y + h / 2.0


def compute_hpwl_wirelength(
    placement: Placement,
    orientations: Orientations,
    blocks: List[Block],
    nets: List[Net],
) -> float:
    """Compute weighted HPWL wirelength."""
    block_dict = {b.id: b for b in blocks}
    total_length = 0.0

    for net in nets:
        xs: List[float] = []
        ys: List[float] = []

        for block_id in net.blocks:
            if block_id not in placement or block_id not in block_dict:
                continue

            block = block_dict[block_id]
            x, y = placement[block_id]
            cx, cy = get_center(x, y, block, orientations)
            
            xs.append(cx)
            ys.append(cy)

        if len(xs) > 1:
            hpwl = (max(xs) - min(xs)) + (max(ys) - min(ys))
            total_length += hpwl * net.weight

    return total_length


def compute_overlap_penalty(
    placement: Placement,
    orientations: Orientations,
    blocks: List[Block],
) -> float:
    """Compute overlap penalty using effective dimensions."""
    penalty = 0.0
    
    rects = []
    for block in blocks:
        if block.id in placement:
            x, y = placement[block.id]
            w, h = get_effective_dims(block, orientations)
            rects.append((x, y, w, h))
        else:
            rects.append(None)

    for i in range(len(rects)):
        if rects[i] is None: continue
        ax, ay, aw, ah = rects[i]
        ax2, ay2 = ax + aw, ay + ah

        for j in range(i + 1, len(rects)):
            if rects[j] is None: continue
            bx, by, bw, bh = rects[j]
            bx2, by2 = bx + bw, by + bh

            overlap_w = min(ax2, bx2) - max(ax, bx)
            overlap_h = min(ay2, by2) - max(ay, by)

            if overlap_w > 0.0 and overlap_h > 0.0:
                penalty += overlap_w * overlap_h * OVERLAP_WEIGHT

    return penalty


def compute_boundary_penalty(
    placement: Placement,
    orientations: Orientations,
    blocks: List[Block],
    die: Die,
) -> float:
    penalty = 0.0
    for block in blocks:
        if block.id not in placement: continue
        x, y = placement[block.id]
        w, h = get_effective_dims(block, orientations)

        # STRICT Check (Binary) for efficiency since SA handles clamping
        if (x < -0.01 or y < -0.01 or (x + w) > die.width + 0.01 or (y + h) > die.height + 0.01):
            penalty += BOUNDARY_PENALTY
    return penalty


def compute_thermal_penalty(
    placement: Placement,
    orientations: Orientations,
    blocks: List[Block],
) -> float:
    """
    Compute Thermal Penalty (Pairwise).
    """
    total_thermal_cost = 0.0
    
    centers = {}
    for block in blocks:
        if block.id in placement:
            x, y = placement[block.id]
            centers[block.id] = get_center(x, y, block, orientations)

    for victim in blocks:
        if victim.id not in centers: continue
        
        # Base temp
        current_temp = victim.heat * 10.0
        vx, vy = centers[victim.id]

        for aggressor in blocks:
            if victim.id == aggressor.id: continue
            if aggressor.id not in centers: continue
            if aggressor.power <= 0: continue

            ax, ay = centers[aggressor.id]
            dist_sq = (vx - ax)**2 + (vy - ay)**2
            
            # TUNED: Using THERMAL_SPREAD_K = 100.0
            transferred_heat = aggressor.power * math.exp(-dist_sq / THERMAL_SPREAD_K)
            current_temp += transferred_heat

        if current_temp > MAX_SAFE_TEMP:
            violation = current_temp - MAX_SAFE_TEMP
            # TUNED: Using THERMAL_PENALTY_WEIGHT = 5.0
            total_thermal_cost += (violation ** 2) * THERMAL_PENALTY_WEIGHT

    return total_thermal_cost

# --- ADD TO CONSTANTS ---
# Tuned to compete with Wire Attraction. 
# 10.0 is usually enough to gently push blocks outward without breaking nets.
CENTER_PENALTY_WEIGHT = 3500.0 

def compute_center_penalty(
    placement: Placement,
    orientations: Orientations,
    blocks: List[Block],
    die: Die,
) -> float:
    """
    Pushes high-power blocks toward the periphery (Edge Attraction).
    Implements the "Power Delivery" constraint by penalizing blocks 
    that sit in the center of the die.
    """
    cx = die.width / 2.0
    cy = die.height / 2.0
    
    # Max possible distance (Center to Corner) - used for normalization
    max_dist = math.sqrt(cx**2 + cy**2)
    
    total_penalty = 0.0

    for block in blocks:
        if block.id not in placement: continue
        
        # Get block center
        x, y = placement[block.id]
        bx, by = get_center(x, y, block, orientations)
        
        # Calculate distance from die center
        dist_from_center = math.sqrt((bx - cx)**2 + (by - cy)**2)
        
        # INVERTED SCORE: 
        # If dist is 0 (at center) -> Score is 1.0 (Max Penalty)
        # If dist is max (at corner) -> Score is 0.0 (No Penalty)
        center_score = 1.0 - (dist_from_center / max_dist)
        
        # Weight by Block Power
        # High power blocks get pushed harder. Zero power blocks (fillers) are ignored.
        total_penalty += center_score * block.power

    return total_penalty * CENTER_PENALTY_WEIGHT

def total_cost(
    placement: Placement,
    orientations: Orientations,
    blocks: List[Block],
    nets: List[Net],
    die: Die,
) -> float:
    wl = compute_hpwl_wirelength(placement, orientations, blocks, nets)
    ov = compute_overlap_penalty(placement, orientations, blocks)
    bd = compute_boundary_penalty(placement, orientations, blocks, die)
    tm = compute_thermal_penalty(placement, orientations, blocks)
    
    # NEW: Add Center Penalty
    cp = compute_center_penalty(placement, orientations, blocks, die)

    return wl + ov + bd + tm + cp