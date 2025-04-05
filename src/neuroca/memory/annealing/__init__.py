"""
Memory Annealing Module
=======================

This module implements simulated annealing techniques for memory optimization in the
NeuroCognitive Architecture (NCA). Annealing is a process inspired by metallurgical
annealing where a system is gradually cooled to find optimal or near-optimal states.

In the context of memory systems, annealing helps to:
1. Consolidate and optimize memory structures
2. Reduce noise and strengthen important connections
3. Improve recall efficiency and accuracy
4. Simulate biological memory consolidation during rest/sleep phases

The module provides a framework for defining different annealing strategies,
temperature schedules, and acceptance criteria that can be applied to various
memory structures within the NCA.

Usage Examples:
--------------
```python
# Basic memory annealing with default parameters
from neuroca.memory.annealing import MemoryAnnealer
annealer = MemoryAnnealer()
annealer.anneal(memory_structure)

# Custom annealing with specific parameters
from neuroca.memory.annealing import MemoryAnnealer, ExponentialSchedule
schedule = ExponentialSchedule(initial_temp=100.0, cooling_rate=0.95)
annealer = MemoryAnnealer(
    temperature_schedule=schedule,
    max_iterations=1000,
    stability_threshold=0.001
)
result = annealer.anneal(memory_structure)
```
"""

import logging
import math
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Callable, Generic, Optional, Protocol, TypeVar

# Configure module logger
logger = logging.getLogger(__name__)

# Type variables for generic implementations
T = TypeVar('T')  # Type for memory structures
S = TypeVar('S')  # Type for state representations
E = TypeVar('E', bound=float)  # Type for energy values (typically float)


class AnnealingStrategy(Enum):
    """Enumeration of supported annealing strategies."""
    STANDARD = auto()  # Standard Metropolis algorithm
    FAST = auto()      # Fast annealing with quicker temperature reduction
    ADAPTIVE = auto()  # Adaptive annealing that adjusts based on progress
    QUANTUM = auto()   # Quantum-inspired annealing with tunneling effects


class AnnealingError(Exception):
    """Base exception for annealing-related errors."""
    pass


class InvalidParameterError(AnnealingError):
    """Exception raised when invalid parameters are provided."""
    pass


class AnnealingTimeoutError(AnnealingError):
    """Exception raised when annealing process times out."""
    pass


class ConvergenceFailureError(AnnealingError):
    """Exception raised when annealing fails to converge."""
    pass


class TemperatureSchedule(ABC):
    """Abstract base class for temperature scheduling in annealing processes."""
    
    @abstractmethod
    def initial_temperature(self) -> float:
        """Return the initial temperature for the annealing process."""
        pass
    
    @abstractmethod
    def temperature(self, step: int) -> float:
        """
        Calculate temperature for a given step.
        
        Args:
            step: Current step in the annealing process
            
        Returns:
            Current temperature value
        """
        pass
    
    @abstractmethod
    def is_frozen(self, current_temp: float) -> bool:
        """
        Determine if the system is considered frozen (annealing complete).
        
        Args:
            current_temp: Current temperature of the system
            
        Returns:
            True if the system is considered frozen, False otherwise
        """
        pass


class LinearSchedule(TemperatureSchedule):
    """Linear temperature reduction schedule."""
    
    def __init__(
        self, 
        initial_temp: float = 100.0, 
        cooling_rate: float = 1.0,
        min_temp: float = 0.01
    ):
        """
        Initialize a linear cooling schedule.
        
        Args:
            initial_temp: Starting temperature
            cooling_rate: Rate of temperature decrease per step
            min_temp: Minimum temperature threshold for freezing
            
        Raises:
            InvalidParameterError: If parameters are invalid
        """
        if initial_temp <= 0:
            raise InvalidParameterError("Initial temperature must be positive")
        if cooling_rate <= 0:
            raise InvalidParameterError("Cooling rate must be positive")
        if min_temp <= 0 or min_temp >= initial_temp:
            raise InvalidParameterError(
                "Minimum temperature must be positive and less than initial temperature"
            )
            
        self._initial_temp = initial_temp
        self._cooling_rate = cooling_rate
        self._min_temp = min_temp
        
        logger.debug(
            f"Initialized LinearSchedule with initial_temp={initial_temp}, "
            f"cooling_rate={cooling_rate}, min_temp={min_temp}"
        )
    
    def initial_temperature(self) -> float:
        return self._initial_temp
    
    def temperature(self, step: int) -> float:
        """
        Calculate temperature using linear cooling.
        
        Args:
            step: Current step in the annealing process
            
        Returns:
            Current temperature value
        """
        if step < 0:
            raise InvalidParameterError("Step must be non-negative")
            
        temp = self._initial_temp - (step * self._cooling_rate)
        return max(temp, self._min_temp)
    
    def is_frozen(self, current_temp: float) -> bool:
        """
        Check if system is frozen (reached minimum temperature).
        
        Args:
            current_temp: Current temperature of the system
            
        Returns:
            True if frozen, False otherwise
        """
        return current_temp <= self._min_temp


