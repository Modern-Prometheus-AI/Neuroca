"""
Memory API Routes Module

This module defines the FastAPI routes for interacting with the NeuroCognitive Architecture's
memory system. It provides endpoints for creating, retrieving, updating, and deleting
memories across all three memory tiers (working, episodic, and semantic).

The routes implement the RESTful API design pattern and include comprehensive validation,
error handling, and logging. Authentication and authorization are enforced for all endpoints.

Usage:
    These routes are automatically registered with the main FastAPI application
    and are available under the /api/memory prefix.

Security:
    All routes require authentication via JWT tokens.
    Authorization is checked for each memory operation.
"""

from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status
from fastapi.responses import JSONResponse

from neuroca.api.auth.dependencies import get_current_user
from neuroca.api.models.memory import (
    MemoryCreate,
    MemoryResponse,
    MemorySearchParams,
    MemoryTier,
    MemoryUpdate,
)
from neuroca.api.models.user import User
from neuroca.core.exceptions import (
    MemoryAccessDeniedError,
    MemoryNotFoundError,
    MemoryStorageError,
    MemoryTierFullError,
)
from neuroca.core.logging import get_logger
from neuroca.memory.service import MemoryService

# Initialize router with prefix and tags for OpenAPI documentation
router = APIRouter(
    prefix="/memory",
    tags=["memory"],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Memory not found"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_403_FORBIDDEN: {"description": "Forbidden"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
    },
)

# Initialize logger
logger = get_logger(__name__)

# Dependency to get memory service
async def get_memory_service() -> MemoryService:
    """Dependency to get the memory service instance."""
    return MemoryService()

@router.post(
    "/",
    response_model=MemoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new memory",
    description="Creates a new memory in the specified memory tier."
)
async def create_memory(
    memory: MemoryCreate = Body(..., description="Memory data to create"),
    current_user: User = Depends(get_current_user),
    memory_service: MemoryService = Depends(get_memory_service)
) -> MemoryResponse:
    """
    Create a new memory in the specified memory tier.
    
    Args:
        memory: The memory data to create
        current_user: The authenticated user
        memory_service: The memory service instance
        
    Returns:
        The created memory with its ID and metadata
        
    Raises:
        HTTPException: If the memory creation fails or validation errors occur
    """
    logger.debug(f"User {current_user.id} creating memory in {memory.tier} tier")
    
    try:
        # Associate the memory with the current user
        memory_with_user = memory.dict()
        memory_with_user["user_id"] = current_user.id
        
        # Create the memory using the service
        created_memory = await memory_service.create_memory(memory_with_user)
        
        logger.info(f"Memory created successfully: {created_memory.id}")
        return created_memory
        
    except MemoryTierFullError as e:
        logger.warning(f"Memory tier full error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Memory tier is full: {str(e)}"
        )
    except MemoryStorageError as e:
        logger.error(f"Memory storage error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store memory: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Unexpected error creating memory: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the memory"
        )

@router.get(
    "/{memory_id}",
    response_model=MemoryResponse,
    summary="Get a specific memory by ID",
    description="Retrieves a specific memory by its unique identifier."
)
async def get_memory(
    memory_id: UUID = Path(..., description="The ID of the memory to retrieve"),
    current_user: User = Depends(get_current_user),
    memory_service: MemoryService = Depends(get_memory_service)
) -> MemoryResponse:
    """
    Retrieve a specific memory by its ID.
    
    Args:
        memory_id: The unique identifier of the memory
        current_user: The authenticated user
        memory_service: The memory service instance
        
    Returns:
        The requested memory if found
        
    Raises:
        HTTPException: If the memory is not found or the user doesn't have access
    """
    logger.debug(f"User {current_user.id} retrieving memory {memory_id}")
    
    try:
        memory = await memory_service.get_memory(memory_id)
        
        # Check if the user has access to this memory
        if memory.user_id != current_user.id and not current_user.is_admin:
            logger.warning(f"User {current_user.id} attempted to access memory {memory_id} without permission")
            raise MemoryAccessDeniedError("You don't have permission to access this memory")
            
        logger.info(f"Memory {memory_id} retrieved successfully")
        return memory
        
    except MemoryNotFoundError:
        logger.warning(f"Memory {memory_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory with ID {memory_id} not found"
        )
    except MemoryAccessDeniedError as e:
        logger.warning(f"Access denied: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Unexpected error retrieving memory {memory_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving the memory"
        )

