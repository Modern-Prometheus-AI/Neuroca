"""
System API Routes for NeuroCognitive Architecture (NCA)

This module provides API endpoints for system-level operations, including:
- System health and status monitoring
- Configuration management
- Diagnostic information
- Resource utilization metrics
- System control operations (restart, maintenance mode, etc.)

These endpoints are primarily used by administrators and monitoring systems
to ensure the NCA platform is operating correctly and to perform maintenance
operations when needed.

Usage:
    These routes are automatically registered when the API is initialized.
    They are accessible under the /api/system/ prefix.

Security:
    All endpoints in this module require administrative privileges.
    Authentication and authorization are enforced through middleware.
"""

import datetime
import logging
import os
import platform
import time
from typing import Any, Optional

import psutil
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from neuroca.api.auth.dependencies import get_admin_user
from neuroca.api.models.responses import ErrorResponse, StandardResponse
from neuroca.config.settings import get_settings
from neuroca.core.system.diagnostics import SystemDiagnostics
from neuroca.core.system.health import ComponentStatus, HealthChecker

# Configure logger
logger = logging.getLogger(__name__)

# Create router with prefix and tags
router = APIRouter(
    prefix="/system",
    tags=["system"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
    }
)

# Models for request and response data
class SystemInfo(BaseModel):
    """System information response model"""
    version: str = Field(..., description="NCA system version")
    environment: str = Field(..., description="Deployment environment (dev, staging, prod)")
    uptime_seconds: int = Field(..., description="System uptime in seconds")
    start_time: datetime.datetime = Field(..., description="System start time")
    hostname: str = Field(..., description="Server hostname")
    platform_info: str = Field(..., description="Operating system information")
    python_version: str = Field(..., description="Python version")

class HealthCheckResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Overall system health status")
    timestamp: datetime.datetime = Field(..., description="Time of health check")
    components: dict[str, ComponentStatus] = Field(..., description="Status of individual components")
    details: Optional[dict[str, Any]] = Field(None, description="Additional health details")

class ConfigurationItem(BaseModel):
    """Configuration item model"""
    key: str = Field(..., description="Configuration key")
    value: Any = Field(..., description="Configuration value")
    description: Optional[str] = Field(None, description="Configuration description")
    editable: bool = Field(..., description="Whether this configuration can be modified")

class ConfigurationUpdateRequest(BaseModel):
    """Configuration update request model"""
    key: str = Field(..., description="Configuration key to update")
    value: Any = Field(..., description="New configuration value")

class ResourceUtilization(BaseModel):
    """Resource utilization model"""
    cpu_percent: float = Field(..., description="CPU utilization percentage")
    memory_used_mb: float = Field(..., description="Memory used in MB")
    memory_total_mb: float = Field(..., description="Total memory in MB")
    memory_percent: float = Field(..., description="Memory utilization percentage")
    disk_used_gb: float = Field(..., description="Disk space used in GB")
    disk_total_gb: float = Field(..., description="Total disk space in GB")
    disk_percent: float = Field(..., description="Disk utilization percentage")
    network_sent_mb: float = Field(..., description="Network data sent in MB")
    network_received_mb: float = Field(..., description="Network data received in MB")

class MaintenanceModeRequest(BaseModel):
    """Maintenance mode request model"""
    enabled: bool = Field(..., description="Whether to enable maintenance mode")
    message: Optional[str] = Field(None, description="Message to display during maintenance")
    estimated_duration_minutes: Optional[int] = Field(None, description="Estimated maintenance duration")


