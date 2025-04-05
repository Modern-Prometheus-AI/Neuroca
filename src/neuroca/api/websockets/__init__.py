"""
Websocket API Module for NeuroCognitive Architecture (NCA)

This module provides the websocket interface for real-time communication with the NCA system.
It handles connection management, authentication, message routing, and event broadcasting.

The websocket API enables:
- Real-time monitoring of NCA cognitive processes
- Streaming of memory state changes
- Interactive debugging and introspection
- Event-driven notifications
- Bidirectional communication for dynamic system interaction

Usage:
    from neuroca.api.websockets import setup_websockets
    
    # In your FastAPI application
    app = FastAPI()
    setup_websockets(app)
"""

import asyncio
import contextlib
import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

import jwt
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, ValidationError

from neuroca.config import settings
from neuroca.core.auth import verify_token
from neuroca.core.models import User
from neuroca.core.utils import get_logger

# Configure module logger
logger = get_logger(__name__)

# Connection registry to track active websocket connections
active_connections: dict[str, dict[str, Any]] = {}

# Event subscription registry
event_subscribers: dict[str, set[str]] = {}


class MessageType(str, Enum):
    """Enumeration of websocket message types."""
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    EVENT = "event"
    COMMAND = "command"
    QUERY = "query"
    RESPONSE = "response"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


class WebSocketMessage(BaseModel):
    """Base model for websocket messages."""
    type: MessageType
    id: str = ""  # Message ID for correlation
    timestamp: datetime = datetime.utcnow()
    payload: dict[str, Any] = {}


