"""
Hybrid Simulated Annealing Engine.
Logic: Based on user's shared repo (Rejection-based stopping condition).
Domain: Coordinate System with Fixed Die & Thermal Costs.
"""

import math
import random
from typing import Dict, Tuple, List

from laiopt.backend.core.models import Block, Net, Die
from laiopt.backend.core.baseline import baseline_place
from laiopt.backend.core.cost import total_cost, get_effective_dims

Placement = Dict[str, Tuple[float, float]]
Orientations = Dict[str, bool]

def simulated_annealing(
    blocks: List[Block],
    nets: List[Net],
    die: Die,
    *,
    initial_temperature: float = 3000.0, # High start (from your repo logic)
    final_temperature: float = 0.001,     # Low end (from your repo logic)
    alpha: float = 0.98,                  # Cooling rate (tuned for Python speed)
    k_steps: int = 100,                   # Steps per temp (K in your repo)
    move_scale: float = 20.0,
    random_seed: int | None = None,
) -> Tuple[Placement, float, List[float], Orientations]:
    
    rng = random.Random(random_seed) if random_seed is not None else random.Random()

    # 1. Initialization (Using LFF Baseline)
    current_place = baseline_place(blocks, die, nets)
    current_orient = {b.id: False for b in blocks}
    
    # Initial Cost (Includes Wires + Overlap + Boundary + THERMAL)
    current_cost = total_cost(current_place, current_orient, blocks, nets, die)

    best_place = dict(current_place)
    best_orient = dict(current_orient)
    best_cost = current_cost
    cost_history = [current_cost]

    temperature = initial_temperature
    
    block_map = {b.id: b for b in blocks}
    block_ids = list(block_map.keys())

    # 2. Main Loop (Logic from Shared Repo)
    # "while reject/K > 0.95 or T > 0.001"
    # We invert the rejection logic: Continue while acceptance > 5% OR T is high
    
    rejection_rate = 0.0
    
    while (rejection_rate < 0.95) or (temperature > final_temperature):
        
        reject_count = 0
        
        # Inner Markov Chain (K steps)
        for _ in range(k_steps):
            next_place = dict(current_place)
            next_orient = dict(current_orient)
            
            # --- SELECTION (Coordinate Moves instead of Polish) ---
            move_type = rng.random()
            
            # 1. Displacement (Coordinate Jiggle)
            if move_type < 0.5: 
                block_id = rng.choice(block_ids)
                block = block_map[block_id]
                x, y = current_place[block_id]
                
                # Dynamic scaling
                scale = move_scale * (temperature / initial_temperature) + 1.0
                raw_x = x + rng.uniform(-scale, scale)
                raw_y = y + rng.uniform(-scale, scale)
                
                # STRICT CLAMPING (User Defined Die Area)
                w, h = get_effective_dims(block, current_orient)
                safe_x = max(0.0, min(raw_x, die.width - w))
                safe_y = max(0.0, min(raw_y, die.height - h))
                
                next_place[block_id] = (safe_x, safe_y)

            # 2. Swap (Exchange Positions)
            elif move_type < 0.85:
                if len(block_ids) < 2: continue
                b1, b2 = rng.sample(block_ids, 2)
                
                # Swap coords
                next_place[b1], next_place[b2] = current_place[b2], current_place[b1]
                
                # Clamp both to be safe
                for bid in [b1, b2]:
                    bx, by = next_place[bid]
                    bw, bh = get_effective_dims(block_map[bid], current_orient)
                    safe_x = max(0.0, min(bx, die.width - bw))
                    safe_y = max(0.0, min(by, die.height - bh))
                    next_place[bid] = (safe_x, safe_y)

            # 3. Rotate (Flip Dimensions)
            else:
                block_id = rng.choice(block_ids)
                next_orient[block_id] = not current_orient[block_id]
                
                # Check validity after rotation
                rx, ry = current_place[block_id]
                rw, rh = get_effective_dims(block_map[block_id], next_orient)
                
                if (rx + rw > die.width) or (ry + rh > die.height):
                    # Clamp back inside
                    safe_x = max(0.0, min(rx, die.width - rw))
                    safe_y = max(0.0, min(ry, die.height - rh))
                    next_place[block_id] = (safe_x, safe_y)

            # --- EVALUATION (Includes Thermal Physics) ---
            new_cost = total_cost(next_place, next_orient, blocks, nets, die)
            delta_cost = new_cost - current_cost

            # --- ACCEPTANCE (Metropolis Criterion) ---
            # "if(newCost < InitialCost or n < math.exp(-1 * dc / T))"
            accepted = False
            if delta_cost <= 0.0:
                accepted = True
            else:
                prob = math.exp(-delta_cost / temperature)
                if rng.random() < prob:
                    accepted = True

            if accepted:
                current_place = next_place
                current_orient = next_orient
                current_cost = new_cost
                
                if current_cost < best_cost:
                    best_place = dict(current_place)
                    best_orient = dict(current_orient)
                    best_cost = current_cost
            else:
                reject_count += 1
                
        # Update Stats
        rejection_rate = reject_count / k_steps
        cost_history.append(current_cost)
        
        # Cooling (Geometric Schedule)
        temperature *= alpha
        
        # Sanity break (to prevent infinite loops if params are bad)
        if len(cost_history) > 5000:
            break

    return best_place, best_cost, cost_history, best_orient