@router.get(
    "/info",
    response_model=SystemInfo,
    summary="Get system information",
    description="Returns basic information about the NCA system including version, environment, and uptime."
)
async def get_system_info(
    admin_user: dict = Depends(get_admin_user)
) -> SystemInfo:
    """
    Retrieve basic system information.
    
    This endpoint provides general information about the NCA system deployment,
    including version, environment, and runtime information.
    
    Args:
        admin_user: The authenticated admin user (injected by dependency)
        
    Returns:
        SystemInfo: Object containing system information
        
    Raises:
        HTTPException: If there's an error retrieving system information
    """
    try:
        settings = get_settings()
        boot_time = psutil.boot_time()
        boot_datetime = datetime.datetime.fromtimestamp(boot_time)
        uptime = int(time.time() - boot_time)
        
        logger.debug(f"System info requested by admin user {admin_user.get('username')}")
        
        return SystemInfo(
            version=settings.version,
            environment=settings.environment,
            uptime_seconds=uptime,
            start_time=boot_datetime,
            hostname=platform.node(),
            platform_info=f"{platform.system()} {platform.release()}",
            python_version=platform.python_version()
        )
    except Exception as e:
        logger.error(f"Error retrieving system info: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve system information: {str(e)}"
        )


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Check system health",
    description="Performs a comprehensive health check of all system components."
)
async def health_check(
    detailed: bool = Query(False, description="Include detailed component information"),
    admin_user: dict = Depends(get_admin_user)
) -> HealthCheckResponse:
    """
    Perform a comprehensive health check of the NCA system.
    
    This endpoint checks the health of all critical system components including
    database connections, memory systems, and external integrations.
    
    Args:
        detailed: Whether to include detailed component information
        admin_user: The authenticated admin user (injected by dependency)
        
    Returns:
        HealthCheckResponse: Object containing health status information
        
    Raises:
        HTTPException: If there's an error performing the health check
    """
    try:
        logger.debug(f"Health check requested by admin user {admin_user.get('username')}")
        
        # Create health checker and run checks
        health_checker = HealthChecker()
        health_status = await health_checker.check_all(detailed=detailed)
        
        # Log warning if system is not healthy
        if health_status.status != "healthy":
            logger.warning(f"System health check returned status: {health_status.status}")
            for component, status in health_status.components.items():
                if status.status != "healthy":
                    logger.warning(f"Component {component} is {status.status}: {status.message}")
        
        return HealthCheckResponse(
            status=health_status.status,
            timestamp=datetime.datetime.now(),
            components=health_status.components,
            details=health_status.details if detailed else None
        )
    except Exception as e:
        logger.error(f"Error performing health check: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform health check: {str(e)}"
        )


@router.get(
    "/configuration",
    response_model=list[ConfigurationItem],
    summary="Get system configuration",
    description="Returns the current system configuration settings."
)
async def get_configuration(
    filter: Optional[str] = Query(None, description="Filter configuration by key prefix"),
    admin_user: dict = Depends(get_admin_user)
) -> list[ConfigurationItem]:
    """
    Retrieve the current system configuration.
    
    This endpoint returns the current configuration settings for the NCA system.
    Settings can be filtered by key prefix.
    
    Args:
        filter: Optional filter to limit returned configuration items
        admin_user: The authenticated admin user (injected by dependency)
        
    Returns:
        List[ConfigurationItem]: List of configuration items
        
    Raises:
        HTTPException: If there's an error retrieving configuration
    """
    try:
        logger.debug(f"Configuration requested by admin user {admin_user.get('username')}")
        settings = get_settings()
        
        # Convert settings to configuration items
        config_items = []
        for key, value in settings.dict().items():
            # Skip sensitive configuration items
            if key.lower() in ["secret_key", "password", "token", "credential"]:
                continue
                
            # Apply filter if provided
            if filter and not key.startswith(filter):
                continue
                
            # Determine if setting is editable
            editable = key not in settings.get_protected_settings()
            
            config_items.append(ConfigurationItem(
                key=key,
                value=value,
                description=settings.get_setting_description(key),
                editable=editable
            ))
        
        return config_items
    except Exception as e:
        logger.error(f"Error retrieving configuration: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve configuration: {str(e)}"
        )


