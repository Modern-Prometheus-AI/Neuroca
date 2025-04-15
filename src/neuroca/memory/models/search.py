"""
Memory Search Models

This module defines data models related to memory search operations,
including search criteria, options, and results.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

from neuroca.memory.models.memory_item import MemoryItem


class SearchSortField(str, Enum):
    """Fields that can be used for sorting search results."""
    
    RELEVANCE = "relevance"  # Sort by relevance score (default for searches)
    CREATED_AT = "created_at"  # Sort by creation time
    LAST_ACCESSED = "last_accessed"  # Sort by last access time
    IMPORTANCE = "importance"  # Sort by importance score
    STRENGTH = "strength"  # Sort by memory strength


class SearchSortOrder(str, Enum):
    """Sort order for search results."""
    
    ASCENDING = "asc"
    DESCENDING = "desc"


class MemorySearchOptions(BaseModel):
    """
    Options for memory search operations.
    
    This model defines parameters that control how memory search
    is performed, including filtering, sorting, and pagination.
    """
    
    # Basic search parameters
    query: Optional[str] = None  # Text query string
    embedding: Optional[List[float]] = None  # Vector embedding for similarity search
    
    # Filter parameters
    tags: Optional[List[str]] = None  # Filter by tags (any match)
    require_all_tags: bool = False  # If True, all tags must match
    metadata_filters: Dict[str, Any] = Field(default_factory=dict)  # Filter by metadata fields
    tiers: Optional[List[str]] = None  # Filter by memory tiers
    status: Optional[List[str]] = None  # Filter by memory status
    created_after: Optional[datetime] = None  # Filter by creation time
    created_before: Optional[datetime] = None  # Filter by creation time
    accessed_after: Optional[datetime] = None  # Filter by last access time
    accessed_before: Optional[datetime] = None  # Filter by last access time
    min_importance: Optional[float] = None  # Filter by minimum importance
    min_strength: Optional[float] = None  # Filter by minimum strength
    
    # Sorting parameters
    sort_by: SearchSortField = SearchSortField.RELEVANCE  # Field to sort by
    sort_order: SearchSortOrder = SearchSortOrder.DESCENDING  # Sort order
    
    # Pagination parameters
    limit: int = Field(default=10, ge=1, le=100)  # Maximum number of results
    offset: int = Field(default=0, ge=0)  # Number of results to skip
    
    # Search behavior parameters
    min_relevance: float = Field(default=0.0, ge=0.0, le=1.0)  # Minimum relevance score
    include_content: bool = True  # Include full content in results
    include_metadata: bool = True  # Include full metadata in results
    include_embedding: bool = False  # Include embeddings in results
    
    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        """Override dict() to handle enum values and empty fields."""
        result = super().dict(*args, **kwargs)
        
        # Convert enum values to strings
        if "sort_by" in result and isinstance(result["sort_by"], SearchSortField):
            result["sort_by"] = result["sort_by"].value
        
        if "sort_order" in result and isinstance(result["sort_order"], SearchSortOrder):
            result["sort_order"] = result["sort_order"].value
        
        # Remove None values to save space
        return {k: v for k, v in result.items() if v is not None}


class MemorySearchResult(BaseModel):
    """
    Result from a memory search operation.
    
    This model represents a single result from a memory search,
    including the memory item and its relevance score.
    """
    
    # The memory item
    memory: MemoryItem
    
    # Search-specific fields
    relevance: float = Field(default=1.0, ge=0.0, le=1.0)  # Relevance score
    tier: str  # Tier where the memory was found
    rank: Optional[int] = None  # Rank in the result set (1-based)
    
    # For vector searches
    similarity: Optional[float] = None  # Similarity score (for vector searches)
    distance: Optional[float] = None  # Distance score (for vector searches)
    
    @validator("memory", pre=True)
    def validate_memory(cls, v):
        """Ensure memory is a MemoryItem object."""
        if isinstance(v, dict):
            return MemoryItem(**v)
        return v
    
    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        """Override dict() to handle custom fields."""
        result = super().dict(*args, **kwargs)
        
        # Convert MemoryItem to dict
        if "memory" in result and isinstance(result["memory"], MemoryItem):
            result["memory"] = result["memory"].dict()
        
        # Remove None values to save space
        return {k: v for k, v in result.items() if v is not None}
    
    @property
    def memory_id(self) -> str:
        """Get the ID of the memory item."""
        return self.memory.id
    
    @property
    def content(self) -> Dict[str, Any]:
        """Get the content of the memory item."""
        if isinstance(self.memory.content, dict):
            return self.memory.content
        return self.memory.content.dict()
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Get the metadata of the memory item."""
        if isinstance(self.memory.metadata, dict):
            return self.memory.metadata
        return self.memory.metadata.dict()
    
    @property
    def text(self) -> str:
        """Get the text of the memory item."""
        return self.memory.get_text()
    
    @property
    def summary(self) -> str:
        """Get the summary of the memory item."""
        if self.memory.summary:
            return self.memory.summary
        if isinstance(self.memory.content, dict) and "summary" in self.memory.content:
            return self.memory.content["summary"]
        # Default to a truncated version of the text
        text = self.text
        if len(text) > 100:
            return text[:97] + "..."
        return text


class MemorySearchResults(BaseModel):
    """
    Collection of results from a memory search operation.
    
    This model represents the complete result set from a memory search,
    including the matched items and metadata about the search operation.
    """
    
    # The search results
    results: List[MemorySearchResult] = Field(default_factory=list)
    
    # Search metadata
    total_count: int  # Total number of matches (may be more than returned)
    query: Optional[str] = None  # The original query string
    options: MemorySearchOptions  # The search options used
    execution_time_ms: Optional[float] = None  # How long the search took
    
    @validator("options", pre=True)
    def validate_options(cls, v):
        """Ensure options is a MemorySearchOptions object."""
        if isinstance(v, dict):
            return MemorySearchOptions(**v)
        return v
    
    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        """Override dict() to handle custom fields."""
        result = super().dict(*args, **kwargs)
        
        # Convert results to dict
        if "results" in result:
            result["results"] = [
                r.dict() if hasattr(r, "dict") else r
                for r in result["results"]
            ]
        
        # Convert options to dict
        if "options" in result and isinstance(result["options"], MemorySearchOptions):
            result["options"] = result["options"].dict()
        
        # Remove None values to save space
        return {k: v for k, v in result.items() if v is not None}
    
    @property
    def memory_ids(self) -> List[str]:
        """Get the list of memory IDs in the results."""
        return [result.memory_id for result in self.results]
    
    def get_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """Get a specific memory by ID from the results."""
        for result in self.results:
            if result.memory_id == memory_id:
                return result.memory
        return None
