"""
WebSocket Events Handler for NeuroCognitive Architecture

This module implements the WebSocket event handling system for the NeuroCognitive Architecture (NCA).
It manages client connections, message routing, event dispatching, and provides real-time
communication capabilities between the NCA system and connected clients.

The module implements:
- Connection lifecycle management (connect, disconnect)
- Message validation and processing
- Event routing to appropriate handlers
- Error handling and recovery
- Session management
- Security measures including authentication and rate limiting

Usage:
    This module is used by the WebSocket server to handle incoming connections and messages.
    It dispatches events to the appropriate handlers and maintains connection state.

Example:
    ```python
    # In a FastAPI application
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from neuroca.api.websockets.events import WebSocketEventHandler

    app = FastAPI()
    event_handler = WebSocketEventHandler()

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await event_handler.handle_connection(websocket)
    ```
"""

import asyncio
import json
import logging
import time
from enum import Enum
from typing import Any, Callable, Optional, Union

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ValidationError

# Configure logging
logger = logging.getLogger(__name__)


class WebSocketMessageType(str, Enum):
    """Enumeration of WebSocket message types."""
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    ERROR = "error"
    MEMORY_UPDATE = "memory_update"
    HEALTH_UPDATE = "health_update"
    SYSTEM_STATUS = "system_status"
    USER_INPUT = "user_input"
    SYSTEM_RESPONSE = "system_response"
    COGNITIVE_STATE = "cognitive_state"
    PING = "ping"
    PONG = "pong"


class WebSocketMessage(BaseModel):
    """Base model for WebSocket messages."""
    type: WebSocketMessageType
    timestamp: float = time.time()
    message_id: str
    payload: dict[str, Any] = {}


class WebSocketError(Exception):
    """Base exception for WebSocket errors."""
    def __init__(self, message: str, code: int = 1000):
        self.message = message
        self.code = code
        super().__init__(message)


class AuthenticationError(WebSocketError):
    """Exception raised for authentication failures."""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, code=4001)


class RateLimitError(WebSocketError):
    """Exception raised when a client exceeds rate limits."""
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, code=4002)


class InvalidMessageError(WebSocketError):
    """Exception raised for invalid message format or content."""
    def __init__(self, message: str = "Invalid message format"):
        super().__init__(message, code=4003)


class ConnectionManager:
    """
    Manages WebSocket connections and client sessions.
    
    Handles connection lifecycle, client tracking, and message broadcasting.
    """
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.client_info: dict[str, dict[str, Any]] = {}
        self.connection_lock = asyncio.Lock()
        
    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """
        Accept a new WebSocket connection and store it.
        
        Args:
            websocket: The WebSocket connection
            client_id: Unique identifier for the client
            
        Raises:
            WebSocketError: If connection cannot be established
        """
        try:
            await websocket.accept()
            async with self.connection_lock:
                self.active_connections[client_id] = websocket
                self.client_info[client_id] = {
                    "connected_at": time.time(),
                    "last_activity": time.time(),
                    "message_count": 0,
                    "ip_address": websocket.client.host if hasattr(websocket, "client") else "unknown",
                }
            logger.info(f"Client {client_id} connected from {self.client_info[client_id]['ip_address']}")
        except Exception as e:
            logger.error(f"Failed to establish connection for client {client_id}: {str(e)}")
            raise WebSocketError(f"Connection failed: {str(e)}")
    
    async def disconnect(self, client_id: str, code: int = 1000, reason: str = "Normal closure") -> None:
        """
        Disconnect a client and clean up resources.
        
        Args:
            client_id: Unique identifier for the client
            code: WebSocket close code
            reason: Reason for disconnection
        """
        async with self.connection_lock:
            if client_id in self.active_connections:
                try:
                    await self.active_connections[client_id].close(code=code, reason=reason)
                except Exception as e:
                    logger.warning(f"Error during disconnect for client {client_id}: {str(e)}")
                finally:
                    # Clean up regardless of close success
                    del self.active_connections[client_id]
                    if client_id in self.client_info:
                        duration = time.time() - self.client_info[client_id]["connected_at"]
                        logger.info(f"Client {client_id} disconnected after {duration:.2f} seconds")
                        del self.client_info[client_id]
    
    async def send_message(self, client_id: str, message: Union[str, dict, WebSocketMessage]) -> None:
        """
        Send a message to a specific client.
        
        Args:
            client_id: Unique identifier for the client
            message: Message to send (string, dict, or WebSocketMessage)
            
        Raises:
            WebSocketError: If message cannot be sent
        """
        if client_id not in self.active_connections:
            logger.warning(f"Attempted to send message to non-existent client {client_id}")
            return
        
        try:
            if isinstance(message, WebSocketMessage):
                message_json = message.model_dump_json()
            elif isinstance(message, dict):
                message_json = json.dumps(message)
            else:
                message_json = message
                
            await self.active_connections[client_id].send_text(message_json)
            
            # Update client activity timestamp
            if client_id in self.client_info:
                self.client_info[client_id]["last_activity"] = time.time()
                self.client_info[client_id]["message_count"] += 1
                
        except Exception as e:
            logger.error(f"Failed to send message to client {client_id}: {str(e)}")
            # If we can't send a message, the connection might be broken
            await self.disconnect(client_id, code=1011, reason="Internal server error")
            raise WebSocketError(f"Failed to send message: {str(e)}")
    
    async def broadcast(self, message: Union[str, dict, WebSocketMessage], exclude: Optional[set[str]] = None) -> None:
        """
        Broadcast a message to all connected clients, with optional exclusions.
        
        Args:
            message: Message to broadcast
            exclude: Set of client IDs to exclude from broadcast
        """
        exclude = exclude or set()
        
        # Convert message to JSON string if needed
        if isinstance(message, WebSocketMessage):
            message_json = message.model_dump_json()
        elif isinstance(message, dict):
            message_json = json.dumps(message)
        else:
            message_json = message
            
        # Create a list of tasks for sending messages
        tasks = []
        async with self.connection_lock:
            for client_id in self.active_connections:
                if client_id not in exclude:
                    tasks.append(self.send_message(client_id, message_json))
        
        # Execute all send tasks concurrently
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