@router.put(
    "/configuration",
    response_model=StandardResponse,
    summary="Update system configuration",
    description="Updates a specific system configuration setting."
)
async def update_configuration(
    update_request: ConfigurationUpdateRequest,
    admin_user: dict = Depends(get_admin_user)
) -> StandardResponse:
    """
    Update a system configuration setting.
    
    This endpoint allows updating a specific configuration setting.
    Only non-protected settings can be updated.
    
    Args:
        update_request: The configuration update request
        admin_user: The authenticated admin user (injected by dependency)
        
    Returns:
        StandardResponse: Response indicating success or failure
        
    Raises:
        HTTPException: If the configuration update fails
    """
    try:
        logger.info(f"Configuration update requested by admin user {admin_user.get('username')}")
        settings = get_settings()
        
        # Check if setting exists
        if update_request.key not in settings.dict():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration key '{update_request.key}' not found"
            )
        
        # Check if setting is protected
        if update_request.key in settings.get_protected_settings():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Configuration key '{update_request.key}' is protected and cannot be modified"
            )
        
        # Update the setting
        success = settings.update_setting(update_request.key, update_request.value)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to update configuration key '{update_request.key}'"
            )
        
        logger.info(f"Configuration key '{update_request.key}' updated successfully")
        return StandardResponse(
            success=True,
            message=f"Configuration key '{update_request.key}' updated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating configuration: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update configuration: {str(e)}"
        )


@router.get(
    "/resources",
    response_model=ResourceUtilization,
    summary="Get resource utilization",
    description="Returns current system resource utilization metrics."
)
async def get_resource_utilization(
    admin_user: dict = Depends(get_admin_user)
) -> ResourceUtilization:
    """
    Retrieve current system resource utilization.
    
    This endpoint provides information about CPU, memory, disk, and network
    utilization for the system.
    
    Args:
        admin_user: The authenticated admin user (injected by dependency)
        
    Returns:
        ResourceUtilization: Object containing resource utilization metrics
        
    Raises:
        HTTPException: If there's an error retrieving resource metrics
    """
    try:
        logger.debug(f"Resource utilization requested by admin user {admin_user.get('username')}")
        
        # Get CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.5)
        
        # Get memory usage
        memory = psutil.virtual_memory()
        memory_used_mb = memory.used / (1024 * 1024)
        memory_total_mb = memory.total / (1024 * 1024)
        
        # Get disk usage
        disk = psutil.disk_usage('/')
        disk_used_gb = disk.used / (1024 * 1024 * 1024)
        disk_total_gb = disk.total / (1024 * 1024 * 1024)
        
        # Get network usage
        net_io = psutil.net_io_counters()
        net_sent_mb = net_io.bytes_sent / (1024 * 1024)
        net_recv_mb = net_io.bytes_recv / (1024 * 1024)
        
        return ResourceUtilization(
            cpu_percent=cpu_percent,
            memory_used_mb=round(memory_used_mb, 2),
            memory_total_mb=round(memory_total_mb, 2),
            memory_percent=memory.percent,
            disk_used_gb=round(disk_used_gb, 2),
            disk_total_gb=round(disk_total_gb, 2),
            disk_percent=disk.percent,
            network_sent_mb=round(net_sent_mb, 2),
            network_received_mb=round(net_recv_mb, 2)
        )
    except Exception as e:
        logger.error(f"Error retrieving resource utilization: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve resource utilization: {str(e)}"
        )


@router.post(
    "/maintenance",
    response_model=StandardResponse,
    summary="Set maintenance mode",
    description="Enables or disables system maintenance mode."
)
async def set_maintenance_mode(
    request: MaintenanceModeRequest,
    background_tasks: BackgroundTasks,
    admin_user: dict = Depends(get_admin_user)
) -> StandardResponse:
    """
    Enable or disable system maintenance mode.
    
    This endpoint allows administrators to put the system into maintenance mode,
    which will prevent non-admin users from accessing the system.
    
    Args:
        request: The maintenance mode request
        background_tasks: FastAPI background tasks
        admin_user: The authenticated admin user (injected by dependency)
        
    Returns:
        StandardResponse: Response indicating success or failure
        
    Raises:
        HTTPException: If setting maintenance mode fails
    """
    try:
        action = "enabled" if request.enabled else "disabled"
        logger.info(f"Maintenance mode {action} requested by admin user {admin_user.get('username')}")
        
        settings = get_settings()
        
        # Update maintenance mode setting
        settings.maintenance_mode = request.enabled
        settings.maintenance_message = request.message if request.enabled else None
        settings.maintenance_end_time = (
            datetime.datetime.now() + datetime.timedelta(minutes=request.estimated_duration_minutes)
            if request.enabled and request.estimated_duration_minutes
            else None
        )
        
        # If enabling maintenance mode, add background task to perform maintenance operations
        if request.enabled:
            background_tasks.add_task(
                perform_maintenance_operations,
                admin_user.get('username'),
                request.estimated_duration_minutes
            )
        
        logger.info(f"Maintenance mode {action} successfully")
        return StandardResponse(
            success=True,
            message=f"Maintenance mode {action} successfully"
        )
    except Exception as e:
        logger.error(f"Error setting maintenance mode: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set maintenance mode: {str(e)}"
        )


