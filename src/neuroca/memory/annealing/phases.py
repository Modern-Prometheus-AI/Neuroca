"""
Memory Annealing Phases Module.

This module defines the different phases of memory annealing in the NeuroCognitive Architecture.
Memory annealing is a process inspired by metallurgical annealing, where memories are consolidated,
strengthened, or weakened based on various factors including recency, importance, and relevance.

The module provides:
1. Base class for annealing phases
2. Concrete implementations of different annealing phases
3. Phase transition logic and scheduling
4. Configuration parameters for each phase

Each phase represents a specific state in the memory consolidation process, with different
temperature ranges and behaviors that affect how memories are processed.

Usage:
    from neuroca.memory.annealing.phases import AnnealingPhaseFactory
    
    # Create a phase based on configuration
    phase = AnnealingPhaseFactory.create_phase(phase_type="slow_cooling", 
                                              initial_temp=0.8,
                                              config=phase_config)
    
    # Apply the phase to a memory item
    modified_memory = phase.process_memory(memory_item)
"""

import abc
import enum
import logging
import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, Union

import numpy as np

from neuroca.core.exceptions import ConfigurationError, InvalidPhaseError
from neuroca.memory.models import MemoryItem

# Configure logger
logger = logging.getLogger(__name__)


class PhaseType(enum.Enum):
    """Enumeration of available annealing phase types."""
    
    HEATING = "heating"
    RAPID_COOLING = "rapid_cooling"
    SLOW_COOLING = "slow_cooling"
    STABILIZATION = "stabilization"
    MAINTENANCE = "maintenance"
    CUSTOM = "custom"


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


