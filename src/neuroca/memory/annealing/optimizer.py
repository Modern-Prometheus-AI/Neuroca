"""
Simulated Annealing Memory Optimizer for NeuroCognitive Architecture.

This module implements a simulated annealing optimization approach for memory consolidation
and optimization within the NeuroCognitive Architecture. It provides mechanisms to:
1. Optimize memory representations through simulated annealing
2. Consolidate related memory fragments
3. Prune less relevant memories based on configurable criteria
4. Adjust memory weights and connections based on usage patterns

The optimizer follows biological principles of memory consolidation during rest/sleep
periods, implementing a temperature-based annealing schedule that gradually stabilizes
important memories while allowing for exploration of memory space early in the process.

Usage:
    optimizer = AnnealingOptimizer(config)
    optimized_memories = optimizer.optimize(memories)
    
    # With custom annealing schedule
    custom_schedule = LinearAnnealingSchedule(start_temp=1.0, end_temp=0.01, steps=1000)
    optimizer = AnnealingOptimizer(config, annealing_schedule=custom_schedule)
    
    # Run optimization with callbacks
    optimizer.optimize(memories, callbacks=[logging_callback, visualization_callback])
"""

import logging
import math
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Callable, Optional, Union

import numpy as np

from neuroca.config.settings import get_settings
from neuroca.core.exceptions import OptimizationError, ValidationError
from neuroca.memory.base import MemoryFragment, MemoryStore
from neuroca.memory.utils import similarity_score

# Configure logger
logger = logging.getLogger(__name__)


class OptimizationStrategy(Enum):
    """Enumeration of available optimization strategies."""
    STANDARD = auto()
    AGGRESSIVE = auto()
    CONSERVATIVE = auto()
    ADAPTIVE = auto()


class OptimizationMetric(Enum):
    """Enumeration of metrics used to evaluate optimization quality."""
    ENERGY = auto()
    COHERENCE = auto()
    RELEVANCE = auto()
    COMPRESSION = auto()
    RETRIEVAL_SPEED = auto()


@dataclass
class OptimizationStats:
    """Statistics collected during the optimization process."""
    
    initial_energy: float
    final_energy: float
    iterations: int
    accepted_moves: int
    rejected_moves: int
    duration_seconds: float
    temperature_history: list[float]
    energy_history: list[float]
    
    @property
    def acceptance_ratio(self) -> float:
        """Calculate the ratio of accepted moves to total iterations."""
        if self.iterations == 0:
            return 0.0
        return self.accepted_moves / self.iterations
    
    @property
    def energy_reduction(self) -> float:
        """Calculate the percentage of energy reduction."""
        if self.initial_energy == 0:
            return 0.0
        return (self.initial_energy - self.final_energy) / self.initial_energy * 100
    
    def to_dict(self) -> dict[str, Any]:
        """Convert stats to dictionary for serialization."""
        return {
            "initial_energy": self.initial_energy,
            "final_energy": self.final_energy,
            "iterations": self.iterations,
            "accepted_moves": self.accepted_moves,
            "rejected_moves": self.rejected_moves,
            "duration_seconds": self.duration_seconds,
            "acceptance_ratio": self.acceptance_ratio,
            "energy_reduction": self.energy_reduction
        }


class AnnealingSchedule(ABC):
    """Abstract base class for temperature scheduling in simulated annealing."""
    
    @abstractmethod
    def get_temperature(self, step: int, max_steps: int) -> float:
        """
        Calculate the temperature for the current step.
        
        Args:
            step: Current step number (0-indexed)
            max_steps: Total number of steps in the annealing process
            
        Returns:
            The temperature value for the current step
        """
        pass


