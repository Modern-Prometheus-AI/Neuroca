"""
Short-Term Memory (STM) Module for NeuroCognitive Architecture.

This module implements the Short-Term Memory component of the three-tiered memory system
in the NeuroCognitive Architecture (NCA). STM serves as an intermediate memory store
with moderate retention duration and capacity between Working Memory (WM) and
Long-Term Memory (LTM).

Key characteristics of STM:
- Medium retention duration (minutes to hours)
- Moderate capacity (larger than WM, smaller than LTM)
- Structured information storage with context preservation
- Supports both explicit retrieval and decay mechanisms
- Interfaces with both WM and LTM components

Usage:
    from neuroca.memory.stm import ShortTermMemory
    
    # Initialize STM with default settings
    stm = ShortTermMemory()
    
    # Store information in STM
    stm.store(content="Important meeting at 3pm", metadata={"source": "calendar"})
    
    # Retrieve information from STM
    results = stm.retrieve(query="meeting time", limit=5)
    
    # Check STM health metrics
    health_status = stm.get_health_metrics()

This module is part of the NeuroCognitive Architecture system and works in conjunction
with other memory tiers to provide a biologically-inspired memory system for LLMs.
"""

import logging
import time
import uuid
from typing import Any, Optional

from neuroca.memory.base import MemoryBase, MemoryEntry, MemoryHealthStatus
from neuroca.memory.exceptions import (
    MemoryCapacityError,
    MemoryRetrievalError,
    MemoryStorageError,
    MemoryValidationError,
)

# Configure module logger
logger = logging.getLogger(__name__)

# Version information
__version__ = "0.1.0"

# Public exports
__all__ = [
    "ShortTermMemory",
    "STMEntry",
    "STMHealthStatus",
    "STMConfig",
]


class STMEntry(MemoryEntry):
    """
    Represents an entry in the Short-Term Memory system.
    
    Extends the base MemoryEntry with STM-specific attributes such as
    activation level, decay rate, and context information.
    
    Attributes:
        activation_level (float): Current activation level of the memory entry (0.0-1.0)
        decay_rate (float): Rate at which this memory entry decays over time
        last_accessed (float): Timestamp of last access (used for decay calculations)
        context (Dict[str, Any]): Contextual information associated with this memory
    """
    
    def __init__(
        self,
        content: Any,
        metadata: Optional[dict[str, Any]] = None,
        entry_id: Optional[str] = None,
        timestamp: Optional[float] = None,
        activation_level: float = 1.0,
        decay_rate: float = 0.05,
        context: Optional[dict[str, Any]] = None
    ):
        """
        Initialize a new STM entry.
        
        Args:
            content: The actual content to store in memory
            metadata: Additional metadata about the content
            entry_id: Unique identifier (generated if not provided)
            timestamp: Creation time (current time if not provided)
            activation_level: Initial activation level (0.0-1.0)
            decay_rate: Rate at which this memory decays (per hour)
            context: Contextual information associated with this memory
        
        Raises:
            MemoryValidationError: If parameters are invalid
        """
        super().__init__(
            content=content,
            metadata=metadata or {},
            entry_id=entry_id or str(uuid.uuid4()),
            timestamp=timestamp or time.time()
        )
        
        # Validate activation level
        if not 0.0 <= activation_level <= 1.0:
            raise MemoryValidationError(f"Activation level must be between 0.0 and 1.0, got {activation_level}")
        
        # Validate decay rate
        if decay_rate < 0.0:
            raise MemoryValidationError(f"Decay rate must be non-negative, got {decay_rate}")
        
        self.activation_level = activation_level
        self.decay_rate = decay_rate
        self.last_accessed = self.timestamp
        self.context = context or {}
    
    def update_activation(self, current_time: Optional[float] = None) -> float:
        """
        Update the activation level based on time decay.
        
        Args:
            current_time: Current timestamp (defaults to current time)
            
        Returns:
            float: Updated activation level
            
        Note:
            This implements an exponential decay model for memory activation.
        """
        current_time = current_time or time.time()
        time_diff_hours = (current_time - self.last_accessed) / 3600.0
        
        # Apply exponential decay: A = A0 * e^(-decay_rate * time)
        decay_factor = 2.718 ** (-self.decay_rate * time_diff_hours)
        self.activation_level *= decay_factor
        
        # Ensure activation stays in valid range
        self.activation_level = max(0.0, min(1.0, self.activation_level))
        
        # Update last accessed time
        self.last_accessed = current_time
        
        return self.activation_level
    
    def boost_activation(self, boost_amount: float = 0.2) -> float:
        """
        Boost the activation level of this memory entry.
        
        Args:
            boost_amount: Amount to boost activation by (0.0-1.0)
            
        Returns:
            float: Updated activation level
            
        Raises:
            MemoryValidationError: If boost amount is invalid
        """
        if not 0.0 <= boost_amount <= 1.0:
            raise MemoryValidationError(f"Boost amount must be between 0.0 and 1.0, got {boost_amount}")
        
        self.activation_level = min(1.0, self.activation_level + boost_amount)
        self.last_accessed = time.time()
        
        return self.activation_level
    
    def to_dict(self) -> dict[str, Any]:
        """
        Convert the STM entry to a dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the entry
        """
        base_dict = super().to_dict()
        stm_dict = {
            "activation_level": self.activation_level,
            "decay_rate": self.decay_rate,
            "last_accessed": self.last_accessed,
            "context": self.context
        }
        return {**base_dict, **stm_dict}


