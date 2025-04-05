"""
Tubules Module for NeuroCognitive Architecture (NCA)

This module implements the tubules component of the memory system, inspired by
biological microtubules that serve as structural and transport elements in neurons.
In the NCA, tubules provide specialized memory pathways between different memory tiers
and facilitate efficient information routing and retrieval.

The tubules module serves as a critical infrastructure component that:
1. Establishes connections between memory components
2. Manages information flow between memory tiers
3. Implements priority-based routing mechanisms
4. Provides monitoring and diagnostics for memory pathways
5. Supports dynamic reconfiguration of memory connections

Usage:
    from neuroca.memory.tubules import TubuleNetwork, Tubule, TubuleConnection
    
    # Create a tubule network
    network = TubuleNetwork()
    
    # Add tubules between memory components
    network.add_tubule(
        source="working_memory",
        destination="long_term_memory",
        priority=TubulePriority.HIGH
    )
    
    # Transfer information through the tubule network
    result = network.transfer(data, source="sensory_buffer", destination="working_memory")

Note:
    This module is designed to work closely with other memory components and
    should be configured according to the specific memory architecture requirements.
"""

import enum
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

# Configure module logger
logger = logging.getLogger(__name__)

class TubuleError(Exception):
    """Base exception class for all tubule-related errors."""
    pass

class TubuleConnectionError(TubuleError):
    """Exception raised when tubule connections cannot be established or fail."""
    pass

class TubuleTransferError(TubuleError):
    """Exception raised when data transfer through tubules fails."""
    pass

class TubuleConfigurationError(TubuleError):
    """Exception raised when tubule configuration is invalid."""
    pass

class TubulePriority(enum.IntEnum):
    """Priority levels for tubule connections and data transfer."""
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    BACKGROUND = 4

@dataclass
class TubuleMetrics:
    """Metrics for monitoring tubule performance and health."""
    created_at: float = field(default_factory=time.time)
    last_transfer_at: Optional[float] = None
    transfer_count: int = 0
    transfer_volume_bytes: int = 0
    transfer_errors: int = 0
    avg_transfer_time_ms: float = 0.0
    
    def record_transfer(self, size_bytes: int, duration_ms: float, success: bool = True) -> None:
        """Record metrics for a single transfer operation.
        
        Args:
            size_bytes: Size of transferred data in bytes
            duration_ms: Duration of transfer in milliseconds
            success: Whether the transfer was successful
        """
        self.last_transfer_at = time.time()
        if success:
            self.transfer_count += 1
            self.transfer_volume_bytes += size_bytes
            # Update rolling average
            if self.transfer_count == 1:
                self.avg_transfer_time_ms = duration_ms
            else:
                self.avg_transfer_time_ms = (
                    (self.avg_transfer_time_ms * (self.transfer_count - 1) + duration_ms) / 
                    self.transfer_count
                )
        else:
            self.transfer_errors += 1

