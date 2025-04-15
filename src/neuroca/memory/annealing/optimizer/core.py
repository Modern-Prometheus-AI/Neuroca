"""
Memory Annealing Optimizer Core Module

This module implements the main AnnealingOptimizer class for memory optimization
using simulated annealing techniques, leveraging modular components for different
aspects of the optimization process.
"""

import logging
import math
import random
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np

from neuroca.config.settings import get_settings
from neuroca.core.exceptions import OptimizationError, ValidationError
from neuroca.memory.annealing.optimizer.types import OptimizationStrategy
from neuroca.memory.annealing.optimizer.stats import OptimizationStats
from neuroca.memory.annealing.optimizer.schedules.base import AnnealingSchedule
from neuroca.memory.annealing.optimizer.schedules.exponential import ExponentialAnnealingSchedule
from neuroca.memory.annealing.optimizer.components.energy import calculate_energy
from neuroca.memory.annealing.optimizer.components.transformations import (
    clone_memories, generate_neighbor, post_process
)
from neuroca.memory.models.memory_item import MemoryItem
from neuroca.memory.interfaces.memory_store import MemoryStore

# Configure logger
logger = logging.getLogger(__name__)


class AnnealingOptimizer:
    """
    Memory optimizer using simulated annealing techniques.
    
    This class implements memory optimization through simulated annealing,
    allowing for consolidation, pruning, and reorganization of memory fragments
    to improve overall system performance and memory quality.
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
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
        memories: Union[List[MemoryItem], MemoryStore],
        callbacks: Optional[List[Callable[[Dict[str, Any]], None]]] = None
    ) -> Tuple[Union[List[MemoryItem], MemoryStore], OptimizationStats]:
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
            # Execute the annealing process
            optimized_fragments, stats = self._run_annealing_process(memory_fragments, callbacks)
            
            # Return in the same format as input
            if using_memory_store:
                result_store = memories.clone()
                result_store.clear()
                for memory in optimized_fragments:
                    result_store.add(memory)
                return result_store, stats
            else:
                return optimized_fragments, stats
                
        except Exception as e:
            logger.exception("Error during memory optimization")
            raise OptimizationError(f"Memory optimization failed: {str(e)}") from e
    
    def _run_annealing_process(
        self,
        memory_fragments: List[MemoryItem],
        callbacks: Optional[List[Callable[[Dict[str, Any]], None]]] = None
    ) -> Tuple[List[MemoryItem], OptimizationStats]:
        """
        Run the simulated annealing optimization process.
        
        Args:
            memory_fragments: List of memory fragments to optimize
            callbacks: Optional list of callback functions
            
        Returns:
            Tuple containing optimized fragments and statistics
        """
        # Create working copy of memories
        current_state = clone_memories(memory_fragments)
        
        # Start timing
        start_time = time.time()
        
        # Calculate initial energy
        current_energy = calculate_energy(current_state, self.strategy)
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
        adaptive_schedule = hasattr(self.annealing_schedule, 'record_acceptance')
        
        # Main annealing loop
        iteration = 0
        for iteration in range(self.max_iterations):
            # Get current temperature
            temperature = self.annealing_schedule.get_temperature(iteration, self.max_iterations)
            temperature_history.append(temperature)
            
            # Generate neighbor state
            neighbor_state = generate_neighbor(current_state)
            neighbor_energy = calculate_energy(neighbor_state, self.strategy)
            
            # Decide whether to accept the new state
            accept = self._decide_acceptance(current_energy, neighbor_energy, temperature)
            
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
                self._execute_callbacks(
                    callbacks, iteration, temperature, current_energy, 
                    best_energy, accept, accepted_moves, current_state
                )
            
            # Log progress periodically
            if iteration % 100 == 0 or iteration == self.max_iterations - 1:
                logger.debug(
                    f"Iteration {iteration}/{self.max_iterations}: "
                    f"T={temperature:.4f}, E={current_energy:.4f}, "
                    f"Best={best_energy:.4f}, "
                    f"Accept ratio={accepted_moves/(iteration+1):.2f}"
                )
            
            # Check early stopping condition
            if self._should_stop_early(iterations_without_improvement, current_energy, best_energy):
                logger.info(
                    f"Early stopping at iteration {iteration}: "
                    f"No improvement for {iterations_without_improvement} iterations"
                )
                break
        
        # Final optimization steps
        optimized_memories = post_process(best_state)
        
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
        
        return optimized_memories, stats
    
    def _decide_acceptance(self, current_energy: float, neighbor_energy: float, temperature: float) -> bool:
        """
        Decide whether to accept a new state.
        
        Args:
            current_energy: Energy of current state
            neighbor_energy: Energy of neighbor state
            temperature: Current temperature
            
        Returns:
            True if the new state should be accepted, False otherwise
        """
        if neighbor_energy < current_energy:
            # Always accept better states
            return True
        else:
            # Accept worse states with probability based on temperature
            energy_delta = neighbor_energy - current_energy
            acceptance_probability = math.exp(-energy_delta / temperature)
            return random.random() < acceptance_probability
    
    def _should_stop_early(
        self, 
        iterations_without_improvement: int,
        current_energy: float,
        best_energy: float
    ) -> bool:
        """
        Determine if the annealing process should stop early.
        
        Args:
            iterations_without_improvement: Number of iterations without improvement
            current_energy: Current state energy
            best_energy: Best state energy
            
        Returns:
            True if the process should stop early, False otherwise
        """
        return (iterations_without_improvement >= self.early_stopping_iterations and
                abs(current_energy - best_energy) < self.early_stopping_threshold)
    
    def _execute_callbacks(
        self,
        callbacks: List[Callable[[Dict[str, Any]], None]],
        iteration: int,
        temperature: float,
        current_energy: float,
        best_energy: float,
        accepted: bool,
        accepted_moves: int,
        current_state: List[MemoryItem]
    ) -> None:
        """
        Execute callback functions.
        
        Args:
            callbacks: List of callback functions
            iteration: Current iteration
            temperature: Current temperature
            current_energy: Current energy
            best_energy: Best energy
            accepted: Whether the last move was accepted
            accepted_moves: Number of accepted moves
            current_state: Current state
        """
        callback_data = {
            "iteration": iteration,
            "temperature": temperature,
            "current_energy": current_energy,
            "best_energy": best_energy,
            "accepted": accepted,
            "acceptance_ratio": accepted_moves / (iteration + 1),
            "current_state": current_state
        }
        
        for callback in callbacks:
            callback(callback_data)
