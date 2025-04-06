"""
Health Check API Routes for NeuroCognitive Architecture (NCA)

This module provides health check endpoints for monitoring the NCA system's operational status.
It includes comprehensive health checks for all system components, memory tiers, and resource
utilization. The health endpoints follow standard practices for health check APIs, providing
both simple availability checks and detailed diagnostic information.

Usage:
    These routes are automatically registered with the FastAPI application and can be accessed
    at the /health endpoint. They provide both overall system health status and detailed
    component-level health information.

Security:
    Health endpoints may expose sensitive system information and should be properly secured
    in production environments. Consider implementing authentication for detailed health checks.
"""

import asyncio
import datetime as dt  # Use alias to avoid conflict
import logging
import os
import platform
import time
from datetime import datetime
from typing import Callable, Optional

import psutil
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from pydantic import BaseModel, Field

# Import memory dependencies
from neuroca.api.dependencies import (
    get_episodic_memory,
    get_semantic_memory,
    get_working_memory,
)
from neuroca.api.schemas.health import (
    DetailedComponentHealthSchema,
    HealthEventSchema,
    HealthParameterSchema,
    HealthState,  # Import HealthState enum for validation
)

# Import dynamics manager and new schemas
from neuroca.config import settings
from neuroca.core.auth import (  # Add WS verification if needed
    get_optional_api_key,
)
from neuroca.core.health.dynamics import ComponentHealth as CoreComponentHealth
from neuroca.core.health.dynamics import (
    HealthEvent,
    get_health_dynamics,
)
from neuroca.db.connection import get_db_status  # Keep for basic DB check if needed
from neuroca.memory.episodic_memory import EpisodicMemoryManager
from neuroca.memory.semantic_memory import SemanticMemoryManager
from neuroca.memory.working_memory import WorkingMemoryManager

# Configure logger
logger = logging.getLogger(__name__)

# --- Pydantic Models for Management Commands ---
class ForceStateRequest(BaseModel):
    state: HealthState = Field(..., description="The target health state to force.")

class AdjustParameterRequest(BaseModel):
    parameter_name: str = Field(..., description="The name of the health parameter to adjust.")
    new_value: float = Field(..., description="The new value to set for the parameter.")
# --- End Pydantic Models ---

# Active WebSocket connections for health events
active_connections: set[WebSocket] = set()
# Listener function reference to allow removal
health_event_listener: Optional[Callable] = None

# Get the global health dynamics manager instance
health_dynamics = get_health_dynamics()

# Create router
router = APIRouter(
    prefix="/health",
    tags=["health"],
    responses={
        503: {"description": "Service Unavailable"},
        500: {"description": "Internal Server Error"},
        401: {"description": "Unauthorized"},
    },
)

# Keep MemoryTierHealth and ResourceUtilization for now, might integrate later
class MemoryTierHealth(BaseModel):
    """Model representing the health status of a memory tier."""
    
    tier: str = Field(..., description="Memory tier name (working, episodic, semantic)")
    status: str = Field(..., description="Status of the memory tier")
    size: int = Field(..., description="Current size in bytes")
    capacity: int = Field(..., description="Maximum capacity in bytes")
    usage_percent: float = Field(..., description="Usage percentage")
    access_latency_ms: Optional[float] = Field(None, description="Access latency in milliseconds")
    details: Optional[dict] = Field(None, description="Additional tier-specific details")


class ResourceUtilization(BaseModel):
    """Model representing system resource utilization."""
    
    cpu_percent: float = Field(..., description="CPU utilization percentage")
    memory_percent: float = Field(..., description="Memory utilization percentage")
    disk_percent: float = Field(..., description="Disk utilization percentage")
    network_io: dict[str, int] = Field(..., description="Network IO statistics")
    process_count: int = Field(..., description="Number of running processes")


