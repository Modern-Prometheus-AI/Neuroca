"""
Annealing Temperature Scheduler for Memory Optimization

This module provides temperature scheduling functionality for simulated annealing processes
in the NeuroCognitive Architecture memory system. It implements various cooling schedules
that control how the "temperature" parameter decreases over time during annealing.

The temperature parameter controls the probability of accepting worse solutions during the
annealing process, which helps the system escape local optima and explore the solution space
more effectively before settling on a final state.

Usage examples:
    # Create a linear cooling schedule from 1.0 to 0.1 over 100 steps
    scheduler = LinearScheduler(start_temp=1.0, end_temp=0.1, max_steps=100)
    
    # Get temperature at step 50
    temp = scheduler.get_temperature(50)
    
    # Create an exponential cooling schedule
    scheduler = ExponentialScheduler(start_temp=1.0, decay_rate=0.95)
    
    # Use the adaptive scheduler that adjusts based on acceptance rate
    scheduler = AdaptiveScheduler(start_temp=1.0, target_acceptance=0.4)
"""

import logging
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Optional

# Configure logger
logger = logging.getLogger(__name__)


class SchedulerType(Enum):
    """Enumeration of available annealing scheduler types."""
    LINEAR = auto()
    EXPONENTIAL = auto()
    LOGARITHMIC = auto()
    COSINE = auto()
    ADAPTIVE = auto()
    CUSTOM = auto()


class AnnealingScheduler(ABC):
    """
    Abstract base class for annealing temperature schedulers.
    
    All concrete scheduler implementations should inherit from this class
    and implement the get_temperature method.
    """
    
    def __init__(self, start_temp: float, min_temp: float = 1e-6):
        """
        Initialize the annealing scheduler.
        
        Args:
            start_temp: The initial temperature value (must be positive)
            min_temp: The minimum temperature value to prevent numerical issues
        
        Raises:
            ValueError: If start_temp is not positive or min_temp is negative
        """
        if start_temp <= 0:
            raise ValueError("Starting temperature must be positive")
        if min_temp < 0:
            raise ValueError("Minimum temperature cannot be negative")
            
        self.start_temp = start_temp
        self.min_temp = min_temp
        self._validate_parameters()
        logger.debug(f"Initialized {self.__class__.__name__} with start_temp={start_temp}, min_temp={min_temp}")
    
    @abstractmethod
    def get_temperature(self, step: int) -> float:
        """
        Calculate the temperature for the given step.
        
        Args:
            step: The current step in the annealing process (0-indexed)
            
        Returns:
            The temperature value for the current step
        """
        pass
    
    def _validate_parameters(self) -> None:
        """
        Validate scheduler-specific parameters.
        
        This method should be overridden by subclasses to perform additional
        parameter validation beyond the basic checks in __init__.
        
        Raises:
            ValueError: If any parameters are invalid
        """
        pass
    
    def reset(self) -> None:
        """
        Reset the scheduler to its initial state.
        
        This method should be overridden by subclasses that maintain internal state.
        """
        pass


class LinearScheduler(AnnealingScheduler):
    """
    Linear cooling schedule that decreases temperature linearly from start_temp to end_temp.
    
    The temperature follows the formula: T(step) = start_temp - step * (start_temp - end_temp) / max_steps
    """
    
    def __init__(self, start_temp: float, end_temp: float, max_steps: int, min_temp: float = 1e-6):
        """
        Initialize a linear cooling schedule.
        
        Args:
            start_temp: The initial temperature value
            end_temp: The final temperature value
            max_steps: The total number of steps in the schedule
            min_temp: The minimum temperature value
            
        Raises:
            ValueError: If parameters are invalid
        """
        super().__init__(start_temp, min_temp)
        self.end_temp = max(end_temp, min_temp)
        self.max_steps = max_steps
        self._validate_parameters()
    
    def _validate_parameters(self) -> None:
        """Validate linear scheduler parameters."""
        if self.end_temp > self.start_temp:
            raise ValueError("End temperature must be less than or equal to start temperature")
        if self.max_steps <= 0:
            raise ValueError("Maximum steps must be positive")
    
    def get_temperature(self, step: int) -> float:
        """
        Calculate the temperature for the given step using linear cooling.
        
        Args:
            step: The current step in the annealing process
            
        Returns:
            The temperature value for the current step
        """
        if step < 0:
            raise ValueError("Step cannot be negative")
            
        if step >= self.max_steps:
            return self.end_temp
            
        temp = self.start_temp - step * (self.start_temp - self.end_temp) / self.max_steps
        return max(temp, self.min_temp)


