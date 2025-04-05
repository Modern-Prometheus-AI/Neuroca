"""
Tubule Connections Module

This module implements the connection management system for neural tubules in the NeuroCognitive
Architecture (NCA). Tubules represent the pathways that connect different memory components,
facilitating information flow between memory tiers and cognitive processes.

The connections system provides:
1. Creation and management of connections between memory nodes
2. Signal propagation along tubule pathways
3. Connection strength modulation based on usage patterns
4. Pruning and formation of new connections based on relevance
5. Support for both excitatory and inhibitory connection types

Usage:
    connection_manager = TubuleConnectionManager()
    
    # Create a connection between two memory nodes
    connection = connection_manager.create_connection(source_id, target_id, strength=0.5)
    
    # Propagate a signal through a connection
    result = connection_manager.propagate_signal(connection_id, signal_value)
    
    # Strengthen a connection based on usage
    connection_manager.modulate_strength(connection_id, delta=0.1)
"""

import uuid
from datetime import datetime
from enum import Enum, auto
from typing import Any, Optional

from neuroca.core.exceptions import (
    ConnectionLimitExceededError,
    InvalidConnectionError,
    SignalPropagationError,
)
from neuroca.core.utils.logging_utils import get_logger
from neuroca.core.utils.validation import validate_range, validate_type

# Configure logger
logger = get_logger(__name__)

class ConnectionType(Enum):
    """Defines the types of connections between memory nodes."""
    EXCITATORY = auto()
    INHIBITORY = auto()
    MODULATORY = auto()


class ConnectionState(Enum):
    """Defines the possible states of a tubule connection."""
    FORMING = auto()    # New connection being established
    ACTIVE = auto()     # Fully functional connection
    WEAKENING = auto()  # Connection that is losing strength
    PRUNED = auto()     # Inactive connection marked for removal


