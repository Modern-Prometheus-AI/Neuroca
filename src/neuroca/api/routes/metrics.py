"""
Metrics API Routes Module

This module provides API endpoints for collecting, retrieving, and managing system metrics
for the NeuroCognitive Architecture (NCA). It includes endpoints for:
- System health metrics
- Memory usage statistics
- Performance metrics
- Component-specific metrics
- Custom metric registration and querying

The metrics system is designed to support both real-time monitoring and historical analysis,
with configurable retention policies and aggregation methods.

Usage:
    These routes are automatically registered with the main API router and
    are available under the /metrics prefix.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Optional, Union

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

from neuroca.config.settings import get_settings
from neuroca.core.auth import Permission, User, get_current_user, require_permissions
from neuroca.core.exceptions import MetricNotFoundException, MetricValidationError
from neuroca.core.models.metrics import (
    MemoryMetrics,
    MetricDefinition,
    MetricSummary,
    MetricTimeseriesData,
    MetricType,
    PerformanceMetrics,
    SystemHealthMetrics,
)
from neuroca.core.services.metrics import MetricsService

# Configure logger
logger = logging.getLogger(__name__)

# Create router with prefix and tags
router = APIRouter(
    prefix="/metrics",
    tags=["metrics"],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Metric not found"},
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid request parameters"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
        status.HTTP_403_FORBIDDEN: {"description": "Not authorized"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
    }
)

# Request and response models
class MetricRequest(BaseModel):
    """Model for submitting a new metric value."""
    name: str = Field(..., description="Unique name of the metric")
    value: Union[float, int, str, bool] = Field(..., description="Value of the metric")
    timestamp: Optional[datetime] = Field(None, description="Timestamp of the metric (defaults to now)")
    labels: dict[str, str] = Field(default_factory=dict, description="Additional labels/dimensions for the metric")
    
    @validator('name')
    def validate_name(cls, v):
        if not v or len(v) < 2:
            raise ValueError("Metric name must be at least 2 characters")
        return v

class MetricDefinitionRequest(BaseModel):
    """Model for registering a new metric definition."""
    name: str = Field(..., description="Unique name for the metric")
    description: str = Field(..., description="Description of what the metric measures")
    type: MetricType = Field(..., description="Type of metric (counter, gauge, histogram, etc.)")
    unit: str = Field(..., description="Unit of measurement (e.g., 'seconds', 'bytes', 'count')")
    aggregation: str = Field("last", description="Default aggregation method (sum, avg, min, max, last)")
    retention_days: int = Field(30, description="Number of days to retain this metric data")
    labels: list[str] = Field(default_factory=list, description="Allowed label keys for this metric")

class MetricQueryParams(BaseModel):
    """Model for metric query parameters."""
    start_time: Optional[datetime] = Field(None, description="Start time for the query range")
    end_time: Optional[datetime] = Field(None, description="End time for the query range")
    interval: Optional[str] = Field("1m", description="Aggregation interval (e.g., '1m', '5m', '1h')")
    aggregation: Optional[str] = Field(None, description="Aggregation method to use")
    limit: Optional[int] = Field(1000, description="Maximum number of data points to return")
    labels: Optional[dict[str, str]] = Field(None, description="Filter by specific label values")

# Dependency for metrics service
def get_metrics_service():
    """Dependency to get the metrics service instance."""
    settings = get_settings()
    return MetricsService(settings)

@router.get("/health", response_model=SystemHealthMetrics)
async def get_system_health(
    metrics_service: MetricsService = Depends(get_metrics_service),
    current_user: User = Depends(get_current_user)
):
    """
    Get current system health metrics.
    
    Returns a comprehensive overview of system health including:
    - CPU usage
    - Memory usage
    - Disk usage
    - Network status
    - Component health statuses
    - Error rates
    
    This endpoint is useful for monitoring dashboards and health checks.
    """
    logger.debug("Retrieving system health metrics")
    try:
        health_metrics = await metrics_service.get_system_health()
        return health_metrics
    except Exception as e:
        logger.error(f"Failed to retrieve system health metrics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve system health metrics: {str(e)}"
        )

@router.get("/memory", response_model=MemoryMetrics)
async def get_memory_metrics(
    tier: Optional[str] = Query(None, description="Filter by memory tier (working, episodic, semantic)"),
    metrics_service: MetricsService = Depends(get_metrics_service),
    current_user: User = Depends(get_current_user)
):
    """
    Get memory system metrics.
    
    Returns metrics related to the three-tiered memory system including:
    - Usage statistics per tier
    - Access patterns
    - Retrieval times
    - Cache hit/miss rates
    - Memory health indicators
    
    Optional query parameter:
    - tier: Filter metrics to a specific memory tier
    """
    logger.debug(f"Retrieving memory metrics{f' for tier: {tier}' if tier else ''}")
    try:
        memory_metrics = await metrics_service.get_memory_metrics(tier=tier)
        return memory_metrics
    except ValueError as e:
        logger.warning(f"Invalid memory tier requested: {tier}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid memory tier: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to retrieve memory metrics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve memory metrics: {str(e)}"
        )

@router.get("/performance", response_model=PerformanceMetrics)
async def get_performance_metrics(
    component: Optional[str] = Query(None, description="Filter by specific component"),
    period: str = Query("1h", description="Time period to analyze (e.g., '15m', '1h', '24h', '7d')"),
    metrics_service: MetricsService = Depends(get_metrics_service),
    current_user: User = Depends(get_current_user)
):
    """
    Get system performance metrics.
    
    Returns performance-related metrics including:
    - Response times
    - Throughput
    - Error rates
    - Resource utilization
    - Bottleneck indicators
    
    Optional query parameters:
    - component: Filter to a specific system component
    - period: Time period to analyze (default: last hour)
    """
    logger.debug(f"Retrieving performance metrics for period: {period}{f', component: {component}' if component else ''}")
    try:
        performance_metrics = await metrics_service.get_performance_metrics(
            component=component,
            period=period
        )
        return performance_metrics
    except ValueError as e:
        logger.warning(f"Invalid parameters for performance metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid parameters: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to retrieve performance metrics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve performance metrics: {str(e)}"
        )

@router.post("/custom", status_code=status.HTTP_201_CREATED)
async def submit_metric(
    metric: MetricRequest,
    background_tasks: BackgroundTasks,
    metrics_service: MetricsService = Depends(get_metrics_service),
    current_user: User = Depends(get_current_user)
):
    """
    Submit a custom metric value.
    
    This endpoint allows components to submit custom metric values for tracking.
    The metric must be previously registered using the /metrics/definitions endpoint.
    
    The metric value is processed asynchronously to avoid blocking the caller.
    """
    logger.debug(f"Submitting custom metric: {metric.name} with value: {metric.value}")
    
    # Set timestamp to now if not provided
    if not metric.timestamp:
        metric.timestamp = datetime.utcnow()
    
    try:
        # Process metric in background to avoid blocking
        background_tasks.add_task(
            metrics_service.record_metric,
            name=metric.name,
            value=metric.value,
            timestamp=metric.timestamp,
            labels=metric.labels
        )
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={"message": f"Metric '{metric.name}' queued for processing"}
        )
    except MetricValidationError as e:
        logger.warning(f"Metric validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Metric validation error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to submit metric: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit metric: {str(e)}"
        )

@router.post("/batch", status_code=status.HTTP_201_CREATED)
async def submit_metrics_batch(
    metrics: list[MetricRequest],
    background_tasks: BackgroundTasks,
    metrics_service: MetricsService = Depends(get_metrics_service),
    current_user: User = Depends(get_current_user)
):
    """
    Submit multiple metrics in a single batch.
    
    This endpoint is optimized for submitting multiple metrics at once,
    reducing network overhead for high-frequency metric reporting.
    
    All metrics are processed asynchronously in the background.
    """
    logger.debug(f"Submitting batch of {len(metrics)} metrics")
    
    if not metrics:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty metrics batch"
        )
    
    # Set timestamps for metrics that don't have one
    now = datetime.utcnow()
    for metric in metrics:
        if not metric.timestamp:
            metric.timestamp = now
    
    try:
        # Process metrics batch in background
        background_tasks.add_task(
            metrics_service.record_metrics_batch,
            metrics=[{
                "name": m.name,
                "value": m.value,
                "timestamp": m.timestamp,
                "labels": m.labels
            } for m in metrics]
        )
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={"message": f"Batch of {len(metrics)} metrics queued for processing"}
        )
    except Exception as e:
        logger.error(f"Failed to submit metrics batch: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit metrics batch: {str(e)}"
        )

@router.post("/definitions", status_code=status.HTTP_201_CREATED, response_model=MetricDefinition)
async def register_metric_definition(
    definition: MetricDefinitionRequest,
    metrics_service: MetricsService = Depends(get_metrics_service),
    current_user: User = Depends(get_current_user)
):
    """
    Register a new metric definition.
    
    This endpoint allows for registering new custom metrics with their metadata.
    Once registered, values for this metric can be submitted using the /metrics/custom endpoint.
    
    Requires admin permissions to create new metric definitions.
    """
    logger.debug(f"Registering new metric definition: {definition.name}")
    
    # Check for admin permissions
    require_permissions(current_user, [Permission.ADMIN])
    
    try:
        new_definition = await metrics_service.register_metric_definition(
            name=definition.name,
            description=definition.description,
            metric_type=definition.type,
            unit=definition.unit,
            aggregation=definition.aggregation,
            retention_days=definition.retention_days,
            labels=definition.labels
        )
        
        return new_definition
    except ValueError as e:
        logger.warning(f"Invalid metric definition: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid metric definition: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to register metric definition: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register metric definition: {str(e)}"
        )

@router.get("/definitions", response_model=list[MetricDefinition])
async def list_metric_definitions(
    metrics_service: MetricsService = Depends(get_metrics_service),
    current_user: User = Depends(get_current_user)
):
    """
    List all registered metric definitions.
    
    Returns a list of all metric definitions registered in the system,
    including system metrics and custom metrics.
    """
    logger.debug("Listing all metric definitions")
    try:
        definitions = await metrics_service.list_metric_definitions()
        return definitions
    except Exception as e:
        logger.error(f"Failed to list metric definitions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list metric definitions: {str(e)}"
        )

@router.get("/definitions/{name}", response_model=MetricDefinition)
async def get_metric_definition(
    name: str = Path(..., description="Name of the metric definition"),
    metrics_service: MetricsService = Depends(get_metrics_service),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific metric definition by name.
    
    Returns detailed information about a specific metric definition,
    including its type, unit, description, and retention policy.
    """
    logger.debug(f"Getting metric definition: {name}")
    try:
        definition = await metrics_service.get_metric_definition(name)
        if not definition:
            raise MetricNotFoundException(f"Metric definition '{name}' not found")
        return definition
    except MetricNotFoundException as e:
        logger.warning(f"Metric definition not found: {name}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get metric definition: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metric definition: {str(e)}"
        )