@router.get(
    "/",
    response_model=list[MemoryResponse],
    summary="List memories",
    description="Retrieves a list of memories based on the provided filters."
)
async def list_memories(
    tier: Optional[MemoryTier] = Query(None, description="Filter by memory tier"),
    query: Optional[str] = Query(None, description="Search query for memory content"),
    tags: Optional[list[str]] = Query(None, description="Filter by tags"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of memories to return"),
    offset: int = Query(0, ge=0, description="Number of memories to skip"),
    current_user: User = Depends(get_current_user),
    memory_service: MemoryService = Depends(get_memory_service)
) -> list[MemoryResponse]:
    """
    List memories with optional filtering.
    
    Args:
        tier: Optional filter by memory tier
        query: Optional search query for memory content
        tags: Optional filter by tags
        limit: Maximum number of memories to return (pagination)
        offset: Number of memories to skip (pagination)
        current_user: The authenticated user
        memory_service: The memory service instance
        
    Returns:
        A list of memories matching the filters
        
    Raises:
        HTTPException: If an error occurs during retrieval
    """
    logger.debug(f"User {current_user.id} listing memories with filters: tier={tier}, query={query}, tags={tags}")
    
    try:
        # Create search parameters
        search_params = MemorySearchParams(
            user_id=current_user.id,
            tier=tier,
            query=query,
            tags=tags,
            limit=limit,
            offset=offset
        )
        
        memories = await memory_service.list_memories(search_params)
        logger.info(f"Retrieved {len(memories)} memories for user {current_user.id}")
        return memories
        
    except Exception as e:
        logger.exception(f"Error listing memories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving memories"
        )

@router.put(
    "/{memory_id}",
    response_model=MemoryResponse,
    summary="Update a memory",
    description="Updates an existing memory with new data."
)
async def update_memory(
    memory_id: UUID = Path(..., description="The ID of the memory to update"),
    memory_update: MemoryUpdate = Body(..., description="Updated memory data"),
    current_user: User = Depends(get_current_user),
    memory_service: MemoryService = Depends(get_memory_service)
) -> MemoryResponse:
    """
    Update an existing memory.
    
    Args:
        memory_id: The unique identifier of the memory to update
        memory_update: The updated memory data
        current_user: The authenticated user
        memory_service: The memory service instance
        
    Returns:
        The updated memory
        
    Raises:
        HTTPException: If the memory is not found, the user doesn't have access, or other errors occur
    """
    logger.debug(f"User {current_user.id} updating memory {memory_id}")
    
    try:
        # First check if the memory exists and the user has access
        existing_memory = await memory_service.get_memory(memory_id)
        
        if existing_memory.user_id != current_user.id and not current_user.is_admin:
            logger.warning(f"User {current_user.id} attempted to update memory {memory_id} without permission")
            raise MemoryAccessDeniedError("You don't have permission to update this memory")
        
        # Update the memory
        updated_memory = await memory_service.update_memory(memory_id, memory_update.dict(exclude_unset=True))
        
        logger.info(f"Memory {memory_id} updated successfully")
        return updated_memory
        
    except MemoryNotFoundError:
        logger.warning(f"Memory {memory_id} not found for update")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory with ID {memory_id} not found"
        )
    except MemoryAccessDeniedError as e:
        logger.warning(f"Access denied for update: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except MemoryStorageError as e:
        logger.error(f"Memory storage error during update: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update memory: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Unexpected error updating memory {memory_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while updating the memory"
        )

@router.delete(
    "/{memory_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a memory",
    description="Deletes a memory by its ID."
)
async def delete_memory(
    memory_id: UUID = Path(..., description="The ID of the memory to delete"),
    current_user: User = Depends(get_current_user),
    memory_service: MemoryService = Depends(get_memory_service)
):
    """
    Delete a memory by its ID.
    
    Args:
        memory_id: The unique identifier of the memory to delete
        current_user: The authenticated user
        memory_service: The memory service instance
        
    Returns:
        204 No Content on successful deletion
        
    Raises:
        HTTPException: If the memory is not found, the user doesn't have access, or other errors occur
    """
    logger.debug(f"User {current_user.id} deleting memory {memory_id}")
    
    try:
        # First check if the memory exists and the user has access
        existing_memory = await memory_service.get_memory(memory_id)
        
        if existing_memory.user_id != current_user.id and not current_user.is_admin:
            logger.warning(f"User {current_user.id} attempted to delete memory {memory_id} without permission")
            raise MemoryAccessDeniedError("You don't have permission to delete this memory")
        
        # Delete the memory
        await memory_service.delete_memory(memory_id)
        
        logger.info(f"Memory {memory_id} deleted successfully")
        return
        
    except MemoryNotFoundError:
        logger.warning(f"Memory {memory_id} not found for deletion")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory with ID {memory_id} not found"
        )
    except MemoryAccessDeniedError as e:
        logger.warning(f"Access denied for deletion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Unexpected error deleting memory {memory_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while deleting the memory"
        )