@dataclass
class TubuleConnection:
    """Represents a connection between two memory components via a tubule."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: str = ""
    destination: str = ""
    priority: TubulePriority = TubulePriority.MEDIUM
    bidirectional: bool = False
    active: bool = True
    max_capacity: Optional[int] = None
    metrics: TubuleMetrics = field(default_factory=TubuleMetrics)
    
    def __post_init__(self) -> None:
        """Validate connection configuration after initialization."""
        if not self.source:
            raise TubuleConfigurationError("Tubule connection requires a source")
        if not self.destination:
            raise TubuleConfigurationError("Tubule connection requires a destination")
        if self.source == self.destination:
            raise TubuleConfigurationError("Tubule source and destination cannot be the same")
        
        logger.debug(
            f"Created tubule connection: {self.source} -> {self.destination} "
            f"(priority={self.priority.name}, bidirectional={self.bidirectional})"
        )

class Tubule:
    """
    Represents a single tubule that can transfer information between memory components.
    
    A tubule is a specialized pathway that facilitates the movement of information
    between different memory components with specific characteristics like priority,
    capacity, and directionality.
    """
    
    def __init__(
        self, 
        source: str,
        destination: str,
        priority: TubulePriority = TubulePriority.MEDIUM,
        bidirectional: bool = False,
        max_capacity: Optional[int] = None
    ) -> None:
        """
        Initialize a new tubule between memory components.
        
        Args:
            source: Identifier of the source memory component
            destination: Identifier of the destination memory component
            priority: Priority level for this tubule
            bidirectional: Whether information can flow in both directions
            max_capacity: Maximum data capacity in bytes (None for unlimited)
        
        Raises:
            TubuleConfigurationError: If the configuration is invalid
        """
        self.connection = TubuleConnection(
            source=source,
            destination=destination,
            priority=priority,
            bidirectional=bidirectional,
            max_capacity=max_capacity
        )
        
        # Internal state
        self._transfer_in_progress: bool = False
        
        logger.debug(f"Initialized tubule: {self.connection.id}")
    
    def transfer(self, data: Any) -> bool:
        """
        Transfer data through the tubule.
        
        Args:
            data: The data to transfer
            
        Returns:
            bool: True if transfer was successful, False otherwise
            
        Raises:
            TubuleTransferError: If transfer fails due to tubule issues
        """
        if not self.connection.active:
            logger.warning(f"Attempted transfer on inactive tubule: {self.connection.id}")
            return False
        
        if self._transfer_in_progress:
            logger.warning(f"Tubule busy, transfer already in progress: {self.connection.id}")
            return False
        
        try:
            self._transfer_in_progress = True
            
            # Calculate approximate data size
            data_size = self._estimate_data_size(data)
            
            # Check capacity constraints
            if self.connection.max_capacity and data_size > self.connection.max_capacity:
                logger.error(
                    f"Data size ({data_size} bytes) exceeds tubule capacity "
                    f"({self.connection.max_capacity} bytes)"
                )
                return False
            
            # Simulate transfer with timing
            start_time = time.time()
            
            # In a real implementation, this would handle the actual data transfer
            # between memory components. For now, we just simulate success.
            success = True
            
            # Calculate metrics
            duration_ms = (time.time() - start_time) * 1000
            self.connection.metrics.record_transfer(data_size, duration_ms, success)
            
            logger.debug(
                f"Transferred {data_size} bytes through tubule {self.connection.id} "
                f"in {duration_ms:.2f}ms"
            )
            
            return success
            
        except Exception as e:
            logger.exception(f"Error during tubule transfer: {str(e)}")
            self.connection.metrics.record_transfer(0, 0, False)
            raise TubuleTransferError(f"Transfer failed: {str(e)}") from e
        finally:
            self._transfer_in_progress = False
    
    def _estimate_data_size(self, data: Any) -> int:
        """
        Estimate the size of data in bytes.
        
        Args:
            data: The data to measure
            
        Returns:
            int: Estimated size in bytes
        """
        # This is a simplified implementation
        # In a real system, this would more accurately measure serialized data size
        import sys
        try:
            return sys.getsizeof(data)
        except:
            # Fallback for objects that don't support getsizeof
            return 1024  # Default assumption
    
    def deactivate(self) -> None:
        """Deactivate the tubule, preventing further transfers."""
        self.connection.active = False
        logger.info(f"Tubule deactivated: {self.connection.id}")
    
    def activate(self) -> None:
        """Activate the tubule, allowing transfers."""
        self.connection.active = True
        logger.info(f"Tubule activated: {self.connection.id}")
    
    def get_metrics(self) -> dict[str, Any]:
        """
        Get performance metrics for this tubule.
        
        Returns:
            Dict[str, Any]: Dictionary of metrics
        """
        metrics = self.connection.metrics
        return {
            "tubule_id": self.connection.id,
            "source": self.connection.source,
            "destination": self.connection.destination,
            "active": self.connection.active,
            "priority": self.connection.priority.name,
            "created_at": metrics.created_at,
            "last_transfer_at": metrics.last_transfer_at,
            "transfer_count": metrics.transfer_count,
            "transfer_volume_bytes": metrics.transfer_volume_bytes,
            "transfer_errors": metrics.transfer_errors,
            "avg_transfer_time_ms": metrics.avg_transfer_time_ms,
        }

class TubuleNetwork:
    """
    Manages a network of tubules connecting different memory components.
    
    The TubuleNetwork provides a higher-level interface for managing multiple
    tubule connections and routing information between memory components.
    """
    
    def __init__(self) -> None:
        """Initialize a new tubule network."""
        self._tubules: dict[str, Tubule] = {}
        self._connections_by_source: dict[str, set[str]] = {}
        self._connections_by_destination: dict[str, set[str]] = {}
        logger.info("Initialized tubule network")
    
    def add_tubule(
        self,
        source: str,
        destination: str,
        priority: TubulePriority = TubulePriority.MEDIUM,
        bidirectional: bool = False,
        max_capacity: Optional[int] = None
    ) -> str:
        """
        Add a new tubule to the network.
        
        Args:
            source: Identifier of the source memory component
            destination: Identifier of the destination memory component
            priority: Priority level for this tubule
            bidirectional: Whether information can flow in both directions
            max_capacity: Maximum data capacity in bytes (None for unlimited)
            
        Returns:
            str: ID of the created tubule
            
        Raises:
            TubuleConfigurationError: If the configuration is invalid
        """
        tubule = Tubule(
            source=source,
            destination=destination,
            priority=priority,
            bidirectional=bidirectional,
            max_capacity=max_capacity
        )
        
        tubule_id = tubule.connection.id
        self._tubules[tubule_id] = tubule
        
        # Update connection mappings
        if source not in self._connections_by_source:
            self._connections_by_source[source] = set()
        self._connections_by_source[source].add(tubule_id)
        
        if destination not in self._connections_by_destination:
            self._connections_by_destination[destination] = set()
        self._connections_by_destination[destination].add(tubule_id)
        
        # If bidirectional, add reverse mappings
        if bidirectional:
            if destination not in self._connections_by_source:
                self._connections_by_source[destination] = set()
            self._connections_by_source[destination].add(tubule_id)
            
            if source not in self._connections_by_destination:
                self._connections_by_destination[source] = set()
            self._connections_by_destination[source].add(tubule_id)
        
        logger.info(f"Added tubule {tubule_id} to network: {source} -> {destination}")
        return tubule_id
    
    def remove_tubule(self, tubule_id: str) -> bool:
        """
        Remove a tubule from the network.
        
        Args:
            tubule_id: ID of the tubule to remove
            
        Returns:
            bool: True if removed successfully, False if not found
        """
        if tubule_id not in self._tubules:
            logger.warning(f"Attempted to remove non-existent tubule: {tubule_id}")
            return False
        
        tubule = self._tubules[tubule_id]
        source = tubule.connection.source
        destination = tubule.connection.destination
        bidirectional = tubule.connection.bidirectional
        
        # Remove from mappings
        if source in self._connections_by_source:
            self._connections_by_source[source].discard(tubule_id)
        
        if destination in self._connections_by_destination:
            self._connections_by_destination[destination].discard(tubule_id)
        
        # If bidirectional, remove reverse mappings
        if bidirectional:
            if destination in self._connections_by_source:
                self._connections_by_source[destination].discard(tubule_id)
            
            if source in self._connections_by_destination:
                self._connections_by_destination[source].discard(tubule_id)
        
        # Remove the tubule
        del self._tubules[tubule_id]
        
        logger.info(f"Removed tubule {tubule_id} from network")
        return True
    
    def get_tubule(self, tubule_id: str) -> Optional[Tubule]:
        """
        Get a tubule by ID.
        
        Args:
            tubule_id: ID of the tubule to retrieve
            
        Returns:
            Optional[Tubule]: The tubule if found, None otherwise
        """
        return self._tubules.get(tubule_id)
    
    def find_tubules(
        self, 
        source: Optional[str] = None, 
        destination: Optional[str] = None
    ) -> list[str]:
        """
        Find tubules matching the given source and/or destination.
        
        Args:
            source: Source memory component (optional)
            destination: Destination memory component (optional)
            
        Returns:
            List[str]: List of matching tubule IDs
        """
        result = set()
        
        if source and destination:
            # Find tubules that connect specific source and destination
            source_tubules = self._connections_by_source.get(source, set())
            dest_tubules = self._connections_by_destination.get(destination, set())
            result = source_tubules.intersection(dest_tubules)
            
            # Also check bidirectional tubules in the reverse direction
            reverse_source = self._connections_by_source.get(destination, set())
            reverse_dest = self._connections_by_destination.get(source, set())
            reverse_matches = reverse_source.intersection(reverse_dest)
            
            # Only include reverse matches that are actually bidirectional
            for tubule_id in reverse_matches:
                if self._tubules[tubule_id].connection.bidirectional:
                    result.add(tubule_id)
                    
        elif source:
            # Find all tubules from this source
            result = self._connections_by_source.get(source, set())
        elif destination:
            # Find all tubules to this destination
            result = self._connections_by_destination.get(destination, set())
        else:
            # No filters, return all tubule IDs
            result = set(self._tubules.keys())
        
        return list(result)
    
    def transfer(
        self, 
        data: Any, 
        source: str, 
        destination: str,
        use_priority: bool = True
    ) -> bool:
        """
        Transfer data from source to destination through the tubule network.
        
        Args:
            data: The data to transfer
            source: Source memory component
            destination: Destination memory component
            use_priority: Whether to prioritize tubules by priority level
            
        Returns:
            bool: True if transfer was successful, False otherwise
            
        Raises:
            TubuleConnectionError: If no valid tubule connection exists
            TubuleTransferError: If transfer fails
        """
        # Find tubules connecting source and destination
        tubule_ids = self.find_tubules(source, destination)
        
        if not tubule_ids:
            logger.error(f"No tubule connection found: {source} -> {destination}")
            raise TubuleConnectionError(f"No tubule connection exists between {source} and {destination}")
        
        # If using priority, sort tubules by priority
        if use_priority and len(tubule_ids) > 1:
            tubule_ids = sorted(
                tubule_ids,
                key=lambda tid: self._tubules[tid].connection.priority.value
            )
        
        # Try each tubule until successful transfer
        for tubule_id in tubule_ids:
            tubule = self._tubules[tubule_id]
            
            # Skip inactive tubules
            if not tubule.connection.active:
                continue
            
            # Check if we need to use the tubule in reverse direction
            reverse_direction = (
                tubule.connection.bidirectional and
                tubule.connection.source == destination and
                tubule.connection.destination == source
            )
            
            if not reverse_direction and (
                tubule.connection.source != source or 
                tubule.connection.destination != destination
            ):
                continue
            
            try:
                success = tubule.transfer(data)
                if success:
                    logger.debug(
                        f"Successfully transferred data from {source} to {destination} "
                        f"via tubule {tubule_id}"
                    )
                    return True
            except Exception as e:
                logger.warning(
                    f"Transfer failed on tubule {tubule_id}: {str(e)}. "
                    f"Trying next tubule if available."
                )
        
        logger.error(f"All tubule transfers failed: {source} -> {destination}")
        return False
    
    def get_network_metrics(self) -> dict[str, Any]:
        """
        Get comprehensive metrics for the entire tubule network.
        
        Returns:
            Dict[str, Any]: Dictionary of network-wide metrics
        """
        total_tubules = len(self._tubules)
        active_tubules = sum(1 for t in self._tubules.values() if t.connection.active)
        total_transfers = sum(t.connection.metrics.transfer_count for t in self._tubules.values())
        total_errors = sum(t.connection.metrics.transfer_errors for t in self._tubules.values())
        total_volume = sum(t.connection.metrics.transfer_volume_bytes for t in self._tubules.values())
        
        # Calculate average transfer time across all tubules
        avg_times = [t.connection.metrics.avg_transfer_time_ms for t in self._tubules.values() 
                    if t.connection.metrics.transfer_count > 0]
        avg_transfer_time = sum(avg_times) / len(avg_times) if avg_times else 0
        
        return {
            "total_tubules": total_tubules,
            "active_tubules": active_tubules,
            "inactive_tubules": total_tubules - active_tubules,
            "total_transfers": total_transfers,
            "total_errors": total_errors,
            "total_volume_bytes": total_volume,
            "avg_transfer_time_ms": avg_transfer_time,
            "error_rate": total_errors / total_transfers if total_transfers > 0 else 0,
            "tubule_metrics": {tid: t.get_metrics() for tid, t in self._tubules.items()},
            "memory_components": {
                "sources": list(self._connections_by_source.keys()),
                "destinations": list(self._connections_by_destination.keys())
            }
        }

# Version information
__version__ = "0.1.0"

# Export public API
__all__ = [
    "Tubule",
    "TubuleNetwork",
    "TubuleConnection",
    "TubuleMetrics",
    "TubulePriority",
    "TubuleError",
    "TubuleConnectionError",
    "TubuleTransferError",
    "TubuleConfigurationError",
]