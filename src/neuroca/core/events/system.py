"""
System Events Module for NeuroCognitive Architecture (NCA).

This module defines system-level events that affect the overall architecture's operation.
System events represent critical operations such as initialization, shutdown, resource
allocation/deallocation, configuration changes, and error conditions that impact the
entire NCA system.

The module provides:
1. A base SystemEvent class that all system events inherit from
2. Specific system event implementations for common operations
3. A SystemEventBus for publishing and subscribing to system events
4. Utilities for event handling, filtering, and processing

Usage:
    # Publishing a system event
    event_bus = SystemEventBus.get_instance()
    event_bus.publish(SystemStartupEvent(startup_time=datetime.now()))
    
    # Subscribing to system events
    def handle_shutdown(event):
        logger.info(f"System shutdown detected: {event.reason}")
        
    event_bus.subscribe(SystemShutdownEvent, handle_shutdown)
"""

import enum
import logging
import threading
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional, TypeVar, Union

# Configure module logger
logger = logging.getLogger(__name__)

# Type variable for event types
T = TypeVar('T', bound='SystemEvent')


class SystemEventPriority(enum.IntEnum):
    """Priority levels for system events."""
    CRITICAL = 0  # Highest priority - immediate handling required
    HIGH = 1      # High priority - handle as soon as possible
    NORMAL = 2    # Normal priority - standard handling
    LOW = 3       # Low priority - handle when resources available
    BACKGROUND = 4  # Lowest priority - handle during idle time


class SystemEventCategory(enum.Enum):
    """Categories of system events for classification and filtering."""
    LIFECYCLE = "lifecycle"       # System startup, shutdown, restart
    RESOURCE = "resource"         # Resource allocation, deallocation
    CONFIGURATION = "configuration"  # Configuration changes
    ERROR = "error"               # System errors and exceptions
    SECURITY = "security"         # Security-related events
    PERFORMANCE = "performance"   # Performance metrics and thresholds
    MAINTENANCE = "maintenance"   # Maintenance operations
    MONITORING = "monitoring"     # System monitoring events
    CUSTOM = "custom"             # Custom/user-defined events


@dataclass
class SystemEvent(ABC):
    """
    Base class for all system events in the NCA.
    
    All system events must inherit from this class and implement required methods.
    """
    # Unique identifier for the event
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Timestamp when the event was created
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Event priority level
    priority: SystemEventPriority = SystemEventPriority.NORMAL
    
    # Event category for classification
    category: SystemEventCategory = SystemEventCategory.CUSTOM
    
    # Additional metadata for the event
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @abstractmethod
    def get_description(self) -> str:
        """Return a human-readable description of the event."""
        pass
    
    def __str__(self) -> str:
        """String representation of the event."""
        return f"{self.__class__.__name__}(id={self.id}, timestamp={self.timestamp}, priority={self.priority.name})"


@dataclass
class SystemStartupEvent(SystemEvent):
    """Event fired when the system is starting up."""
    startup_time: datetime = field(default_factory=datetime.now)
    startup_mode: str = "normal"  # normal, recovery, maintenance, etc.
    components_loaded: list[str] = field(default_factory=list)
    
    def __post_init__(self):
        self.category = SystemEventCategory.LIFECYCLE
        self.priority = SystemEventPriority.HIGH
    
    def get_description(self) -> str:
        return f"System startup initiated at {self.startup_time} in {self.startup_mode} mode"


@dataclass
class SystemShutdownEvent(SystemEvent):
    """Event fired when the system is shutting down."""
    shutdown_time: datetime = field(default_factory=datetime.now)
    reason: str = "normal"  # normal, error, maintenance, etc.
    graceful: bool = True  # Whether shutdown is graceful or forced
    
    def __post_init__(self):
        self.category = SystemEventCategory.LIFECYCLE
        self.priority = SystemEventPriority.CRITICAL
    
    def get_description(self) -> str:
        shutdown_type = "graceful" if self.graceful else "forced"
        return f"System {shutdown_type} shutdown initiated at {self.shutdown_time} due to: {self.reason}"


@dataclass
class SystemErrorEvent(SystemEvent):
    """Event fired when a system-level error occurs."""
    error_message: str
    error_type: str
    traceback: Optional[str] = None
    component: Optional[str] = None
    recoverable: bool = True
    
    def __post_init__(self):
        self.category = SystemEventCategory.ERROR
        self.priority = SystemEventPriority.HIGH if self.recoverable else SystemEventPriority.CRITICAL
    
    def get_description(self) -> str:
        component_str = f" in component {self.component}" if self.component else ""
        recovery_str = "recoverable" if self.recoverable else "non-recoverable"
        return f"{recovery_str.capitalize()} error{component_str}: {self.error_type} - {self.error_message}"


