"""
Response Schema Definitions for NeuroCognitive Architecture API

This module defines standardized response schemas for the NeuroCognitive Architecture API.
These schemas ensure consistent response formats across all API endpoints, making the API
more predictable and easier to consume for clients.

The module includes:
- Base response schemas that all responses inherit from
- Success response schemas for different data types
- Error response schemas with standardized error codes and messages
- Pagination support for list responses
- Health and status response schemas

Usage:
    from neuroca.api.schemas.responses import (
        SuccessResponse, ErrorResponse, PaginatedResponse
    )

    @app.get("/example", response_model=SuccessResponse[ExampleModel])
    def get_example():
        return SuccessResponse(data=example_data)
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field, validator

# Configure logger
logger = logging.getLogger(__name__)

# Type variable for generic response types
T = TypeVar('T')


class ResponseStatus(str, Enum):
    """Enumeration of possible response status values."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


class ErrorCode(str, Enum):
    """Standardized error codes for API responses."""
    # General errors
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # Memory-related errors
    MEMORY_ACCESS_ERROR = "MEMORY_ACCESS_ERROR"
    MEMORY_STORAGE_ERROR = "MEMORY_STORAGE_ERROR"
    MEMORY_RETRIEVAL_ERROR = "MEMORY_RETRIEVAL_ERROR"
    
    # LLM integration errors
    LLM_CONNECTION_ERROR = "LLM_CONNECTION_ERROR"
    LLM_RESPONSE_ERROR = "LLM_RESPONSE_ERROR"
    LLM_TIMEOUT_ERROR = "LLM_TIMEOUT_ERROR"
    
    # Health-related errors
    HEALTH_CHECK_FAILED = "HEALTH_CHECK_FAILED"
    RESOURCE_EXHAUSTED = "RESOURCE_EXHAUSTED"
    
    # Data processing errors
    DATA_PROCESSING_ERROR = "DATA_PROCESSING_ERROR"
    INVALID_FORMAT = "INVALID_FORMAT"


class BaseResponse(BaseModel):
    """Base response model that all API responses inherit from."""
    status: ResponseStatus = Field(
        ..., 
        description="Response status indicating success, error, or warning"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when the response was generated"
    )
    
    class Config:
        """Pydantic configuration for the BaseResponse model."""
        json_encoders = {
            datetime: lambda dt: dt.isoformat() + "Z"
        }


class MetaData(BaseModel):
    """Metadata for responses, including processing information."""
    request_id: Optional[str] = Field(
        None, 
        description="Unique identifier for the request for tracing purposes"
    )
    processing_time_ms: Optional[float] = Field(
        None, 
        description="Time taken to process the request in milliseconds"
    )
    version: Optional[str] = Field(
        None, 
        description="API version used for the request"
    )


class ErrorDetail(BaseModel):
    """Detailed error information for error responses."""
    code: ErrorCode = Field(
        ..., 
        description="Standardized error code"
    )
    message: str = Field(
        ..., 
        description="Human-readable error message"
    )
    field: Optional[str] = Field(
        None, 
        description="Field that caused the error, if applicable"
    )
    details: Optional[dict[str, Any]] = Field(
        None, 
        description="Additional error details"
    )


class SuccessResponse(BaseResponse, Generic[T]):
    """
    Standard success response model with generic data type.
    
    This model is used for all successful API responses, with the data field
    containing the actual response data of type T.
    """
    status: ResponseStatus = ResponseStatus.SUCCESS
    data: T = Field(..., description="Response data")
    meta: Optional[MetaData] = Field(
        None, 
        description="Optional metadata about the response"
    )
    
    @validator('status')
    def validate_status(cls, v):
        """Ensure status is always 'success' for SuccessResponse."""
        if v != ResponseStatus.SUCCESS:
            logger.warning(f"SuccessResponse initialized with non-success status: {v}")
            return ResponseStatus.SUCCESS
        return v


class ErrorResponse(BaseResponse):
    """
    Standard error response model.
    
    This model is used for all error responses, with standardized error codes
    and detailed error information.
    """
    status: ResponseStatus = ResponseStatus.ERROR
    error: ErrorDetail = Field(..., description="Error details")
    meta: Optional[MetaData] = Field(
        None, 
        description="Optional metadata about the response"
    )
    
    @validator('status')
    def validate_status(cls, v):
        """Ensure status is always 'error' for ErrorResponse."""
        if v != ResponseStatus.ERROR:
            logger.warning(f"ErrorResponse initialized with non-error status: {v}")
            return ResponseStatus.ERROR
        return v
    
    @classmethod
    def create(cls, code: ErrorCode, message: str, field: Optional[str] = None, 
               details: Optional[dict[str, Any]] = None, meta: Optional[MetaData] = None) -> 'ErrorResponse':
        """
        Factory method to create an ErrorResponse with the given parameters.
        
        Args:
            code: The error code
            message: Human-readable error message
            field: Optional field that caused the error
            details: Optional additional error details
            meta: Optional metadata
            
        Returns:
            An ErrorResponse instance
        """
        error_detail = ErrorDetail(code=code, message=message, field=field, details=details)
        return cls(error=error_detail, meta=meta)