class STMHealthStatus(MemoryHealthStatus):
    """
    Health status metrics specific to the Short-Term Memory system.
    
    Extends the base MemoryHealthStatus with STM-specific metrics.
    
    Attributes:
        avg_activation_level (float): Average activation level across all entries
        decay_efficiency (float): Measure of how efficiently memory is decaying
        context_richness (float): Measure of how rich the contextual information is
        retrieval_latency_ms (float): Average retrieval time in milliseconds
    """
    
    def __init__(
        self,
        capacity_used: float,
        entry_count: int,
        avg_activation_level: float,
        decay_efficiency: float,
        context_richness: float,
        retrieval_latency_ms: float
    ):
        """
        Initialize STM health status.
        
        Args:
            capacity_used: Percentage of capacity used (0.0-1.0)
            entry_count: Number of entries in memory
            avg_activation_level: Average activation level across all entries
            decay_efficiency: Measure of decay efficiency (0.0-1.0)
            context_richness: Measure of contextual information richness (0.0-1.0)
            retrieval_latency_ms: Average retrieval time in milliseconds
        """
        super().__init__(capacity_used=capacity_used, entry_count=entry_count)
        self.avg_activation_level = avg_activation_level
        self.decay_efficiency = decay_efficiency
        self.context_richness = context_richness
        self.retrieval_latency_ms = retrieval_latency_ms
    
    def to_dict(self) -> dict[str, Any]:
        """
        Convert health status to dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary of health metrics
        """
        base_dict = super().to_dict()
        stm_dict = {
            "avg_activation_level": self.avg_activation_level,
            "decay_efficiency": self.decay_efficiency,
            "context_richness": self.context_richness,
            "retrieval_latency_ms": self.retrieval_latency_ms
        }
        return {**base_dict, **stm_dict}


class STMConfig:
    """
    Configuration settings for the Short-Term Memory system.
    
    Attributes:
        max_capacity (int): Maximum number of entries in STM
        activation_threshold (float): Minimum activation level for retention
        default_decay_rate (float): Default decay rate for new entries
        consolidation_interval (float): Time interval for LTM consolidation in seconds
        retrieval_boost_amount (float): Activation boost on retrieval
    """
    
    def __init__(
        self,
        max_capacity: int = 1000,
        activation_threshold: float = 0.1,
        default_decay_rate: float = 0.05,
        consolidation_interval: float = 3600.0,  # 1 hour
        retrieval_boost_amount: float = 0.2
    ):
        """
        Initialize STM configuration.
        
        Args:
            max_capacity: Maximum number of entries in STM
            activation_threshold: Minimum activation level for retention (0.0-1.0)
            default_decay_rate: Default decay rate for new entries
            consolidation_interval: Time interval for LTM consolidation in seconds
            retrieval_boost_amount: Activation boost on retrieval (0.0-1.0)
            
        Raises:
            MemoryValidationError: If configuration parameters are invalid
        """
        # Validate parameters
        if max_capacity <= 0:
            raise MemoryValidationError(f"Max capacity must be positive, got {max_capacity}")
        
        if not 0.0 <= activation_threshold <= 1.0:
            raise MemoryValidationError(
                f"Activation threshold must be between 0.0 and 1.0, got {activation_threshold}"
            )
        
        if default_decay_rate < 0.0:
            raise MemoryValidationError(f"Default decay rate must be non-negative, got {default_decay_rate}")
        
        if consolidation_interval <= 0.0:
            raise MemoryValidationError(
                f"Consolidation interval must be positive, got {consolidation_interval}"
            )
        
        if not 0.0 <= retrieval_boost_amount <= 1.0:
            raise MemoryValidationError(
                f"Retrieval boost amount must be between 0.0 and 1.0, got {retrieval_boost_amount}"
            )
        
        self.max_capacity = max_capacity
        self.activation_threshold = activation_threshold
        self.default_decay_rate = default_decay_rate
        self.consolidation_interval = consolidation_interval
        self.retrieval_boost_amount = retrieval_boost_amount
    
    def to_dict(self) -> dict[str, Any]:
        """
        Convert configuration to dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary of configuration settings
        """
        return {
            "max_capacity": self.max_capacity,
            "activation_threshold": self.activation_threshold,
            "default_decay_rate": self.default_decay_rate,
            "consolidation_interval": self.consolidation_interval,
            "retrieval_boost_amount": self.retrieval_boost_amount
        }