@router.post(
    "/transfer",
    response_model=MemoryResponse,
    summary="Transfer memory between tiers",
    description="Transfers a memory from one tier to another."
)
async def transfer_memory(
    memory_id: UUID = Body(..., description="The ID of the memory to transfer"),
    target_tier: MemoryTier = Body(..., description="The target memory tier"),
    current_user: User = Depends(get_current_user),
    memory_service: MemoryService = Depends(get_memory_service)
) -> MemoryResponse:
    """
    Transfer a memory from one tier to another.
    
    Args:
        memory_id: The unique identifier of the memory to transfer
        target_tier: The target memory tier to transfer to
        current_user: The authenticated user
        memory_service: The memory service instance
        
    Returns:
        The transferred memory with updated tier information
        
    Raises:
        HTTPException: If the memory is not found, the user doesn't have access, or other errors occur
    """
    logger.debug(f"User {current_user.id} transferring memory {memory_id} to {target_tier} tier")
    
    try:
        # First check if the memory exists and the user has access
        existing_memory = await memory_service.get_memory(memory_id)
        
        if existing_memory.user_id != current_user.id and not current_user.is_admin:
            logger.warning(f"User {current_user.id} attempted to transfer memory {memory_id} without permission")
            raise MemoryAccessDeniedError("You don't have permission to transfer this memory")
        
        # Check if the memory is already in the target tier
        if existing_memory.tier == target_tier:
            logger.info(f"Memory {memory_id} is already in {target_tier} tier")
            return existing_memory
        
        # Transfer the memory
        transferred_memory = await memory_service.transfer_memory(memory_id, target_tier)
        
        logger.info(f"Memory {memory_id} transferred successfully to {target_tier} tier")
        return transferred_memory
        
    except MemoryNotFoundError:
        logger.warning(f"Memory {memory_id} not found for transfer")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory with ID {memory_id} not found"
        )
    except MemoryAccessDeniedError as e:
        logger.warning(f"Access denied for transfer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except MemoryTierFullError as e:
        logger.warning(f"Target tier full error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Target memory tier is full: {str(e)}"
        )
    except MemoryStorageError as e:
        logger.error(f"Memory storage error during transfer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to transfer memory: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Unexpected error transferring memory {memory_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while transferring the memory"
        )

@router.post(
    "/consolidate",
    response_model=list[MemoryResponse],
    summary="Consolidate memories",
    description="Consolidates multiple memories into a new semantic memory."
)
async def consolidate_memories(
    memory_ids: list[UUID] = Body(..., description="List of memory IDs to consolidate"),
    summary: str = Body(..., description="Summary of the consolidated memory"),
    tags: Optional[list[str]] = Body(None, description="Tags for the consolidated memory"),
    current_user: User = Depends(get_current_user),
    memory_service: MemoryService = Depends(get_memory_service)
) -> list[MemoryResponse]:
    """
    Consolidate multiple memories into a new semantic memory.
    
    Args:
        memory_ids: List of memory IDs to consolidate
        summary: Summary of the consolidated memory
        tags: Optional tags for the consolidated memory
        current_user: The authenticated user
        memory_service: The memory service instance
        
    Returns:
        List containing the new consolidated memory and the original memories
        
    Raises:
        HTTPException: If memories are not found, the user doesn't have access, or other errors occur
    """
    logger.debug(f"User {current_user.id} consolidating memories: {memory_ids}")
    
    if len(memory_ids) < 2:
        logger.warning("Attempted to consolidate fewer than 2 memories")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 2 memories must be provided for consolidation"
        )
    
    try:
        # Check if all memories exist and the user has access to all of them
        for memory_id in memory_ids:
            memory = await memory_service.get_memory(memory_id)
            if memory.user_id != current_user.id and not current_user.is_admin:
                logger.warning(f"User {current_user.id} attempted to consolidate memory {memory_id} without permission")
                raise MemoryAccessDeniedError(f"You don't have permission to access memory {memory_id}")
        
        # Consolidate the memories
        consolidated_result = await memory_service.consolidate_memories(
            memory_ids=memory_ids,
            user_id=current_user.id,
            summary=summary,
            tags=tags or []
        )
        
        logger.info(f"Successfully consolidated {len(memory_ids)} memories into new memory {consolidated_result[0].id}")
        return consolidated_result
        
    except MemoryNotFoundError as e:
        logger.warning(f"Memory not found during consolidation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except MemoryAccessDeniedError as e:
        logger.warning(f"Access denied during consolidation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except MemoryTierFullError as e:
        logger.warning(f"Semantic tier full during consolidation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Semantic memory tier is full: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Unexpected error during memory consolidation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during memory consolidation"
        )

@router.get(
    "/stats",
    response_model=dict[str, Any],
    summary="Get memory statistics",
    description="Retrieves statistics about the user's memory usage across tiers."
)
async def get_memory_stats(
    current_user: User = Depends(get_current_user),
    memory_service: MemoryService = Depends(get_memory_service)
) -> dict[str, Any]:
    """
    Get statistics about the user's memory usage.
    
    Args:
        current_user: The authenticated user
        memory_service: The memory service instance
        
    Returns:
        Dictionary containing memory statistics
        
    Raises:
        HTTPException: If an error occurs while retrieving statistics
    """
    logger.debug(f"User {current_user.id} retrieving memory statistics")
    
    try:
        stats = await memory_service.get_memory_stats(current_user.id)
        logger.info(f"Retrieved memory statistics for user {current_user.id}")
        return stats
        
    except Exception as e:
        logger.exception(f"Error retrieving memory statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving memory statistics"
        )

@router.post(
    "/health-check",
    status_code=status.HTTP_200_OK,
    summary="Memory system health check",
    description="Performs a health check on the memory system."
)
async def memory_health_check(
    current_user: User = Depends(get_current_user),
    memory_service: MemoryService = Depends(get_memory_service)
) -> JSONResponse:
    """
    Perform a health check on the memory system.
    
    Args:
        current_user: The authenticated user (must be admin)
        memory_service: The memory service instance
        
    Returns:
        Health status of the memory system
        
    Raises:
        HTTPException: If the user is not an admin or if the health check fails
    """
    logger.debug(f"User {current_user.id} requesting memory system health check")
    
    # Only admins can perform health checks
    if not current_user.is_admin:
        logger.warning(f"Non-admin user {current_user.id} attempted to perform memory health check")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can perform health checks"
        )
    
    try:
        health_status = await memory_service.health_check()
        logger.info("Memory system health check completed successfully")
        return JSONResponse(content=health_status)
        
    except Exception as e:
        logger.exception(f"Memory system health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Memory system health check failed: {str(e)}"
        )