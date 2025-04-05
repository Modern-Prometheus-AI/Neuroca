"""
Event Handlers Module for NeuroCognitive Architecture (NCA).

This module provides a comprehensive event handling system for the NCA, enabling
components to subscribe to and process events throughout the system. It implements
the observer pattern to allow loose coupling between event producers and consumers.

The module includes:
- Base event handler classes
- Registration and management of event handlers
- Prioritization and execution of event handlers
- Error handling and recovery mechanisms
- Logging and monitoring capabilities

Usage:
    # Register a handler for a specific event type
    @register_handler(EventType.MEMORY_UPDATE)
    def handle_memory_update(event):
        # Process memory update event
        pass

    # Trigger an event
    event_bus.publish(MemoryUpdateEvent(memory_id="123", content="new data"))
"""

import abc
import enum
import functools
import inspect
import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional, Union

# Setup module logger
logger = logging.getLogger(__name__)

# Thread-local storage for event context tracking
_event_context = threading.local()


class EventPriority(enum.IntEnum):
    """Priority levels for event handlers."""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


@dataclass
class Event:
    """Base class for all events in the system.
    
    All events must inherit from this class to ensure consistent handling.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate event after initialization."""
        if not self.id:
            self.id = str(uuid.uuid4())
        if not isinstance(self.timestamp, datetime):
            self.timestamp = datetime.now()
        if not isinstance(self.metadata, dict):
            self.metadata = {}


class EventHandlerError(Exception):
    """Base exception for all event handler related errors."""
    pass


class EventHandlerRegistrationError(EventHandlerError):
    """Exception raised when there's an error registering an event handler."""
    pass


class EventHandlerExecutionError(EventHandlerError):
    """Exception raised when there's an error executing an event handler."""
    pass


class EventBusError(EventHandlerError):
    """Exception raised for errors in the event bus."""
    pass


class EventContext:
    """Context for event propagation and tracking.
    
    Provides context for event handling, including propagation control,
    execution tracking, and metadata for debugging and monitoring.
    """
    def __init__(self, event: Event, parent_context_id: Optional[str] = None):
        self.context_id = str(uuid.uuid4())
        self.event = event
        self.parent_context_id = parent_context_id
        self.start_time = time.time()
        self.propagation_stopped = False
        self.results = {}
        self.errors = []
        self.handler_execution_times = {}
        
    def stop_propagation(self):
        """Stop further propagation of this event to other handlers."""
        self.propagation_stopped = True
        
    def add_result(self, handler_id: str, result: Any):
        """Add a result from a handler execution."""
        self.results[handler_id] = result
        
    def add_error(self, handler_id: str, error: Exception):
        """Add an error that occurred during handler execution."""
        self.errors.append((handler_id, error))
        
    def record_execution_time(self, handler_id: str, execution_time: float):
        """Record the execution time of a handler."""
        self.handler_execution_times[handler_id] = execution_time
        
    @property
    def total_execution_time(self) -> float:
        """Get the total execution time so far."""
        return time.time() - self.start_time
    
    @property
    def has_errors(self) -> bool:
        """Check if any errors occurred during event handling."""
        return len(self.errors) > 0


class EventHandler(abc.ABC):
    """Abstract base class for all event handlers.
    
    Defines the interface that all event handlers must implement.
    """
    def __init__(self, event_types: Union[type[Event], list[type[Event]]], 
                 priority: EventPriority = EventPriority.NORMAL,
                 name: Optional[str] = None):
        """Initialize the event handler.
        
        Args:
            event_types: The event type(s) this handler processes
            priority: The execution priority of this handler
            name: Optional name for the handler (defaults to class name)
        """
        self.event_types = [event_types] if isinstance(event_types, type) else event_types
        self.priority = priority
        self.name = name or self.__class__.__name__
        self.id = f"{self.name}_{str(uuid.uuid4())[:8]}"
        self.enabled = True
        
    @abc.abstractmethod
    async def handle(self, event: Event, context: EventContext) -> Any:
        """Handle the event.
        
        Args:
            event: The event to handle
            context: The event context
            
        Returns:
            Any result from handling the event
            
        Raises:
            EventHandlerExecutionError: If there's an error handling the event
        """
        pass
    
    def can_handle(self, event: Event) -> bool:
        """Check if this handler can handle the given event.
        
        Args:
            event: The event to check
            
        Returns:
            True if this handler can handle the event, False otherwise
        """
        return any(isinstance(event, event_type) for event_type in self.event_types)
    
    def enable(self):
        """Enable this handler."""
        self.enabled = True
        
    def disable(self):
        """Disable this handler."""
        self.enabled = False