@router.post(
    "/restart",
    response_model=StandardResponse,
    summary="Restart system",
    description="Initiates a controlled system restart."
)
async def restart_system(
    background_tasks: BackgroundTasks,
    admin_user: dict = Depends(get_admin_user)
) -> StandardResponse:
    """
    Initiate a controlled system restart.
    
    This endpoint allows administrators to restart the NCA system in a controlled manner.
    The restart is performed as a background task to allow the API to respond.
    
    Args:
        background_tasks: FastAPI background tasks
        admin_user: The authenticated admin user (injected by dependency)
        
    Returns:
        StandardResponse: Response indicating the restart has been initiated
        
    Raises:
        HTTPException: If initiating the restart fails
    """
    try:
        logger.warning(f"System restart requested by admin user {admin_user.get('username')}")
        
        # Add restart task to background tasks
        background_tasks.add_task(
            perform_system_restart,
            admin_user.get('username')
        )
        
        return StandardResponse(
            success=True,
            message="System restart initiated. The system will restart in 10 seconds."
        )
    except Exception as e:
        logger.error(f"Error initiating system restart: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate system restart: {str(e)}"
        )


@router.get(
    "/diagnostics",
    response_model=dict[str, Any],
    summary="Run system diagnostics",
    description="Runs comprehensive system diagnostics and returns detailed results."
)
async def run_diagnostics(
    components: Optional[str] = Query(None, description="Comma-separated list of components to diagnose"),
    admin_user: dict = Depends(get_admin_user)
) -> dict[str, Any]:
    """
    Run comprehensive system diagnostics.
    
    This endpoint runs diagnostics on system components and returns detailed results.
    Specific components can be targeted by providing a comma-separated list.
    
    Args:
        components: Optional comma-separated list of components to diagnose
        admin_user: The authenticated admin user (injected by dependency)
        
    Returns:
        Dict[str, Any]: Diagnostic results for each component
        
    Raises:
        HTTPException: If diagnostics fail
    """
    try:
        logger.info(f"System diagnostics requested by admin user {admin_user.get('username')}")
        
        # Parse components if provided
        component_list = None
        if components:
            component_list = [c.strip() for c in components.split(",")]
            logger.debug(f"Running diagnostics for specific components: {component_list}")
        
        # Run diagnostics
        diagnostics = SystemDiagnostics()
        results = await diagnostics.run_diagnostics(components=component_list)
        
        return results
    except Exception as e:
        logger.error(f"Error running system diagnostics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run system diagnostics: {str(e)}"
        )