class ExponentialSchedule(TemperatureSchedule):
    """Exponential temperature reduction schedule."""
    
    def __init__(
        self, 
        initial_temp: float = 100.0, 
        cooling_rate: float = 0.95,
        min_temp: float = 0.01
    ):
        """
        Initialize an exponential cooling schedule.
        
        Args:
            initial_temp: Starting temperature
            cooling_rate: Multiplicative factor for temperature reduction (0-1)
            min_temp: Minimum temperature threshold for freezing
            
        Raises:
            InvalidParameterError: If parameters are invalid
        """
        if initial_temp <= 0:
            raise InvalidParameterError("Initial temperature must be positive")
        if cooling_rate <= 0 or cooling_rate >= 1:
            raise InvalidParameterError("Cooling rate must be between 0 and 1 exclusive")
        if min_temp <= 0 or min_temp >= initial_temp:
            raise InvalidParameterError(
                "Minimum temperature must be positive and less than initial temperature"
            )
            
        self._initial_temp = initial_temp
        self._cooling_rate = cooling_rate
        self._min_temp = min_temp
        
        logger.debug(
            f"Initialized ExponentialSchedule with initial_temp={initial_temp}, "
            f"cooling_rate={cooling_rate}, min_temp={min_temp}"
        )
    
    def initial_temperature(self) -> float:
        return self._initial_temp
    
    def temperature(self, step: int) -> float:
        """
        Calculate temperature using exponential cooling.
        
        Args:
            step: Current step in the annealing process
            
        Returns:
            Current temperature value
        """
        if step < 0:
            raise InvalidParameterError("Step must be non-negative")
            
        temp = self._initial_temp * (self._cooling_rate ** step)
        return max(temp, self._min_temp)
    
    def is_frozen(self, current_temp: float) -> bool:
        """
        Check if system is frozen (reached minimum temperature).
        
        Args:
            current_temp: Current temperature of the system
            
        Returns:
            True if frozen, False otherwise
        """
        return current_temp <= self._min_temp


class BoltzmannSchedule(TemperatureSchedule):
    """Boltzmann temperature reduction schedule (logarithmic cooling)."""
    
    def __init__(
        self, 
        initial_temp: float = 100.0,
        c: float = 1.0,
        min_temp: float = 0.01
    ):
        """
        Initialize a Boltzmann cooling schedule.
        
        Args:
            initial_temp: Starting temperature
            c: Cooling coefficient
            min_temp: Minimum temperature threshold for freezing
            
        Raises:
            InvalidParameterError: If parameters are invalid
        """
        if initial_temp <= 0:
            raise InvalidParameterError("Initial temperature must be positive")
        if c <= 0:
            raise InvalidParameterError("Cooling coefficient must be positive")
        if min_temp <= 0 or min_temp >= initial_temp:
            raise InvalidParameterError(
                "Minimum temperature must be positive and less than initial temperature"
            )
            
        self._initial_temp = initial_temp
        self._c = c
        self._min_temp = min_temp
        
        logger.debug(
            f"Initialized BoltzmannSchedule with initial_temp={initial_temp}, "
            f"c={c}, min_temp={min_temp}"
        )
    
    def initial_temperature(self) -> float:
        return self._initial_temp
    
    def temperature(self, step: int) -> float:
        """
        Calculate temperature using Boltzmann cooling.
        
        Args:
            step: Current step in the annealing process
            
        Returns:
            Current temperature value
        """
        if step < 0:
            raise InvalidParameterError("Step must be non-negative")
        
        # Avoid division by zero or log(1)
        if step <= 1:
            return self._initial_temp
            
        temp = self._initial_temp / math.log(1 + step * self._c)
        return max(temp, self._min_temp)
    
    def is_frozen(self, current_temp: float) -> bool:
        """
        Check if system is frozen (reached minimum temperature).
        
        Args:
            current_temp: Current temperature of the system
            
        Returns:
            True if frozen, False otherwise
        """
        return current_temp <= self._min_temp