class ExponentialScheduler(AnnealingScheduler):
    """
    Exponential cooling schedule that decreases temperature exponentially.
    
    The temperature follows the formula: T(step) = start_temp * (decay_rate ^ step)
    """
    
    def __init__(self, start_temp: float, decay_rate: float, min_temp: float = 1e-6):
        """
        Initialize an exponential cooling schedule.
        
        Args:
            start_temp: The initial temperature value
            decay_rate: The rate at which temperature decreases (between 0 and 1)
            min_temp: The minimum temperature value
            
        Raises:
            ValueError: If parameters are invalid
        """
        super().__init__(start_temp, min_temp)
        self.decay_rate = decay_rate
        self._validate_parameters()
    
    def _validate_parameters(self) -> None:
        """Validate exponential scheduler parameters."""
        if not 0 < self.decay_rate < 1:
            raise ValueError("Decay rate must be between 0 and 1 (exclusive)")
    
    def get_temperature(self, step: int) -> float:
        """
        Calculate the temperature for the given step using exponential cooling.
        
        Args:
            step: The current step in the annealing process
            
        Returns:
            The temperature value for the current step
        """
        if step < 0:
            raise ValueError("Step cannot be negative")
            
        temp = self.start_temp * (self.decay_rate ** step)
        return max(temp, self.min_temp)


class LogarithmicScheduler(AnnealingScheduler):
    """
    Logarithmic cooling schedule that decreases temperature logarithmically.
    
    The temperature follows the formula: T(step) = start_temp / (1 + c * log(1 + step))
    """
    
    def __init__(self, start_temp: float, c: float = 1.0, min_temp: float = 1e-6):
        """
        Initialize a logarithmic cooling schedule.
        
        Args:
            start_temp: The initial temperature value
            c: The cooling coefficient (controls cooling speed)
            min_temp: The minimum temperature value
            
        Raises:
            ValueError: If parameters are invalid
        """
        super().__init__(start_temp, min_temp)
        self.c = c
        self._validate_parameters()
    
    def _validate_parameters(self) -> None:
        """Validate logarithmic scheduler parameters."""
        if self.c <= 0:
            raise ValueError("Cooling coefficient must be positive")
    
    def get_temperature(self, step: int) -> float:
        """
        Calculate the temperature for the given step using logarithmic cooling.
        
        Args:
            step: The current step in the annealing process
            
        Returns:
            The temperature value for the current step
        """
        if step < 0:
            raise ValueError("Step cannot be negative")
            
        temp = self.start_temp / (1 + self.c * math.log(1 + step))
        return max(temp, self.min_temp)


class CosineScheduler(AnnealingScheduler):
    """
    Cosine cooling schedule that decreases temperature following a cosine curve.
    
    The temperature follows the formula: 
    T(step) = end_temp + 0.5 * (start_temp - end_temp) * (1 + cos(step * pi / max_steps))
    """
    
    def __init__(self, start_temp: float, end_temp: float, max_steps: int, min_temp: float = 1e-6):
        """
        Initialize a cosine cooling schedule.
        
        Args:
            start_temp: The initial temperature value
            end_temp: The final temperature value
            max_steps: The total number of steps in the schedule
            min_temp: The minimum temperature value
            
        Raises:
            ValueError: If parameters are invalid
        """
        super().__init__(start_temp, min_temp)
        self.end_temp = max(end_temp, min_temp)
        self.max_steps = max_steps
        self._validate_parameters()
    
    def _validate_parameters(self) -> None:
        """Validate cosine scheduler parameters."""
        if self.end_temp > self.start_temp:
            raise ValueError("End temperature must be less than or equal to start temperature")
        if self.max_steps <= 0:
            raise ValueError("Maximum steps must be positive")
    
    def get_temperature(self, step: int) -> float:
        """
        Calculate the temperature for the given step using cosine cooling.
        
        Args:
            step: The current step in the annealing process
            
        Returns:
            The temperature value for the current step
        """
        if step < 0:
            raise ValueError("Step cannot be negative")
            
        if step >= self.max_steps:
            return self.end_temp
            
        temp = self.end_temp + 0.5 * (self.start_temp - self.end_temp) * (
            1 + math.cos(step * math.pi / self.max_steps)
        )
        return max(temp, self.min_temp)


