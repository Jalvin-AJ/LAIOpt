"""
Simulated Annealing optimizer.

This module implements the optimization engine using:
- Legal move generation that respects constraints
- Acceptance logic based on cost comparison and controlled randomness
- Deterministic behavior aside from documented controllable randomness
- Temperature schedule management

The optimizer uses cost functions to iteratively improve macro placement.
"""
"""
Simulated Annealing engine for macro placement optimization.

This module performs controlled, explainable optimization over
a legal baseline placement using a well-defined cost function.
"""

import math
import random
from typing import Dict, Tuple, List

from laiopt.backend.core.models import Block, Net, Die
from laiopt.backend.core.baseline import baseline_place
from laiopt.backend.core.cost import total_cost


Placement = Dict[str, Tuple[float, float]]


def simulated_annealing(
    blocks: List[Block],
    nets: List[Net],
    die: Die,
    *,
    initial_temperature: float = 1000.0,
    final_temperature: float = 1.0,
    alpha: float = 0.95,
    max_iterations: int = 1000,
    move_scale: float = 10.0,
    random_seed: int = 42,
) -> Tuple[Placement, float]:
    """
    Optimize macro placement using Simulated Annealing.

    Args:
        blocks (List[Block]): Blocks to place.
        nets (List[Net]): Connectivity.
        die (Die): Die area.
        initial_temperature (float): Starting temperature.
        final_temperature (float): Ending temperature.
        alpha (float): Temperature decay factor.
        max_iterations (int): Maximum SA iterations.
        move_scale (float): Maximum coordinate perturbation.
        random_seed (int): Random seed for reproducibility.

    Returns:
        Tuple[Placement, float]: Best placement found and its cost.
    """
    rng = random.Random(random_seed)

    # Start from deterministic baseline placement
    current_placement: Placement = baseline_place(blocks, die)
    current_cost = total_cost(current_placement, blocks, nets, die)

    best_placement = dict(current_placement)
    best_cost = current_cost

    temperature = initial_temperature
    block_ids = [b.id for b in blocks]

    for _ in range(max_iterations):
        if temperature < final_temperature:
            break

        # Select a block to move
        block_id = rng.choice(block_ids)
        block = next(b for b in blocks if b.id == block_id)

        x, y = current_placement[block_id]

        # Propose a small random move
        dx = rng.uniform(-move_scale, move_scale)
        dy = rng.uniform(-move_scale, move_scale)
        new_x = x + dx
        new_y = y + dy

        # Reject moves that violate die boundaries immediately
        if (
            new_x < 0.0 or
            new_y < 0.0 or
            new_x + block.width > die.width or
            new_y + block.height > die.height
        ):
            temperature *= alpha
            continue

        # Construct candidate placement
        candidate_placement = dict(current_placement)
        candidate_placement[block_id] = (new_x, new_y)

        candidate_cost = total_cost(candidate_placement, blocks, nets, die)
        delta = candidate_cost - current_cost

        # Accept move
        if delta <= 0.0 or rng.random() < math.exp(-delta / temperature):
            current_placement = candidate_placement
            current_cost = candidate_cost

            if current_cost < best_cost:
                best_cost = current_cost
                best_placement = dict(current_placement)

        temperature *= alpha

    return best_placement, best_cost