class DetailedHealthResponse(BaseModel):
    """Model for the detailed health check response."""
    
    status: str = Field(..., description="Overall system status (healthy, degraded, unhealthy)")
    version: str = Field(..., description="System version")
    environment: str = Field(..., description="Deployment environment")
    uptime_seconds: int = Field(..., description="System uptime in seconds")
    timestamp: dt.datetime = Field(..., description="Current timestamp") # Use alias dt
    components: list[DetailedComponentHealthSchema] = Field(..., description="Detailed health status of system components") # Use new schema
    # memory_tiers: List[MemoryTierHealth] = Field(..., description="Health status of memory tiers") # Keep or integrate into components
    resources: ResourceUtilization = Field(..., description="System resource utilization")
    host_info: dict = Field(..., description="Host system information")


@router.get(
    "",
    summary="Basic health check",
    description="Simple health check endpoint that returns 200 OK if the service is running",
    status_code=status.HTTP_200_OK,
    response_description="Service is healthy",
    responses={
        503: {"description": "Service is unhealthy or starting up"},
    },
)
async def health_check(request: Request) -> dict[str, str]:
    """
    Basic health check endpoint that returns a simple status response.
    
    This endpoint is designed for load balancers and simple monitoring systems
    that only need to know if the service is running.
    
    Returns:
        Dict[str, str]: A simple status response with the service status
    
    Raises:
        HTTPException: 503 status code if the service is unhealthy
    """
    try:
        # Check if the application is in startup mode
        app = request.app
        if hasattr(app, "is_startup_complete") and not app.is_startup_complete:
            logger.info("Health check during startup phase")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is starting up",
            )
        
        # Basic DB connection check
        db_status = get_db_status()
        if not db_status["connected"]:
            logger.error(f"Database connection failed: {db_status.get('error')}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection failed",
            )
        
        return {"status": "healthy"}
    
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.exception("Health check failed with unexpected error")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Service is unhealthy: {str(e)}",
            ) from e # B904
        raise