@router.get(
    "/logs",
    response_model=list[dict[str, Any]],
    summary="Get system logs",
    description="Retrieves recent system logs with filtering options."
)
async def get_system_logs(
    level: Optional[str] = Query(None, description="Log level filter (DEBUG, INFO, WARNING, ERROR, CRITICAL)"),
    component: Optional[str] = Query(None, description="Component filter"),
    limit: int = Query(100, description="Maximum number of log entries to return"),
    admin_user: dict = Depends(get_admin_user)
) -> list[dict[str, Any]]:
    """
    Retrieve recent system logs.
    
    This endpoint returns recent system logs with options for filtering by
    log level and component.
    
    Args:
        level: Optional log level filter
        component: Optional component filter
        limit: Maximum number of log entries to return
        admin_user: The authenticated admin user (injected by dependency)
        
    Returns:
        List[Dict[str, Any]]: List of log entries
        
    Raises:
        HTTPException: If retrieving logs fails
    """
    try:
        logger.debug(f"System logs requested by admin user {admin_user.get('username')}")
        
        # Validate log level if provided
        if level and level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid log level: {level}"
            )
        
        # This is a placeholder - in a real implementation, you would retrieve logs
        # from your logging system (e.g., file, database, or external service)
        # For demonstration, we'll return a mock response
        
        # Mock log retrieval
        logs = []
        log_file_path = os.path.join(os.path.dirname(__file__), "../../../logs/system.log")
        
        try:
            if os.path.exists(log_file_path):
                with open(log_file_path) as f:
                    lines = f.readlines()
                    # Process the most recent lines first
                    for line in reversed(lines):
                        # Parse log line (format depends on your logging configuration)
                        # This is a simplified example
                        parts = line.strip().split(" - ")
                        if len(parts) >= 3:
                            timestamp = parts[0]
                            log_level = parts[1]
                            message = " - ".join(parts[2:])
                            
                            # Apply filters
                            if level and log_level != level:
                                continue
                            if component and component not in message:
                                continue
                            
                            logs.append({
                                "timestamp": timestamp,
                                "level": log_level,
                                "message": message
                            })
                            
                            if len(logs) >= limit:
                                break
        except Exception as e:
            logger.warning(f"Error reading log file: {str(e)}")
            # Continue with empty logs rather than failing the request
        
        return logs
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving system logs: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve system logs: {str(e)}"
        )


# Helper functions for background tasks

async def perform_maintenance_operations(username: str, duration_minutes: Optional[int] = None):
    """
    Perform maintenance operations in the background.
    
    Args:
        username: The username of the admin who initiated maintenance
        duration_minutes: The estimated duration of maintenance in minutes
    """
    try:
        logger.info(f"Starting maintenance operations (initiated by {username})")
        
        # Perform maintenance tasks here
        # Examples:
        # - Database optimization
        # - Cache clearing
        # - Log rotation
        # - Resource cleanup
        
        # For demonstration, we'll just log some messages
        logger.info("Performing database optimization...")
        time.sleep(2)  # Simulate work
        
        logger.info("Clearing system caches...")
        time.sleep(1)  # Simulate work
        
        logger.info("Rotating logs...")
        time.sleep(1)  # Simulate work
        
        logger.info("Cleaning up temporary resources...")
        time.sleep(2)  # Simulate work
        
        logger.info("Maintenance operations completed successfully")
        
        # If duration was specified, automatically disable maintenance mode after duration
        if duration_minutes:
            # This would be implemented in a real system
            # For now, we'll just log it
            logger.info(f"Maintenance mode will be automatically disabled after {duration_minutes} minutes")
    except Exception as e:
        logger.error(f"Error during maintenance operations: {str(e)}", exc_info=True)


async def perform_system_restart(username: str):
    """
    Perform a controlled system restart.
    
    Args:
        username: The username of the admin who initiated the restart
    """
    try:
        logger.warning(f"Preparing for system restart (initiated by {username})")
        
        # In a real implementation, this would:
        # 1. Set the system to maintenance mode
        # 2. Wait for existing operations to complete
        # 3. Perform cleanup
        # 4. Signal the process manager (e.g., systemd, supervisor) to restart the service
        
        # For demonstration, we'll just log the steps
        logger.info("Setting system to maintenance mode...")
        time.sleep(1)  # Simulate work
        
        logger.info("Waiting for existing operations to complete...")
        time.sleep(3)  # Simulate work
        
        logger.info("Performing pre-restart cleanup...")
        time.sleep(2)  # Simulate work
        
        logger.warning("Initiating system restart...")
        # In a real implementation, this might exit the process or signal a process manager
        # os.system("systemctl restart neuroca.service")  # Example for systemd
    except Exception as e:
        logger.error(f"Error during system restart: {str(e)}", exc_info=True)