class AnnealingPhase(abc.ABC):
    """Base abstract class for all annealing phases.
    
    This class defines the interface and common functionality for all annealing phases.
    Each phase has a temperature range, duration, and specific behavior for processing memories.
    """
    
    def __init__(self, initial_temp: float, config: PhaseConfig):
        """Initialize the annealing phase.
        
        Args:
            initial_temp: Starting temperature for this phase (0.0 to 1.0)
            config: Configuration parameters for this phase
            
        Raises:
            ConfigurationError: If the initial temperature is outside the valid range
                                or incompatible with the phase configuration
        """
        if not 0 <= initial_temp <= 1:
            raise ConfigurationError(f"Initial temperature {initial_temp} must be between 0 and 1")
        
        if initial_temp < config.min_temperature or initial_temp > config.max_temperature:
            raise ConfigurationError(
                f"Initial temperature {initial_temp} is outside the configured range "
                f"[{config.min_temperature}, {config.max_temperature}]"
            )
        
        self.current_temp = initial_temp
        self.config = config
        self.start_time = datetime.now()
        self.phase_complete = False
        
        logger.debug(
            "Initialized %s phase with temperature %.3f and config: %s",
            self.__class__.__name__,
            initial_temp,
            config
        )
    
    @property
    def elapsed_time(self) -> float:
        """Calculate the elapsed time since the phase started.
        
        Returns:
            Elapsed time in seconds
        """
        return (datetime.now() - self.start_time).total_seconds()
    
    @property
    def phase_progress(self) -> float:
        """Calculate the progress of the phase as a percentage.
        
        Returns:
            Progress as a value between 0.0 and 1.0
        """
        progress = min(self.elapsed_time / self.config.duration_seconds, 1.0)
        return progress
    
    def update_temperature(self) -> float:
        """Update the current temperature based on phase-specific logic.
        
        This method must be implemented by concrete phase classes.
        
        Returns:
            The updated temperature value
        """
        if self.phase_progress >= 1.0:
            self.phase_complete = True
            
        return self._update_temperature_impl()
    
    @abc.abstractmethod
    def _update_temperature_impl(self) -> float:
        """Implementation of temperature update logic specific to each phase.
        
        Returns:
            The updated temperature value
        """
        pass
    
    def process_memory(self, memory: MemoryItem) -> MemoryItem:
        """Process a memory item according to the current phase and temperature.
        
        This method applies phase-specific transformations to the memory item,
        potentially modifying its strength, connections, or other attributes.
        
        Args:
            memory: The memory item to process
            
        Returns:
            The processed memory item
            
        Raises:
            ValueError: If the memory item is invalid or incompatible with this phase
        """
        if not memory:
            raise ValueError("Cannot process None memory item")
        
        # Update temperature before processing
        self.update_temperature()
        
        # Apply common processing logic
        processed_memory = self._apply_common_processing(memory)
        
        # Apply phase-specific processing
        return self._process_memory_impl(processed_memory)
    
    def _apply_common_processing(self, memory: MemoryItem) -> MemoryItem:
        """Apply common processing logic to a memory item.
        
        This method handles processing steps that are common across all phases.
        
        Args:
            memory: The memory item to process
            
        Returns:
            The processed memory item
        """
        # Create a copy to avoid modifying the original
        processed = memory.copy()
        
        # Apply temperature-based decay
        if hasattr(processed, "strength"):
            decay = self.config.decay_factor * self.current_temp
            processed.strength = max(0.0, processed.strength - decay)
        
        # Apply volatility effects (random fluctuations)
        if hasattr(processed, "strength"):
            volatility_effect = (np.random.random() - 0.5) * self.config.volatility * self.current_temp
            processed.strength = max(0.0, min(1.0, processed.strength + volatility_effect))
        
        return processed
    
    @abc.abstractmethod
    def _process_memory_impl(self, memory: MemoryItem) -> MemoryItem:
        """Implementation of memory processing logic specific to each phase.
        
        Args:
            memory: The memory item to process
            
        Returns:
            The processed memory item
        """
        pass
    
    def is_complete(self) -> bool:
        """Check if the phase is complete.
        
        Returns:
            True if the phase is complete, False otherwise
        """
        return self.phase_complete or self.phase_progress >= 1.0
    
    def get_state(self) -> dict[str, Any]:
        """Get the current state of the phase.
        
        Returns:
            Dictionary containing the current state
        """
        return {
            "phase_type": self.__class__.__name__,
            "current_temperature": self.current_temp,
            "progress": self.phase_progress,
            "elapsed_time": self.elapsed_time,
            "is_complete": self.is_complete(),
            "config": {
                "duration_seconds": self.config.duration_seconds,
                "min_temperature": self.config.min_temperature,
                "max_temperature": self.config.max_temperature,
                "cooling_rate": self.config.cooling_rate,
                "heating_rate": self.config.heating_rate,
            }
        }


class HeatingPhase(AnnealingPhase):
    """Heating phase of memory annealing.
    
    During this phase, the temperature increases, making memories more volatile
    and susceptible to change. This phase is typically used to prepare memories
    for reorganization or to break down rigid memory structures.
    """
    
    def _update_temperature_impl(self) -> float:
        """Implement temperature increase for heating phase.
        
        Returns:
            The updated temperature value
        """
        # Calculate target temperature based on progress
        target_temp = min(
            self.config.max_temperature,
            self.config.min_temperature + 
            (self.config.max_temperature - self.config.min_temperature) * self.phase_progress
        )
        
        # Gradually move current temperature toward target
        temp_diff = target_temp - self.current_temp
        self.current_temp += temp_diff * self.config.heating_rate
        
        logger.debug(
            "Heating phase: progress=%.2f, temperature=%.3f, target=%.3f",
            self.phase_progress,
            self.current_temp,
            target_temp
        )
        
        return self.current_temp
    
    def _process_memory_impl(self, memory: MemoryItem) -> MemoryItem:
        """Process memory during heating phase.
        
        In the heating phase, memories become more malleable and connections
        between related memories may be strengthened or weakened.
        
        Args:
            memory: The memory item to process
            
        Returns:
            The processed memory item
        """
        # Increase memory malleability based on temperature
        if hasattr(memory, "malleability"):
            memory.malleability = min(1.0, memory.malleability + (self.current_temp * 0.1))
        
        # Potentially strengthen important memories that should survive heating
        if hasattr(memory, "importance") and hasattr(memory, "strength"):
            if memory.importance > 0.7:  # Important memories
                # Strengthen important memories to counteract general decay
                reinforcement = self.config.reinforcement_factor * memory.importance
                memory.strength = min(1.0, memory.strength + reinforcement)
        
        return memory