class ShortTermMemory(MemoryBase):
    """
    Short-Term Memory (STM) implementation for the NeuroCognitive Architecture.
    
    STM serves as an intermediate memory store with moderate retention duration
    and capacity between Working Memory (WM) and Long-Term Memory (LTM).
    
    Features:
    - Time-based decay of memory entries
    - Activation-based retention and retrieval
    - Context-aware memory storage and retrieval
    - Automatic consolidation to LTM for important memories
    - Health monitoring and diagnostics
    
    This implementation follows biological memory principles while providing
    practical functionality for AI systems.
    """
    
    def __init__(
        self,
        config: Optional[STMConfig] = None,
        ltm_interface: Any = None
    ):
        """
        Initialize the Short-Term Memory system.
        
        Args:
            config: Configuration settings for STM
            ltm_interface: Interface to Long-Term Memory for consolidation
            
        Note:
            If config is not provided, default configuration will be used.
            If ltm_interface is not provided, consolidation to LTM will be disabled.
        """
        super().__init__()
        self.config = config or STMConfig()
        self.ltm_interface = ltm_interface
        self._entries: dict[str, STMEntry] = {}
        self._last_consolidation = time.time()
        self._retrieval_times: list[float] = []  # For tracking retrieval performance
        
        logger.info(
            "Initialized Short-Term Memory with capacity %d and activation threshold %.2f",
            self.config.max_capacity,
            self.config.activation_threshold
        )
    
    def store(
        self,
        content: Any,
        metadata: Optional[dict[str, Any]] = None,
        context: Optional[dict[str, Any]] = None,
        decay_rate: Optional[float] = None,
        activation_level: float = 1.0
    ) -> str:
        """
        Store information in Short-Term Memory.
        
        Args:
            content: The content to store
            metadata: Additional metadata about the content
            context: Contextual information for this memory
            decay_rate: Custom decay rate (uses default if None)
            activation_level: Initial activation level (0.0-1.0)
            
        Returns:
            str: ID of the stored memory entry
            
        Raises:
            MemoryCapacityError: If STM is at capacity
            MemoryValidationError: If parameters are invalid
            MemoryStorageError: If storage operation fails
        """
        try:
            # Check capacity before adding new entry
            if len(self._entries) >= self.config.max_capacity:
                # Try to make room by removing low-activation entries
                self._cleanup_low_activation_entries()
                
                # If still at capacity, raise error
                if len(self._entries) >= self.config.max_capacity:
                    raise MemoryCapacityError(
                        f"STM at maximum capacity ({self.config.max_capacity} entries)"
                    )
            
            # Use default decay rate if not specified
            if decay_rate is None:
                decay_rate = self.config.default_decay_rate
            
            # Create and store the new entry
            entry = STMEntry(
                content=content,
                metadata=metadata,
                activation_level=activation_level,
                decay_rate=decay_rate,
                context=context
            )
            
            self._entries[entry.entry_id] = entry
            
            logger.debug(
                "Stored new entry in STM: id=%s, activation=%.2f, decay_rate=%.3f",
                entry.entry_id,
                entry.activation_level,
                entry.decay_rate
            )
            
            # Check if consolidation to LTM is due
            self._check_consolidation()
            
            return entry.entry_id
            
        except MemoryValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            # Log and wrap other exceptions
            logger.error("Failed to store entry in STM: %s", str(e), exc_info=True)
            raise MemoryStorageError(f"Failed to store entry in STM: {str(e)}") from e
    
    def retrieve(
        self,
        query: Any,
        limit: int = 10,
        min_activation: Optional[float] = None,
        context_filter: Optional[dict[str, Any]] = None,
        boost_retrieved: bool = True
    ) -> list[STMEntry]:
        """
        Retrieve information from Short-Term Memory.
        
        Args:
            query: Search query or criteria
            limit: Maximum number of results to return
            min_activation: Minimum activation level for results
            context_filter: Filter results by context attributes
            boost_retrieved: Whether to boost activation of retrieved entries
            
        Returns:
            List[STMEntry]: List of matching memory entries
            
        Raises:
            MemoryRetrievalError: If retrieval operation fails
            MemoryValidationError: If parameters are invalid
        """
        if limit <= 0:
            raise MemoryValidationError(f"Limit must be positive, got {limit}")
        
        if min_activation is not None and not 0.0 <= min_activation <= 1.0:
            raise MemoryValidationError(
                f"Minimum activation must be between 0.0 and 1.0, got {min_activation}"
            )
        
        # Use configured threshold if not specified
        if min_activation is None:
            min_activation = self.config.activation_threshold
        
        start_time = time.time()
        
        try:
            # Update activation levels for all entries
            self._update_all_activations()
            
            # Filter entries by activation level and context
            filtered_entries = []
            for entry in self._entries.values():
                # Skip entries below activation threshold
                if entry.activation_level < min_activation:
                    continue
                
                # Apply context filter if provided
                if context_filter and not self._matches_context(entry, context_filter):
                    continue
                
                # Apply query matching (simplified implementation)
                # In a real implementation, this would use semantic search or other matching logic
                if self._matches_query(entry, query):
                    filtered_entries.append(entry)
            
            # Sort by activation level (highest first)
            results = sorted(
                filtered_entries,
                key=lambda e: e.activation_level,
                reverse=True
            )[:limit]
            
            # Boost activation of retrieved entries if requested
            if boost_retrieved:
                for entry in results:
                    entry.boost_activation(self.config.retrieval_boost_amount)
            
            # Track retrieval time for performance metrics
            retrieval_time = (time.time() - start_time) * 1000  # Convert to ms
            self._retrieval_times.append(retrieval_time)
            if len(self._retrieval_times) > 100:
                self._retrieval_times.pop(0)  # Keep only the last 100 measurements
            
            logger.debug(
                "Retrieved %d entries from STM (query=%s, retrieval_time=%.2fms)",
                len(results),
                str(query)[:50],
                retrieval_time
            )
            
            return results
            
        except Exception as e:
            logger.error("Failed to retrieve entries from STM: %s", str(e), exc_info=True)
            raise MemoryRetrievalError(f"Failed to retrieve entries from STM: {str(e)}") from e
    
    def get_by_id(self, entry_id: str) -> Optional[STMEntry]:
        """
        Retrieve a specific entry by its ID.
        
        Args:
            entry_id: ID of the entry to retrieve
            
        Returns:
            Optional[STMEntry]: The entry if found, None otherwise
        """
        entry = self._entries.get(entry_id)
        
        if entry:
            # Update activation
            entry.update_activation()
        
        return entry
    
    def update(
        self,
        entry_id: str,
        content: Optional[Any] = None,
        metadata: Optional[dict[str, Any]] = None,
        context: Optional[dict[str, Any]] = None,
        activation_level: Optional[float] = None,
        decay_rate: Optional[float] = None
    ) -> bool:
        """
        Update an existing entry in Short-Term Memory.
        
        Args:
            entry_id: ID of the entry to update
            content: New content (if None, keeps existing)
            metadata: New metadata (if None, keeps existing)
            context: New context (if None, keeps existing)
            activation_level: New activation level (if None, keeps existing)
            decay_rate: New decay rate (if None, keeps existing)
            
        Returns:
            bool: True if update successful, False if entry not found
            
        Raises:
            MemoryValidationError: If parameters are invalid
            MemoryStorageError: If update operation fails
        """
        try:
            entry = self._entries.get(entry_id)
            if not entry:
                logger.warning("Attempted to update non-existent STM entry: %s", entry_id)
                return False
            
            # Update fields if provided
            if content is not None:
                entry.content = content
            
            if metadata is not None:
                entry.metadata = metadata
            
            if context is not None:
                entry.context = context
            
            if activation_level is not None:
                if not 0.0 <= activation_level <= 1.0:
                    raise MemoryValidationError(
                        f"Activation level must be between 0.0 and 1.0, got {activation_level}"
                    )
                entry.activation_level = activation_level
            
            if decay_rate is not None:
                if decay_rate < 0.0:
                    raise MemoryValidationError(f"Decay rate must be non-negative, got {decay_rate}")
                entry.decay_rate = decay_rate
            
            # Update last accessed time
            entry.last_accessed = time.time()
            
            logger.debug("Updated STM entry: %s", entry_id)
            return True
            
        except MemoryValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error("Failed to update STM entry: %s", str(e), exc_info=True)
            raise MemoryStorageError(f"Failed to update STM entry: {str(e)}") from e
    
    def remove(self, entry_id: str) -> bool:
        """
        Remove an entry from Short-Term Memory.
        
        Args:
            entry_id: ID of the entry to remove
            
        Returns:
            bool: True if removal successful, False if entry not found
        """
        if entry_id in self._entries:
            del self._entries[entry_id]
            logger.debug("Removed entry from STM: %s", entry_id)
            return True
        
        logger.warning("Attempted to remove non-existent STM entry: %s", entry_id)
        return False
    
    def clear(self) -> None:
        """
        Clear all entries from Short-Term Memory.
        """
        entry_count = len(self._entries)
        self._entries.clear()
        self._retrieval_times.clear()
        logger.info("Cleared STM (%d entries removed)", entry_count)
    
    def get_health_metrics(self) -> STMHealthStatus:
        """
        Get health metrics for the Short-Term Memory system.
        
        Returns:
            STMHealthStatus: Current health metrics
        """
        # Update activations before calculating metrics
        self._update_all_activations()
        
        # Calculate metrics
        entry_count = len(self._entries)
        capacity_used = entry_count / self.config.max_capacity if self.config.max_capacity > 0 else 0.0
        
        # Calculate average activation level
        avg_activation = 0.0
        if entry_count > 0:
            avg_activation = sum(e.activation_level for e in self._entries.values()) / entry_count
        
        # Calculate decay efficiency (ratio of entries with appropriate decay rates)
        decay_efficiency = 0.0
        if entry_count > 0:
            appropriate_decay = sum(
                1 for e in self._entries.values() 
                if 0.01 <= e.decay_rate <= 0.2  # Reasonable decay rate range
            )
            decay_efficiency = appropriate_decay / entry_count
        
        # Calculate context richness (average number of context attributes)
        context_richness = 0.0
        if entry_count > 0:
            avg_context_attrs = sum(len(e.context) for e in self._entries.values()) / entry_count
            # Normalize to 0.0-1.0 scale (assuming 10 attributes is "rich")
            context_richness = min(1.0, avg_context_attrs / 10.0)
        
        # Calculate retrieval latency
        retrieval_latency_ms = 0.0
        if self._retrieval_times:
            retrieval_latency_ms = sum(self._retrieval_times) / len(self._retrieval_times)
        
        return STMHealthStatus(
            capacity_used=capacity_used,
            entry_count=entry_count,
            avg_activation_level=avg_activation,
            decay_efficiency=decay_efficiency,
            context_richness=context_richness,
            retrieval_latency_ms=retrieval_latency_ms
        )
    
    def _update_all_activations(self) -> None:
        """
        Update activation levels for all entries based on time decay.
        
        This also removes entries that fall below the activation threshold.
        """
        current_time = time.time()
        to_remove = []
        
        for entry_id, entry in self._entries.items():
            # Update activation level
            entry.update_activation(current_time)
            
            # Mark for removal if below threshold
            if entry.activation_level < self.config.activation_threshold:
                to_remove.append(entry_id)
        
        # Remove entries with low activation
        for entry_id in to_remove:
            del self._entries[entry_id]
        
        if to_remove:
            logger.debug("Removed %d entries from STM due to low activation", len(to_remove))
    
    def _cleanup_low_activation_entries(self) -> int:
        """
        Remove entries with the lowest activation levels to free up space.
        
        Returns:
            int: Number of entries removed
        """
        # Update all activations first
        self._update_all_activations()
        
        # If still at capacity, remove lowest activation entries
        if len(self._entries) >= self.config.max_capacity:
            # Sort entries by activation level (lowest first)
            sorted_entries = sorted(
                self._entries.items(),
                key=lambda item: item[1].activation_level
            )
            
            # Remove up to 10% of entries
            remove_count = max(1, int(self.config.max_capacity * 0.1))
            entries_to_remove = sorted_entries[:remove_count]
            
            for entry_id, _ in entries_to_remove:
                del self._entries[entry_id]
            
            logger.info(
                "Removed %d low-activation entries from STM to free up space",
                len(entries_to_remove)
            )
            
            return len(entries_to_remove)
        
        return 0
    
    def _check_consolidation(self) -> None:
        """
        Check if it's time to consolidate memories to LTM and perform consolidation if needed.
        """
        current_time = time.time()
        time_since_last = current_time - self._last_consolidation
        
        # Check if consolidation interval has passed
        if time_since_last >= self.config.consolidation_interval:
            self._consolidate_to_ltm()
            self._last_consolidation = current_time
    
    def _consolidate_to_ltm(self) -> None:
        """
        Consolidate important memories to Long-Term Memory.
        
        This identifies high-activation, stable memories and transfers them to LTM
        if an LTM interface is available.
        """
        if not self.ltm_interface:
            logger.debug("LTM interface not available, skipping consolidation")
            return
        
        try:
            # Find entries suitable for consolidation (high activation, not recently added)
            current_time = time.time()
            consolidation_candidates = []
            
            for entry in self._entries.values():
                # Update activation
                entry.update_activation(current_time)
                
                # Check if entry is suitable for consolidation:
                # 1. High activation (stable memory)
                # 2. At least 30 minutes old (not too recent)
                # 3. Has been accessed multiple times (important)
                if (
                    entry.activation_level > 0.7 and
                    (current_time - entry.timestamp) > 1800 and  # 30 minutes
                    (current_time - entry.last_accessed) < 3600  # Accessed in last hour
                ):
                    consolidation_candidates.append(entry)
            
            # Consolidate to LTM
            if consolidation_candidates:
                logger.info(
                    "Consolidating %d entries from STM to LTM",
                    len(consolidation_candidates)
                )
                
                # In a real implementation, this would call the LTM interface
                # self.ltm_interface.store_batch(consolidation_candidates)
                
                # For now, just log the consolidation
                for entry in consolidation_candidates:
                    logger.debug(
                        "Consolidated entry to LTM: id=%s, activation=%.2f",
                        entry.entry_id,
                        entry.activation_level
                    )
        
        except Exception as e:
            logger.error("Error during STM to LTM consolidation: %s", str(e), exc_info=True)
    
    def _matches_query(self, entry: STMEntry, query: Any) -> bool:
        """
        Check if an entry matches the given query.
        
        Args:
            entry: The memory entry to check
            query: The search query
            
        Returns:
            bool: True if the entry matches the query
            
        Note:
            This is a simplified implementation. In a real system, this would
            use semantic search, embedding similarity, or other matching techniques.
        """
        # Simple string matching for demonstration
        query_str = str(query).lower()
        
        # Check content
        if isinstance(entry.content, str) and query_str in entry.content.lower():
            return True
        
        # Check metadata
        for key, value in entry.metadata.items():
            if query_str in str(key).lower() or query_str in str(value).lower():
                return True
        
        # Check context
        for key, value in entry.context.items():
            if query_str in str(key).lower() or query_str in str(value).lower():
                return True
        
        return False
    
    def _matches_context(self, entry: STMEntry, context_filter: dict[str, Any]) -> bool:
        """
        Check if an entry matches the given context filter.
        
        Args:
            entry: The memory entry to check
            context_filter: Context attributes to match
            
        Returns:
            bool: True if the entry matches all context filter criteria
        """
        for key, value in context_filter.items():
            # If key doesn't exist in entry context, no match
            if key not in entry.context:
                return False
            
            # If value doesn't match, no match
            if entry.context[key] != value:
                return False
        
        # All criteria matched
        return True