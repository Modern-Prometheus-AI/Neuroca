"""
Adaptive Annealing Scheduler

This module provides the AdaptiveScheduler class that adjusts temperature based on acceptance rate.
"""

import logging
from typing import List
from neuroca.memory.annealing.scheduler.core import AnnealingScheduler

logger = logging.getLogger(__name__)


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
        self.acceptance_history: List[bool] = []
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