class ConnectionManager:
    """
    Manages websocket connections, including authentication, message routing,
    and broadcasting capabilities.
    """
    
    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: dict[str, dict[str, Any]] = {}
        self.message_handlers: dict[MessageType, Callable] = {
            MessageType.CONNECT: self._handle_connect,
            MessageType.DISCONNECT: self._handle_disconnect,
            MessageType.SUBSCRIBE: self._handle_subscribe,
            MessageType.UNSUBSCRIBE: self._handle_unsubscribe,
            MessageType.COMMAND: self._handle_command,
            MessageType.QUERY: self._handle_query,
            MessageType.HEARTBEAT: self._handle_heartbeat,
        }
        self._heartbeat_task = None
        
    async def connect(self, websocket: WebSocket, user: User) -> str:
        """
        Accept a websocket connection and register it.
        
        Args:
            websocket: The websocket connection
            user: The authenticated user
            
        Returns:
            str: The connection ID
        """
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        
        self.active_connections[connection_id] = {
            "websocket": websocket,
            "user": user,
            "connected_at": datetime.utcnow(),
            "subscriptions": set(),
            "last_activity": datetime.utcnow()
        }
        
        logger.info(f"New websocket connection established: {connection_id} (User: {user.username})")
        
        # Send welcome message
        await self.send_message(
            connection_id,
            WebSocketMessage(
                type=MessageType.CONNECT,
                id=connection_id,
                payload={"message": "Connected to NCA Websocket API"}
            )
        )
        
        return connection_id
    
    async def disconnect(self, connection_id: str) -> None:
        """
        Disconnect and unregister a websocket connection.
        
        Args:
            connection_id: The connection ID to disconnect
        """
        if connection_id not in self.active_connections:
            logger.warning(f"Attempted to disconnect unknown connection: {connection_id}")
            return
            
        connection = self.active_connections[connection_id]
        user = connection["user"]
        
        # Remove all subscriptions
        for event_type in list(event_subscribers.keys()):
            if connection_id in event_subscribers.get(event_type, set()):
                event_subscribers[event_type].remove(connection_id)
                if not event_subscribers[event_type]:
                    del event_subscribers[event_type]
        
        # Remove from active connections
        del self.active_connections[connection_id]
        logger.info(f"Websocket connection closed: {connection_id} (User: {user.username})")
    
    async def send_message(self, connection_id: str, message: WebSocketMessage) -> None:
        """
        Send a message to a specific connection.
        
        Args:
            connection_id: The connection ID to send to
            message: The message to send
        """
        if connection_id not in self.active_connections:
            logger.warning(f"Attempted to send message to unknown connection: {connection_id}")
            return
            
        try:
            websocket = self.active_connections[connection_id]["websocket"]
            await websocket.send_json(message.dict())
            self.active_connections[connection_id]["last_activity"] = datetime.utcnow()
            logger.debug(f"Message sent to {connection_id}: {message.type}")
        except Exception as e:
            logger.error(f"Error sending message to {connection_id}: {str(e)}")
            # Connection might be broken, disconnect it
            await self.disconnect(connection_id)
    
    async def broadcast(self, event_type: str, payload: dict[str, Any]) -> None:
        """
        Broadcast a message to all subscribers of an event type.
        
        Args:
            event_type: The event type to broadcast
            payload: The message payload
        """
        if event_type not in event_subscribers or not event_subscribers[event_type]:
            logger.debug(f"No subscribers for event type: {event_type}")
            return
            
        message = WebSocketMessage(
            type=MessageType.EVENT,
            id=str(uuid.uuid4()),
            payload={"event_type": event_type, "data": payload}
        )
        
        # Get subscribers for this event type
        subscribers = event_subscribers.get(event_type, set())
        logger.debug(f"Broadcasting {event_type} to {len(subscribers)} subscribers")
        
        # Send to each subscriber
        for connection_id in list(subscribers):
            if connection_id in self.active_connections:
                await self.send_message(connection_id, message)
            else:
                # Clean up stale subscription
                if connection_id in subscribers:
                    subscribers.remove(connection_id)
    
    async def process_message(self, connection_id: str, data: str) -> None:
        """
        Process an incoming websocket message.
        
        Args:
            connection_id: The connection ID that sent the message
            data: The raw message data
        """
        if connection_id not in self.active_connections:
            logger.warning(f"Message received from unknown connection: {connection_id}")
            return
            
        # Update last activity timestamp
        self.active_connections[connection_id]["last_activity"] = datetime.utcnow()
        
        try:
            # Parse and validate the message
            message_data = json.loads(data)
            message = WebSocketMessage(**message_data)
            
            # Route to appropriate handler
            if message.type in self.message_handlers:
                await self.message_handlers[message.type](connection_id, message)
            else:
                logger.warning(f"Unsupported message type: {message.type}")
                await self._send_error(
                    connection_id, 
                    message.id, 
                    f"Unsupported message type: {message.type}"
                )
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received from {connection_id}")
            await self._send_error(connection_id, "", "Invalid JSON format")
        except ValidationError as e:
            logger.error(f"Message validation error from {connection_id}: {str(e)}")
            await self._send_error(connection_id, "", f"Message validation error: {str(e)}")
        except Exception as e:
            logger.exception(f"Error processing message from {connection_id}: {str(e)}")
            await self._send_error(connection_id, "", f"Internal server error: {str(e)}")
    
    async def _handle_connect(self, connection_id: str, message: WebSocketMessage) -> None:
        """Handle connect message type."""
        # Connection is already established at this point
        logger.debug(f"Received connect message from {connection_id}")
    
    async def _handle_disconnect(self, connection_id: str, message: WebSocketMessage) -> None:
        """Handle disconnect message type."""
        logger.debug(f"Received disconnect request from {connection_id}")
        await self.disconnect(connection_id)
    
    async def _handle_subscribe(self, connection_id: str, message: WebSocketMessage) -> None:
        """Handle subscription requests."""
        if "event_types" not in message.payload:
            await self._send_error(connection_id, message.id, "Missing event_types in subscription request")
            return
            
        event_types = message.payload["event_types"]
        if not isinstance(event_types, list):
            event_types = [event_types]
            
        # Add subscriptions
        for event_type in event_types:
            if event_type not in event_subscribers:
                event_subscribers[event_type] = set()
            event_subscribers[event_type].add(connection_id)
            self.active_connections[connection_id]["subscriptions"].add(event_type)
            
        logger.info(f"Connection {connection_id} subscribed to: {', '.join(event_types)}")
        
        # Send confirmation
        await self.send_message(
            connection_id,
            WebSocketMessage(
                type=MessageType.RESPONSE,
                id=message.id,
                payload={"status": "subscribed", "event_types": event_types}
            )
        )
    
    async def _handle_unsubscribe(self, connection_id: str, message: WebSocketMessage) -> None:
        """Handle unsubscribe requests."""
        if "event_types" not in message.payload:
            await self._send_error(connection_id, message.id, "Missing event_types in unsubscribe request")
            return
            
        event_types = message.payload["event_types"]
        if not isinstance(event_types, list):
            event_types = [event_types]
            
        # Remove subscriptions
        for event_type in event_types:
            if event_type in event_subscribers and connection_id in event_subscribers[event_type]:
                event_subscribers[event_type].remove(connection_id)
                if not event_subscribers[event_type]:
                    del event_subscribers[event_type]
                    
            if connection_id in self.active_connections:
                if event_type in self.active_connections[connection_id]["subscriptions"]:
                    self.active_connections[connection_id]["subscriptions"].remove(event_type)
                    
        logger.info(f"Connection {connection_id} unsubscribed from: {', '.join(event_types)}")
        
        # Send confirmation
        await self.send_message(
            connection_id,
            WebSocketMessage(
                type=MessageType.RESPONSE,
                id=message.id,
                payload={"status": "unsubscribed", "event_types": event_types}
            )
        )
    
    async def _handle_command(self, connection_id: str, message: WebSocketMessage) -> None:
        """Handle command messages."""
        if "command" not in message.payload:
            await self._send_error(connection_id, message.id, "Missing command in request")
            return
            
        command = message.payload["command"]
        message.payload.get("args", {})
        
        logger.info(f"Command received from {connection_id}: {command}")
        
        # NOTE: Implement command routing to appropriate handlers.
        # This should connect to the core NCA command processing system
        # (e.g., CognitiveController or a dedicated command dispatcher).
        
        # For now, send a placeholder response
        await self.send_message(
            connection_id,
            WebSocketMessage(
                type=MessageType.RESPONSE,
                id=message.id,
                payload={
                    "status": "acknowledged",
                    "message": f"Command '{command}' received but not yet implemented"
                }
            )
        )
    
    async def _handle_query(self, connection_id: str, message: WebSocketMessage) -> None:
        """Handle query messages."""
        if "query" not in message.payload:
            await self._send_error(connection_id, message.id, "Missing query in request")
            return
            
        query = message.payload["query"]
        message.payload.get("params", {})
        
        logger.info(f"Query received from {connection_id}: {query}")
        
        # NOTE: Implement query routing to appropriate handlers.
        # This should connect to the core NCA query processing system
        # (e.g., MemoryManager, HealthManager, or a dedicated query dispatcher).
        
        # For now, send a placeholder response
        await self.send_message(
            connection_id,
            WebSocketMessage(
                type=MessageType.RESPONSE,
                id=message.id,
                payload={
                    "status": "acknowledged",
                    "message": f"Query '{query}' received but not yet implemented"
                }
            )
        )
    
    async def _handle_heartbeat(self, connection_id: str, message: WebSocketMessage) -> None:
        """Handle heartbeat messages."""
        # Simply respond with a heartbeat response
        await self.send_message(
            connection_id,
            WebSocketMessage(
                type=MessageType.HEARTBEAT,
                id=message.id,
                payload={"server_time": datetime.utcnow().isoformat()}
            )
        )
    
    async def _send_error(self, connection_id: str, message_id: str, error_message: str) -> None:
        """
        Send an error message to a connection.
        
        Args:
            connection_id: The connection ID to send to
            message_id: The original message ID if available
            error_message: The error message
        """
        await self.send_message(
            connection_id,
            WebSocketMessage(
                type=MessageType.ERROR,
                id=message_id,
                payload={"error": error_message}
            )
        )
    
    async def start_heartbeat_monitor(self) -> None:
        """Start the heartbeat monitoring task."""
        if self._heartbeat_task is not None:
            return
            
        self._heartbeat_task = asyncio.create_task(self._heartbeat_monitor())
        logger.info("Websocket heartbeat monitor started")
    
    async def stop_heartbeat_monitor(self) -> None:
        """Stop the heartbeat monitoring task."""
        if self._heartbeat_task is None:
            return
            
        self._heartbeat_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._heartbeat_task

        self._heartbeat_task = None
        logger.info("Websocket heartbeat monitor stopped")
    
    async def _heartbeat_monitor(self) -> None:
        """
        Monitor connections for activity and disconnect inactive ones.
        Also sends periodic heartbeats to keep connections alive.
        """
        heartbeat_interval = settings.WEBSOCKET_HEARTBEAT_INTERVAL
        timeout_threshold = settings.WEBSOCKET_TIMEOUT_THRESHOLD
        
        while True:
            try:
                now = datetime.utcnow()
                
                # Check for inactive connections
                for connection_id in list(self.active_connections.keys()):
                    if connection_id not in self.active_connections:
                        continue
                        
                    last_activity = self.active_connections[connection_id]["last_activity"]
                    inactive_time = (now - last_activity).total_seconds()
                    
                    if inactive_time > timeout_threshold:
                        logger.info(f"Connection {connection_id} timed out after {inactive_time}s of inactivity")
                        await self.disconnect(connection_id)
                    elif inactive_time > heartbeat_interval:
                        # Send heartbeat to keep connection alive
                        try:
                            await self.send_message(
                                connection_id,
                                WebSocketMessage(
                                    type=MessageType.HEARTBEAT,
                                    payload={"server_time": now.isoformat()}
                                )
                            )
                        except Exception as e:
                            logger.error(f"Error sending heartbeat to {connection_id}: {str(e)}")
                            await self.disconnect(connection_id)
                
                # Sleep until next check
                await asyncio.sleep(min(heartbeat_interval, 30))  # Check at least every 30 seconds
                
            except asyncio.CancelledError:
                logger.info("Heartbeat monitor task cancelled")
                break
            except Exception as e:
                logger.exception(f"Error in heartbeat monitor: {str(e)}")
                await asyncio.sleep(5)  # Short delay before retrying