@dataclass
class ResourceAllocationEvent(SystemEvent):
    """Event fired when system resources are allocated or deallocated."""
    resource_type: str  # memory, cpu, gpu, etc.
    resource_id: str
    allocated: bool = True  # True for allocation, False for deallocation
    amount: Optional[Union[int, float]] = None  # Amount of resource
    unit: Optional[str] = None  # Unit of measurement (MB, GB, cores, etc.)
    
    def __post_init__(self):
        self.category = SystemEventCategory.RESOURCE
        self.priority = SystemEventPriority.NORMAL
    
    def get_description(self) -> str:
        action = "allocated" if self.allocated else "deallocated"
        amount_str = f" {self.amount}{self.unit}" if self.amount and self.unit else ""
        return f"Resource {action}: {self.resource_type} {self.resource_id}{amount_str}"


@dataclass
class ConfigurationChangeEvent(SystemEvent):
    """Event fired when system configuration changes."""
    config_key: str
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    source: str = "user"  # user, system, api, etc.
    
    def __post_init__(self):
        self.category = SystemEventCategory.CONFIGURATION
        self.priority = SystemEventPriority.HIGH
    
    def get_description(self) -> str:
        return f"Configuration changed: {self.config_key} from {self.old_value} to {self.new_value} by {self.source}"


@dataclass
class PerformanceThresholdEvent(SystemEvent):
    """Event fired when a performance threshold is crossed."""
    metric_name: str
    current_value: Union[int, float]
    threshold_value: Union[int, float]
    direction: str  # "above" or "below"
    component: Optional[str] = None
    
    def __post_init__(self):
        self.category = SystemEventCategory.PERFORMANCE
        self.priority = SystemEventPriority.HIGH
    
    def get_description(self) -> str:
        component_str = f" for {self.component}" if self.component else ""
        return f"Performance threshold crossed{component_str}: {self.metric_name} is {self.direction} threshold " \
               f"({self.current_value} vs {self.threshold_value})"


class EventHandler:
    """
    Handler for processing system events.
    
    This class wraps a callback function with metadata and filtering capabilities.
    """
    
    def __init__(
        self,
        callback: Callable[[SystemEvent], None],
        event_type: type[SystemEvent],
        handler_id: Optional[str] = None,
        filter_fn: Optional[Callable[[SystemEvent], bool]] = None
    ):
        """
        Initialize a new event handler.
        
        Args:
            callback: Function to call when an event is received
            event_type: Type of event this handler processes
            handler_id: Unique identifier for this handler (auto-generated if None)
            filter_fn: Optional function to filter events before processing
        """
        self.callback = callback
        self.event_type = event_type
        self.handler_id = handler_id or str(uuid.uuid4())
        self.filter_fn = filter_fn
        
    def can_handle(self, event: SystemEvent) -> bool:
        """
        Check if this handler can process the given event.
        
        Args:
            event: The event to check
            
        Returns:
            True if this handler can process the event, False otherwise
        """
        if not isinstance(event, self.event_type):
            return False
            
        if self.filter_fn is not None:
            return self.filter_fn(event)
            
        return True
        
    def handle(self, event: SystemEvent) -> None:
        """
        Process the given event.
        
        Args:
            event: The event to process
        """
        if not self.can_handle(event):
            return
            
        try:
            self.callback(event)
        except Exception as e:
            logger.error(f"Error in event handler {self.handler_id}: {str(e)}", exc_info=True)