class TubuleConnection:
    """
    Represents a connection between two memory nodes in the tubule system.
    
    A tubule connection models the pathway through which signals propagate between
    memory components, with properties that determine signal transmission characteristics.
    """
    
    def __init__(
        self,
        source_id: str,
        target_id: str,
        connection_type: ConnectionType = ConnectionType.EXCITATORY,
        initial_strength: float = 0.5,
        max_capacity: float = 1.0,
        decay_rate: float = 0.01,
        connection_id: Optional[str] = None
    ):
        """
        Initialize a new tubule connection.
        
        Args:
            source_id: Identifier of the source memory node
            target_id: Identifier of the target memory node
            connection_type: Type of connection (excitatory, inhibitory, modulatory)
            initial_strength: Initial connection strength (0.0 to 1.0)
            max_capacity: Maximum signal capacity of the connection
            decay_rate: Rate at which connection strength decays when unused
            connection_id: Optional custom identifier for the connection
            
        Raises:
            ValueError: If parameters are outside valid ranges
        """
        # Validate inputs
        validate_type(source_id, str, "source_id")
        validate_type(target_id, str, "target_id")
        validate_type(connection_type, ConnectionType, "connection_type")
        validate_range(initial_strength, 0.0, 1.0, "initial_strength")
        validate_range(max_capacity, 0.1, float('inf'), "max_capacity")
        validate_range(decay_rate, 0.0, 1.0, "decay_rate")
        
        # Core properties
        self.connection_id = connection_id or str(uuid.uuid4())
        self.source_id = source_id
        self.target_id = target_id
        self.connection_type = connection_type
        
        # Dynamic properties
        self._strength = initial_strength
        self.max_capacity = max_capacity
        self.decay_rate = decay_rate
        
        # State tracking
        self.state = ConnectionState.FORMING
        self.creation_time = datetime.now()
        self.last_activation = self.creation_time
        self.activation_count = 0
        self.cumulative_signal = 0.0
        
        # Metadata for analysis and debugging
        self.metadata = {
            "creator": "system",
            "notes": "",
            "tags": set()
        }
        
        logger.debug(
            f"Created tubule connection {self.connection_id} from {source_id} to {target_id} "
            f"with initial strength {initial_strength:.2f}"
        )
    
    @property
    def strength(self) -> float:
        """Get the current connection strength."""
        return self._strength
    
    @strength.setter
    def strength(self, value: float) -> None:
        """
        Set the connection strength with validation.
        
        Args:
            value: New strength value between 0.0 and 1.0
            
        Raises:
            ValueError: If value is outside the valid range
        """
        validate_range(value, 0.0, 1.0, "strength")
        self._strength = value
        
        # Update connection state based on strength
        if self._strength < 0.1:
            self.state = ConnectionState.WEAKENING
        elif self.state != ConnectionState.FORMING:
            self.state = ConnectionState.ACTIVE
    
    def activate(self, signal_value: float) -> float:
        """
        Activate the connection with a signal and return the propagated value.
        
        Args:
            signal_value: Input signal value to propagate through the connection
            
        Returns:
            float: The modulated signal value after passing through the connection
            
        Raises:
            SignalPropagationError: If signal propagation fails
        """
        try:
            # Validate input
            validate_type(signal_value, (int, float), "signal_value")
            
            # Skip processing if connection is pruned
            if self.state == ConnectionState.PRUNED:
                logger.warning(f"Attempted to activate pruned connection {self.connection_id}")
                return 0.0
            
            # Apply connection type modulation
            if self.connection_type == ConnectionType.EXCITATORY:
                modulated_signal = signal_value * self._strength
            elif self.connection_type == ConnectionType.INHIBITORY:
                modulated_signal = -signal_value * self._strength
            else:  # MODULATORY
                # Modulatory connections affect the signal differently
                modulated_signal = signal_value * (1.0 + (self._strength - 0.5))
            
            # Apply capacity limit
            modulated_signal = min(modulated_signal, self.max_capacity)
            
            # Update connection statistics
            self.last_activation = datetime.now()
            self.activation_count += 1
            self.cumulative_signal += abs(signal_value)
            
            # Transition to active state if forming
            if self.state == ConnectionState.FORMING and self.activation_count >= 5:
                self.state = ConnectionState.ACTIVE
                logger.debug(f"Connection {self.connection_id} transitioned to ACTIVE state")
            
            return modulated_signal
            
        except Exception as e:
            logger.error(f"Signal propagation failed on connection {self.connection_id}: {str(e)}")
            raise SignalPropagationError(f"Failed to propagate signal: {str(e)}") from e
    
    def apply_decay(self) -> None:
        """
        Apply time-based decay to the connection strength.
        This should be called periodically to simulate natural connection weakening.
        """
        if self.state == ConnectionState.PRUNED:
            return
            
        # Calculate time since last activation
        time_delta = (datetime.now() - self.last_activation).total_seconds()
        
        # Apply decay based on time elapsed
        decay_amount = self.decay_rate * (time_delta / 3600)  # Scale by hours
        decay_amount = min(decay_amount, self._strength)  # Don't go below zero
        
        self.strength = self._strength - decay_amount
        
        # Check if connection should be marked for pruning
        if self._strength < 0.05:
            self.state = ConnectionState.PRUNED
            logger.info(f"Connection {self.connection_id} marked as PRUNED due to decay")
    
    def to_dict(self) -> dict[str, Any]:
        """
        Convert the connection to a dictionary representation for serialization.
        
        Returns:
            Dict containing all connection properties
        """
        return {
            "connection_id": self.connection_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "connection_type": self.connection_type.name,
            "strength": self._strength,
            "max_capacity": self.max_capacity,
            "decay_rate": self.decay_rate,
            "state": self.state.name,
            "creation_time": self.creation_time.isoformat(),
            "last_activation": self.last_activation.isoformat(),
            "activation_count": self.activation_count,
            "cumulative_signal": self.cumulative_signal,
            "metadata": {
                "creator": self.metadata["creator"],
                "notes": self.metadata["notes"],
                "tags": list(self.metadata["tags"])
            }
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'TubuleConnection':
        """
        Create a connection instance from a dictionary representation.
        
        Args:
            data: Dictionary containing connection properties
            
        Returns:
            TubuleConnection: Reconstructed connection object
            
        Raises:
            ValueError: If the dictionary contains invalid data
        """
        try:
            # Create connection with core properties
            connection = cls(
                source_id=data["source_id"],
                target_id=data["target_id"],
                connection_type=ConnectionType[data["connection_type"]],
                initial_strength=data["strength"],
                max_capacity=data["max_capacity"],
                decay_rate=data["decay_rate"],
                connection_id=data["connection_id"]
            )
            
            # Restore state and tracking data
            connection.state = ConnectionState[data["state"]]
            connection.creation_time = datetime.fromisoformat(data["creation_time"])
            connection.last_activation = datetime.fromisoformat(data["last_activation"])
            connection.activation_count = data["activation_count"]
            connection.cumulative_signal = data["cumulative_signal"]
            
            # Restore metadata
            connection.metadata["creator"] = data["metadata"]["creator"]
            connection.metadata["notes"] = data["metadata"]["notes"]
            connection.metadata["tags"] = set(data["metadata"]["tags"])
            
            return connection
            
        except (KeyError, ValueError) as e:
            logger.error(f"Failed to create connection from dictionary: {str(e)}")
            raise ValueError(f"Invalid connection data: {str(e)}") from e
    
    def __repr__(self) -> str:
        """String representation of the connection for debugging."""
        return (
            f"TubuleConnection(id={self.connection_id}, "
            f"source={self.source_id}, target={self.target_id}, "
            f"type={self.connection_type.name}, strength={self._strength:.2f}, "
            f"state={self.state.name})"
        )


class TubuleConnectionManager:
    """
    Manages the creation, tracking, and operations of tubule connections.
    
    This class provides a centralized system for handling all connections between
    memory nodes, including creation, querying, signal propagation, and maintenance
    operations like pruning and strengthening.
    """
    
    def __init__(self, max_connections_per_node: int = 1000):
        """
        Initialize the connection manager.
        
        Args:
            max_connections_per_node: Maximum number of connections allowed per node
        """
        self._connections: dict[str, TubuleConnection] = {}
        self._source_connections: dict[str, set[str]] = {}  # source_id -> set of connection_ids
        self._target_connections: dict[str, set[str]] = {}  # target_id -> set of connection_ids
        self.max_connections_per_node = max_connections_per_node
        
        logger.info(f"Initialized TubuleConnectionManager with {max_connections_per_node} max connections per node")
    
    def create_connection(
        self,
        source_id: str,
        target_id: str,
        connection_type: ConnectionType = ConnectionType.EXCITATORY,
        initial_strength: float = 0.5,
        max_capacity: float = 1.0,
        decay_rate: float = 0.01,
        metadata: Optional[dict[str, Any]] = None
    ) -> TubuleConnection:
        """
        Create a new connection between two memory nodes.
        
        Args:
            source_id: Identifier of the source memory node
            target_id: Identifier of the target memory node
            connection_type: Type of connection
            initial_strength: Initial connection strength
            max_capacity: Maximum signal capacity
            decay_rate: Rate of strength decay when unused
            metadata: Optional metadata for the connection
            
        Returns:
            TubuleConnection: The newly created connection
            
        Raises:
            ConnectionLimitExceededError: If adding this connection would exceed limits
            ValueError: If parameters are invalid
        """
        # Validate inputs
        validate_type(source_id, str, "source_id")
        validate_type(target_id, str, "target_id")
        
        # Check connection limits
        source_connections = self._source_connections.get(source_id, set())
        if len(source_connections) >= self.max_connections_per_node:
            msg = f"Source node {source_id} has reached maximum connections limit"
            logger.warning(msg)
            raise ConnectionLimitExceededError(msg)
        
        # Create the connection
        connection = TubuleConnection(
            source_id=source_id,
            target_id=target_id,
            connection_type=connection_type,
            initial_strength=initial_strength,
            max_capacity=max_capacity,
            decay_rate=decay_rate
        )
        
        # Add metadata if provided
        if metadata:
            connection.metadata.update(metadata)
        
        # Register the connection
        self._connections[connection.connection_id] = connection
        
        # Update index mappings
        if source_id not in self._source_connections:
            self._source_connections[source_id] = set()
        self._source_connections[source_id].add(connection.connection_id)
        
        if target_id not in self._target_connections:
            self._target_connections[target_id] = set()
        self._target_connections[target_id].add(connection.connection_id)
        
        logger.info(f"Created connection {connection.connection_id} from {source_id} to {target_id}")
        return connection
    
    def get_connection(self, connection_id: str) -> TubuleConnection:
        """
        Retrieve a connection by its ID.
        
        Args:
            connection_id: The unique identifier of the connection
            
        Returns:
            TubuleConnection: The requested connection
            
        Raises:
            InvalidConnectionError: If the connection does not exist
        """
        if connection_id not in self._connections:
            raise InvalidConnectionError(f"Connection {connection_id} does not exist")
        return self._connections[connection_id]
    
    def get_connections_from_source(self, source_id: str) -> list[TubuleConnection]:
        """
        Get all connections originating from a specific source node.
        
        Args:
            source_id: The identifier of the source node
            
        Returns:
            List of connections from the specified source
        """
        connection_ids = self._source_connections.get(source_id, set())
        return [self._connections[cid] for cid in connection_ids if cid in self._connections]
    
    def get_connections_to_target(self, target_id: str) -> list[TubuleConnection]:
        """
        Get all connections leading to a specific target node.
        
        Args:
            target_id: The identifier of the target node
            
        Returns:
            List of connections to the specified target
        """
        connection_ids = self._target_connections.get(target_id, set())
        return [self._connections[cid] for cid in connection_ids if cid in self._connections]
    
    def find_connection(self, source_id: str, target_id: str) -> Optional[TubuleConnection]:
        """
        Find a connection between specific source and target nodes.
        
        Args:
            source_id: The identifier of the source node
            target_id: The identifier of the target node
            
        Returns:
            The connection if found, None otherwise
        """
        source_connections = self._source_connections.get(source_id, set())
        target_connections = self._target_connections.get(target_id, set())
        
        # Find intersection of connections
        common_connections = source_connections.intersection(target_connections)
        
        if common_connections:
            # Return the first matching connection
            connection_id = next(iter(common_connections))
            return self._connections[connection_id]
        
        return None
    
    def propagate_signal(self, connection_id: str, signal_value: float) -> float:
        """
        Propagate a signal through a specific connection.
        
        Args:
            connection_id: The identifier of the connection
            signal_value: The signal value to propagate
            
        Returns:
            The modulated signal value after propagation
            
        Raises:
            InvalidConnectionError: If the connection does not exist
            SignalPropagationError: If signal propagation fails
        """
        try:
            connection = self.get_connection(connection_id)
            return connection.activate(signal_value)
        except InvalidConnectionError:
            logger.error(f"Cannot propagate signal: Connection {connection_id} not found")
            raise
        except Exception as e:
            logger.error(f"Signal propagation failed on connection {connection_id}: {str(e)}")
            raise SignalPropagationError(f"Failed to propagate signal: {str(e)}") from e
    
    def modulate_strength(self, connection_id: str, delta: float) -> float:
        """
        Adjust the strength of a connection.
        
        Args:
            connection_id: The identifier of the connection
            delta: The amount to adjust the strength by (positive or negative)
            
        Returns:
            The new connection strength
            
        Raises:
            InvalidConnectionError: If the connection does not exist
        """
        connection = self.get_connection(connection_id)
        
        # Calculate new strength with bounds checking
        new_strength = max(0.0, min(1.0, connection.strength + delta))
        connection.strength = new_strength
        
        logger.debug(
            f"Modulated connection {connection_id} strength by {delta:+.2f} "
            f"to new value {new_strength:.2f}"
        )
        
        return new_strength
    
    def prune_connection(self, connection_id: str) -> None:
        """
        Mark a connection as pruned and prepare it for removal.
        
        Args:
            connection_id: The identifier of the connection to prune
            
        Raises:
            InvalidConnectionError: If the connection does not exist
        """
        connection = self.get_connection(connection_id)
        connection.state = ConnectionState.PRUNED
        logger.info(f"Marked connection {connection_id} as PRUNED")
    
    def remove_connection(self, connection_id: str) -> None:
        """
        Completely remove a connection from the system.
        
        Args:
            connection_id: The identifier of the connection to remove
            
        Raises:
            InvalidConnectionError: If the connection does not exist
        """
        if connection_id not in self._connections:
            raise InvalidConnectionError(f"Connection {connection_id} does not exist")
        
        # Get the connection to access its source and target
        connection = self._connections[connection_id]
        
        # Remove from source and target indices
        if connection.source_id in self._source_connections:
            self._source_connections[connection.source_id].discard(connection_id)
            if not self._source_connections[connection.source_id]:
                del self._source_connections[connection.source_id]
                
        if connection.target_id in self._target_connections:
            self._target_connections[connection.target_id].discard(connection_id)
            if not self._target_connections[connection.target_id]:
                del self._target_connections[connection.target_id]
        
        # Remove the connection itself
        del self._connections[connection_id]
        logger.info(f"Removed connection {connection_id} from system")
    
    def apply_decay_to_all(self) -> None:
        """
        Apply time-based decay to all connections in the system.
        This simulates the natural weakening of unused connections.
        """
        pruned_count = 0
        for connection in self._connections.values():
            if connection.state != ConnectionState.PRUNED:
                connection.apply_decay()
                if connection.state == ConnectionState.PRUNED:
                    pruned_count += 1
        
        if pruned_count > 0:
            logger.info(f"Applied decay to all connections: {pruned_count} connections marked for pruning")
        else:
            logger.debug("Applied decay to all connections")
    
    def cleanup_pruned_connections(self) -> int:
        """
        Remove all connections that have been marked as pruned.
        
        Returns:
            The number of connections removed
        """
        pruned_connections = [
            conn_id for conn_id, conn in self._connections.items() 
            if conn.state == ConnectionState.PRUNED
        ]
        
        for conn_id in pruned_connections:
            self.remove_connection(conn_id)
        
        logger.info(f"Cleaned up {len(pruned_connections)} pruned connections")
        return len(pruned_connections)
    
    def get_connection_stats(self) -> dict[str, Any]:
        """
        Get statistics about the current connection system.
        
        Returns:
            Dictionary containing connection statistics
        """
        total_connections = len(self._connections)
        
        # Count connections by state
        state_counts = {state: 0 for state in ConnectionState}
        for conn in self._connections.values():
            state_counts[conn.state] += 1
        
        # Count connections by type
        type_counts = {conn_type: 0 for conn_type in ConnectionType}
        for conn in self._connections.values():
            type_counts[conn.connection_type] += 1
        
        # Calculate average strength
        avg_strength = 0.0
        if total_connections > 0:
            avg_strength = sum(conn.strength for conn in self._connections.values()) / total_connections
        
        return {
            "total_connections": total_connections,
            "total_sources": len(self._source_connections),
            "total_targets": len(self._target_connections),
            "state_counts": {state.name: count for state, count in state_counts.items()},
            "type_counts": {conn_type.name: count for conn_type, count in type_counts.items()},
            "average_strength": avg_strength
        }
    
    def to_dict(self) -> dict[str, Any]:
        """
        Convert the connection manager state to a dictionary for serialization.
        
        Returns:
            Dictionary containing all connection data
        """
        return {
            "connections": {
                conn_id: conn.to_dict() 
                for conn_id, conn in self._connections.items()
            },
            "max_connections_per_node": self.max_connections_per_node
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'TubuleConnectionManager':
        """
        Create a connection manager from a dictionary representation.
        
        Args:
            data: Dictionary containing connection manager data
            
        Returns:
            Reconstructed connection manager
            
        Raises:
            ValueError: If the dictionary contains invalid data
        """
        try:
            manager = cls(max_connections_per_node=data["max_connections_per_node"])
            
            # Reconstruct all connections
            for conn_id, conn_data in data["connections"].items():
                connection = TubuleConnection.from_dict(conn_data)
                
                # Add to manager's internal structures
                manager._connections[conn_id] = connection
                
                # Update index mappings
                source_id = connection.source_id
                target_id = connection.target_id
                
                if source_id not in manager._source_connections:
                    manager._source_connections[source_id] = set()
                manager._source_connections[source_id].add(conn_id)
                
                if target_id not in manager._target_connections:
                    manager._target_connections[target_id] = set()
                manager._target_connections[target_id].add(conn_id)
            
            logger.info(f"Reconstructed connection manager with {len(manager._connections)} connections")
            return manager
            
        except (KeyError, ValueError) as e:
            logger.error(f"Failed to create connection manager from dictionary: {str(e)}")
            raise ValueError(f"Invalid connection manager data: {str(e)}") from e