class AdaptiveScheduler(AnnealingScheduler):
    """
    Adaptive cooling schedule that adjusts temperature based on acceptance rate.
    
    This scheduler increases or decreases temperature to maintain a target
    acceptance rate of proposed moves in the annealing process.
    """
    
    def __init__(
        self, 
        start_temp: float, 
        target_acceptance: float = 0.4,
        adjustment_rate: float = 0.1,
        history_window: int = 100,
        min_temp: float = 1e-6
    ):
        """
        Initialize an adaptive cooling schedule.
        
        Args:
            start_temp: The initial temperature value
            target_acceptance: The target acceptance rate (between 0 and 1)
            adjustment_rate: How quickly to adjust temperature (between 0 and 1)
            history_window: Number of recent moves to consider for acceptance rate
            min_temp: The minimum temperature value
            
        Raises:
            ValueError: If parameters are invalid
        """
        super().__init__(start_temp, min_temp)
        self.target_acceptance = target_acceptance
        self.adjustment_rate = adjustment_rate
        self.history_window = history_window
        self.current_temp = start_temp
        self.acceptance_history: list[bool] = []
        self._validate_parameters()
    
    def _validate_parameters(self) -> None:
        """Validate adaptive scheduler parameters."""
        if not 0 < self.target_acceptance < 1:
            raise ValueError("Target acceptance rate must be between 0 and 1")
        if not 0 < self.adjustment_rate < 1:
            raise ValueError("Adjustment rate must be between 0 and 1")
        if self.history_window <= 0:
            raise ValueError("History window must be positive")
    
    def get_temperature(self, step: int) -> float:
        """
        Get the current temperature.
        
        For the adaptive scheduler, the step parameter is ignored since
        temperature is based on acceptance history rather than step count.
        
        Args:
            step: The current step (ignored in this implementation)
            
        Returns:
            The current temperature value
        """
        if step < 0:
            raise ValueError("Step cannot be negative")
            
        return max(self.current_temp, self.min_temp)
    
    def update(self, accepted: bool) -> None:
        """
        Update the temperature based on whether the last move was accepted.
        
        Args:
            accepted: Whether the last proposed move was accepted
        """
        # Add to history and maintain window size
        self.acceptance_history.append(accepted)
        if len(self.acceptance_history) > self.history_window:
            self.acceptance_history.pop(0)
        
        # Calculate current acceptance rate
        if not self.acceptance_history:
            return
            
        current_rate = sum(self.acceptance_history) / len(self.acceptance_history)
        
        # Adjust temperature based on difference from target rate
        if current_rate < self.target_acceptance:
            # Increase temperature to accept more moves
            self.current_temp *= (1 + self.adjustment_rate)
        else:
            # Decrease temperature to accept fewer moves
            self.current_temp *= (1 - self.adjustment_rate)
        
        logger.debug(
            f"Adaptive scheduler: acceptance_rate={current_rate:.3f}, "
            f"adjusted_temp={self.current_temp:.6f}"
        )
    
    def reset(self) -> None:
        """Reset the scheduler to its initial state."""
        self.current_temp = self.start_temp
        self.acceptance_history = []
        logger.debug(f"Reset adaptive scheduler to initial temperature {self.start_temp}")


class CustomScheduler(AnnealingScheduler):
    """
    Custom cooling schedule using a user-provided temperature function.
    
    This scheduler allows for arbitrary temperature schedules by accepting
    a custom function that calculates temperature based on step number.
    """
    
    def __init__(
        self, 
        temp_func: Callable[[int], float], 
        start_temp: float,
        min_temp: float = 1e-6
    ):
        """
        Initialize a custom cooling schedule.
        
        Args:
            temp_func: A function that takes a step number and returns a temperature
            start_temp: The initial temperature value (used for validation)
            min_temp: The minimum temperature value
            
        Raises:
            ValueError: If parameters are invalid
        """
        super().__init__(start_temp, min_temp)
        self.temp_func = temp_func
        
        # Validate that the function returns expected values
        try:
            test_temp = self.temp_func(0)
            if not isinstance(test_temp, (int, float)):
                raise ValueError("Temperature function must return a numeric value")
            if test_temp < 0:
                raise ValueError("Temperature function must return non-negative values")
        except Exception as e:
            raise ValueError(f"Invalid temperature function: {str(e)}")
    
    def get_temperature(self, step: int) -> float:
        """
        Calculate the temperature for the given step using the custom function.
        
        Args:
            step: The current step in the annealing process
            
        Returns:
            The temperature value for the current step
        
        Raises:
            ValueError: If step is negative or the temperature function fails
        """
        if step < 0:
            raise ValueError("Step cannot be negative")
            
        try:
            temp = self.temp_func(step)
            return max(temp, self.min_temp)
        except Exception as e:
            logger.error(f"Error in custom temperature function: {str(e)}")
            # Return minimum temperature as fallback
            return self.min_temp


@dataclass
class SchedulerConfig:
    """Configuration parameters for creating annealing schedulers."""
    scheduler_type: SchedulerType
    start_temp: float
    end_temp: Optional[float] = None
    max_steps: Optional[int] = None
    decay_rate: Optional[float] = None
    c: Optional[float] = None
    target_acceptance: Optional[float] = None
    adjustment_rate: Optional[float] = None
    history_window: Optional[int] = None
    temp_func: Optional[Callable[[int], float]] = None
    min_temp: float = 1e-6