@router.get(
    "/detailed",
    summary="Detailed health check",
    description="Comprehensive health check with detailed system status information",
    response_model=DetailedHealthResponse,
    status_code=status.HTTP_200_OK,
    response_description="Detailed health status",
    responses={
        401: {"description": "Unauthorized access"},
        503: {"description": "Service is unhealthy"},
    },
)
async def detailed_health_check(
    request: Request,
    response: Response,
    api_key: Optional[str] = Depends(get_optional_api_key),  # noqa: B008
) -> DetailedHealthResponse:
    """
    Detailed health check endpoint that provides comprehensive system status information.
    
    This endpoint requires authentication in production environments and provides
    detailed information about all system components, memory tiers, and resource utilization.
    
    Args:
        request: The incoming request
        response: The outgoing response
        api_key: Optional API key for authentication
    
    Returns:
        DetailedHealthResponse: Comprehensive health status information
    
    Raises:
        HTTPException: 401 if authentication fails, 503 if service is unhealthy
    """
    # Check authentication in production
    if settings.ENVIRONMENT == "production" and not api_key:
        logger.warning("Unauthorized access attempt to detailed health check")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for detailed health check in production",
        )
    
    start_time = time.time()
    
    try:
        # Get system metrics (keep for resource usage)
        # metrics = get_system_metrics() # This function doesn't seem to be used later
        
        # Fetch detailed component health from HealthDynamicsManager
        component_health_details: list[DetailedComponentHealthSchema] = []
        all_component_ids = list(health_dynamics._components.keys()) # Access internal dict for now
        
        for component_id in all_component_ids:
            core_health: Optional[CoreComponentHealth] = health_dynamics.get_component_health(component_id)
            if core_health:
                # Convert core parameters to schema parameters
                schema_params = {}
                for name, param in core_health.parameters.items():
                    schema_params[name] = HealthParameterSchema(
                        name=param.name,
                        type=param.type,
                        value=param.value,
                        min_value=param.min_value,
                        max_value=param.max_value,
                        optimal_value=param.optimal_value,
                        decay_rate=param.decay_rate,
                        recovery_rate=param.recovery_rate,
                        last_updated=dt.datetime.fromtimestamp(param.last_updated),
                        is_optimal=param.is_optimal() # Call the method
                    )
                
                # Convert core events to schema events
                schema_events = [
                    HealthEventSchema(
                        event_type=event.event_type,
                        component_id=event.component_id,
                        parameter_name=event.parameter_name,
                        old_value=event.old_value,
                        new_value=event.new_value,
                        timestamp=dt.datetime.fromtimestamp(event.timestamp),
                        details=event.details
                    ) for event in core_health.events
                ]

                component_health_details.append(
                    DetailedComponentHealthSchema(
                        component_id=core_health.component_id,
                        status=core_health.state,
                        parameters=schema_params,
                        recent_events=schema_events,
                        last_state_change=dt.datetime.fromtimestamp(core_health.last_state_change)
                    )
                )
            else:
                 # Should not happen if iterating keys, but handle defensively
                 logger.warning(f"Could not retrieve health for registered component ID: {component_id}")

        # Memory tier health (keep for now, could be integrated into component details if memory tiers are registered components)
        # memory_tiers = [] # Remove or keep based on decision
        # ... (keep existing memory tier logic if needed separately) ...
        
        # Resource utilization
        resources = ResourceUtilization(
            cpu_percent=psutil.cpu_percent(),
            memory_percent=psutil.virtual_memory().percent,
            disk_percent=psutil.disk_usage('/').percent,
            network_io={
                "bytes_sent": psutil.net_io_counters().bytes_sent,
                "bytes_recv": psutil.net_io_counters().bytes_recv,
            },
            process_count=len(psutil.pids()),
        )
        
        # Host information
        host_info = {
            "hostname": platform.node(),
            "os": platform.system(),
            "os_version": platform.version(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "total_memory": psutil.virtual_memory().total,
        }
        
        # Determine overall status based on detailed component health states
        component_states = [c.status for c in component_health_details]
        overall_status = "healthy" # Default
        if HealthState.CRITICAL in component_states or HealthState.IMPAIRED in component_states:
            overall_status = "unhealthy"
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        elif HealthState.STRESSED in component_states or HealthState.FATIGUED in component_states:
            overall_status = "degraded"
        elif HealthState.NORMAL not in component_states and HealthState.OPTIMAL in component_states:
             # If all components are optimal
             overall_status = "optimal" # Or keep as 'healthy'
        # If mix of normal/optimal, stays 'healthy'
        
        # Calculate uptime
        process = psutil.Process(os.getpid())
        uptime_seconds = int(time.time() - process.create_time())
        
        # Construct response
        health_response = DetailedHealthResponse(
            status=overall_status,
            version=settings.VERSION,
            environment=settings.ENVIRONMENT,
            uptime_seconds=uptime_seconds,
            timestamp=dt.datetime.now(), # Use alias dt
            components=component_health_details, # Use new list
            # memory_tiers=memory_tiers, # Include if kept
            resources=resources,
            host_info=host_info,
        )
        
        # Log health check results
        execution_time = (time.time() - start_time) * 1000
        logger.info(f"Detailed health check completed in {execution_time:.2f}ms. Status: {overall_status}")
        
        return health_response
    
    except Exception as e:
        logger.exception("Detailed health check failed with unexpected error")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service is unhealthy: {str(e)}",
        ) from e # B904