class SystemEventBus:
    """
    Central event bus for publishing and subscribing to system events.
    
    This class implements the Singleton pattern to ensure a single event bus instance.
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._handlers: dict[type[SystemEvent], list[EventHandler]] = {}
        self._global_handlers: list[EventHandler] = []
        self._event_history: list[SystemEvent] = []
        self._max_history_size = 1000  # Default history size
        self._history_enabled = True
        self._lock = threading.RLock()
        self._initialized = True
        
        logger.info("System event bus initialized")
    
    @classmethod
    def get_instance(cls) -> 'SystemEventBus':
        """
        Get the singleton instance of the event bus.
        
        Returns:
            The event bus instance
        """
        return cls()
    
    def subscribe(
        self,
        event_type: type[T],
        callback: Callable[[T], None],
        handler_id: Optional[str] = None,
        filter_fn: Optional[Callable[[T], bool]] = None
    ) -> str:
        """
        Subscribe to events of the specified type.
        
        Args:
            event_type: Type of event to subscribe to
            callback: Function to call when an event is received
            handler_id: Optional unique identifier for this subscription
            filter_fn: Optional function to filter events
            
        Returns:
            Handler ID that can be used to unsubscribe
        """
        handler = EventHandler(callback, event_type, handler_id, filter_fn)
        
        with self._lock:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append(handler)
            
        logger.debug(f"Subscribed handler {handler.handler_id} to {event_type.__name__}")
        return handler.handler_id
    
    def subscribe_all(
        self,
        callback: Callable[[SystemEvent], None],
        handler_id: Optional[str] = None,
        filter_fn: Optional[Callable[[SystemEvent], bool]] = None
    ) -> str:
        """
        Subscribe to all system events.
        
        Args:
            callback: Function to call when any event is received
            handler_id: Optional unique identifier for this subscription
            filter_fn: Optional function to filter events
            
        Returns:
            Handler ID that can be used to unsubscribe
        """
        handler = EventHandler(callback, SystemEvent, handler_id, filter_fn)
        
        with self._lock:
            self._global_handlers.append(handler)
            
        logger.debug(f"Subscribed global handler {handler.handler_id}")
        return handler.handler_id
    
    def unsubscribe(self, handler_id: str) -> bool:
        """
        Unsubscribe a handler by its ID.
        
        Args:
            handler_id: The ID of the handler to unsubscribe
            
        Returns:
            True if the handler was found and removed, False otherwise
        """
        with self._lock:
            # Check global handlers
            for i, handler in enumerate(self._global_handlers):
                if handler.handler_id == handler_id:
                    self._global_handlers.pop(i)
                    logger.debug(f"Unsubscribed global handler {handler_id}")
                    return True
            
            # Check specific event handlers
            for event_type, handlers in self._handlers.items():
                for i, handler in enumerate(handlers):
                    if handler.handler_id == handler_id:
                        handlers.pop(i)
                        logger.debug(f"Unsubscribed handler {handler_id} from {event_type.__name__}")
                        return True
        
        logger.warning(f"Handler {handler_id} not found for unsubscription")
        return False
    
    def publish(self, event: SystemEvent) -> None:
        """
        Publish an event to all subscribed handlers.
        
        Args:
            event: The event to publish
        """
        if not isinstance(event, SystemEvent):
            raise TypeError(f"Expected SystemEvent, got {type(event).__name__}")
        
        # Store in history if enabled
        if self._history_enabled:
            with self._lock:
                self._event_history.append(event)
                # Trim history if needed
                if len(self._event_history) > self._max_history_size:
                    self._event_history = self._event_history[-self._max_history_size:]
        
        # Get relevant handlers
        handlers_to_call = []
        
        with self._lock:
            # Add type-specific handlers
            event_type = type(event)
            for handler_type, handlers in self._handlers.items():
                if issubclass(event_type, handler_type):
                    handlers_to_call.extend(handlers)
            
            # Add global handlers
            handlers_to_call.extend(self._global_handlers)
        
        # Call handlers outside the lock to prevent deadlocks
        for handler in handlers_to_call:
            try:
                if handler.can_handle(event):
                    handler.handle(event)
            except Exception as e:
                logger.error(f"Error dispatching event {event.id} to handler {handler.handler_id}: {str(e)}", 
                             exc_info=True)
        
        logger.debug(f"Published event: {event}")
    
    def get_history(self, limit: Optional[int] = None) -> list[SystemEvent]:
        """
        Get the event history.
        
        Args:
            limit: Optional maximum number of events to return
            
        Returns:
            List of historical events, newest first
        """
        with self._lock:
            if not limit:
                return list(self._event_history)
            return list(self._event_history[-limit:])
    
    def clear_history(self) -> None:
        """Clear the event history."""
        with self._lock:
            self._event_history.clear()
        logger.debug("Event history cleared")
    
    def set_history_size(self, max_size: int) -> None:
        """
        Set the maximum history size.
        
        Args:
            max_size: Maximum number of events to keep in history
        """
        if max_size < 0:
            raise ValueError("History size must be non-negative")
            
        with self._lock:
            self._max_history_size = max_size
            # Trim history if needed
            if len(self._event_history) > max_size:
                self._event_history = self._event_history[-max_size:]
        
        logger.debug(f"Event history size set to {max_size}")
    
    def enable_history(self, enabled: bool = True) -> None:
        """
        Enable or disable event history.
        
        Args:
            enabled: Whether to enable event history
        """
        with self._lock:
            self._history_enabled = enabled
            if not enabled:
                self._event_history.clear()
        
        logger.debug(f"Event history {'enabled' if enabled else 'disabled'}")


class EventMonitor:
    """
    Utility class for monitoring and analyzing system events.
    
    This class provides tools for tracking event patterns, frequencies,
    and other metrics useful for system diagnostics.
    """
    
    def __init__(self, event_bus: Optional[SystemEventBus] = None):
        """
        Initialize a new event monitor.
        
        Args:
            event_bus: Event bus to monitor (uses singleton if None)
        """
        self.event_bus = event_bus or SystemEventBus.get_instance()
        self.event_counts: dict[type[SystemEvent], int] = {}
        self.category_counts: dict[SystemEventCategory, int] = {}
        self.priority_counts: dict[SystemEventPriority, int] = {}
        self.start_time = datetime.now()
        self.handler_id: Optional[str] = None
        self._lock = threading.RLock()
    
    def start_monitoring(self) -> None:
        """Start monitoring events."""
        if self.handler_id:
            return  # Already monitoring
            
        self.handler_id = self.event_bus.subscribe_all(self._handle_event)
        logger.info("Event monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop monitoring events."""
        if not self.handler_id:
            return  # Not monitoring
            
        self.event_bus.unsubscribe(self.handler_id)
        self.handler_id = None
        logger.info("Event monitoring stopped")
    
    def _handle_event(self, event: SystemEvent) -> None:
        """
        Process an event for monitoring.
        
        Args:
            event: The event to process
        """
        with self._lock:
            # Update event type counts
            event_type = type(event)
            self.event_counts[event_type] = self.event_counts.get(event_type, 0) + 1
            
            # Update category counts
            self.category_counts[event.category] = self.category_counts.get(event.category, 0) + 1
            
            # Update priority counts
            self.priority_counts[event.priority] = self.priority_counts.get(event.priority, 0) + 1
    
    def get_statistics(self) -> dict[str, Any]:
        """
        Get monitoring statistics.
        
        Returns:
            Dictionary of monitoring statistics
        """
        with self._lock:
            duration = (datetime.now() - self.start_time).total_seconds()
            total_events = sum(self.event_counts.values())
            
            return {
                "start_time": self.start_time,
                "duration_seconds": duration,
                "total_events": total_events,
                "events_per_second": total_events / duration if duration > 0 else 0,
                "event_type_counts": {et.__name__: count for et, count in self.event_counts.items()},
                "category_counts": {cat.name: count for cat, count in self.category_counts.items()},
                "priority_counts": {pri.name: count for pri, count in self.priority_counts.items()},
            }
    
    def reset_statistics(self) -> None:
        """Reset all monitoring statistics."""
        with self._lock:
            self.event_counts.clear()
            self.category_counts.clear()
            self.priority_counts.clear()
            self.start_time = datetime.now()
        logger.debug("Event monitoring statistics reset")