class SchedulerFactory:
    """
    Factory class for creating annealing schedulers.
    
    This factory simplifies the creation of different scheduler types
    based on configuration parameters.
    """
    
    @staticmethod
    def create_scheduler(config: SchedulerConfig) -> AnnealingScheduler:
        """
        Create an annealing scheduler based on the provided configuration.
        
        Args:
            config: Configuration parameters for the scheduler
            
        Returns:
            An instance of the specified scheduler type
            
        Raises:
            ValueError: If the configuration is invalid for the specified scheduler type
        """
        try:
            if config.scheduler_type == SchedulerType.LINEAR:
                if config.end_temp is None or config.max_steps is None:
                    raise ValueError("Linear scheduler requires end_temp and max_steps")
                return LinearScheduler(
                    start_temp=config.start_temp,
                    end_temp=config.end_temp,
                    max_steps=config.max_steps,
                    min_temp=config.min_temp
                )
                
            elif config.scheduler_type == SchedulerType.EXPONENTIAL:
                if config.decay_rate is None:
                    raise ValueError("Exponential scheduler requires decay_rate")
                return ExponentialScheduler(
                    start_temp=config.start_temp,
                    decay_rate=config.decay_rate,
                    min_temp=config.min_temp
                )
                
            elif config.scheduler_type == SchedulerType.LOGARITHMIC:
                c = config.c if config.c is not None else 1.0
                return LogarithmicScheduler(
                    start_temp=config.start_temp,
                    c=c,
                    min_temp=config.min_temp
                )
                
            elif config.scheduler_type == SchedulerType.COSINE:
                if config.end_temp is None or config.max_steps is None:
                    raise ValueError("Cosine scheduler requires end_temp and max_steps")
                return CosineScheduler(
                    start_temp=config.start_temp,
                    end_temp=config.end_temp,
                    max_steps=config.max_steps,
                    min_temp=config.min_temp
                )
                
            elif config.scheduler_type == SchedulerType.ADAPTIVE:
                target = config.target_acceptance if config.target_acceptance is not None else 0.4
                adj_rate = config.adjustment_rate if config.adjustment_rate is not None else 0.1
                history = config.history_window if config.history_window is not None else 100
                return AdaptiveScheduler(
                    start_temp=config.start_temp,
                    target_acceptance=target,
                    adjustment_rate=adj_rate,
                    history_window=history,
                    min_temp=config.min_temp
                )
                
            elif config.scheduler_type == SchedulerType.CUSTOM:
                if config.temp_func is None:
                    raise ValueError("Custom scheduler requires a temperature function")
                return CustomScheduler(
                    temp_func=config.temp_func,
                    start_temp=config.start_temp,
                    min_temp=config.min_temp
                )
                
            else:
                raise ValueError(f"Unknown scheduler type: {config.scheduler_type}")
                
        except Exception as e:
            logger.error(f"Failed to create scheduler: {str(e)}")
            raise ValueError(f"Failed to create scheduler: {str(e)}") from e


# Convenience functions for common scheduler configurations
def create_linear_scheduler(
    start_temp: float, 
    end_temp: float, 
    max_steps: int,
    min_temp: float = 1e-6
) -> LinearScheduler:
    """
    Create a linear cooling schedule.
    
    Args:
        start_temp: The initial temperature value
        end_temp: The final temperature value
        max_steps: The total number of steps in the schedule
        min_temp: The minimum temperature value
        
    Returns:
        A configured LinearScheduler instance
    """
    return LinearScheduler(start_temp, end_temp, max_steps, min_temp)


def create_exponential_scheduler(
    start_temp: float, 
    decay_rate: float,
    min_temp: float = 1e-6
) -> ExponentialScheduler:
    """
    Create an exponential cooling schedule.
    
    Args:
        start_temp: The initial temperature value
        decay_rate: The rate at which temperature decreases (between 0 and 1)
        min_temp: The minimum temperature value
        
    Returns:
        A configured ExponentialScheduler instance
    """
    return ExponentialScheduler(start_temp, decay_rate, min_temp)


def create_adaptive_scheduler(
    start_temp: float, 
    target_acceptance: float = 0.4,
    min_temp: float = 1e-6
) -> AdaptiveScheduler:
    """
    Create an adaptive cooling schedule.
    
    Args:
        start_temp: The initial temperature value
        target_acceptance: The target acceptance rate (between 0 and 1)
        min_temp: The minimum temperature value
        
    Returns:
        A configured AdaptiveScheduler instance
    """
    return AdaptiveScheduler(start_temp, target_acceptance, min_temp=min_temp)