"""
Event System for NeuroCognitive Architecture (NCA)

This module implements a comprehensive event system for the NCA project, enabling
asynchronous communication between different components through a publish-subscribe
pattern. The event system is designed to be thread-safe, efficient, and flexible
to support the complex interactions required in a cognitive architecture.

Key components:
- EventBus: Central event dispatcher that manages subscriptions and event distribution
- Event: Base class for all events in the system
- EventSubscriber: Interface for components that want to receive events
- EventPriority: Enumeration for defining event handling priorities

Usage examples:
    # Creating and publishing an event
    from neuroca.core.events import EventBus, Event
    
    class MemoryUpdateEvent(Event):
        def __init__(self, memory_id, content):
            super().__init__()
            self.memory_id = memory_id
            self.content = content
    
    # Publishing an event
    event_bus = EventBus.get_instance()
    event_bus.publish(MemoryUpdateEvent("mem123", "New memory content"))
    
    # Subscribing to events
    class MemoryMonitor:
        def __init__(self):
            self.event_bus = EventBus.get_instance()
            self.event_bus.subscribe(MemoryUpdateEvent, self.on_memory_update)
        
        def on_memory_update(self, event):
            print(f"Memory {event.memory_id} updated with: {event.content}")
"""

import enum
import inspect
import logging
import threading
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional, TypeVar

# Configure module logger
logger = logging.getLogger(__name__)

# Type variable for event types
T = TypeVar('T', bound='Event')


class EventPriority(enum.IntEnum):
    """
    Defines priority levels for event handlers.
    
    Higher priority handlers are executed before lower priority ones.
    """
    HIGHEST = 100
    HIGH = 75
    NORMAL = 50
    LOW = 25
    LOWEST = 0


class Event:
    """
    Base class for all events in the system.
    
    All events should inherit from this class and may add additional
    attributes specific to the event type.
    """
    
    def __init__(self):
        """
        Initialize a new event with metadata.
        """
        self.id = str(uuid.uuid4())
        self.timestamp = datetime.now()
        self.is_canceled = False
        self.metadata: dict[str, Any] = {}
    
    def cancel(self) -> None:
        """
        Mark the event as canceled to prevent further processing.
        
        Handlers can check this flag and skip processing if desired.
        """
        self.is_canceled = True
        logger.debug(f"Event {self.id} of type {self.__class__.__name__} has been canceled")
    
    def add_metadata(self, key: str, value: Any) -> None:
        """
        Add metadata to the event.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Retrieve metadata from the event.
        
        Args:
            key: Metadata key
            default: Default value if key doesn't exist
            
        Returns:
            The metadata value or default if not found
        """
        return self.metadata.get(key, default)
    
    def __str__(self) -> str:
        """String representation of the event."""
        return f"{self.__class__.__name__}(id={self.id}, timestamp={self.timestamp})"