class ExponentialAnnealingSchedule(AnnealingSchedule):
    """
    Exponential cooling schedule for simulated annealing.
    
    Temperature decreases exponentially from start_temp to end_temp.
    """
    
    def __init__(self, start_temp: float = 1.0, end_temp: float = 0.01, decay: float = 0.95):
        """
        Initialize exponential annealing schedule.
        
        Args:
            start_temp: Starting temperature (default: 1.0)
            end_temp: Ending temperature (default: 0.01)
            decay: Exponential decay factor (default: 0.95)
        
        Raises:
            ValidationError: If parameters are invalid
        """
        if start_temp <= 0 or end_temp <= 0:
            raise ValidationError("Temperatures must be positive")
        if start_temp <= end_temp:
            raise ValidationError("Start temperature must be greater than end temperature")
        if decay <= 0 or decay >= 1:
            raise ValidationError("Decay must be between 0 and 1 exclusive")
            
        self.start_temp = start_temp
        self.end_temp = end_temp
        self.decay = decay
        
    def get_temperature(self, step: int, max_steps: int) -> float:
        """
        Calculate temperature using exponential decay.
        
        Args:
            step: Current step number (0-indexed)
            max_steps: Total number of steps in the annealing process
            
        Returns:
            The temperature value for the current step
        """
        progress = step / max_steps
        return self.start_temp * (self.decay ** (progress * max_steps))


class LinearAnnealingSchedule(AnnealingSchedule):
    """
    Linear cooling schedule for simulated annealing.
    
    Temperature decreases linearly from start_temp to end_temp.
    """
    
    def __init__(self, start_temp: float = 1.0, end_temp: float = 0.01):
        """
        Initialize linear annealing schedule.
        
        Args:
            start_temp: Starting temperature (default: 1.0)
            end_temp: Ending temperature (default: 0.01)
            
        Raises:
            ValidationError: If parameters are invalid
        """
        if start_temp <= 0 or end_temp <= 0:
            raise ValidationError("Temperatures must be positive")
        if start_temp <= end_temp:
            raise ValidationError("Start temperature must be greater than end temperature")
            
        self.start_temp = start_temp
        self.end_temp = end_temp
        
    def get_temperature(self, step: int, max_steps: int) -> float:
        """
        Calculate temperature using linear interpolation.
        
        Args:
            step: Current step number (0-indexed)
            max_steps: Total number of steps in the annealing process
            
        Returns:
            The temperature value for the current step
        """
        if max_steps <= 1:
            return self.end_temp
        progress = step / (max_steps - 1)
        return self.start_temp - progress * (self.start_temp - self.end_temp)


class AdaptiveAnnealingSchedule(AnnealingSchedule):
    """
    Adaptive cooling schedule that adjusts based on acceptance rate.
    
    This schedule monitors the acceptance rate of moves and adjusts the
    temperature to maintain an optimal acceptance rate range.
    """
    
    def __init__(
        self, 
        start_temp: float = 1.0, 
        end_temp: float = 0.01,
        target_acceptance: float = 0.4,
        adjustment_rate: float = 0.1
    ):
        """
        Initialize adaptive annealing schedule.
        
        Args:
            start_temp: Starting temperature (default: 1.0)
            end_temp: Ending temperature (default: 0.01)
            target_acceptance: Target acceptance rate (default: 0.4)
            adjustment_rate: Rate at which to adjust temperature (default: 0.1)
            
        Raises:
            ValidationError: If parameters are invalid
        """
        if start_temp <= 0 or end_temp <= 0:
            raise ValidationError("Temperatures must be positive")
        if start_temp <= end_temp:
            raise ValidationError("Start temperature must be greater than end temperature")
        if target_acceptance <= 0 or target_acceptance >= 1:
            raise ValidationError("Target acceptance must be between 0 and 1")
        if adjustment_rate <= 0 or adjustment_rate >= 1:
            raise ValidationError("Adjustment rate must be between 0 and 1")
            
        self.start_temp = start_temp
        self.end_temp = end_temp
        self.target_acceptance = target_acceptance
        self.adjustment_rate = adjustment_rate
        self.current_temp = start_temp
        self.acceptance_history: list[bool] = []
        
    def record_acceptance(self, accepted: bool) -> None:
        """
        Record whether a move was accepted.
        
        Args:
            accepted: Whether the move was accepted
        """
        self.acceptance_history.append(accepted)
        # Keep history limited to recent moves
        if len(self.acceptance_history) > 100:
            self.acceptance_history.pop(0)
            
    def get_temperature(self, step: int, max_steps: int) -> float:
        """
        Calculate temperature adaptively based on acceptance history.
        
        Args:
            step: Current step number (0-indexed)
            max_steps: Total number of steps in the annealing process
            
        Returns:
            The temperature value for the current step
        """
        # Calculate base temperature from linear schedule
        base_temp = LinearAnnealingSchedule(
            self.start_temp, self.end_temp
        ).get_temperature(step, max_steps)
        
        # If we have enough history, adjust based on acceptance rate
        if len(self.acceptance_history) >= 10:
            current_acceptance = sum(self.acceptance_history) / len(self.acceptance_history)
            
            # Adjust temperature based on difference from target acceptance
            if current_acceptance < self.target_acceptance:
                # Increase temperature to accept more moves
                adjustment = 1 + self.adjustment_rate
            else:
                # Decrease temperature to accept fewer moves
                adjustment = 1 - self.adjustment_rate
                
            self.current_temp = max(self.end_temp, min(self.start_temp, base_temp * adjustment))
            return self.current_temp
        
        # Not enough history yet, use base temperature
        self.current_temp = base_temp
        return base_temp