# Utility functions for working with system events

def create_error_event(
    error: Exception,
    component: Optional[str] = None,
    recoverable: bool = True,
    metadata: Optional[dict[str, Any]] = None
) -> SystemErrorEvent:
    """
    Create a system error event from an exception.
    
    Args:
        error: The exception that occurred
        component: Optional component name where the error occurred
        recoverable: Whether the error is recoverable
        metadata: Additional metadata for the event
        
    Returns:
        A SystemErrorEvent representing the error
    """
    import traceback
    
    error_event = SystemErrorEvent(
        error_message=str(error),
        error_type=type(error).__name__,
        traceback=traceback.format_exc(),
        component=component,
        recoverable=recoverable,
        metadata=metadata or {}
    )
    
    return error_event


def publish_error(
    error: Exception,
    component: Optional[str] = None,
    recoverable: bool = True,
    metadata: Optional[dict[str, Any]] = None
) -> None:
    """
    Create and publish a system error event from an exception.
    
    Args:
        error: The exception that occurred
        component: Optional component name where the error occurred
        recoverable: Whether the error is recoverable
        metadata: Additional metadata for the event
    """
    event_bus = SystemEventBus.get_instance()
    error_event = create_error_event(error, component, recoverable, metadata)
    event_bus.publish(error_event)


def filter_by_priority(min_priority: SystemEventPriority, max_priority: Optional[SystemEventPriority] = None):
    """
    Create a filter function for events based on priority.
    
    Args:
        min_priority: Minimum priority level (inclusive)
        max_priority: Maximum priority level (inclusive, optional)
        
    Returns:
        A filter function that can be used with event subscriptions
    """
    def priority_filter(event: SystemEvent) -> bool:
        if max_priority is not None:
            return min_priority <= event.priority <= max_priority
        return min_priority <= event.priority
    
    return priority_filter


def filter_by_category(categories: Union[SystemEventCategory, list[SystemEventCategory]]):
    """
    Create a filter function for events based on category.
    
    Args:
        categories: Category or list of categories to include
        
    Returns:
        A filter function that can be used with event subscriptions
    """
    if isinstance(categories, SystemEventCategory):
        categories = [categories]
    
    category_set = set(categories)
    
    def category_filter(event: SystemEvent) -> bool:
        return event.category in category_set
    
    return category_filter