@dataclass
class AnnealingResult(Generic[T, E]):
    """Results from an annealing process."""
    
    # The optimized memory structure
    final_state: T
    
    # Energy (quality metric) of the final state
    final_energy: E
    
    # Number of iterations performed
    iterations: int
    
    # Total time taken for annealing (seconds)
    time_taken: float
    
    # Whether the annealing process converged successfully
    converged: bool
    
    # Temperature at completion
    final_temperature: float
    
    # History of energy values (if tracking enabled)
    energy_history: Optional[list[E]] = None
    
    # History of acceptance rates (if tracking enabled)
    acceptance_history: Optional[list[float]] = None
    
    # Additional metrics and information
    metrics: dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize default values for optional fields."""
        if self.metrics is None:
            self.metrics = {}


class EnergyFunction(Protocol, Generic[T, E]):
    """Protocol for energy functions used in annealing."""
    
    def __call__(self, state: T) -> E:
        """
        Calculate the energy (quality metric) of a given state.
        
        Args:
            state: The state to evaluate
            
        Returns:
            Energy value (lower is better)
        """
        ...


class NeighborFunction(Protocol, Generic[T]):
    """Protocol for neighbor generation functions used in annealing."""
    
    def __call__(self, current_state: T) -> T:
        """
        Generate a neighboring state from the current state.
        
        Args:
            current_state: The current state
            
        Returns:
            A neighboring state
        """
        ...


class AcceptanceCriterion(Protocol, Generic[E]):
    """Protocol for acceptance criteria used in annealing."""
    
    def __call__(self, current_energy: E, new_energy: E, temperature: float) -> bool:
        """
        Determine whether to accept a new state.
        
        Args:
            current_energy: Energy of the current state
            new_energy: Energy of the proposed new state
            temperature: Current temperature
            
        Returns:
            True if the new state should be accepted, False otherwise
        """
        ...


def metropolis_criterion(current_energy: float, new_energy: float, temperature: float) -> bool:
    """
    Standard Metropolis acceptance criterion for simulated annealing.
    
    Args:
        current_energy: Energy of the current state
        new_energy: Energy of the proposed new state
        temperature: Current temperature
        
    Returns:
        True if the new state should be accepted, False otherwise
    """
    if new_energy <= current_energy:
        return True
    
    # Avoid division by zero or overflow
    if temperature <= 1e-10:
        return False
        
    try:
        # Calculate acceptance probability
        delta_e = new_energy - current_energy
        probability = math.exp(-delta_e / temperature)
        return random.random() < probability
    except (OverflowError, ValueError) as e:
        logger.warning(f"Numerical error in metropolis criterion: {e}")
        # If we have numerical issues, reject the move
        return False


class MemoryAnnealer(Generic[T, E]):
    """
    Implements simulated annealing for memory optimization.
    
    This class provides a framework for applying simulated annealing techniques
    to optimize memory structures in the NCA system.
    """
    
    def __init__(
        self,
        temperature_schedule: Optional[TemperatureSchedule] = None,
        acceptance_criterion: Optional[AcceptanceCriterion] = None,
        max_iterations: int = 1000,
        stability_threshold: float = 0.001,
        timeout_seconds: Optional[float] = None,
        track_history: bool = False,
        history_sampling_rate: int = 10,
        random_seed: Optional[int] = None
    ):
        """
        Initialize the memory annealer.
        
        Args:
            temperature_schedule: Schedule for temperature reduction
            acceptance_criterion: Function to determine state acceptance
            max_iterations: Maximum number of iterations
            stability_threshold: Energy change threshold for early stopping
            timeout_seconds: Maximum runtime in seconds (None for no limit)
            track_history: Whether to track energy and acceptance history
            history_sampling_rate: Record history every N iterations
            random_seed: Seed for random number generation
            
        Raises:
            InvalidParameterError: If parameters are invalid
        """
        # Validate parameters
        if max_iterations <= 0:
            raise InvalidParameterError("Maximum iterations must be positive")
        if stability_threshold < 0:
            raise InvalidParameterError("Stability threshold must be non-negative")
        if timeout_seconds is not None and timeout_seconds <= 0:
            raise InvalidParameterError("Timeout must be positive or None")
        if history_sampling_rate <= 0:
            raise InvalidParameterError("History sampling rate must be positive")
            
        # Set default temperature schedule if none provided
        self._temperature_schedule = temperature_schedule or ExponentialSchedule()
        
        # Set default acceptance criterion if none provided
        self._acceptance_criterion = acceptance_criterion or metropolis_criterion
        
        self._max_iterations = max_iterations
        self._stability_threshold = stability_threshold
        self._timeout_seconds = timeout_seconds
        self._track_history = track_history
        self._history_sampling_rate = history_sampling_rate
        
        # Initialize random number generator
        if random_seed is not None:
            random.seed(random_seed)
            
        logger.debug(
            f"Initialized MemoryAnnealer with max_iterations={max_iterations}, "
            f"stability_threshold={stability_threshold}, timeout_seconds={timeout_seconds}"
        )
    
    def anneal(
        self,
        initial_state: T,
        energy_function: EnergyFunction[T, E],
        neighbor_function: NeighborFunction[T],
        callback: Optional[Callable[[int, T, E, float], None]] = None
    ) -> AnnealingResult[T, E]:
        """
        Perform simulated annealing to optimize a memory structure.
        
        Args:
            initial_state: Starting memory structure
            energy_function: Function to evaluate state quality (lower is better)
            neighbor_function: Function to generate neighboring states
            callback: Optional function called after each iteration
            
        Returns:
            AnnealingResult containing the optimized state and metrics
            
        Raises:
            AnnealingTimeoutError: If the process exceeds the timeout
            ConvergenceFailureError: If the process fails to converge
        """
        logger.info("Starting memory annealing process")
        start_time = time.time()
        
        # Initialize tracking variables
        current_state = initial_state
        current_energy = energy_function(current_state)
        best_state = current_state
        best_energy = current_energy
        
        # Initialize history tracking if enabled
        energy_history = [] if self._track_history else None
        acceptance_history = [] if self._track_history else None
        acceptance_count = 0
        
        # Get initial temperature
        temperature = self._temperature_schedule.initial_temperature()
        
        # Main annealing loop
        iteration = 0
        stable_iterations = 0
        last_energy = current_energy
        
        try:
            while iteration < self._max_iterations:
                # Check timeout
                if self._timeout_seconds and (time.time() - start_time) > self._timeout_seconds:
                    raise AnnealingTimeoutError(
                        f"Annealing timed out after {self._timeout_seconds} seconds"
                    )
                
                # Update temperature
                temperature = self._temperature_schedule.temperature(iteration)
                
                # Check if system is frozen
                if self._temperature_schedule.is_frozen(temperature):
                    logger.info(f"Annealing complete: system frozen at iteration {iteration}")
                    break
                
                # Generate neighbor state
                neighbor_state = neighbor_function(current_state)
                neighbor_energy = energy_function(neighbor_state)
                
                # Decide whether to accept the new state
                if self._acceptance_criterion(current_energy, neighbor_energy, temperature):
                    current_state = neighbor_state
                    current_energy = neighbor_energy
                    acceptance_count += 1
                    
                    # Update best state if this is better
                    if current_energy < best_energy:
                        best_state = current_state
                        best_energy = current_energy
                        logger.debug(f"New best state found at iteration {iteration} with energy {best_energy}")
                
                # Track history if enabled
                if self._track_history and iteration % self._history_sampling_rate == 0:
                    energy_history.append(current_energy)
                    # Calculate acceptance rate over the last window
                    if iteration > 0:
                        acceptance_rate = acceptance_count / self._history_sampling_rate
                        acceptance_history.append(acceptance_rate)
                        acceptance_count = 0
                
                # Check for stability (early stopping)
                energy_change = abs(current_energy - last_energy)
                if energy_change < self._stability_threshold:
                    stable_iterations += 1
                    # If stable for a significant number of iterations, stop
                    if stable_iterations >= max(50, self._max_iterations // 20):
                        logger.info(f"Annealing converged: stable for {stable_iterations} iterations")
                        break
                else:
                    stable_iterations = 0
                    last_energy = current_energy
                
                # Call the callback if provided
                if callback:
                    callback(iteration, current_state, current_energy, temperature)
                
                iteration += 1
            
            # Check if we reached max iterations without convergence
            if iteration >= self._max_iterations:
                logger.warning("Annealing reached maximum iterations without convergence")
                converged = False
            else:
                converged = True
            
            # Calculate total time
            total_time = time.time() - start_time
            
            # Create and return result
            result = AnnealingResult(
                final_state=best_state,
                final_energy=best_energy,
                iterations=iteration,
                time_taken=total_time,
                converged=converged,
                final_temperature=temperature,
                energy_history=energy_history,
                acceptance_history=acceptance_history,
                metrics={
                    "initial_energy": energy_function(initial_state),
                    "energy_improvement": energy_function(initial_state) - best_energy,
                    "stable_iterations": stable_iterations
                }
            )
            
            logger.info(
                f"Annealing completed in {total_time:.2f}s after {iteration} iterations. "
                f"Final energy: {best_energy}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error during annealing: {str(e)}", exc_info=True)
            raise


# Export public API
__all__ = [
    # Main classes
    'MemoryAnnealer',
    'AnnealingResult',
    
    # Temperature schedules
    'TemperatureSchedule',
    'LinearSchedule',
    'ExponentialSchedule',
    'BoltzmannSchedule',
    
    # Strategies and criteria
    'AnnealingStrategy',
    'metropolis_criterion',
    
    # Protocols
    'EnergyFunction',
    'NeighborFunction',
    'AcceptanceCriterion',
    
    # Exceptions
    'AnnealingError',
    'InvalidParameterError',
    'AnnealingTimeoutError',
    'ConvergenceFailureError',
]