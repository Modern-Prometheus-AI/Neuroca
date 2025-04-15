"""
Custom Phase Module

This module implements a customizable phase of memory annealing.
"""

import logging
import math
from neuroca.core.exceptions import ConfigurationError
from neuroca.memory.annealing.phases.base import AnnealingPhase
from neuroca.memory.annealing.phases.config import PhaseConfig
from neuroca.memory.models import MemoryItem

# Configure logger
logger = logging.getLogger(__name__)


class CustomPhase(AnnealingPhase):
    """Custom phase of memory annealing with configurable behavior.
    
    This phase allows for specialized annealing behaviors defined through
    custom parameters. It provides flexibility for experimental or specialized
    memory processing requirements.
    """
    
    def __init__(self, initial_temp: float, config: 'PhaseConfig'):
        """Initialize the custom annealing phase.
        
        Args:
            initial_temp: Starting temperature for this phase (0.0 to 1.0)
            config: Configuration parameters for this phase
            
        Raises:
            ConfigurationError: If required custom parameters are missing
        """
        super().__init__(initial_temp, config)
        
        if not config.custom_params:
            raise ConfigurationError("Custom phase requires custom_params to be defined")
        
        # Extract custom parameters with defaults
        self.temp_function = config.custom_params.get("temp_function", "linear")
        self.strength_modifier = config.custom_params.get("strength_modifier", 1.0)
        self.connection_modifier = config.custom_params.get("connection_modifier", 1.0)
        self.custom_decay = config.custom_params.get("custom_decay", 0.01)
        
        logger.info(
            "Initialized custom phase with function=%s, strength_mod=%.2f, connection_mod=%.2f",
            self.temp_function,
            self.strength_modifier,
            self.connection_modifier
        )
    
    def _update_temperature_impl(self) -> float:
        """Implement custom temperature update logic.
        
        Returns:
            The updated temperature value
        """
        progress = self.phase_progress
        temp_range = self.config.max_temperature - self.config.min_temperature
        
        # Apply different temperature functions based on configuration
        if self.temp_function == "linear":
            self.current_temp = self.config.max_temperature - (temp_range * progress)
        elif self.temp_function == "exponential":
            self.current_temp = self.config.min_temperature + temp_range * math.exp(-3 * progress)
        elif self.temp_function == "sigmoid":
            # Sigmoid function centered at progress=0.5
            sigmoid_value = 1 / (1 + math.exp(10 * (progress - 0.5)))
            self.current_temp = self.config.min_temperature + temp_range * sigmoid_value
        elif self.temp_function == "oscillating":
            # Oscillating with decreasing amplitude
            amplitude = 1 - progress
            oscillation = math.sin(progress * 6 * math.pi) * amplitude * 0.3
            base_temp = self.config.max_temperature - (temp_range * progress)
            self.current_temp = max(self.config.min_temperature, 
                                   min(self.config.max_temperature, 
                                      base_temp + oscillation))
        else:
            # Default to linear if unknown function
            self.current_temp = self.config.max_temperature - (temp_range * progress)
        
        logger.debug(
            "Custom phase (%s): progress=%.2f, temperature=%.3f",
            self.temp_function,
            progress,
            self.current_temp
        )
        
        return self.current_temp
    
    def _process_memory_impl(self, memory: MemoryItem) -> MemoryItem:
        """Process memory using custom logic.
        
        Args:
            memory: The memory item to process
            
        Returns:
            The processed memory item
        """
        # Apply custom strength modifications
        if hasattr(memory, "strength"):
            # Apply custom strength modifier
            if memory.strength > 0.5:
                # Strengthen strong memories
                reinforcement = self.config.reinforcement_factor * self.strength_modifier
                memory.strength = min(1.0, memory.strength + reinforcement)
            else:
                # Weaken weak memories
                decay = self.custom_decay * self.strength_modifier
                memory.strength = max(0.0, memory.strength - decay)
        
        # Apply custom connection modifications if they exist
        if hasattr(memory, "connections") and isinstance(memory.connections, dict):
            for connection_id, strength in list(memory.connections.items()):
                # Apply connection modifier to connection strengths
                if self.connection_modifier > 1.0 and strength > 0.5:
                    # Strengthen important connections
                    memory.connections[connection_id] = min(1.0, strength + 0.02 * (self.connection_modifier - 1.0))
                elif self.connection_modifier < 1.0 and strength < 0.5:
                    # Weaken or prune weak connections
                    new_strength = strength - 0.02 * (1.0 - self.connection_modifier)
                    if new_strength <= 0:
                        del memory.connections[connection_id]
                    else:
                        memory.connections[connection_id] = new_strength
        
        # Apply custom parameters to malleability if it exists
        if hasattr(memory, "malleability") and "malleability_target" in self.config.custom_params:
            target = self.config.custom_params["malleability_target"]
            memory.malleability = memory.malleability * 0.9 + target * 0.1
        
        return memory