class RapidCoolingPhase(AnnealingPhase):
    """Rapid cooling phase of memory annealing.
    
    This phase rapidly decreases temperature, quickly solidifying memory structures.
    It's useful for preserving important insights or patterns discovered during
    the heating phase, but may result in suboptimal memory organization.
    """
    
    def _update_temperature_impl(self) -> float:
        """Implement rapid temperature decrease.
        
        Returns:
            The updated temperature value
        """
        # Exponential cooling function for rapid decrease
        cooling_factor = math.exp(-5 * self.phase_progress)
        temp_range = self.config.max_temperature - self.config.min_temperature
        
        self.current_temp = self.config.min_temperature + temp_range * cooling_factor
        
        logger.debug(
            "Rapid cooling phase: progress=%.2f, temperature=%.3f, cooling_factor=%.3f",
            self.phase_progress,
            self.current_temp,
            cooling_factor
        )
        
        return self.current_temp
    
    def _process_memory_impl(self, memory: MemoryItem) -> MemoryItem:
        """Process memory during rapid cooling phase.
        
        In rapid cooling, strong memories are preserved while weak ones may be
        rapidly forgotten. This creates a more focused but potentially less nuanced
        memory structure.
        
        Args:
            memory: The memory item to process
            
        Returns:
            The processed memory item
        """
        # Decrease malleability rapidly
        if hasattr(memory, "malleability"):
            memory.malleability = max(0.0, memory.malleability - (0.2 * (1 - self.current_temp)))
        
        # Apply threshold-based consolidation
        if hasattr(memory, "strength"):
            if memory.strength > self.config.consolidation_threshold:
                # Strengthen memories above threshold
                memory.strength = min(1.0, memory.strength + (0.1 * (1 - self.current_temp)))
            else:
                # Weaken memories below threshold
                memory.strength = max(0.0, memory.strength - (0.15 * (1 - self.current_temp)))
        
        return memory


class SlowCoolingPhase(AnnealingPhase):
    """Slow cooling phase of memory annealing.
    
    This phase gradually decreases temperature, allowing for more optimal
    organization of memory structures. It balances between preserving important
    memories and allowing for some flexibility in memory organization.
    """
    
    def _update_temperature_impl(self) -> float:
        """Implement gradual temperature decrease.
        
        Returns:
            The updated temperature value
        """
        # Linear cooling with slight curve
        temp_range = self.config.max_temperature - self.config.min_temperature
        cooling_progress = math.pow(self.phase_progress, 1.2)  # Slightly curved cooling
        
        self.current_temp = self.config.max_temperature - (temp_range * cooling_progress)
        self.current_temp = max(self.current_temp, self.config.min_temperature)
        
        logger.debug(
            "Slow cooling phase: progress=%.2f, temperature=%.3f",
            self.phase_progress,
            self.current_temp
        )
        
        return self.current_temp
    
    def _process_memory_impl(self, memory: MemoryItem) -> MemoryItem:
        """Process memory during slow cooling phase.
        
        In slow cooling, memories are gradually consolidated, with important and
        frequently accessed memories being strengthened while less important ones
        may be weakened.
        
        Args:
            memory: The memory item to process
            
        Returns:
            The processed memory item
        """
        # Gradually decrease malleability
        if hasattr(memory, "malleability"):
            memory.malleability = max(0.1, memory.malleability - (0.05 * (1 - self.current_temp)))
        
        # Apply nuanced consolidation based on multiple factors
        if hasattr(memory, "strength") and hasattr(memory, "access_count"):
            # Consider both strength and access frequency
            consolidation_score = (memory.strength * 0.7) + (min(1.0, memory.access_count / 10) * 0.3)
            
            if consolidation_score > self.config.consolidation_threshold:
                # Strengthen memories with high consolidation score
                reinforcement = self.config.reinforcement_factor * (1 - self.current_temp)
                memory.strength = min(1.0, memory.strength + reinforcement)
            else:
                # Gradually weaken memories with low consolidation score
                decay = self.config.decay_factor * (1 - self.current_temp) * 0.5
                memory.strength = max(0.0, memory.strength - decay)
        
        return memory