class FunctionEventHandler(EventHandler):
    """Event handler that wraps a function.
    
    Allows using functions as event handlers without creating a full class.
    """
    def __init__(self, func: Callable[[Event, EventContext], Any], 
                 event_types: Union[type[Event], list[type[Event]]],
                 priority: EventPriority = EventPriority.NORMAL,
                 name: Optional[str] = None):
        """Initialize the function event handler.
        
        Args:
            func: The function to call when handling events
            event_types: The event type(s) this handler processes
            priority: The execution priority of this handler
            name: Optional name for the handler (defaults to function name)
        """
        super().__init__(event_types, priority, name or func.__name__)
        self.func = func
        
    async def handle(self, event: Event, context: EventContext) -> Any:
        """Handle the event by calling the wrapped function.
        
        Args:
            event: The event to handle
            context: The event context
            
        Returns:
            The result of the wrapped function
            
        Raises:
            EventHandlerExecutionError: If there's an error in the function
        """
        try:
            # Check if the function is a coroutine
            if inspect.iscoroutinefunction(self.func):
                return await self.func(event, context)
            else:
                return self.func(event, context)
        except Exception as e:
            error_msg = f"Error executing function handler {self.name}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise EventHandlerExecutionError(error_msg) from e


class EventBus:
    """Central event bus for publishing and handling events.
    
    Manages event handlers and coordinates event distribution.
    """
    def __init__(self):
        """Initialize the event bus."""
        self._handlers: dict[type[Event], list[EventHandler]] = {}
        self._all_handlers: set[EventHandler] = set()
        self._lock = threading.RLock()
        
    def register_handler(self, handler: EventHandler) -> None:
        """Register an event handler with the bus.
        
        Args:
            handler: The handler to register
            
        Raises:
            EventHandlerRegistrationError: If there's an error registering the handler
        """
        if not isinstance(handler, EventHandler):
            raise EventHandlerRegistrationError(
                f"Handler must be an instance of EventHandler, got {type(handler)}"
            )
            
        with self._lock:
            # Add to the set of all handlers
            self._all_handlers.add(handler)
            
            # Register for each event type
            for event_type in handler.event_types:
                if not issubclass(event_type, Event):
                    raise EventHandlerRegistrationError(
                        f"Event type must be a subclass of Event, got {event_type}"
                    )
                
                if event_type not in self._handlers:
                    self._handlers[event_type] = []
                
                # Add handler and sort by priority
                self._handlers[event_type].append(handler)
                self._handlers[event_type].sort(key=lambda h: h.priority)
                
        logger.debug(f"Registered handler {handler.id} for event types: {[et.__name__ for et in handler.event_types]}")
    
    def unregister_handler(self, handler: EventHandler) -> None:
        """Unregister an event handler from the bus.
        
        Args:
            handler: The handler to unregister
        """
        with self._lock:
            # Remove from all handlers set
            if handler in self._all_handlers:
                self._all_handlers.remove(handler)
            
            # Remove from each event type
            for event_type in list(self._handlers.keys()):
                if handler in self._handlers[event_type]:
                    self._handlers[event_type].remove(handler)
                    
                    # Clean up empty lists
                    if not self._handlers[event_type]:
                        del self._handlers[event_type]
                        
        logger.debug(f"Unregistered handler {handler.id}")
    
    def get_handlers_for_event(self, event: Event) -> list[EventHandler]:
        """Get all handlers that can process the given event.
        
        Args:
            event: The event to find handlers for
            
        Returns:
            List of handlers that can process the event, sorted by priority
        """
        with self._lock:
            handlers = []
            
            # Get handlers registered for this exact event type
            event_type = type(event)
            if event_type in self._handlers:
                handlers.extend(self._handlers[event_type])
            
            # Get handlers registered for parent event types
            for registered_type, type_handlers in self._handlers.items():
                if registered_type != event_type and issubclass(event_type, registered_type):
                    for handler in type_handlers:
                        if handler not in handlers:
                            handlers.append(handler)
            
            # Sort by priority
            return sorted(handlers, key=lambda h: h.priority)
    
    async def publish(self, event: Event) -> EventContext:
        """Publish an event to all registered handlers.
        
        Args:
            event: The event to publish
            
        Returns:
            The event context containing results and execution information
            
        Raises:
            EventBusError: If there's an error publishing the event
        """
        if not isinstance(event, Event):
            raise EventBusError(f"Can only publish Event objects, got {type(event)}")
        
        # Create event context
        parent_context_id = getattr(_event_context, 'current_context_id', None)
        context = EventContext(event, parent_context_id)
        
        # Set current context for nested events
        _event_context.current_context_id = context.context_id
        
        try:
            logger.debug(f"Publishing event {event.id} of type {type(event).__name__}")
            
            # Get handlers for this event
            handlers = self.get_handlers_for_event(event)
            
            if not handlers:
                logger.debug(f"No handlers registered for event type {type(event).__name__}")
                return context
            
            # Execute handlers in priority order
            for handler in handlers:
                if not handler.enabled:
                    continue
                    
                if context.propagation_stopped:
                    logger.debug(f"Event propagation stopped before handler {handler.id}")
                    break
                
                try:
                    start_time = time.time()
                    result = await handler.handle(event, context)
                    execution_time = time.time() - start_time
                    
                    context.add_result(handler.id, result)
                    context.record_execution_time(handler.id, execution_time)
                    
                    logger.debug(
                        f"Handler {handler.id} processed event {event.id} in {execution_time:.4f}s"
                    )
                except Exception as e:
                    error_msg = f"Error in handler {handler.id} for event {event.id}: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    context.add_error(handler.id, e)
            
            return context
        except Exception as e:
            error_msg = f"Error publishing event {event.id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise EventBusError(error_msg) from e
        finally:
            # Restore parent context
            if parent_context_id:
                _event_context.current_context_id = parent_context_id
            else:
                delattr(_event_context, 'current_context_id')