@router.delete("/definitions/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_metric_definition(
    name: str = Path(..., description="Name of the metric definition to delete"),
    metrics_service: MetricsService = Depends(get_metrics_service),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a metric definition.
    
    Permanently removes a metric definition and all its historical data.
    This operation cannot be undone.
    
    Requires admin permissions.
    """
    logger.debug(f"Deleting metric definition: {name}")
    
    # Check for admin permissions
    require_permissions(current_user, [Permission.ADMIN])
    
    try:
        await metrics_service.delete_metric_definition(name)
        return
    except MetricNotFoundException as e:
        logger.warning(f"Metric definition not found for deletion: {name}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to delete metric definition: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete metric definition: {str(e)}"
        )

@router.get("/data/{name}", response_model=MetricTimeseriesData)
async def get_metric_data(
    name: str = Path(..., description="Name of the metric to query"),
    start_time: Optional[datetime] = Query(None, description="Start time for the query range"),
    end_time: Optional[datetime] = Query(None, description="End time for the query range"),
    interval: str = Query("1m", description="Aggregation interval (e.g., '1m', '5m', '1h')"),
    aggregation: Optional[str] = Query(None, description="Aggregation method to use"),
    limit: int = Query(1000, description="Maximum number of data points to return"),
    labels: Optional[dict[str, str]] = Query(None, description="Filter by specific label values"),
    metrics_service: MetricsService = Depends(get_metrics_service),
    current_user: User = Depends(get_current_user)
):
    """
    Query time-series data for a specific metric.
    
    Returns time-series data for the specified metric, with options for:
    - Time range filtering
    - Aggregation method and interval
    - Label-based filtering
    - Limiting the number of data points
    
    If start_time is not provided, defaults to 24 hours ago.
    If end_time is not provided, defaults to current time.
    """
    logger.debug(f"Querying metric data for: {name}")
    
    # Set default time range if not provided
    if not end_time:
        end_time = datetime.utcnow()
    if not start_time:
        start_time = end_time - timedelta(days=1)
    
    try:
        data = await metrics_service.get_metric_data(
            name=name,
            start_time=start_time,
            end_time=end_time,
            interval=interval,
            aggregation=aggregation,
            limit=limit,
            labels=labels
        )
        return data
    except MetricNotFoundException as e:
        logger.warning(f"Metric not found: {name}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValueError as e:
        logger.warning(f"Invalid query parameters: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid query parameters: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to query metric data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query metric data: {str(e)}"
        )

@router.get("/summary/{name}", response_model=MetricSummary)
async def get_metric_summary(
    name: str = Path(..., description="Name of the metric to summarize"),
    period: str = Query("24h", description="Time period to summarize (e.g., '1h', '24h', '7d')"),
    metrics_service: MetricsService = Depends(get_metrics_service),
    current_user: User = Depends(get_current_user)
):
    """
    Get a statistical summary of a metric over a time period.
    
    Returns a summary of the metric including:
    - Min, max, average values
    - Percentiles (p50, p90, p95, p99)
    - Count of data points
    - Rate of change
    - Anomaly indicators
    
    The period parameter determines the time window to analyze.
    """
    logger.debug(f"Getting metric summary for {name} over period {period}")
    try:
        summary = await metrics_service.get_metric_summary(name=name, period=period)
        return summary
    except MetricNotFoundException as e:
        logger.warning(f"Metric not found for summary: {name}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValueError as e:
        logger.warning(f"Invalid period format: {period}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid period format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to get metric summary: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metric summary: {str(e)}"
        )

@router.get("/dashboard", response_model=dict[str, Any])
async def get_metrics_dashboard(
    dashboard_id: Optional[str] = Query(None, description="ID of a saved dashboard configuration"),
    metrics: Optional[list[str]] = Query(None, description="List of metrics to include"),
    period: str = Query("24h", description="Time period to analyze"),
    metrics_service: MetricsService = Depends(get_metrics_service),
    current_user: User = Depends(get_current_user)
):
    """
    Get a pre-configured dashboard of multiple metrics.
    
    Returns data for multiple metrics in a format suitable for dashboard visualization.
    Can either use a saved dashboard configuration or a custom list of metrics.
    
    This endpoint is optimized for populating monitoring dashboards with a single request.
    """
    logger.debug(f"Getting metrics dashboard{f' with ID: {dashboard_id}' if dashboard_id else ''}")
    
    try:
        dashboard_data = await metrics_service.get_metrics_dashboard(
            dashboard_id=dashboard_id,
            metrics=metrics,
            period=period
        )
        return dashboard_data
    except ValueError as e:
        logger.warning(f"Invalid dashboard parameters: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid dashboard parameters: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to get metrics dashboard: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics dashboard: {str(e)}"
        )

@router.get("/export", status_code=status.HTTP_200_OK)
async def export_metrics(
    metrics: list[str] = Query(..., description="List of metrics to export"),
    start_time: datetime = Query(..., description="Start time for export range"),
    end_time: datetime = Query(..., description="End time for export range"),
    format: str = Query("json", description="Export format (json, csv)"),
    metrics_service: MetricsService = Depends(get_metrics_service),
    current_user: User = Depends(get_current_user)
):
    """
    Export metric data for archiving or external analysis.
    
    Exports the specified metrics within the given time range in the requested format.
    Supports JSON and CSV formats.
    
    For large exports, this endpoint streams the response to avoid memory issues.
    """
    logger.debug(f"Exporting {len(metrics)} metrics from {start_time} to {end_time} in {format} format")
    
    # Validate format
    if format not in ["json", "csv"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported export format: {format}. Supported formats: json, csv"
        )
    
    try:
        # This would typically return a StreamingResponse for large datasets
        # but we'll return a simple JSONResponse for this implementation
        export_data = await metrics_service.export_metrics(
            metrics=metrics,
            start_time=start_time,
            end_time=end_time,
            format=format
        )
        
        return JSONResponse(
            content={"message": "Export successful", "data": export_data}
        )
    except Exception as e:
        logger.error(f"Failed to export metrics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export metrics: {str(e)}"
        )

@router.get("/alerts", status_code=status.HTTP_200_OK)
async def get_metric_alerts(
    status: Optional[str] = Query(None, description="Filter by alert status (active, resolved)"),
    severity: Optional[str] = Query(None, description="Filter by alert severity (info, warning, critical)"),
    metrics_service: MetricsService = Depends(get_metrics_service),
    current_user: User = Depends(get_current_user)
):
    """
    Get active or historical metric alerts.
    
    Returns alerts generated from metric thresholds and anomaly detection.
    Can be filtered by status and severity.
    
    This endpoint is useful for monitoring dashboards and alert management.
    """
    logger.debug(f"Getting metric alerts with filters: status={status}, severity={severity}")
    
    try:
        alerts = await metrics_service.get_metric_alerts(
            status=status,
            severity=severity
        )
        
        return JSONResponse(
            content={"alerts": alerts}
        )
    except ValueError as e:
        logger.warning(f"Invalid alert filter parameters: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid alert filter parameters: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to get metric alerts: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metric alerts: {str(e)}"
        )

@router.get("/", status_code=status.HTTP_200_OK)
async def get_metrics_overview(
    metrics_service: MetricsService = Depends(get_metrics_service),
    current_user: User = Depends(get_current_user)
):
    """
    Get a high-level overview of system metrics.
    
    Returns a summary of key metrics across all system components,
    providing a quick snapshot of system health and performance.
    
    This is useful as a landing page for monitoring dashboards.
    """
    logger.debug("Getting metrics overview")
    
    try:
        start_time = time.time()
        overview = await metrics_service.get_metrics_overview()
        
        # Add response time as a meta field
        overview["meta"] = {
            "response_time_ms": round((time.time() - start_time) * 1000, 2),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return JSONResponse(content=overview)
    except Exception as e:
        logger.error(f"Failed to get metrics overview: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics overview: {str(e)}"
        )