# Create a global connection manager instance
connection_manager = ConnectionManager()


async def get_token_from_websocket(websocket: WebSocket) -> Optional[str]:
    """
    Extract authentication token from websocket connection.
    
    Args:
        websocket: The websocket connection
        
    Returns:
        Optional[str]: The authentication token if found
    """
    # Try to get token from query parameters
    token = websocket.query_params.get("token")
    
    # If not in query params, try cookies
    if not token:
        cookies = websocket.cookies
        token = cookies.get("access_token")
    
    # If not in cookies, try headers
    if not token:
        headers = websocket.headers
        auth_header = headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
    
    return token


async def authenticate_websocket(websocket: WebSocket) -> Optional[User]:
    """
    Authenticate a websocket connection.
    
    Args:
        websocket: The websocket connection
        
    Returns:
        Optional[User]: The authenticated user if successful
    """
    token = await get_token_from_websocket(websocket)
    
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing authentication token")
        return None
    
    try:
        user = await verify_token(token)
        return user
    except jwt.PyJWTError as e:
        logger.warning(f"Invalid authentication token: {str(e)}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid authentication token")
        return None
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Authentication error")
        return None


async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    Main websocket endpoint handler.
    
    Args:
        websocket: The websocket connection
    """
    # Authenticate the connection
    user = await authenticate_websocket(websocket)
    if not user:
        return  # Connection was closed during authentication
    
    # Accept and register the connection
    connection_id = await connection_manager.connect(websocket, user)
    
    try:
        # Process messages until disconnection
        while True:
            data = await websocket.receive_text()
            await connection_manager.process_message(connection_id, data)
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.exception(f"Error in websocket connection {connection_id}: {str(e)}")
    finally:
        # Clean up the connection
        await connection_manager.disconnect(connection_id)


def setup_websockets(app: FastAPI) -> None:
    """
    Set up websocket routes and start the heartbeat monitor.
    
    Args:
        app: The FastAPI application instance
    """
    # Register the websocket endpoint
    app.websocket("/ws")(websocket_endpoint)
    
    # Start the heartbeat monitor on application startup
    @app.on_event("startup")
    async def startup_websocket_heartbeat():
        await connection_manager.start_heartbeat_monitor()
    
    # Stop the heartbeat monitor on application shutdown
    @app.on_event("shutdown")
    async def shutdown_websocket_heartbeat():
        await connection_manager.stop_heartbeat_monitor()
    
    logger.info("Websocket API initialized")


async def broadcast_event(event_type: str, payload: dict[str, Any]) -> None:
    """
    Broadcast an event to all subscribed websocket connections.
    
    This function can be called from other parts of the application to send
    real-time updates to connected clients.
    
    Args:
        event_type: The type of event to broadcast
        payload: The event payload data
    """
    await connection_manager.broadcast(event_type, payload)


__all__ = [
    "setup_websockets",
    "broadcast_event",
    "WebSocketMessage",
    "MessageType",
    "ConnectionManager",
]
