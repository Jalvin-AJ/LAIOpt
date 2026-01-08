"""
Smart Wall-Aware Baseline Placer.
Logic: Sorts blocks by Difficulty, then places them using a 'Wall-Hugging' heuristic
to respect the periphery constraints (Power Delivery/Cooling).
"""
from typing import List, Tuple, Dict
from collections import defaultdict
from laiopt.backend.core.models import Block, Die, Net

Placement = Dict[str, Tuple[float, float]]

def baseline_place(blocks: List[Block], die: Die, nets: List[Net] = None) -> Placement:
    """
    Places blocks using a 'Wall-Hugging' First Fit principle.
    
    1. Sorts blocks by 'Inflexibility' (Area + Connectivity + Heat).
    2. Places them in positions that minimize the distance to the nearest die boundary.
    """
    
    # --- 1. Scoring & Sorting (Same as before) ---
    connectivity_map = defaultdict(float)
    if nets:
        for net in nets:
            for block_id in net.blocks:
                connectivity_map[block_id] += net.weight

    def get_inflexibility_score(b: Block) -> float:
        # Heat is weighted heavily (10x) because hot blocks MUST be on the wall
        return (b.width * b.height) + connectivity_map.get(b.id, 0.0) + (b.heat * 10.0)

    # Sort descending (Hardest blocks first)
    sorted_blocks = sorted(blocks, key=get_inflexibility_score, reverse=True)
    
    # --- 2. Wall-Hugging Packing Logic ---
    placement = {}
    occupied_spaces = [] # Format: (x, y, w, h)

    def check_overlap(nx, ny, nw, nh, occupied):
        for (ox, oy, ow, oh) in occupied:
            # Standard AABB overlap check
            if (nx < ox + ow and nx + nw > ox and 
                ny < oy + oh and ny + nh > oy):
                return True
        return False

    for block in sorted_blocks:
        w, h = block.width, block.height
        valid_candidates = []
        
        # A. Always propose the 4 Corners of the Die (The VIP Spots)
        #    This ensures we check the walls even if no other blocks are there.
        corners = [
            (0.0, 0.0),                     # Bottom-Left
            (0.0, die.height - h),          # Top-Left
            (die.width - w, 0.0),           # Bottom-Right
            (die.width - w, die.height - h) # Top-Right
        ]
        
        # B. Propose spots next to existing blocks (The "Growth" Spots)
        adjacent = []
        for (ox, oy, ow, oh) in occupied_spaces:
            adjacent.append((ox + ow, oy))       # Right of neighbor
            adjacent.append((ox, oy + oh))       # Top of neighbor
            adjacent.append((ox - w, oy))        # Left of neighbor
            adjacent.append((ox, oy - h))        # Bottom of neighbor
        
        # Combine and Filter
        raw_candidates = corners + adjacent
        
        for cx, cy in raw_candidates:
            # 1. Boundary Check
            if cx < 0 or cy < 0 or cx + w > die.width or cy + h > die.height:
                continue
                
            # 2. Overlap Check
            if not check_overlap(cx, cy, w, h, occupied_spaces):
                valid_candidates.append((cx, cy))

        # --- THE SMART PART: Selection Heuristic ---
        # Instead of sorting by (y, x), we sort by "Distance to Nearest Wall".
        # We want minimizing this distance (0 is best).
        
        def wall_dist_score(pos):
            px, py = pos
            # Distance to Left, Right, Bottom, Top
            d_left = px
            d_right = die.width - (px + w)
            d_bottom = py
            d_top = die.height - (py + h)
            
            # Primary Score: Minimum distance to ANY wall
            min_dist = min(d_left, d_right, d_bottom, d_top)
            
            # Tie-Breaker: Prefer Bottom-Left (py + px) to keep it deterministic
            return (min_dist, py, px)

        if valid_candidates:
            # Sort: Find the spot closest to a wall
            valid_candidates.sort(key=wall_dist_score)
            best_x, best_y = valid_candidates[0]
            
            placement[block.id] = (best_x, best_y)
            occupied_spaces.append((best_x, best_y, w, h))
        else:
            # Fallback (Should rarely happen if die is big enough)
            placement[block.id] = (0.0, 0.0)

    return placement