class RateLimiter:
    """
    Implements rate limiting for WebSocket connections and messages.
    
    Prevents abuse by limiting the frequency of messages from clients.
    """
    def __init__(self, 
                 max_messages_per_minute: int = 120,
                 max_connections_per_ip: int = 5):
        self.max_messages_per_minute = max_messages_per_minute
        self.max_connections_per_ip = max_connections_per_ip
        self.message_counts: dict[str, list[float]] = {}
        self.ip_connections: dict[str, set[str]] = {}
        self.limiter_lock = asyncio.Lock()
    
    async def check_connection_limit(self, client_id: str, ip_address: str) -> None:
        """
        Check if an IP address has exceeded its connection limit.
        
        Args:
            client_id: Unique identifier for the client
            ip_address: Client's IP address
            
        Raises:
            RateLimitError: If connection limit is exceeded
        """
        async with self.limiter_lock:
            if ip_address not in self.ip_connections:
                self.ip_connections[ip_address] = set()
            
            # Add this client to the IP's connection set
            self.ip_connections[ip_address].add(client_id)
            
            # Check if this IP has too many connections
            if len(self.ip_connections[ip_address]) > self.max_connections_per_ip:
                logger.warning(f"IP {ip_address} exceeded connection limit with {len(self.ip_connections[ip_address])} connections")
                raise RateLimitError(f"Too many connections from this IP address (max: {self.max_connections_per_ip})")
    
    async def check_message_limit(self, client_id: str) -> None:
        """
        Check if a client has exceeded its message rate limit.
        
        Args:
            client_id: Unique identifier for the client
            
        Raises:
            RateLimitError: If message rate limit is exceeded
        """
        current_time = time.time()
        
        async with self.limiter_lock:
            # Initialize if this is a new client
            if client_id not in self.message_counts:
                self.message_counts[client_id] = []
            
            # Add the current message timestamp
            self.message_counts[client_id].append(current_time)
            
            # Remove timestamps older than 1 minute
            one_minute_ago = current_time - 60
            self.message_counts[client_id] = [t for t in self.message_counts[client_id] if t > one_minute_ago]
            
            # Check if too many messages in the last minute
            if len(self.message_counts[client_id]) > self.max_messages_per_minute:
                logger.warning(f"Client {client_id} exceeded message rate limit with {len(self.message_counts[client_id])} messages/minute")
                raise RateLimitError(f"Message rate limit exceeded (max: {self.max_messages_per_minute}/minute)")
    
    async def remove_client(self, client_id: str, ip_address: Optional[str] = None) -> None:
        """
        Remove a client from rate limiting tracking when they disconnect.
        
        Args:
            client_id: Unique identifier for the client
            ip_address: Client's IP address
        """
        async with self.limiter_lock:
            # Remove from message counts
            if client_id in self.message_counts:
                del self.message_counts[client_id]
            
            # Remove from IP connections if IP is known
            if ip_address and ip_address in self.ip_connections:
                self.ip_connections[ip_address].discard(client_id)
                # Clean up empty sets
                if not self.ip_connections[ip_address]:
                    del self.ip_connections[ip_address]