@router.get(
    "/readiness",
    summary="Readiness probe",
    description="Checks if the service is ready to accept traffic",
    status_code=status.HTTP_200_OK,
    response_description="Service is ready",
    responses={
        503: {"description": "Service is not ready"},
    },
)
async def readiness_probe(
    request: Request,
    # Inject memory dependencies to check their availability/initialization
    working_memory: WorkingMemoryManager = Depends(get_working_memory),  # noqa: B008
    episodic_memory: EpisodicMemoryManager = Depends(get_episodic_memory),  # noqa: B008
    semantic_memory: SemanticMemoryManager = Depends(get_semantic_memory),  # noqa: B008
) -> dict[str, str]:
    """
    Readiness probe endpoint for Kubernetes and other orchestration systems.
    
    This endpoint checks if the service is ready to accept traffic by verifying
    that all required dependencies and components are available.
    
    Returns:
        Dict[str, str]: A simple status response indicating readiness
    
    Raises:
        HTTPException: 503 status code if the service is not ready
    """
    try:
        # Check if the application is in startup mode
        app = request.app
        if hasattr(app, "is_startup_complete") and not app.is_startup_complete:
            logger.info("Readiness check failed: startup not complete")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service startup not complete",
            )
        
        # Check database connection
        db_status = get_db_status()
        if not db_status["connected"]:
            logger.warning(f"Readiness check failed: database connection error: {db_status.get('error')}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not ready",
            )
        
        # By successfully injecting the memory dependencies above, we implicitly check
        # if they could be initialized. If any dependency failed (e.g., DB connection
        # error during its initialization), FastAPI would have already raised an
        # exception, failing the readiness probe.
        # No explicit check like `memory_manager.is_initialized()` is needed here.
        
        return {"status": "ready"}
    
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.exception("Readiness check failed with unexpected error")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service is not ready: {str(e)}",
            ) from e # B904
        raise


# --- Management Command Endpoints ---