# Global event bus instance
event_bus = EventBus()


def register_handler(event_types: Union[type[Event], list[type[Event]]], 
                     priority: EventPriority = EventPriority.NORMAL):
    """Decorator to register a function as an event handler.
    
    Args:
        event_types: The event type(s) this handler processes
        priority: The execution priority of this handler
        
    Returns:
        Decorator function
        
    Example:
        @register_handler(MemoryUpdateEvent)
        async def handle_memory_update(event, context):
            # Process memory update
            pass
    """
    def decorator(func):
        handler = FunctionEventHandler(func, event_types, priority)
        event_bus.register_handler(handler)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        # Store reference to handler for potential unregistration
        wrapper._event_handler = handler
        return wrapper
    
    return decorator


def unregister_handler(func):
    """Unregister a function handler that was registered with the decorator.
    
    Args:
        func: The decorated function to unregister
        
    Raises:
        EventHandlerError: If the function wasn't registered as a handler
    """
    if not hasattr(func, '_event_handler'):
        raise EventHandlerError(f"Function {func.__name__} is not registered as an event handler")
    
    event_bus.unregister_handler(func._event_handler)
    delattr(func, '_event_handler')


class EventMiddleware(abc.ABC):
    """Abstract base class for event middleware.
    
    Middleware can intercept events before they're processed by handlers.
    """
    @abc.abstractmethod
    async def process(self, event: Event, context: EventContext, next_middleware: Callable) -> EventContext:
        """Process the event and call the next middleware in the chain.
        
        Args:
            event: The event being processed
            context: The event context
            next_middleware: Function to call the next middleware
            
        Returns:
            The event context after processing
        """
        pass