class StabilizationPhase(AnnealingPhase):
    """Stabilization phase of memory annealing.
    
    This phase maintains a low but non-zero temperature, allowing for minor
    adjustments to memory structures while generally preserving their organization.
    It helps to fine-tune memory connections and strengths.
    """
    
    def _update_temperature_impl(self) -> float:
        """Implement temperature stabilization.
        
        Returns:
            The updated temperature value
        """
        # Maintain a low, slightly fluctuating temperature
        base_temp = self.config.min_temperature + (
            (self.config.max_temperature - self.config.min_temperature) * 0.2
        )
        
        # Add small oscillations
        oscillation = math.sin(self.phase_progress * 6 * math.pi) * 0.05
        self.current_temp = max(self.config.min_temperature, 
                               min(self.config.max_temperature, 
                                  base_temp + oscillation))
        
        logger.debug(
            "Stabilization phase: progress=%.2f, temperature=%.3f",
            self.phase_progress,
            self.current_temp
        )
        
        return self.current_temp
    
    def _process_memory_impl(self, memory: MemoryItem) -> MemoryItem:
        """Process memory during stabilization phase.
        
        In stabilization, memory structures are fine-tuned, with minor adjustments
        to strengths and connections based on importance and relevance.
        
        Args:
            memory: The memory item to process
            
        Returns:
            The processed memory item
        """
        # Fine-tune memory attributes
        if hasattr(memory, "malleability"):
            # Reduce malleability to a stable low value
            target_malleability = 0.2
            memory.malleability = memory.malleability * 0.9 + target_malleability * 0.1
        
        if hasattr(memory, "strength") and hasattr(memory, "importance"):
            # Align strength with importance during stabilization
            strength_diff = memory.importance - memory.strength
            adjustment = strength_diff * 0.05
            memory.strength = max(0.0, min(1.0, memory.strength + adjustment))
        
        # Stabilize connections if they exist
        if hasattr(memory, "connections") and isinstance(memory.connections, dict):
            for connection_id, strength in memory.connections.items():
                # Strengthen important connections, weaken trivial ones
                if strength > 0.6:  # Important connection
                    memory.connections[connection_id] = min(1.0, strength + 0.01)
                elif strength < 0.3:  # Weak connection
                    memory.connections[connection_id] = max(0.0, strength - 0.01)
        
        return memory


class MaintenancePhase(AnnealingPhase):
    """Maintenance phase of memory annealing.
    
    This phase keeps temperature at a minimal level, focusing on preserving
    established memory structures while allowing for very minor adjustments
    based on new information or access patterns.
    """
    
    def _update_temperature_impl(self) -> float:
        """Implement temperature maintenance at low level.
        
        Returns:
            The updated temperature value
        """
        # Maintain a very low, stable temperature
        target_temp = self.config.min_temperature + (
            (self.config.max_temperature - self.config.min_temperature) * 0.1
        )
        
        # Gradually approach target temperature
        temp_diff = target_temp - self.current_temp
        self.current_temp += temp_diff * 0.1
        
        logger.debug(
            "Maintenance phase: progress=%.2f, temperature=%.3f",
            self.phase_progress,
            self.current_temp
        )
        
        return self.current_temp
    
    def _process_memory_impl(self, memory: MemoryItem) -> MemoryItem:
        """Process memory during maintenance phase.
        
        In maintenance, the focus is on preserving memory structures while allowing
        for minor reinforcement of frequently accessed memories.
        
        Args:
            memory: The memory item to process
            
        Returns:
            The processed memory item
        """
        # Set malleability to a very low value
        if hasattr(memory, "malleability"):
            memory.malleability = max(0.05, memory.malleability * 0.9)
        
        # Apply minimal reinforcement for recently accessed memories
        if hasattr(memory, "last_accessed") and hasattr(memory, "strength"):
            time_since_access = (datetime.now() - memory.last_accessed).total_seconds()
            
            # Reinforce recently accessed memories
            if time_since_access < 3600:  # Accessed within the last hour
                recency_factor = max(0, 1 - (time_since_access / 3600))
                reinforcement = 0.01 * recency_factor
                memory.strength = min(1.0, memory.strength + reinforcement)
        
        # Apply very slow decay to all memories
        if hasattr(memory, "strength"):
            minimal_decay = 0.001 * self.current_temp
            memory.strength = max(0.0, memory.strength - minimal_decay)
        
        return memory