class AnnealingOptimizer:
    """
    Memory optimizer using simulated annealing techniques.
    
    This class implements memory optimization through simulated annealing,
    allowing for consolidation, pruning, and reorganization of memory fragments
    to improve overall system performance and memory quality.
    """
    
    def __init__(
        self,
        config: Optional[dict[str, Any]] = None,
        annealing_schedule: Optional[AnnealingSchedule] = None,
        strategy: OptimizationStrategy = OptimizationStrategy.STANDARD,
        max_iterations: int = 1000,
        early_stopping_threshold: float = 0.001,
        early_stopping_iterations: int = 50,
        random_seed: Optional[int] = None
    ):
        """
        Initialize the annealing optimizer.
        
        Args:
            config: Configuration dictionary (default: None, uses system settings)
            annealing_schedule: Temperature schedule to use (default: ExponentialAnnealingSchedule)
            strategy: Optimization strategy to use (default: STANDARD)
            max_iterations: Maximum number of iterations (default: 1000)
            early_stopping_threshold: Energy change threshold for early stopping (default: 0.001)
            early_stopping_iterations: Number of iterations below threshold to trigger early stopping (default: 50)
            random_seed: Seed for random number generator (default: None)
            
        Raises:
            ValidationError: If configuration parameters are invalid
        """
        # Initialize configuration
        self.config = config or get_settings().memory.annealing
        
        # Validate and set parameters
        if max_iterations <= 0:
            raise ValidationError("Max iterations must be positive")
        if early_stopping_threshold < 0:
            raise ValidationError("Early stopping threshold must be non-negative")
        if early_stopping_iterations <= 0:
            raise ValidationError("Early stopping iterations must be positive")
            
        self.max_iterations = max_iterations
        self.early_stopping_threshold = early_stopping_threshold
        self.early_stopping_iterations = early_stopping_iterations
        self.strategy = strategy
        
        # Set random seed if provided
        if random_seed is not None:
            random.seed(random_seed)
            np.random.seed(random_seed)
            
        # Set annealing schedule
        self.annealing_schedule = annealing_schedule or ExponentialAnnealingSchedule()
        
        logger.info(
            f"Initialized AnnealingOptimizer with strategy={strategy.name}, "
            f"max_iterations={max_iterations}, schedule={type(self.annealing_schedule).__name__}"
        )
        
    def optimize(
        self,
        memories: Union[list[MemoryFragment], MemoryStore],
        callbacks: Optional[list[Callable[[dict[str, Any]], None]]] = None
    ) -> tuple[Union[list[MemoryFragment], MemoryStore], OptimizationStats]:
        """
        Optimize memory fragments using simulated annealing.
        
        Args:
            memories: List of memory fragments or a MemoryStore to optimize
            callbacks: Optional list of callback functions to call after each iteration
                       with the current state of the optimization
                       
        Returns:
            Tuple containing:
                - Optimized memories (same type as input)
                - OptimizationStats object with optimization statistics
                
        Raises:
            OptimizationError: If optimization fails
            ValidationError: If input is invalid
        """
        if not memories:
            raise ValidationError("No memories provided for optimization")
            
        start_time = time.time()
        logger.info(f"Starting memory optimization with {len(memories)} memory fragments")
        
        # Track if we're working with a MemoryStore or list
        using_memory_store = isinstance(memories, MemoryStore)
        
        # Extract memory fragments if using MemoryStore
        memory_fragments = memories.get_all() if using_memory_store else memories
        
        if not memory_fragments:
            logger.warning("No memory fragments to optimize")
            stats = OptimizationStats(
                initial_energy=0.0,
                final_energy=0.0,
                iterations=0,
                accepted_moves=0,
                rejected_moves=0,
                duration_seconds=0.0,
                temperature_history=[],
                energy_history=[]
            )
            return memories, stats
            
        try:
            # Create working copy of memories
            current_state = self._clone_memories(memory_fragments)
            
            # Calculate initial energy
            current_energy = self._calculate_energy(current_state)
            initial_energy = current_energy
            
            # Initialize tracking variables
            best_state = current_state
            best_energy = current_energy
            iterations_without_improvement = 0
            accepted_moves = 0
            rejected_moves = 0
            
            temperature_history = []
            energy_history = [current_energy]
            
            # Use adaptive schedule if specified
            adaptive_schedule = isinstance(self.annealing_schedule, AdaptiveAnnealingSchedule)
            
            # Main annealing loop
            for iteration in range(self.max_iterations):
                # Get current temperature
                temperature = self.annealing_schedule.get_temperature(iteration, self.max_iterations)
                temperature_history.append(temperature)
                
                # Generate neighbor state
                neighbor_state = self._generate_neighbor(current_state)
                neighbor_energy = self._calculate_energy(neighbor_state)
                
                # Decide whether to accept the new state
                accept = False
                if neighbor_energy < current_energy:
                    # Always accept better states
                    accept = True
                else:
                    # Accept worse states with probability based on temperature
                    energy_delta = neighbor_energy - current_energy
                    acceptance_probability = math.exp(-energy_delta / temperature)
                    accept = random.random() < acceptance_probability
                
                # Update adaptive schedule if used
                if adaptive_schedule:
                    self.annealing_schedule.record_acceptance(accept)  # type: ignore
                
                # Update state if accepted
                if accept:
                    current_state = neighbor_state
                    current_energy = neighbor_energy
                    accepted_moves += 1
                    
                    # Update best state if this is better
                    if current_energy < best_energy:
                        best_state = current_state
                        best_energy = current_energy
                        iterations_without_improvement = 0
                    else:
                        iterations_without_improvement += 1
                else:
                    rejected_moves += 1
                    iterations_without_improvement += 1
                
                energy_history.append(current_energy)
                
                # Call callbacks if provided
                if callbacks:
                    callback_data = {
                        "iteration": iteration,
                        "temperature": temperature,
                        "current_energy": current_energy,
                        "best_energy": best_energy,
                        "accepted": accept,
                        "acceptance_ratio": accepted_moves / (iteration + 1),
                        "current_state": current_state
                    }
                    for callback in callbacks:
                        callback(callback_data)
                
                # Log progress periodically
                if iteration % 100 == 0 or iteration == self.max_iterations - 1:
                    logger.debug(
                        f"Iteration {iteration}/{self.max_iterations}: "
                        f"T={temperature:.4f}, E={current_energy:.4f}, "
                        f"Best={best_energy:.4f}, "
                        f"Accept ratio={accepted_moves/(iteration+1):.2f}"
                    )
                
                # Check early stopping condition
                if (iterations_without_improvement >= self.early_stopping_iterations and
                    abs(current_energy - best_energy) < self.early_stopping_threshold):
                    logger.info(
                        f"Early stopping at iteration {iteration}: "
                        f"No improvement for {iterations_without_improvement} iterations"
                    )
                    break
            
            # Final optimization steps
            optimized_memories = self._post_process(best_state)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Create statistics object
            stats = OptimizationStats(
                initial_energy=initial_energy,
                final_energy=best_energy,
                iterations=iteration + 1,
                accepted_moves=accepted_moves,
                rejected_moves=rejected_moves,
                duration_seconds=duration,
                temperature_history=temperature_history,
                energy_history=energy_history
            )
            
            logger.info(
                f"Memory optimization completed in {duration:.2f}s: "
                f"Energy reduced from {initial_energy:.4f} to {best_energy:.4f} "
                f"({stats.energy_reduction:.1f}% reduction)"
            )
            
            # Return in the same format as input
            if using_memory_store:
                result_store = memories.clone()
                result_store.clear()
                for memory in optimized_memories:
                    result_store.add(memory)
                return result_store, stats
            else:
                return optimized_memories, stats
                
        except Exception as e:
            logger.exception("Error during memory optimization")
            raise OptimizationError(f"Memory optimization failed: {str(e)}") from e
    
    def _clone_memories(self, memories: list[MemoryFragment]) -> list[MemoryFragment]:
        """
        Create a deep copy of memory fragments for optimization.
        
        Args:
            memories: List of memory fragments to clone
            
        Returns:
            Deep copy of memory fragments
        """
        return [memory.clone() for memory in memories]
    
    def _calculate_energy(self, state: list[MemoryFragment]) -> float:
        """
        Calculate the energy (cost function) of the current state.
        
        Lower energy indicates a better state. The energy function considers:
        - Redundancy between memories
        - Fragmentation of related concepts
        - Relevance and importance of memories
        - Memory access patterns
        
        Args:
            state: Current state of memory fragments
            
        Returns:
            Energy value (lower is better)
        """
        if not state:
            return 0.0
            
        # Initialize energy components
        redundancy_energy = 0.0
        fragmentation_energy = 0.0
        relevance_energy = 0.0
        
        # Calculate redundancy between memories
        for i, mem1 in enumerate(state):
            for _j, mem2 in enumerate(state[i+1:], i+1):
                sim = similarity_score(mem1, mem2)
                redundancy_energy += sim * sim
        
        # Normalize redundancy by number of pairs
        n_pairs = len(state) * (len(state) - 1) / 2
        if n_pairs > 0:
            redundancy_energy /= n_pairs
        
        # Calculate fragmentation (related memories should be connected)
        # Higher fragmentation = higher energy
        connection_graph = self._build_connection_graph(state)
        fragmentation_energy = self._calculate_fragmentation(connection_graph)
        
        # Calculate relevance (less relevant memories contribute more energy)
        for memory in state:
            # Invert relevance so lower relevance = higher energy
            relevance_energy += 1.0 - min(1.0, memory.relevance_score)
        
        # Normalize relevance
        if state:
            relevance_energy /= len(state)
        
        # Combine energy components with weights based on strategy
        if self.strategy == OptimizationStrategy.AGGRESSIVE:
            # Aggressive optimization prioritizes reducing redundancy
            weights = {
                "redundancy": 0.5,
                "fragmentation": 0.3,
                "relevance": 0.2
            }
        elif self.strategy == OptimizationStrategy.CONSERVATIVE:
            # Conservative optimization prioritizes maintaining relevance
            weights = {
                "redundancy": 0.2,
                "fragmentation": 0.3,
                "relevance": 0.5
            }
        elif self.strategy == OptimizationStrategy.ADAPTIVE:
            # Adaptive weights based on current state characteristics
            redundancy_level = min(1.0, redundancy_energy)
            weights = {
                "redundancy": 0.3 + 0.2 * redundancy_level,
                "fragmentation": 0.3,
                "relevance": 0.4 - 0.2 * redundancy_level
            }
        else:  # STANDARD
            # Balanced weights
            weights = {
                "redundancy": 0.4,
                "fragmentation": 0.3,
                "relevance": 0.3
            }
        
        # Calculate total energy
        total_energy = (
            weights["redundancy"] * redundancy_energy +
            weights["fragmentation"] * fragmentation_energy +
            weights["relevance"] * relevance_energy
        )
        
        return total_energy
    
    def _build_connection_graph(self, state: list[MemoryFragment]) -> dict[int, set[int]]:
        """
        Build a graph of connections between memory fragments.
        
        Args:
            state: Current state of memory fragments
            
        Returns:
            Dictionary mapping memory indices to sets of connected memory indices
        """
        connection_graph: dict[int, set[int]] = {i: set() for i in range(len(state))}
        
        # Connect memories with similarity above threshold
        similarity_threshold = 0.3
        for i, mem1 in enumerate(state):
            for j, mem2 in enumerate(state):
                if i != j and similarity_score(mem1, mem2) > similarity_threshold:
                    connection_graph[i].add(j)
                    connection_graph[j].add(i)
        
        return connection_graph
    
    def _calculate_fragmentation(self, connection_graph: dict[int, set[int]]) -> float:
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
                self._dfs(node, connection_graph, visited)
        
        # Normalize by number of nodes
        return (components - 1) / max(1, len(connection_graph))
    
    def _dfs(self, node: int, graph: dict[int, set[int]], visited: set[int]) -> None:
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
                self._dfs(neighbor, graph, visited)
    
    def _generate_neighbor(self, state: list[MemoryFragment]) -> list[MemoryFragment]:
        """
        Generate a neighboring state by applying a random transformation.
        
        Possible transformations:
        1. Merge two similar memories
        2. Split a memory into components
        3. Prune a low-relevance memory
        4. Adjust memory weights
        5. Reorder memories
        
        Args:
            state: Current state of memory fragments
            
        Returns:
            New state after applying transformation
        """
        if not state:
            return []
            
        # Create a copy of the state
        new_state = self._clone_memories(state)
        
        # Choose a random transformation
        transformation = random.choice([
            "merge", "adjust_weights", "reorder", "prune", "split"
        ])
        
        try:
            if transformation == "merge" and len(new_state) >= 2:
                # Merge two similar memories
                idx1, idx2 = random.sample(range(len(new_state)), 2)
                mem1, mem2 = new_state[idx1], new_state[idx2]
                
                # Only merge if similarity is above threshold
                if similarity_score(mem1, mem2) > 0.4:
                    merged = self._merge_memories(mem1, mem2)
                    # Replace the first memory with merged and remove the second
                    new_state[idx1] = merged
                    new_state.pop(idx2 if idx2 > idx1 else idx1)
                
            elif transformation == "split" and new_state:
                # Split a memory into components
                idx = random.randrange(len(new_state))
                memory = new_state[idx]
                
                # Only split if memory is complex enough
                if len(memory.content) > 50:
                    components = self._split_memory(memory)
                    if len(components) > 1:
                        # Replace original with first component and add others
                        new_state[idx] = components[0]
                        for comp in components[1:]:
                            new_state.append(comp)
                
            elif transformation == "prune" and new_state:
                # Prune a low-relevance memory
                # Sort by relevance and consider bottom 30% as candidates
                candidates = sorted(
                    range(len(new_state)), 
                    key=lambda i: new_state[i].relevance_score
                )
                prune_candidates = candidates[:max(1, int(len(candidates) * 0.3))]
                
                if prune_candidates:
                    idx_to_prune = random.choice(prune_candidates)
                    new_state.pop(idx_to_prune)
                
            elif transformation == "adjust_weights" and new_state:
                # Adjust memory weights
                idx = random.randrange(len(new_state))
                memory = new_state[idx]
                
                # Adjust relevance score slightly
                adjustment = random.uniform(-0.1, 0.1)
                memory.relevance_score = max(0.0, min(1.0, memory.relevance_score + adjustment))
                
            elif transformation == "reorder" and len(new_state) >= 2:
                # Reorder memories (swap two random memories)
                idx1, idx2 = random.sample(range(len(new_state)), 2)
                new_state[idx1], new_state[idx2] = new_state[idx2], new_state[idx1]
                
        except Exception as e:
            # Log error but continue with original state
            logger.warning(f"Error generating neighbor state: {str(e)}")
            return state
            
        return new_state
    
    def _merge_memories(self, mem1: MemoryFragment, mem2: MemoryFragment) -> MemoryFragment:
        """
        Merge two memory fragments into one.
        
        Args:
            mem1: First memory fragment
            mem2: Second memory fragment
            
        Returns:
            Merged memory fragment
        """
        # Create a new memory with combined content
        merged = mem1.clone()
        
        # Combine content intelligently
        if len(mem1.content) > len(mem2.content):
            # Use longer content as base
            merged.content = mem1.content
            # Add unique information from mem2
            if mem2.content not in mem1.content:
                merged.content += f" {mem2.content}"
        else:
            merged.content = mem2.content
            if mem1.content not in mem2.content:
                merged.content = f"{mem1.content} {merged.content}"
                
        # Take max of creation times
        merged.created_at = max(mem1.created_at, mem2.created_at)
        
        # Take max of relevance scores
        merged.relevance_score = max(mem1.relevance_score, mem2.relevance_score)
        
        # Combine tags
        merged.tags = list(set(mem1.tags + mem2.tags))
        
        return merged
    
    def _split_memory(self, memory: MemoryFragment) -> list[MemoryFragment]:
        """
        Split a memory fragment into multiple components.
        
        Args:
            memory: Memory fragment to split
            
        Returns:
            List of memory fragments after splitting
        """
        # Simple splitting by sentences
        content = memory.content
        sentences = [s.strip() for s in content.split('.') if s.strip()]
        
        # If not enough sentences, return original
        if len(sentences) <= 1:
            return [memory]
            
        # Group sentences into 1-3 components
        num_components = min(3, max(1, len(sentences) // 2))
        components = []
        
        sentences_per_component = len(sentences) // num_components
        for i in range(num_components):
            start_idx = i * sentences_per_component
            end_idx = start_idx + sentences_per_component if i < num_components - 1 else len(sentences)
            
            component_content = '. '.join(sentences[start_idx:end_idx])
            if not component_content.endswith('.'):
                component_content += '.'
                
            component = memory.clone()
            component.content = component_content
            component.relevance_score = max(0.1, memory.relevance_score - 0.1)
            components.append(component)
            
        return components
    
    def _post_process(self, state: list[MemoryFragment]) -> list[MemoryFragment]:
        """
        Perform final post-processing on the optimized state.
        
        Args:
            state: Optimized state of memory fragments
            
        Returns:
            Post-processed memory fragments
        """
        if not state:
            return []
            
        # Create a copy for post-processing
        processed_state = self._clone_memories(state)
        
        # Sort memories by relevance (most relevant first)
        processed_state.sort(key=lambda m: m.relevance_score, reverse=True)
        
        # Normalize relevance scores to [0.1, 1.0] range
        if processed_state:
            min_relevance = min(m.relevance_score for m in processed_state)
            max_relevance = max(m.relevance_score for m in processed_state)
            
            if max_relevance > min_relevance:
                for memory in processed_state:
                    normalized = 0.1 + 0.9 * (memory.relevance_score - min_relevance) / (max_relevance - min_relevance)
                    memory.relevance_score = normalized
        
        return processed_state


def create_optimizer(
    config: Optional[dict[str, Any]] = None,
    strategy: str = "STANDARD",
    schedule_type: str = "exponential",
    **kwargs
) -> AnnealingOptimizer:
    """
    Factory function to create an annealing optimizer with the specified configuration.
    
    Args:
        config: Configuration dictionary (default: None, uses system settings)
        strategy: Optimization strategy name (default: "STANDARD")
        schedule_type: Annealing schedule type (default: "exponential")
        **kwargs: Additional parameters for the optimizer
        
    Returns:
        Configured AnnealingOptimizer instance
        
    Raises:
        ValidationError: If parameters are invalid
    """
    # Parse strategy
    try:
        opt_strategy = OptimizationStrategy[strategy.upper()]
    except KeyError:
        raise ValidationError(
            f"Invalid optimization strategy: {strategy}. "
            f"Valid options: {', '.join(s.name for s in OptimizationStrategy)}"
        )
    
    # Create annealing schedule
    if schedule_type.lower() == "exponential":
        schedule = ExponentialAnnealingSchedule(**kwargs.get("schedule_params", {}))
    elif schedule_type.lower() == "linear":
        schedule = LinearAnnealingSchedule(**kwargs.get("schedule_params", {}))
    elif schedule_type.lower() == "adaptive":
        schedule = AdaptiveAnnealingSchedule(**kwargs.get("schedule_params", {}))
    else:
        raise ValidationError(
            f"Invalid schedule type: {schedule_type}. "
            f"Valid options: exponential, linear, adaptive"
        )
    
    # Filter kwargs to only include valid parameters for AnnealingOptimizer
    valid_params = {
        k: v for k, v in kwargs.items() 
        if k in ["max_iterations", "early_stopping_threshold", 
                "early_stopping_iterations", "random_seed"]
    }
    
    return AnnealingOptimizer(
        config=config,
        annealing_schedule=schedule,
        strategy=opt_strategy,
        **valid_params
    )