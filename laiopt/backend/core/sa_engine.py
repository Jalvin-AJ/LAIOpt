"""
Simulated Annealing engine for macro placement optimization.

Performs controlled, explainable optimization over a legal baseline
using continuous, geometry-aware moves.
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
    initial_temperature: float = 2000.0,
    final_temperature: float = 1.0,
    alpha: float = 0.97,
    max_iterations: int = 1500,
    move_scale: float = 15.0,
    random_seed: int | None = None,
) -> Tuple[Placement, float, List[float]]:
    """
    Optimize macro placement using Simulated Annealing.

    Returns:
        - Best placement
        - Best cost
        - Cost history (for analysis & plotting)
    """

    rng = random.Random(random_seed) if random_seed is not None else random.Random()

    # Deterministic legal baseline
    current = baseline_place(blocks, die)
    current_cost = total_cost(current, blocks, nets, die)

    best = dict(current)
    best_cost = current_cost

    cost_history: List[float] = [current_cost]

    block_map = {b.id: b for b in blocks}
    block_ids = list(block_map.keys())

    temperature = initial_temperature

    for _ in range(max_iterations):
        if temperature < final_temperature:
            break

        # ---- LEGAL MOVE: single-block perturbation ----
        block_id = rng.choice(block_ids)
        block = block_map[block_id]

        x, y = current[block_id]

        dx = rng.uniform(-move_scale, move_scale)
        dy = rng.uniform(-move_scale, move_scale)

        new_x = x + dx
        new_y = y + dy

        # Hard boundary enforcement
        if (
            new_x < 0.0 or
            new_y < 0.0 or
            new_x + block.width > die.width or
            new_y + block.height > die.height
        ):
            temperature *= alpha
            continue

        candidate = dict(current)
        candidate[block_id] = (new_x, new_y)

        candidate_cost = total_cost(candidate, blocks, nets, die)
        delta = candidate_cost - current_cost

        # ---- SA acceptance rule ----
        if delta <= 0.0 or rng.random() < math.exp(-delta / temperature):
            current = candidate
            current_cost = candidate_cost
            cost_history.append(current_cost)

            if current_cost < best_cost:
                best = dict(current)
                best_cost = current_cost

        temperature *= alpha

    return best, best_cost, cost_history