class CustomPhase(AnnealingPhase):
    """Custom phase of memory annealing with configurable behavior.
    
    This phase allows for specialized annealing behaviors defined through
    custom parameters. It provides flexibility for experimental or specialized
    memory processing requirements.
    """
    
    def __init__(self, initial_temp: float, config: PhaseConfig):
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


class AnnealingPhaseFactory:
    """Factory class for creating annealing phase instances.
    
    This factory provides a centralized way to create different types of annealing
    phases based on configuration parameters.
    """
    
    @staticmethod
    def create_phase(
        phase_type: Union[str, PhaseType],
        initial_temp: float,
        config: PhaseConfig
    ) -> AnnealingPhase:
        """Create an annealing phase instance.
        
        Args:
            phase_type: Type of phase to create
            initial_temp: Initial temperature for the phase
            config: Configuration parameters for the phase
            
        Returns:
            An instance of the requested annealing phase
            
        Raises:
            InvalidPhaseError: If the requested phase type is unknown
        """
        # Convert string to enum if needed
        if isinstance(phase_type, str):
            try:
                phase_type = PhaseType(phase_type.lower())
            except ValueError:
                raise InvalidPhaseError(f"Unknown phase type: {phase_type}")
        
        # Create the appropriate phase instance
        if phase_type == PhaseType.HEATING:
            return HeatingPhase(initial_temp, config)
        elif phase_type == PhaseType.RAPID_COOLING:
            return RapidCoolingPhase(initial_temp, config)
        elif phase_type == PhaseType.SLOW_COOLING:
            return SlowCoolingPhase(initial_temp, config)
        elif phase_type == PhaseType.STABILIZATION:
            return StabilizationPhase(initial_temp, config)
        elif phase_type == PhaseType.MAINTENANCE:
            return MaintenancePhase(initial_temp, config)
        elif phase_type == PhaseType.CUSTOM:
            return CustomPhase(initial_temp, config)
        else:
            raise InvalidPhaseError(f"Unsupported phase type: {phase_type}")
    
    @staticmethod
    def create_default_phase_sequence() -> list[tuple[PhaseType, PhaseConfig]]:
        """Create a default sequence of annealing phases.
        
        This method provides a standard sequence of phases that can be used
        for typical memory annealing processes.
        
        Returns:
            A list of (phase_type, config) tuples defining a sequence of phases
        """
        sequence = [
            (PhaseType.HEATING, PhaseConfig(
                duration_seconds=300,  # 5 minutes
                min_temperature=0.3,
                max_temperature=0.9,
                heating_rate=0.05,
                volatility=0.3
            )),
            (PhaseType.SLOW_COOLING, PhaseConfig(
                duration_seconds=600,  # 10 minutes
                min_temperature=0.2,
                max_temperature=0.8,
                cooling_rate=0.02,
                consolidation_threshold=0.6
            )),
            (PhaseType.STABILIZATION, PhaseConfig(
                duration_seconds=300,  # 5 minutes
                min_temperature=0.1,
                max_temperature=0.3,
                decay_factor=0.02
            )),
            (PhaseType.MAINTENANCE, PhaseConfig(
                duration_seconds=1800,  # 30 minutes
                min_temperature=0.05,
                max_temperature=0.15,
                decay_factor=0.01
            ))
        ]
        
        return sequence