class EventSubscriber(ABC):
    """
    Interface for components that want to receive events.
    
    Implementing this interface ensures that subscribers properly
    handle event registration and unregistration.
    """
    
    @abstractmethod
    def handle_event(self, event: Event) -> None:
        """
        Process an event.
        
        Args:
            event: The event to process
        """
        pass
    
    def __enter__(self):
        """Context manager support for automatic registration."""
        EventBus.get_instance().register_subscriber(self)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager support for automatic unregistration."""
        EventBus.get_instance().unregister_subscriber(self)


@dataclass
class EventHandler:
    """
    Represents a registered event handler function.
    
    Attributes:
        callback: The function to call when an event occurs
        priority: The priority of this handler
        subscriber: Optional reference to the subscriber object
        filter_func: Optional function to filter events before handling
    """
    callback: Callable[[Event], None]
    priority: EventPriority = EventPriority.NORMAL
    subscriber: Optional[EventSubscriber] = None
    filter_func: Optional[Callable[[Event], bool]] = None
    
    # Metadata for debugging and monitoring
    registration_time: datetime = field(default_factory=datetime.now)
    call_count: int = 0
    last_call_time: Optional[datetime] = None
    avg_execution_time: float = 0.0
    
    def matches_event(self, event: Event) -> bool:
        """
        Check if this handler should process the given event.
        
        Args:
            event: The event to check
            
        Returns:
            True if the handler should process the event, False otherwise
        """
        if self.filter_func is not None:
            try:
                return self.filter_func(event)
            except Exception as e:
                logger.error(f"Error in event filter function: {e}")
                return False
        return True
    
    def __call__(self, event: Event) -> None:
        """
        Call the handler with the given event.
        
        Args:
            event: The event to handle
        """
        start_time = time.time()
        try:
            self.callback(event)
            self.call_count += 1
            self.last_call_time = datetime.now()
            
            # Update average execution time
            execution_time = time.time() - start_time
            if self.call_count == 1:
                self.avg_execution_time = execution_time
            else:
                # Exponential moving average with alpha=0.1
                self.avg_execution_time = 0.1 * execution_time + 0.9 * self.avg_execution_time
                
        except Exception as e:
            logger.error(f"Error in event handler {self.callback.__name__}: {e}", exc_info=True)


class EventBus:
    """
    Central event dispatcher that manages subscriptions and event distribution.
    
    This class implements the Singleton pattern to ensure a single event bus
    instance throughout the application.
    """
    _instance = None
    _lock = threading.RLock()
    
    def __init__(self):
        """
        Initialize the event bus.
        
        Note: This should not be called directly. Use get_instance() instead.
        """
        if EventBus._instance is not None:
            raise RuntimeError("EventBus is a singleton. Use EventBus.get_instance() instead.")
        
        # Map of event types to handlers
        self._handlers: dict[type[Event], list[EventHandler]] = {}
        
        # Set of all registered subscribers
        self._subscribers: set[EventSubscriber] = set()
        
        # Lock for thread safety
        self._handlers_lock = threading.RLock()
        
        # Event history for debugging (limited size)
        self._max_history_size = 100
        self._event_history: list[Event] = []
        self._history_lock = threading.RLock()
        
        logger.info("EventBus initialized")
    
    @classmethod
    def get_instance(cls) -> 'EventBus':
        """
        Get the singleton instance of the EventBus.
        
        Returns:
            The EventBus instance
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = EventBus()
        return cls._instance
    
    @classmethod
    def reset(cls) -> None:
        """
        Reset the EventBus singleton (primarily for testing).
        """
        with cls._lock:
            if cls._instance is not None:
                logger.warning("EventBus singleton is being reset")
                cls._instance = None
    
    def subscribe(self, 
                  event_type: type[T], 
                  callback: Callable[[T], None], 
                  priority: EventPriority = EventPriority.NORMAL,
                  subscriber: Optional[EventSubscriber] = None,
                  filter_func: Optional[Callable[[T], bool]] = None) -> None:
        """
        Subscribe to events of a specific type.
        
        Args:
            event_type: The type of event to subscribe to
            callback: The function to call when an event occurs
            priority: The priority of this handler
            subscriber: Optional reference to the subscriber object
            filter_func: Optional function to filter events before handling
        """
        if not inspect.isclass(event_type) or not issubclass(event_type, Event):
            raise TypeError(f"event_type must be a subclass of Event, got {event_type}")
        
        handler = EventHandler(
            callback=callback,
            priority=priority,
            subscriber=subscriber,
            filter_func=filter_func
        )
        
        with self._handlers_lock:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            
            # Insert handler in priority order (highest first)
            handlers = self._handlers[event_type]
            index = 0
            while index < len(handlers) and handlers[index].priority > priority:
                index += 1
            handlers.insert(index, handler)
        
        logger.debug(f"Subscribed to {event_type.__name__} events with priority {priority}")
    
    def unsubscribe(self, event_type: type[Event], callback: Callable[[Event], None]) -> bool:
        """
        Unsubscribe from events of a specific type.
        
        Args:
            event_type: The type of event to unsubscribe from
            callback: The callback function to remove
            
        Returns:
            True if the subscription was removed, False if it wasn't found
        """
        with self._handlers_lock:
            if event_type not in self._handlers:
                return False
            
            handlers = self._handlers[event_type]
            for i, handler in enumerate(handlers):
                if handler.callback == callback:
                    handlers.pop(i)
                    logger.debug(f"Unsubscribed from {event_type.__name__} events")
                    
                    # Clean up empty handler lists
                    if not handlers:
                        del self._handlers[event_type]
                    return True
        
        return False
    
    def register_subscriber(self, subscriber: EventSubscriber) -> None:
        """
        Register a subscriber object.
        
        Args:
            subscriber: The subscriber to register
        """
        if not isinstance(subscriber, EventSubscriber):
            raise TypeError(f"subscriber must be an instance of EventSubscriber, got {type(subscriber)}")
        
        with self._handlers_lock:
            self._subscribers.add(subscriber)
        logger.debug(f"Registered subscriber: {subscriber.__class__.__name__}")
    
    def unregister_subscriber(self, subscriber: EventSubscriber) -> None:
        """
        Unregister a subscriber and remove all its event handlers.
        
        Args:
            subscriber: The subscriber to unregister
        """
        with self._handlers_lock:
            # Remove from subscribers set
            self._subscribers.discard(subscriber)
            
            # Remove all handlers associated with this subscriber
            for event_type, handlers in list(self._handlers.items()):
                self._handlers[event_type] = [h for h in handlers if h.subscriber is not subscriber]
                
                # Clean up empty handler lists
                if not self._handlers[event_type]:
                    del self._handlers[event_type]
        
        logger.debug(f"Unregistered subscriber: {subscriber.__class__.__name__}")
    
    def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers.
        
        Args:
            event: The event to publish
        """
        if not isinstance(event, Event):
            raise TypeError(f"event must be an instance of Event, got {type(event)}")
        
        # Add to history
        with self._history_lock:
            self._event_history.append(event)
            if len(self._event_history) > self._max_history_size:
                self._event_history.pop(0)
        
        # Find all handlers that should receive this event
        handlers_to_call = []
        with self._handlers_lock:
            # Check for exact type matches
            if type(event) in self._handlers:
                handlers_to_call.extend(self._handlers[type(event)])
            
            # Check for parent class matches
            for event_type, handlers in self._handlers.items():
                if event_type != type(event) and isinstance(event, event_type):
                    handlers_to_call.extend(handlers)
        
        # Sort by priority (highest first)
        handlers_to_call.sort(key=lambda h: h.priority, reverse=True)
        
        # Call handlers
        logger.debug(f"Publishing event: {event}")
        for handler in handlers_to_call:
            if event.is_canceled:
                logger.debug(f"Event {event.id} was canceled, stopping propagation")
                break
                
            if handler.matches_event(event):
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Error handling event {event.id}: {e}", exc_info=True)
    
    def publish_async(self, event: Event, executor=None) -> None:
        """
        Publish an event asynchronously using a thread pool executor.
        
        Args:
            event: The event to publish
            executor: Optional executor to use (if None, will use threading)
        """
        if executor is None:
            thread = threading.Thread(target=self.publish, args=(event,), daemon=True)
            thread.start()
        else:
            executor.submit(self.publish, event)
    
    def get_event_history(self) -> list[Event]:
        """
        Get a copy of the recent event history.
        
        Returns:
            List of recent events
        """
        with self._history_lock:
            return self._event_history.copy()
    
    def clear_event_history(self) -> None:
        """Clear the event history."""
        with self._history_lock:
            self._event_history.clear()
    
    def get_subscriber_count(self) -> int:
        """
        Get the number of registered subscribers.
        
        Returns:
            Number of subscribers
        """
        with self._handlers_lock:
            return len(self._subscribers)
    
    def get_handler_count(self) -> dict[str, int]:
        """
        Get the number of handlers registered for each event type.
        
        Returns:
            Dictionary mapping event type names to handler counts
        """
        with self._handlers_lock:
            return {event_type.__name__: len(handlers) 
                    for event_type, handlers in self._handlers.items()}


# Common system events

class SystemEvent(Event):
    """Base class for system-level events."""
    pass


class StartupEvent(SystemEvent):
    """Event fired when the system is starting up."""
    def __init__(self, startup_time: datetime = None):
        super().__init__()
        self.startup_time = startup_time or datetime.now()


class ShutdownEvent(SystemEvent):
    """Event fired when the system is shutting down."""
    def __init__(self, reason: str = None):
        super().__init__()
        self.reason = reason


class ErrorEvent(SystemEvent):
    """Event fired when a system error occurs."""
    def __init__(self, error: Exception, source: str = None):
        super().__init__()
        self.error = error
        self.source = source
        self.error_type = type(error).__name__
        self.error_message = str(error)


class ConfigChangeEvent(SystemEvent):
    """Event fired when configuration changes."""
    def __init__(self, key: str, old_value: Any, new_value: Any):
        super().__init__()
        self.key = key
        self.old_value = old_value
        self.new_value = new_value


# Export public API
__all__ = [
    'Event',
    'EventBus',
    'EventSubscriber',
    'EventPriority',
    'EventHandler',
    'SystemEvent',
    'StartupEvent',
    'ShutdownEvent',
    'ErrorEvent',
    'ConfigChangeEvent',
]