class PaginationInfo(BaseModel):
    """Pagination information for paginated responses."""
    page: int = Field(..., description="Current page number (1-based)")
    page_size: int = Field(..., description="Number of items per page")
    total_items: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")
    
    @validator('page')
    def validate_page(cls, v):
        """Ensure page is at least 1."""
        if v < 1:
            raise ValueError("Page must be at least 1")
        return v
    
    @validator('page_size')
    def validate_page_size(cls, v):
        """Ensure page_size is at least 1."""
        if v < 1:
            raise ValueError("Page size must be at least 1")
        return v
    
    @validator('total_pages')
    def calculate_total_pages(cls, v, values):
        """Validate total_pages or calculate it if not provided."""
        if 'total_items' in values and 'page_size' in values:
            page_size = values['page_size']
            total_items = values['total_items']
            calculated = (total_items + page_size - 1) // page_size  # Ceiling division
            if v != calculated:
                logger.warning(f"Provided total_pages {v} doesn't match calculated value {calculated}")
                return calculated
        return v
    
    @validator('has_next')
    def calculate_has_next(cls, v, values):
        """Validate has_next or calculate it if not provided."""
        if all(k in values for k in ['page', 'total_pages']):
            calculated = values['page'] < values['total_pages']
            if v != calculated:
                logger.warning(f"Provided has_next {v} doesn't match calculated value {calculated}")
                return calculated
        return v
    
    @validator('has_prev')
    def calculate_has_prev(cls, v, values):
        """Validate has_prev or calculate it if not provided."""
        if 'page' in values:
            calculated = values['page'] > 1
            if v != calculated:
                logger.warning(f"Provided has_prev {v} doesn't match calculated value {calculated}")
                return calculated
        return v


class PaginatedResponse(SuccessResponse, Generic[T]):
    """
    Response model for paginated data.
    
    This model extends SuccessResponse to include pagination information.
    """
    data: list[T] = Field(..., description="List of items for the current page")
    pagination: PaginationInfo = Field(..., description="Pagination information")


class HealthStatus(str, Enum):
    """Enumeration of possible health status values."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth(BaseModel):
    """Health information for a specific system component."""
    status: HealthStatus = Field(..., description="Health status of the component")
    name: str = Field(..., description="Component name")
    message: Optional[str] = Field(None, description="Additional health information")
    last_check: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the component was last checked"
    )
    metrics: Optional[dict[str, Any]] = Field(
        None, 
        description="Component-specific metrics"
    )


class HealthResponse(SuccessResponse):
    """
    Response model for health check endpoints.
    
    This model provides detailed health information about the system and its components.
    """
    data: dict[str, Any] = Field(
        ..., 
        description="Health check data"
    )
    overall_status: HealthStatus = Field(
        ..., 
        description="Overall system health status"
    )
    components: list[ComponentHealth] = Field(
        ..., 
        description="Health status of individual components"
    )
    
    @validator('overall_status', pre=True)
    def calculate_overall_status(cls, v, values):
        """
        Calculate overall status based on component statuses if not explicitly provided.
        
        The system is:
        - UNHEALTHY if any component is UNHEALTHY
        - DEGRADED if any component is DEGRADED and none are UNHEALTHY
        - HEALTHY if all components are HEALTHY
        """
        if 'components' in values:
            components = values['components']
            if any(c.status == HealthStatus.UNHEALTHY for c in components):
                return HealthStatus.UNHEALTHY
            elif any(c.status == HealthStatus.DEGRADED for c in components):
                return HealthStatus.DEGRADED
            else:
                return HealthStatus.HEALTHY
        return v


class EmptyResponse(SuccessResponse):
    """
    Response model for endpoints that don't return data.
    
    This model is used for operations like DELETE that successfully complete
    but don't have meaningful return data.
    """
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Empty data object"
    )


class WarningResponse(BaseResponse, Generic[T]):
    """
    Response model for successful operations with warnings.
    
    This model is used when an operation succeeds but there are non-critical issues
    that the client should be aware of.
    """
    status: ResponseStatus = ResponseStatus.WARNING
    data: T = Field(..., description="Response data")
    warnings: list[str] = Field(..., description="List of warning messages")
    meta: Optional[MetaData] = Field(
        None, 
        description="Optional metadata about the response"
    )
    
    @validator('status')
    def validate_status(cls, v):
        """Ensure status is always 'warning' for WarningResponse."""
        if v != ResponseStatus.WARNING:
            logger.warning(f"WarningResponse initialized with non-warning status: {v}")
            return ResponseStatus.WARNING
        return v


class BatchOperationResult(BaseModel):
    """
    Result of a single operation in a batch request.
    
    This model is used to represent the result of each individual operation
    in a batch request, including success/failure status and relevant data.
    """
    success: bool = Field(..., description="Whether the operation succeeded")
    data: Optional[Any] = Field(None, description="Operation result data if successful")
    error: Optional[ErrorDetail] = Field(None, description="Error details if failed")
    
    @validator('error')
    def validate_error_presence(cls, v, values):
        """Ensure error is present only for failed operations."""
        if 'success' in values:
            if values['success'] and v is not None:
                raise ValueError("Error should not be present for successful operations")
            elif not values['success'] and v is None:
                raise ValueError("Error must be present for failed operations")
        return v


class BatchResponse(SuccessResponse):
    """
    Response model for batch operations.
    
    This model is used for endpoints that process multiple operations in a single request,
    providing results for each individual operation.
    """
    data: list[BatchOperationResult] = Field(
        ..., 
        description="Results of individual operations in the batch"
    )
    summary: dict[str, Any] = Field(
        default_factory=lambda: {"total": 0, "succeeded": 0, "failed": 0},
        description="Summary of batch operation results"
    )
    
    @validator('summary', always=True)
    def calculate_summary(cls, v, values):
        """Calculate summary statistics based on operation results."""
        if 'data' in values:
            results = values['data']
            total = len(results)
            succeeded = sum(1 for r in results if r.success)
            failed = total - succeeded
            
            return {
                "total": total,
                "succeeded": succeeded,
                "failed": failed,
                "success_rate": succeeded / total if total > 0 else 0
            }
        return v