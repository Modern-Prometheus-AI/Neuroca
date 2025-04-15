"""
Adaptive Annealing Schedule Module

This module provides the AdaptiveAnnealingSchedule class that adjusts temperature
based on acceptance rate during the optimization process.
"""

import logging
from typing import List
from neuroca.core.exceptions import ValidationError
from neuroca.memory.annealing.optimizer.schedules.base import AnnealingSchedule
from neuroca.memory.annealing.optimizer.schedules.linear import LinearAnnealingSchedule

# Configure logger
logger = logging.getLogger(__name__)


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
        self.acceptance_history: List[bool] = []
        
        logger.debug(
            f"Initialized AdaptiveAnnealingSchedule with "
            f"start_temp={start_temp}, end_temp={end_temp}, "
            f"target_acceptance={target_acceptance}, adjustment_rate={adjustment_rate}"
        )
        
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
        # Call the parent method for validation
        super().get_temperature(step, max_steps)
        
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
            
            logger.debug(
                f"Adaptive schedule: acceptance_rate={current_acceptance:.3f}, "
                f"base_temp={base_temp:.6f}, adjusted_temp={self.current_temp:.6f}"
            )
            
            return self.current_temp
        
        # Not enough history yet, use base temperature
        self.current_temp = base_temp
        return base_temp
        
    def reset(self) -> None:
        """Reset the schedule state to initial conditions."""
        self.current_temp = self.start_temp
        self.acceptance_history = []
        logger.debug(f"Reset adaptive scheduler to initial temperature {self.start_temp}")
