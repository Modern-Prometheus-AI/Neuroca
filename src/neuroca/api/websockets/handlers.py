"""
WebSocket Handlers for NeuroCognitive Architecture (NCA)

This module implements the WebSocket handlers for real-time communication between
clients and the NCA system. It provides functionality for:
- Connection management (authentication, establishment, maintenance)
- Message processing and routing
- Integration with memory systems and cognitive processes
- Health monitoring and diagnostics
- Session management and persistence

The handlers follow the ASGI specification and are designed to work with FastAPI's
WebSocket implementation, providing robust error handling, logging, and security.
"""

import asyncio
import json
import logging
import time
import uuid
from enum import Enum
from typing import Any, Callable

from fastapi import Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field, ValidationError

from neuroca.config import settings
from neuroca.core.auth import User, get_current_user
from neuroca.core.cognitive import cognitive_processor
from neuroca.core.exceptions import (
    AuthenticationError,
    ProcessingError,
    ResourceNotFoundError,
)
from neuroca.memory import memory_manager
from neuroca.monitoring.metrics import increment_counter, record_latency

# Configure logger
logger = logging.getLogger(__name__)

# Define message types for WebSocket communication
class MessageType(str, Enum):
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    QUERY = "query"
    RESPONSE = "response"
    MEMORY_UPDATE = "memory_update"
    COGNITIVE_EVENT = "cognitive_event"
    HEALTH_CHECK = "health_check"
    ERROR = "error"
    SYSTEM = "system"


class WebSocketMessage(BaseModel):
    """Base model for WebSocket messages"""
    type: MessageType
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = Field(default_factory=time.time)
    payload: dict[str, Any] = {}


