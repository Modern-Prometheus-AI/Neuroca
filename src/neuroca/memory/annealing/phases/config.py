"""
Phase Configuration Module

This module provides the PhaseConfig dataclass for configuring annealing phases.
"""

from dataclasses import dataclass
from typing import Any, Optional

from neuroca.core.exceptions import ConfigurationError


@dataclass
class PhaseConfig:
    """Configuration parameters for an annealing phase.
    
    Attributes:
        duration_seconds: Duration of the phase in seconds
        min_temperature: Minimum temperature for this phase
        max_temperature: Maximum temperature for this phase
        cooling_rate: Rate at which temperature decreases (for cooling phases)
        heating_rate: Rate at which temperature increases (for heating phases)
        consolidation_threshold: Threshold for memory consolidation
        decay_factor: Factor controlling memory decay during this phase
        reinforcement_factor: Factor controlling memory reinforcement
        volatility: How volatile memories are during this phase
        custom_params: Additional custom parameters for specialized phases
    """
    
    duration_seconds: int
    min_temperature: float
    max_temperature: float
    cooling_rate: float = 0.01
    heating_rate: float = 0.01
    consolidation_threshold: float = 0.7
    decay_factor: float = 0.05
    reinforcement_factor: float = 0.1
    volatility: float = 0.2
    custom_params: Optional[dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate configuration parameters."""
        if self.min_temperature < 0 or self.min_temperature > 1:
            raise ConfigurationError("min_temperature must be between 0 and 1")
        
        if self.max_temperature < 0 or self.max_temperature > 1:
            raise ConfigurationError("max_temperature must be between 0 and 1")
        
        if self.min_temperature > self.max_temperature:
            raise ConfigurationError("min_temperature cannot be greater than max_temperature")
        
        if self.duration_seconds <= 0:
            raise ConfigurationError("duration_seconds must be positive")
        
        if self.cooling_rate <= 0 or self.cooling_rate > 1:
            raise ConfigurationError("cooling_rate must be between 0 and 1")
        
        if self.heating_rate <= 0 or self.heating_rate > 1:
            raise ConfigurationError("heating_rate must be between 0 and 1")
