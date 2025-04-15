"""
Memory Annealing Optimizer Components Package

This package provides modular components used by the memory annealing optimizer.
"""

from neuroca.memory.annealing.optimizer.components.energy import (
    calculate_energy,
    calculate_redundancy_energy,
    calculate_fragmentation_energy,
    calculate_relevance_energy,
    get_strategy_weights,
    build_connection_graph,
    calculate_fragmentation
)

from neuroca.memory.annealing.optimizer.components.transformations import (
    clone_memories,
    generate_neighbor,
    merge_memories,
    split_memory,
    post_process
)

__all__ = [
    'calculate_energy',
    'calculate_redundancy_energy',
    'calculate_fragmentation_energy',
    'calculate_relevance_energy',
    'get_strategy_weights',
    'build_connection_graph',
    'calculate_fragmentation',
    'clone_memories',
    'generate_neighbor',
    'merge_memories',
    'split_memory',
    'post_process'
]
