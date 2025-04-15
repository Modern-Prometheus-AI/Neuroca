"""
Energy Calculation Module for Memory Annealing Optimizer

This module provides functions to calculate the energy (cost function) of memory states
during the annealing optimization process.
"""

import logging
from typing import Dict, List, Set

from neuroca.memory.annealing.optimizer.types import OptimizationStrategy
from neuroca.memory.models.memory_item import MemoryItem
from neuroca.memory.utils.similarity import calculate_similarity

# Configure logger
logger = logging.getLogger(__name__)


def calculate_energy(state: List[MemoryItem], strategy: OptimizationStrategy) -> float:
    """
    Calculate the energy (cost function) of the current state.
    
    Lower energy indicates a better state. The energy function considers:
    - Redundancy between memories
    - Fragmentation of related concepts
    - Relevance and importance of memories
    
    Args:
        state: Current state of memory fragments
        strategy: The optimization strategy to use
        
    Returns:
        Energy value (lower is better)
    """
    if not state:
        return 0.0
        
    # Initialize energy components
    redundancy_energy = calculate_redundancy_energy(state)
    fragmentation_energy = calculate_fragmentation_energy(state)
    relevance_energy = calculate_relevance_energy(state)
    
    # Combine energy components with weights based on strategy
    weights = get_strategy_weights(strategy, redundancy_energy)
    
    # Calculate total energy
    total_energy = (
        weights["redundancy"] * redundancy_energy +
        weights["fragmentation"] * fragmentation_energy +
        weights["relevance"] * relevance_energy
    )
    
    return total_energy


def calculate_redundancy_energy(state: List[MemoryItem]) -> float:
    """
    Calculate the redundancy energy component.
    
    Args:
        state: Current state of memory fragments
        
    Returns:
        Redundancy energy value
    """
    redundancy_energy = 0.0
    
    # Calculate redundancy between memories
    for i, mem1 in enumerate(state):
        for _j, mem2 in enumerate(state[i+1:], i+1):
            sim = calculate_similarity(mem1, mem2)
            redundancy_energy += sim * sim
    
    # Normalize redundancy by number of pairs
    n_pairs = len(state) * (len(state) - 1) / 2
    if n_pairs > 0:
        redundancy_energy /= n_pairs
        
    return redundancy_energy


def calculate_fragmentation_energy(state: List[MemoryItem]) -> float:
    """
    Calculate the fragmentation energy component.
    
    Args:
        state: Current state of memory fragments
        
    Returns:
        Fragmentation energy value
    """
    if not state:
        return 0.0
        
    # Build connection graph
    connection_graph = build_connection_graph(state)
    
    # Calculate fragmentation
    return calculate_fragmentation(connection_graph)


def calculate_relevance_energy(state: List[MemoryItem]) -> float:
    """
    Calculate the relevance energy component.
    
    Args:
        state: Current state of memory fragments
        
    Returns:
        Relevance energy value
    """
    if not state:
        return 0.0
    
    relevance_energy = 0.0
    
    # Calculate relevance (less relevant memories contribute more energy)
    for memory in state:
        # Invert relevance so lower relevance = higher energy
        relevance_energy += 1.0 - min(1.0, memory.relevance_score)
    
    # Normalize relevance
    relevance_energy /= len(state)
    
    return relevance_energy


def get_strategy_weights(
    strategy: OptimizationStrategy, 
    redundancy_level: float = 0.0
) -> Dict[str, float]:
    """
    Get energy component weights based on the optimization strategy.
    
    Args:
        strategy: The optimization strategy to use
        redundancy_level: Current redundancy level (used for ADAPTIVE strategy)
        
    Returns:
        Dictionary of weights for each energy component
    """
    if strategy == OptimizationStrategy.AGGRESSIVE:
        # Aggressive optimization prioritizes reducing redundancy
        return {
            "redundancy": 0.5,
            "fragmentation": 0.3,
            "relevance": 0.2
        }
    elif strategy == OptimizationStrategy.CONSERVATIVE:
        # Conservative optimization prioritizes maintaining relevance
        return {
            "redundancy": 0.2,
            "fragmentation": 0.3,
            "relevance": 0.5
        }
    elif strategy == OptimizationStrategy.ADAPTIVE:
        # Adaptive weights based on current state characteristics
        redundancy_level = min(1.0, redundancy_level)
        return {
            "redundancy": 0.3 + 0.2 * redundancy_level,
            "fragmentation": 0.3,
            "relevance": 0.4 - 0.2 * redundancy_level
        }
    else:  # STANDARD
        # Balanced weights
        return {
            "redundancy": 0.4,
            "fragmentation": 0.3,
            "relevance": 0.3
        }


def build_connection_graph(state: List[MemoryItem]) -> Dict[int, Set[int]]:
    """
    Build a graph of connections between memory fragments.
    
    Args:
        state: Current state of memory fragments
        
    Returns:
        Dictionary mapping memory indices to sets of connected memory indices
    """
    connection_graph: Dict[int, Set[int]] = {i: set() for i in range(len(state))}
    
    # Connect memories with similarity above threshold
    similarity_threshold = 0.3
    for i, mem1 in enumerate(state):
        for j, mem2 in enumerate(state):
            if i != j and calculate_similarity(mem1, mem2) > similarity_threshold:
                connection_graph[i].add(j)
                connection_graph[j].add(i)
    
    return connection_graph


def calculate_fragmentation(connection_graph: Dict[int, Set[int]]) -> float:
    """
    Calculate fragmentation score based on connection graph.
    
    Args:
        connection_graph: Graph of connections between memories
        
    Returns:
        Fragmentation score (higher means more fragmented)
    """
    if not connection_graph:
        return 0.0
        
    # Count number of connected components
    visited = set()
    components = 0
    
    for node in connection_graph:
        if node not in visited:
            components += 1
            dfs(node, connection_graph, visited)
    
    # Normalize by number of nodes
    return (components - 1) / max(1, len(connection_graph))


def dfs(node: int, graph: Dict[int, Set[int]], visited: Set[int]) -> None:
    """
    Depth-first search to find connected components.
    
    Args:
        node: Current node
        graph: Connection graph
        visited: Set of visited nodes
    """
    visited.add(node)
    for neighbor in graph[node]:
        if neighbor not in visited:
            dfs(neighbor, graph, visited)