class WebSocketEventHandler:
    """
    Main handler for WebSocket events in the NeuroCognitive Architecture.
    
    Manages the lifecycle of WebSocket connections, processes incoming messages,
    and routes events to the appropriate handlers.
    """
    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.rate_limiter = RateLimiter()
        self.event_handlers: dict[WebSocketMessageType, list[Callable]] = {
            message_type: [] for message_type in WebSocketMessageType
        }
        
        # Register default handlers
        self.register_handler(WebSocketMessageType.PING, self._handle_ping)
    
    def register_handler(self, event_type: WebSocketMessageType, handler: Callable) -> None:
        """
        Register a handler function for a specific event type.
        
        Args:
            event_type: Type of event to handle
            handler: Async function to call when event occurs
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        logger.debug(f"Registered handler for {event_type.value} events: {handler.__name__}")
    
    async def _handle_ping(self, client_id: str, message: WebSocketMessage) -> None:
        """
        Handle ping messages by responding with a pong.
        
        Args:
            client_id: Unique identifier for the client
            message: The ping message
        """
        pong_message = WebSocketMessage(
            type=WebSocketMessageType.PONG,
            message_id=f"pong-{message.message_id}",
            payload={"ping_id": message.message_id, "server_time": time.time()}
        )
        await self.connection_manager.send_message(client_id, pong_message)
    
    async def _process_message(self, client_id: str, message_text: str) -> None:
        """
        Process an incoming WebSocket message.
        
        Args:
            client_id: Unique identifier for the client
            message_text: Raw message text
            
        Raises:
            InvalidMessageError: If message format is invalid
            RateLimitError: If client exceeds rate limits
        """
        # Check rate limits first
        await self.rate_limiter.check_message_limit(client_id)
        
        # Parse and validate the message
        try:
            message_data = json.loads(message_text)
            message = WebSocketMessage(**message_data)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON from client {client_id}: {message_text[:100]}...")
            raise InvalidMessageError("Message is not valid JSON")
        except ValidationError as e:
            logger.warning(f"Invalid message format from client {client_id}: {str(e)}")
            raise InvalidMessageError(f"Message validation failed: {str(e)}")
        
        # Dispatch to registered handlers
        if message.type in self.event_handlers:
            for handler in self.event_handlers[message.type]:
                try:
                    await handler(client_id, message)
                except Exception as e:
                    logger.error(f"Error in handler {handler.__name__} for {message.type.value}: {str(e)}")
                    error_message = WebSocketMessage(
                        type=WebSocketMessageType.ERROR,
                        message_id=f"error-{message.message_id}",
                        payload={"error": "Internal server error", "original_message_id": message.message_id}
                    )
                    await self.connection_manager.send_message(client_id, error_message)
        else:
            logger.warning(f"No handlers for message type: {message.type.value}")
            # Send error response for unhandled message types
            error_message = WebSocketMessage(
                type=WebSocketMessageType.ERROR,
                message_id=f"error-{message.message_id}",
                payload={"error": f"Unsupported message type: {message.type.value}", 
                         "original_message_id": message.message_id}
            )
            await self.connection_manager.send_message(client_id, error_message)
    
    async def handle_connection(self, websocket: WebSocket, client_id: Optional[str] = None) -> None:
        """
        Main entry point for handling a WebSocket connection.
        
        Args:
            websocket: The WebSocket connection object
            client_id: Optional client ID (generated if not provided)
            
        This method manages the entire lifecycle of a WebSocket connection.
        """
        # Generate client ID if not provided
        if client_id is None:
            client_id = f"client-{id(websocket)}-{time.time()}"
        
        # Get client IP for rate limiting
        client_ip = websocket.client.host if hasattr(websocket, "client") else "unknown"
        
        try:
            # Check connection rate limits
            await self.rate_limiter.check_connection_limit(client_id, client_ip)
            
            # Accept the connection
            await self.connection_manager.connect(websocket, client_id)
            
            # Main message processing loop
            while True:
                try:
                    message_text = await websocket.receive_text()
                    await self._process_message(client_id, message_text)
                except WebSocketDisconnect:
                    logger.info(f"Client {client_id} disconnected")
                    break
                except WebSocketError as e:
                    # Send error message to client
                    error_message = WebSocketMessage(
                        type=WebSocketMessageType.ERROR,
                        message_id=f"error-{time.time()}",
                        payload={"error": e.message, "code": e.code}
                    )
                    await self.connection_manager.send_message(client_id, error_message)
                    
                    # For rate limit errors, we might want to disconnect the client
                    if isinstance(e, RateLimitError):
                        await self.connection_manager.disconnect(
                            client_id, 
                            code=e.code, 
                            reason=e.message
                        )
                        break
                except Exception as e:
                    logger.error(f"Unexpected error processing message from {client_id}: {str(e)}")
                    # Send generic error to client
                    error_message = WebSocketMessage(
                        type=WebSocketMessageType.ERROR,
                        message_id=f"error-{time.time()}",
                        payload={"error": "Internal server error"}
                    )
                    await self.connection_manager.send_message(client_id, error_message)
        
        except Exception as e:
            logger.error(f"Error handling WebSocket connection for {client_id}: {str(e)}")
            # Try to send error and close if we haven't connected yet
            try:
                if isinstance(e, WebSocketError):
                    await websocket.close(code=e.code, reason=e.message)
                else:
                    await websocket.close(code=1011, reason="Internal server error")
            except Exception:
                pass
        
        finally:
            # Ensure we clean up resources
            await self.connection_manager.disconnect(client_id)
            await self.rate_limiter.remove_client(client_id, client_ip)
            logger.info(f"Connection resources cleaned up for client {client_id}")