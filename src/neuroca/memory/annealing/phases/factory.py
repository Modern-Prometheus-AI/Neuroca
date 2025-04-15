"""
Annealing Phase Factory Module

This module provides a factory for creating annealing phase instances.
"""

import logging
from typing import List, Tuple, Union

from neuroca.core.exceptions import InvalidPhaseError
from neuroca.memory.annealing.phases.types import PhaseType
from neuroca.memory.annealing.phases.config import PhaseConfig
from neuroca.memory.annealing.phases.base import AnnealingPhase
from neuroca.memory.annealing.phases.heating import HeatingPhase
from neuroca.memory.annealing.phases.rapid_cooling import RapidCoolingPhase
from neuroca.memory.annealing.phases.slow_cooling import SlowCoolingPhase
from neuroca.memory.annealing.phases.stabilization import StabilizationPhase
from neuroca.memory.annealing.phases.maintenance import MaintenancePhase
from neuroca.memory.annealing.phases.custom import CustomPhase

# Configure logger
logger = logging.getLogger(__name__)


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
    def create_default_phase_sequence() -> List[Tuple[PhaseType, PhaseConfig]]:
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