class ConnectionManager:
    """
    Manages WebSocket connections to the NCA system.
    
    Responsibilities:
    - Track active connections
    - Broadcast messages to connected clients
    - Handle connection lifecycle events
    - Implement connection pools and groups
    """
    
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.user_connections: dict[str, set[str]] = {}  # user_id -> set of connection_ids
        self.connection_user_map: dict[str, str] = {}  # connection_id -> user_id
        self.connection_locks: dict[str, asyncio.Lock] = {}  # Prevent race conditions
        
    async def connect(self, websocket: WebSocket, user: User) -> str:
        """
        Accept a new WebSocket connection and register it.
        
        Args:
            websocket: The WebSocket connection to register
            user: The authenticated user for this connection
            
        Returns:
            connection_id: Unique identifier for this connection
            
        Raises:
            AuthenticationError: If user authentication fails
        """
        try:
            await websocket.accept()
            connection_id = str(uuid.uuid4())
            
            self.active_connections[connection_id] = websocket
            self.connection_locks[connection_id] = asyncio.Lock()
            
            # Associate connection with user
            if user.id not in self.user_connections:
                self.user_connections[user.id] = set()
            self.user_connections[user.id].add(connection_id)
            self.connection_user_map[connection_id] = user.id
            
            # Log and metrics
            logger.info(f"WebSocket connection established: {connection_id} for user {user.id}")
            increment_counter("websocket_connections_total")
            
            # Send welcome message
            await self.send_personal_message(
                WebSocketMessage(
                    type=MessageType.CONNECT,
                    payload={"message": "Connected to NCA WebSocket", "connection_id": connection_id}
                ),
                connection_id
            )
            
            return connection_id
            
        except Exception as e:
            logger.error(f"Error establishing WebSocket connection: {str(e)}")
            raise AuthenticationError("Failed to establish WebSocket connection") from e
    
    async def disconnect(self, connection_id: str) -> None:
        """
        Remove a WebSocket connection from the manager.
        
        Args:
            connection_id: The ID of the connection to remove
        """
        if connection_id in self.active_connections:
            # Clean up user association
            if connection_id in self.connection_user_map:
                user_id = self.connection_user_map[connection_id]
                if user_id in self.user_connections:
                    self.user_connections[user_id].discard(connection_id)
                    if not self.user_connections[user_id]:
                        del self.user_connections[user_id]
                del self.connection_user_map[connection_id]
            
            # Remove connection and lock
            del self.active_connections[connection_id]
            if connection_id in self.connection_locks:
                del self.connection_locks[connection_id]
            
            logger.info(f"WebSocket connection closed: {connection_id}")
            increment_counter("websocket_disconnections_total")
    
    async def send_personal_message(self, message: WebSocketMessage, connection_id: str) -> None:
        """
        Send a message to a specific connection.
        
        Args:
            message: The message to send
            connection_id: The connection to send the message to
            
        Raises:
            ResourceNotFoundError: If the connection is not found
        """
        if connection_id not in self.active_connections:
            logger.warning(f"Attempted to send message to non-existent connection: {connection_id}")
            raise ResourceNotFoundError(f"Connection {connection_id} not found")
        
        websocket = self.active_connections[connection_id]
        lock = self.connection_locks.get(connection_id)
        
        if lock:
            async with lock:
                await websocket.send_text(message.json())
        else:
            await websocket.send_text(message.json())
            
        logger.debug(f"Message sent to connection {connection_id}: {message.type}")
    
    async def broadcast(self, message: WebSocketMessage) -> None:
        """
        Broadcast a message to all active connections.
        
        Args:
            message: The message to broadcast
        """
        disconnected = []
        
        for connection_id, websocket in self.active_connections.items():
            try:
                lock = self.connection_locks.get(connection_id)
                if lock:
                    async with lock:
                        await websocket.send_text(message.json())
                else:
                    await websocket.send_text(message.json())
            except Exception as e:
                logger.error(f"Error sending broadcast to {connection_id}: {str(e)}")
                disconnected.append(connection_id)
        
        # Clean up any disconnected clients
        for connection_id in disconnected:
            await self.disconnect(connection_id)
            
        logger.debug(f"Broadcast message sent to {len(self.active_connections)} connections: {message.type}")
    
    async def broadcast_to_user(self, user_id: str, message: WebSocketMessage) -> None:
        """
        Send a message to all connections for a specific user.
        
        Args:
            user_id: The user to send the message to
            message: The message to send
            
        Raises:
            ResourceNotFoundError: If the user has no active connections
        """
        if user_id not in self.user_connections or not self.user_connections[user_id]:
            logger.warning(f"Attempted to send message to user with no connections: {user_id}")
            raise ResourceNotFoundError(f"No active connections for user {user_id}")
        
        disconnected = []
        
        for connection_id in self.user_connections[user_id]:
            try:
                await self.send_personal_message(message, connection_id)
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}, connection {connection_id}: {str(e)}")
                disconnected.append(connection_id)
        
        # Clean up any disconnected clients
        for connection_id in disconnected:
            await self.disconnect(connection_id)
            
        logger.debug(f"Message sent to all connections for user {user_id}: {message.type}")


# Create a singleton connection manager
connection_manager = ConnectionManager()