@router.post(
    "/components/{component_id}/force_state",
    summary="Force a component into a specific health state",
    status_code=status.HTTP_200_OK,
    response_description="Component state successfully updated",
    responses={
        401: {"description": "Unauthorized access"},
        404: {"description": "Component not found"},
        500: {"description": "Internal Server Error"},
    },
)
async def force_component_state(
    component_id: str,
    request_body: ForceStateRequest,
    api_key: Optional[str] = Depends(get_optional_api_key),  # noqa: B008
) -> dict[str, str]:
    """
    Manually forces a registered component into a specified health state.
    Requires appropriate authentication, especially in production.
    """
    # Authentication check (similar to detailed health)
    if settings.ENVIRONMENT == "production" and not api_key:
        logger.warning(f"Unauthorized attempt to force state for component {component_id}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    try:
        component_health = health_dynamics.get_component_health(component_id)
        if not component_health:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Component '{component_id}' not registered for health tracking")

        new_state = request_body.state
        event = component_health.update_state(new_state) # This already generates an event
        if event:
             health_dynamics._notify_listeners(event) # Ensure listeners are notified

        logger.info(f"Manually forced state of component '{component_id}' to {new_state.value}")
        return {"message": f"Component '{component_id}' state forced to {new_state.value}"}

    except HTTPException:
        raise # Re-raise HTTP exceptions
    except Exception as e:
        logger.exception(f"Error forcing state for component {component_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to force state: {e}") from e # B904


@router.post(
    "/components/{component_id}/adjust_parameter",
    summary="Manually adjust a health parameter for a component",
    status_code=status.HTTP_200_OK,
    response_description="Parameter successfully adjusted",
    responses={
        401: {"description": "Unauthorized access"},
        404: {"description": "Component or Parameter not found"},
        422: {"description": "Invalid parameter value"},
        500: {"description": "Internal Server Error"},
    },
)
async def adjust_component_parameter(
    component_id: str,
    request_body: AdjustParameterRequest,
    api_key: Optional[str] = Depends(get_optional_api_key),  # noqa: B008
) -> dict[str, str]:
    """
    Manually adjusts the value of a specific health parameter for a component.
    Requires appropriate authentication.
    """
     # Authentication check
    if settings.ENVIRONMENT == "production" and not api_key:
        logger.warning(f"Unauthorized attempt to adjust parameter for component {component_id}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    try:
        param_name = request_body.parameter_name
        new_value = request_body.new_value

        # Use the manager's update method which handles locking and event notification
        health_dynamics.update_parameter(component_id, param_name, new_value)

        # Check if the parameter exists (update_parameter raises KeyError if component missing,
        # but ComponentHealth.update_parameter raises if param missing - catch that here implicitly)
        # The manager's update_parameter should ideally handle both not found cases.
        # Assuming HealthDynamicsManager.update_parameter raises KeyError for both component/param not found.

        logger.info(f"Manually adjusted parameter '{param_name}' for component '{component_id}' to {new_value}")
        return {"message": f"Parameter '{param_name}' for component '{component_id}' adjusted to {new_value}"}

    except KeyError as e:
         # Raised by HealthDynamicsManager if component not found, or by ComponentHealth if param not found
         logger.warning(f"Failed to adjust parameter: {e}")
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e # B904
    except ValueError as e: # Potentially raised by parameter validation if added
         logger.warning(f"Invalid value for parameter adjustment: {e}")
         raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e # B904 - Add from e for ValueError
    except Exception as e:
        logger.exception(f"Error adjusting parameter for component {component_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to adjust parameter: {e}") from e # B904

# --- End Management Command Endpoints ---


# WebSocket endpoint for real-time health events
@router.websocket("/ws/health/events")
async def websocket_health_events(websocket: WebSocket):
    """
    WebSocket endpoint to stream real-time health events.

    Connect to this endpoint to receive JSON-formatted HealthEventSchema
    objects as they occur in the system.
    """
    global health_event_listener
    await websocket.accept()
    active_connections.add(websocket)
    logger.info(f"WebSocket client connected for health events: {websocket.client}")

    # Define the listener function if it doesn't exist
    if health_event_listener is None:
        async def broadcast_health_event(event: HealthEvent):
            """Formats and broadcasts health events to connected WebSocket clients."""
            try:
                # Convert core event to schema event
                schema_event = HealthEventSchema(
                    event_type=event.event_type,
                    component_id=event.component_id,
                    parameter_name=event.parameter_name,
                    old_value=event.old_value,
                    new_value=event.new_value,
                    timestamp=dt.datetime.fromtimestamp(event.timestamp),
                    details=event.details
                )
                event_json = schema_event.model_dump_json() # Use model_dump_json for Pydantic v2+

                # Use asyncio.gather to send to all connections concurrently
                await asyncio.gather(
                    *[connection.send_text(event_json) for connection in active_connections],
                    return_exceptions=True # Log errors but don't crash broadcaster
                )
            except Exception as e:  # noqa: BLE001
                logger.error(f"Error broadcasting health event via WebSocket: {e}")

        health_event_listener = broadcast_health_event
        # Register the listener only once
        health_dynamics.add_listener(health_event_listener)
        logger.info("Health event listener registered for WebSocket broadcasting.")

    try:
        # Keep the connection alive, listening for disconnect
        while True:
            # We don't expect messages from the client in this simple broadcast setup
            # If we needed client interaction, we'd await websocket.receive_text() here
            await asyncio.sleep(60) # Keep alive, check connection status periodically
            # Ping client to ensure connection is alive (optional)
            # await websocket.send_text('{"type": "ping"}')
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected: {websocket.client}")
    except Exception as e:  # noqa: BLE001
        logger.error(f"WebSocket error for client {websocket.client}: {e}")
    finally:
        active_connections.remove(websocket)
        logger.info(f"WebSocket connection removed: {websocket.client}. Remaining connections: {len(active_connections)}")
        # Optional: If no connections left, remove the listener to save resources
        # if not active_connections and health_event_listener:
        #     health_dynamics.remove_listener(health_event_listener)
        #     health_event_listener = None
        #     logger.info("Health event listener removed as no clients are connected.")


@router.get(
    "/liveness",
    summary="Liveness probe",
    description="Checks if the service is alive and functioning",
    status_code=status.HTTP_200_OK,
    response_description="Service is alive",
    responses={
        503: {"description": "Service is not functioning properly"},
    },
)
async def liveness_probe() -> dict[str, str]:
    """
    Liveness probe endpoint for Kubernetes and other orchestration systems.
    
    This endpoint performs a minimal check to verify that the service is alive
    and functioning properly. It should be lightweight and fast.
    
    Returns:
        Dict[str, str]: A simple status response indicating liveness
    
    Raises:
        HTTPException: 503 status code if the service is not functioning properly
    """
    try:
        # Simple check to verify the service is running
        # This should be very lightweight and not depend on external services
        return {"status": "alive"}
    
    except Exception as e:
        logger.exception("Liveness check failed with unexpected error")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service is not functioning properly: {str(e)}",
        ) from e # B904