class EventBusWithMiddleware(EventBus):
    """Event bus with middleware support.
    
    Extends the standard event bus with middleware capabilities.
    """
    def __init__(self):
        """Initialize the event bus with middleware support."""
        super().__init__()
        self._middleware: list[EventMiddleware] = []
        
    def add_middleware(self, middleware: EventMiddleware) -> None:
        """Add middleware to the event bus.
        
        Args:
            middleware: The middleware to add
        """
        if not isinstance(middleware, EventMiddleware):
            raise EventBusError(f"Middleware must be an instance of EventMiddleware, got {type(middleware)}")
        
        self._middleware.append(middleware)
        logger.debug(f"Added middleware: {middleware.__class__.__name__}")
        
    def remove_middleware(self, middleware: EventMiddleware) -> None:
        """Remove middleware from the event bus.
        
        Args:
            middleware: The middleware to remove
        """
        if middleware in self._middleware:
            self._middleware.remove(middleware)
            logger.debug(f"Removed middleware: {middleware.__class__.__name__}")
    
    async def publish(self, event: Event) -> EventContext:
        """Publish an event through middleware and to all registered handlers.
        
        Args:
            event: The event to publish
            
        Returns:
            The event context containing results and execution information
        """
        if not isinstance(event, Event):
            raise EventBusError(f"Can only publish Event objects, got {type(event)}")
        
        # Create event context
        parent_context_id = getattr(_event_context, 'current_context_id', None)
        context = EventContext(event, parent_context_id)
        
        # Set current context for nested events
        _event_context.current_context_id = context.context_id
        
        try:
            # If we have middleware, process through the chain
            if self._middleware:
                return await self._process_middleware(event, context, 0)
            
            # Otherwise, just process normally
            return await super().publish(event)
        finally:
            # Restore parent context
            if parent_context_id:
                _event_context.current_context_id = parent_context_id
            else:
                delattr(_event_context, 'current_context_id')
    
    async def _process_middleware(self, event: Event, context: EventContext, index: int) -> EventContext:
        """Process the event through middleware at the given index.
        
        Args:
            event: The event to process
            context: The event context
            index: The current middleware index
            
        Returns:
            The event context after processing
        """
        # If we've processed all middleware, publish the event
        if index >= len(self._middleware):
            return await super().publish(event)
        
        # Get the current middleware
        middleware = self._middleware[index]
        
        # Create a function to call the next middleware
        async def next_middleware():
            return await self._process_middleware(event, context, index + 1)
        
        # Process through this middleware
        return await middleware.process(event, context, next_middleware)


# Logging middleware example
class LoggingMiddleware(EventMiddleware):
    """Middleware that logs all events passing through the system."""
    
    async def process(self, event: Event, context: EventContext, next_middleware: Callable) -> EventContext:
        """Log the event and pass it to the next middleware.
        
        Args:
            event: The event being processed
            context: The event context
            next_middleware: Function to call the next middleware
            
        Returns:
            The event context after processing
        """
        logger.info(f"Event received: {type(event).__name__} (ID: {event.id})")
        
        try:
            # Process the event through the rest of the middleware chain
            result_context = await next_middleware()
            
            # Log the results
            if result_context.has_errors:
                logger.warning(
                    f"Event {event.id} processed with {len(result_context.errors)} errors in "
                    f"{result_context.total_execution_time:.4f}s"
                )
            else:
                logger.info(
                    f"Event {event.id} processed successfully in {result_context.total_execution_time:.4f}s"
                )
                
            return result_context
        except Exception as e:
            logger.error(f"Error processing event {event.id}: {str(e)}", exc_info=True)
            raise


# Create a global event bus with middleware support
event_bus_with_middleware = EventBusWithMiddleware()
event_bus_with_middleware.add_middleware(LoggingMiddleware())