class WebSocketHandler:
    """
    Handles WebSocket connections and message processing for the NCA system.
    
    This class provides the core functionality for processing incoming WebSocket
    messages, routing them to the appropriate handlers, and managing the connection
    lifecycle.
    """
    
    def __init__(self):
        self.connection_manager = connection_manager
        self.message_handlers: dict[MessageType, Callable] = {
            MessageType.QUERY: self.handle_query,
            MessageType.MEMORY_UPDATE: self.handle_memory_update,
            MessageType.COGNITIVE_EVENT: self.handle_cognitive_event,
            MessageType.HEALTH_CHECK: self.handle_health_check,
        }
    
    async def handle_connection(self, websocket: WebSocket, user: User) -> None:
        """
        Main handler for WebSocket connections.
        
        Args:
            websocket: The WebSocket connection
            user: The authenticated user
        """
        connection_id = await self.connection_manager.connect(websocket, user)
        
        try:
            while True:
                # Wait for messages from the client
                data = await websocket.receive_text()
                start_time = time.time()
                
                try:
                    # Parse and validate the incoming message
                    message_data = json.loads(data)
                    message = WebSocketMessage(**message_data)
                    
                    # Process the message
                    await self.process_message(message, connection_id, user)
                    
                    # Record processing latency
                    processing_time = time.time() - start_time
                    record_latency("websocket_message_processing_time", processing_time)
                    
                except ValidationError as e:
                    logger.warning(f"Invalid message format from connection {connection_id}: {str(e)}")
                    await self.send_error(connection_id, "Invalid message format", details=str(e))
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON from connection {connection_id}: {str(e)}")
                    await self.send_error(connection_id, "Invalid JSON format", details=str(e))
                    
                except Exception as e:
                    logger.error(f"Error processing message from {connection_id}: {str(e)}", exc_info=True)
                    await self.send_error(connection_id, "Error processing message", details=str(e))
                    
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: {connection_id}")
            await self.connection_manager.disconnect(connection_id)
            
        except Exception as e:
            logger.error(f"Unexpected WebSocket error for {connection_id}: {str(e)}", exc_info=True)
            await self.connection_manager.disconnect(connection_id)
    
    async def process_message(self, message: WebSocketMessage, connection_id: str, user: User) -> None:
        """
        Process an incoming WebSocket message.
        
        Args:
            message: The message to process
            connection_id: The connection ID that sent the message
            user: The authenticated user
            
        Raises:
            ProcessingError: If message processing fails
        """
        logger.debug(f"Processing message type {message.type} from connection {connection_id}")
        
        # Get the appropriate handler for this message type
        handler = self.message_handlers.get(message.type)
        
        if handler:
            try:
                await handler(message, connection_id, user)
            except Exception as e:
                logger.error(f"Error in handler for {message.type}: {str(e)}", exc_info=True)
                raise ProcessingError(f"Failed to process {message.type} message") from e
        else:
            logger.warning(f"No handler for message type: {message.type}")
            await self.send_error(
                connection_id, 
                f"Unsupported message type: {message.type}",
                details="This message type is not supported by the server"
            )
    
    async def handle_query(self, message: WebSocketMessage, connection_id: str, user: User) -> None:
        """
        Handle a query message from a client.
        
        Args:
            message: The query message
            connection_id: The connection ID that sent the message
            user: The authenticated user
        """
        query_text = message.payload.get("query")
        if not query_text:
            await self.send_error(connection_id, "Missing query parameter")
            return
        
        logger.info(f"Processing query from user {user.id}: {query_text}")
        
        try:
            # Process the query through the cognitive processor
            start_time = time.time()
            result = await cognitive_processor.process_query(query_text, user.id)
            processing_time = time.time() - start_time
            
            # Send the response back to the client
            response = WebSocketMessage(
                type=MessageType.RESPONSE,
                payload={
                    "query_id": message.id,
                    "result": result,
                    "processing_time": processing_time
                }
            )
            await self.connection_manager.send_personal_message(response, connection_id)
            
            # Record metrics
            record_latency("query_processing_time", processing_time)
            increment_counter("queries_processed_total")
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}", exc_info=True)
            await self.send_error(
                connection_id,
                "Query processing failed",
                details=str(e),
                query_id=message.id
            )
    
    async def handle_memory_update(self, message: WebSocketMessage, connection_id: str, user: User) -> None:
        """
        Handle a memory update message from a client.
        
        Args:
            message: The memory update message
            connection_id: The connection ID that sent the message
            user: The authenticated user
        """
        memory_data = message.payload.get("memory_data")
        memory_tier = message.payload.get("memory_tier")
        
        if not memory_data or not memory_tier:
            await self.send_error(connection_id, "Missing memory_data or memory_tier parameter")
            return
        
        logger.info(f"Processing memory update for user {user.id} in tier {memory_tier}")
        
        try:
            # Update the memory system
            result = await memory_manager.update_memory(user.id, memory_tier, memory_data)
            
            # Send confirmation back to the client
            response = WebSocketMessage(
                type=MessageType.MEMORY_UPDATE,
                payload={
                    "update_id": message.id,
                    "status": "success",
                    "result": result
                }
            )
            await self.connection_manager.send_personal_message(response, connection_id)
            
            # Increment metrics
            increment_counter("memory_updates_total")
            
        except Exception as e:
            logger.error(f"Error updating memory: {str(e)}", exc_info=True)
            await self.send_error(
                connection_id,
                "Memory update failed",
                details=str(e),
                update_id=message.id
            )
    
    async def handle_cognitive_event(self, message: WebSocketMessage, connection_id: str, user: User) -> None:
        """
        Handle a cognitive event message from a client.
        
        Args:
            message: The cognitive event message
            connection_id: The connection ID that sent the message
            user: The authenticated user
        """
        event_type = message.payload.get("event_type")
        event_data = message.payload.get("event_data")
        
        if not event_type:
            await self.send_error(connection_id, "Missing event_type parameter")
            return
        
        logger.info(f"Processing cognitive event {event_type} for user {user.id}")
        
        try:
            # Process the cognitive event
            result = await cognitive_processor.process_event(event_type, event_data, user.id)
            
            # Send confirmation back to the client
            response = WebSocketMessage(
                type=MessageType.COGNITIVE_EVENT,
                payload={
                    "event_id": message.id,
                    "status": "success",
                    "result": result
                }
            )
            await self.connection_manager.send_personal_message(response, connection_id)
            
            # Increment metrics
            increment_counter("cognitive_events_total")
            
        except Exception as e:
            logger.error(f"Error processing cognitive event: {str(e)}", exc_info=True)
            await self.send_error(
                connection_id,
                "Cognitive event processing failed",
                details=str(e),
                event_id=message.id
            )
    
    async def handle_health_check(self, message: WebSocketMessage, connection_id: str, user: User) -> None:
        """
        Handle a health check message from a client.
        
        Args:
            message: The health check message
            connection_id: The connection ID that sent the message
            user: The authenticated user
        """
        logger.debug(f"Health check from connection {connection_id}")
        
        # Get system health information
        health_info = {
            "status": "healthy",
            "timestamp": time.time(),
            "version": settings.VERSION,
            "connection_id": connection_id,
            "user_id": user.id,
            "memory_system": await memory_manager.get_health_status(),
            "cognitive_system": await cognitive_processor.get_health_status(),
        }
        
        # Send health information back to the client
        response = WebSocketMessage(
            type=MessageType.HEALTH_CHECK,
            payload=health_info
        )
        await self.connection_manager.send_personal_message(response, connection_id)
        
        # Increment metrics
        increment_counter("health_checks_total")
    
    async def send_error(
        self, 
        connection_id: str, 
        message: str, 
        details: str = None, 
        **extra_fields
    ) -> None:
        """
        Send an error message to a client.
        
        Args:
            connection_id: The connection to send the error to
            message: The error message
            details: Detailed error information (optional)
            **extra_fields: Additional fields to include in the error payload
        """
        error_payload = {
            "message": message,
            "timestamp": time.time(),
            **extra_fields
        }
        
        if details and settings.DEBUG:
            # Only include detailed error information in debug mode
            error_payload["details"] = details
        
        error_message = WebSocketMessage(
            type=MessageType.ERROR,
            payload=error_payload
        )
        
        try:
            await self.connection_manager.send_personal_message(error_message, connection_id)
            increment_counter("websocket_errors_total")
        except Exception as e:
            logger.error(f"Failed to send error message to {connection_id}: {str(e)}")


# Create a singleton WebSocket handler
websocket_handler = WebSocketHandler()


async def get_websocket_handler() -> WebSocketHandler:
    """
    Dependency to get the WebSocket handler instance.
    
    Returns:
        The WebSocket handler singleton
    """
    return websocket_handler


async def handle_websocket(
    websocket: WebSocket,
    user: User = Depends(get_current_user),
    handler: WebSocketHandler = Depends(get_websocket_handler)
) -> None:
    """
    Main entry point for handling WebSocket connections.
    
    This function is designed to be used as a FastAPI WebSocket endpoint handler.
    
    Args:
        websocket: The WebSocket connection
        user: The authenticated user (from dependency)
        handler: The WebSocket handler (from dependency)
    """
    await handler.handle_connection(websocket, user)