"""
Common Pydantic schemas for the NeuroCognitive Architecture (NCA) API.

This module provides reusable schema components that are shared across different
API endpoints in the NCA system. These include base models, common field types,
validation utilities, and response structures that ensure consistency throughout
the API layer.

Usage:
    from neuroca.api.schemas.common import (
        BaseResponse, PaginatedResponse, StatusEnum, 
        HealthStatus, TimeRange, ResourceID
    )
"""

import datetime
import enum
import logging
import uuid
from typing import Any, Generic, Optional, TypeVar

from pydantic import (
    BaseModel,
    Field,
    confloat,
    conint,
    constr,
    root_validator,
    validator,
)

# Configure module logger
logger = logging.getLogger(__name__)

# Type variable for generic models
T = TypeVar('T')


class StatusEnum(str, enum.Enum):
    """Common status values used across the system."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    FAILED = "failed"
    COMPLETED = "completed"
    PROCESSING = "processing"


class HealthStatusEnum(str, enum.Enum):
    """Health status indicators for system components."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ErrorSeverityEnum(str, enum.Enum):
    """Error severity levels for consistent error reporting."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ResourceID(BaseModel):
    """Standard resource identifier model."""
    id: uuid.UUID = Field(
        ...,
        description="Unique identifier for the resource",
        example="123e4567-e89b-12d3-a456-426614174000"
    )

    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }


class TimeRange(BaseModel):
    """Time range specification for queries and filters."""
    start_time: Optional[datetime.datetime] = Field(
        None,
        description="Start time of the range (inclusive)",
        example="2023-01-01T00:00:00Z"
    )
    end_time: Optional[datetime.datetime] = Field(
        None,
        description="End time of the range (inclusive)",
        example="2023-12-31T23:59:59Z"
    )

    @validator('end_time')
    def end_time_after_start_time(cls, v, values):
        """Validate that end_time is after start_time if both are provided."""
        if v and 'start_time' in values and values['start_time'] and v < values['start_time']:
            error_msg = "End time must be after start time"
            logger.error(f"Validation error: {error_msg}")
            raise ValueError(error_msg)
        return v

    class Config:
        schema_extra = {
            "example": {
                "start_time": "2023-01-01T00:00:00Z",
                "end_time": "2023-12-31T23:59:59Z"
            }
        }


class Pagination(BaseModel):
    """Standard pagination parameters."""
    page: int = Field(
        1,
        description="Page number (1-indexed)",
        ge=1
    )
    page_size: int = Field(
        50,
        description="Number of items per page",
        ge=1,
        le=1000
    )

    class Config:
        schema_extra = {
            "example": {
                "page": 1,
                "page_size": 50
            }
        }


class SortOrder(str, enum.Enum):
    """Sort order options."""
    ASC = "asc"
    DESC = "desc"


class SortParams(BaseModel):
    """Sorting parameters for list endpoints."""
    sort_by: str = Field(
        ...,
        description="Field to sort by"
    )
    order: SortOrder = Field(
        SortOrder.ASC,
        description="Sort order (ascending or descending)"
    )

    class Config:
        schema_extra = {
            "example": {
                "sort_by": "created_at",
                "order": "desc"
            }
        }


class BaseResponse(BaseModel):
    """Base response model for all API responses."""
    success: bool = Field(
        ...,
        description="Indicates if the request was successful"
    )
    message: Optional[str] = Field(
        None,
        description="Human-readable message about the response"
    )
    error_code: Optional[str] = Field(
        None,
        description="Error code for unsuccessful requests"
    )
    error_details: Optional[dict[str, Any]] = Field(
        None,
        description="Additional error details for debugging"
    )

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully"
            }
        }


class PaginatedResponse(BaseResponse, Generic[T]):
    """Generic paginated response model."""
    data: list[T] = Field(
        ...,
        description="List of items in the current page"
    )
    total: int = Field(
        ...,
        description="Total number of items across all pages",
        ge=0
    )
    page: int = Field(
        ...,
        description="Current page number",
        ge=1
    )
    page_size: int = Field(
        ...,
        description="Number of items per page",
        ge=1
    )
    total_pages: int = Field(
        ...,
        description="Total number of pages",
        ge=0
    )
    has_next: bool = Field(
        ...,
        description="Whether there is a next page"
    )
    has_prev: bool = Field(
        ...,
        description="Whether there is a previous page"
    )

    @root_validator
    def calculate_pagination_fields(cls, values):
        """Calculate derived pagination fields."""
        total = values.get('total', 0)
        page_size = values.get('page_size', 1)
        page = values.get('page', 1)
        
        # Calculate total pages
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        values['total_pages'] = total_pages
        
        # Determine if there are next/previous pages
        values['has_next'] = page < total_pages
        values['has_prev'] = page > 1
        
        return values

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Items retrieved successfully",
                "data": [{"id": "123e4567-e89b-12d3-a456-426614174000", "name": "Example Item"}],
                "total": 100,
                "page": 1,
                "page_size": 10,
                "total_pages": 10,
                "has_next": True,
                "has_prev": False
            }
        }


class DataResponse(BaseResponse, Generic[T]):
    """Generic data response model for single resource operations."""
    data: T = Field(
        ...,
        description="Response data"
    )

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Resource retrieved successfully",
                "data": {"id": "123e4567-e89b-12d3-a456-426614174000", "name": "Example Resource"}
            }
        }


class ErrorResponse(BaseResponse):
    """Detailed error response model."""
    success: bool = Field(
        False,
        description="Always false for error responses"
    )
    error_code: str = Field(
        ...,
        description="Machine-readable error code"
    )
    message: str = Field(
        ...,
        description="Human-readable error message"
    )
    severity: ErrorSeverityEnum = Field(
        ErrorSeverityEnum.ERROR,
        description="Error severity level"
    )
    request_id: Optional[str] = Field(
        None,
        description="Request identifier for tracing"
    )
    timestamp: datetime.datetime = Field(
        default_factory=datetime.datetime.utcnow,
        description="Time when the error occurred (UTC)"
    )

    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "error_code": "RESOURCE_NOT_FOUND",
                "message": "The requested resource could not be found",
                "severity": "error",
                "request_id": "req-123456",
                "timestamp": "2023-06-15T10:30:45Z",
                "error_details": {
                    "resource_type": "User",
                    "resource_id": "123e4567-e89b-12d3-a456-426614174000"
                }
            }
        }


class HealthStatus(BaseModel):
    """Health status information for system components."""
    component: str = Field(
        ...,
        description="Name of the system component"
    )
    status: HealthStatusEnum = Field(
        ...,
        description="Current health status"
    )
    message: Optional[str] = Field(
        None,
        description="Additional information about the health status"
    )
    last_checked: datetime.datetime = Field(
        default_factory=datetime.datetime.utcnow,
        description="Time when the health was last checked"
    )
    metrics: Optional[dict[str, Any]] = Field(
        None,
        description="Component-specific health metrics"
    )

    class Config:
        schema_extra = {
            "example": {
                "component": "database",
                "status": "healthy",
                "message": "All database connections operational",
                "last_checked": "2023-06-15T10:30:45Z",
                "metrics": {
                    "connection_pool_usage": 0.25,
                    "query_latency_ms": 5.2
                }
            }
        }


class SystemHealthResponse(BaseResponse):
    """Overall system health response."""
    status: HealthStatusEnum = Field(
        ...,
        description="Overall system health status"
    )
    components: list[HealthStatus] = Field(
        ...,
        description="Health status of individual components"
    )
    timestamp: datetime.datetime = Field(
        default_factory=datetime.datetime.utcnow,
        description="Time when the health check was performed"
    )

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "System health check completed",
                "status": "healthy",
                "components": [
                    {
                        "component": "database",
                        "status": "healthy",
                        "message": "All database connections operational",
                        "last_checked": "2023-06-15T10:30:45Z"
                    },
                    {
                        "component": "memory_service",
                        "status": "healthy",
                        "message": "Memory service responding normally",
                        "last_checked": "2023-06-15T10:30:40Z"
                    }
                ],
                "timestamp": "2023-06-15T10:30:45Z"
            }
        }


# Common field validators and constraints

def validate_name(name: str) -> str:
    """Validate a name field for common requirements."""
    if not name or name.strip() == "":
        raise ValueError("Name cannot be empty")
    
    if len(name) > 255:
        raise ValueError("Name cannot exceed 255 characters")
    
    return name.strip()


# Common field types with validation
NameStr = constr(strip_whitespace=True, min_length=1, max_length=255)
DescriptionStr = constr(strip_whitespace=True, max_length=2000)
SlugStr = constr(regex=r'^[a-z0-9]+(?:-[a-z0-9]+)*$', min_length=1, max_length=100)
PositiveInt = conint(ge=0)
PositiveFloat = confloat(ge=0.0)
PercentageFloat = confloat(ge=0.0, le=100.0)
NormalizedFloat = confloat(ge=0.0, le=1.0)

# Common regex patterns
EMAIL_PATTERN = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
PHONE_PATTERN = r'^\+?[1-9]\d{1,14}$'  # E.164 format
USERNAME_PATTERN = r'^[a-zA-Z0-9_-]{3,50}$'

# Common timestamp fields
class TimestampMixin(BaseModel):
    """Mixin for common timestamp fields."""
    created_at: datetime.datetime = Field(
        default_factory=datetime.datetime.utcnow,
        description="Time when the resource was created"
    )
    updated_at: Optional[datetime.datetime] = Field(
        None,
        description="Time when the resource was last updated"
    )

    @validator('updated_at')
    def updated_after_created(cls, v, values):
        """Validate that updated_at is after created_at if both are provided."""
        if v and 'created_at' in values and values['created_at'] and v < values['created_at']:
            raise ValueError("Updated time cannot be before creation time")
        return v


class AuditMixin(TimestampMixin):
    """Mixin for audit fields."""
    created_by: Optional[uuid.UUID] = Field(
        None,
        description="ID of the user who created the resource"
    )
    updated_by: Optional[uuid.UUID] = Field(
        None,
        description="ID of the user who last updated the resource"
    )