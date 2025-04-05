"""
Context Retrieval Module for NeuroCognitive Architecture

This module provides functionality for retrieving relevant context from various sources
to support LLM operations. It implements sophisticated retrieval strategies including
semantic search, recency-based retrieval, and importance-based retrieval.

The module serves as a bridge between the memory systems and the LLM integration layer,
allowing for contextually relevant information to be provided to the LLM during processing.

Usage:
    retriever = ContextRetriever()
    context = await retriever.retrieve_context(query="project planning", max_items=5)
    
    # With specific memory tiers
    context = await retriever.retrieve_context(
        query="project planning",
        memory_tiers=["working", "episodic"],
        max_items=5
    )
"""

import asyncio
import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

from neuroca.core.exceptions import (
    ContextRetrievalError,
    InvalidParameterError,
    MemoryAccessError,
)
from neuroca.core.models import ContextItem, RelevanceScore
from neuroca.core.utils.logging import get_logger
from neuroca.memory.base import MemoryItem
from neuroca.memory.episodic import EpisodicMemory
from neuroca.memory.semantic import SemanticMemory
from neuroca.memory.working import WorkingMemory

logger = get_logger(__name__)

class RetrievalStrategy(Enum):
    """Enumeration of available context retrieval strategies."""
    SEMANTIC = auto()  # Semantic similarity-based retrieval
    RECENCY = auto()   # Time-based retrieval (most recent first)
    IMPORTANCE = auto()  # Importance-based retrieval
    HYBRID = auto()    # Combination of multiple strategies
    ADAPTIVE = auto()  # Dynamically adapts based on query and system state


@dataclass
class RetrievalOptions:
    """Configuration options for context retrieval."""
    strategy: RetrievalStrategy = RetrievalStrategy.HYBRID
    max_items: int = 10
    min_relevance_score: float = 0.5  # Minimum relevance score (0-1)
    time_decay_factor: float = 0.1  # How quickly older items lose relevance
    importance_weight: float = 0.3  # Weight given to item importance
    recency_weight: float = 0.3  # Weight given to item recency
    semantic_weight: float = 0.4  # Weight given to semantic similarity
    include_metadata: bool = True  # Whether to include metadata in results
    timeout_seconds: float = 5.0  # Maximum time for retrieval operations


class ContextRetriever:
    """
    Retrieves relevant context from memory systems based on queries and parameters.
    
    This class provides methods to search across different memory tiers and retrieve
    the most relevant context items based on various strategies including semantic
    similarity, recency, and importance.
    """
    
    def __init__(
        self,
        working_memory: Optional[WorkingMemory] = None,
        episodic_memory: Optional[EpisodicMemory] = None,
        semantic_memory: Optional[SemanticMemory] = None,
    ):
        """
        Initialize the ContextRetriever with memory system instances.
        
        Args:
            working_memory: Instance of WorkingMemory
            episodic_memory: Instance of EpisodicMemory
            semantic_memory: Instance of SemanticMemory
        """
        self.working_memory = working_memory
        self.episodic_memory = episodic_memory
        self.semantic_memory = semantic_memory
        self._validate_memory_systems()
        logger.debug("ContextRetriever initialized with memory systems")
    
    def _validate_memory_systems(self) -> None:
        """
        Validate that at least one memory system is available.
        
        Raises:
            InvalidParameterError: If no memory systems are provided
        """
        if not any([self.working_memory, self.episodic_memory, self.semantic_memory]):
            logger.error("No memory systems provided to ContextRetriever")
            raise InvalidParameterError(
                "At least one memory system must be provided to ContextRetriever"
            )
    
    async def retrieve_context(
        self,
        query: str,
        memory_tiers: Optional[list[str]] = None,
        options: Optional[RetrievalOptions] = None,
    ) -> list[ContextItem]:
        """
        Retrieve context items relevant to the provided query.
        
        Args:
            query: The query string to retrieve context for
            memory_tiers: Optional list of memory tiers to search (e.g., ["working", "episodic"])
                          If None, all available memory tiers will be searched
            options: Optional retrieval configuration options
            
        Returns:
            List of ContextItem objects sorted by relevance
            
        Raises:
            ContextRetrievalError: If retrieval fails
            InvalidParameterError: If parameters are invalid
        """
        start_time = time.time()
        logger.debug(f"Starting context retrieval for query: '{query}'")
        
        if not query or not isinstance(query, str):
            raise InvalidParameterError("Query must be a non-empty string")
        
        # Use default options if none provided
        if options is None:
            options = RetrievalOptions()
        
        # Determine which memory tiers to search
        tiers_to_search = self._resolve_memory_tiers(memory_tiers)
        if not tiers_to_search:
            logger.warning("No valid memory tiers specified for retrieval")
            return []
        
        try:
            # Create tasks for each memory tier
            retrieval_tasks = []
            for tier_name in tiers_to_search:
                retrieval_tasks.append(
                    self._retrieve_from_tier(tier_name, query, options)
                )
            
            # Execute all retrieval tasks with timeout
            retrieval_results = await asyncio.wait_for(
                asyncio.gather(*retrieval_tasks, return_exceptions=True),
                timeout=options.timeout_seconds
            )
            
            # Process results, handling any exceptions
            all_items = []
            for i, result in enumerate(retrieval_results):
                if isinstance(result, Exception):
                    tier_name = tiers_to_search[i]
                    logger.error(f"Error retrieving from {tier_name}: {str(result)}")
                    # Continue with other results rather than failing completely
                else:
                    all_items.extend(result)
            
            # Apply final ranking and filtering
            final_items = self._rank_and_filter_items(all_items, query, options)
            
            elapsed_time = time.time() - start_time
            logger.debug(
                f"Context retrieval completed in {elapsed_time:.3f}s. "
                f"Retrieved {len(final_items)} items."
            )
            
            return final_items
            
        except asyncio.TimeoutError:
            logger.error(f"Context retrieval timed out after {options.timeout_seconds}s")
            raise ContextRetrievalError(
                f"Context retrieval operation timed out after {options.timeout_seconds} seconds"
            )
        except Exception as e:
            logger.error(f"Error during context retrieval: {str(e)}", exc_info=True)
            raise ContextRetrievalError(f"Failed to retrieve context: {str(e)}")
    
    def _resolve_memory_tiers(self, memory_tiers: Optional[list[str]]) -> list[str]:
        """
        Resolve which memory tiers to search based on input and availability.
        
        Args:
            memory_tiers: Optional list of memory tier names to search
            
        Returns:
            List of valid memory tier names to search
        """
        available_tiers = []
        if self.working_memory:
            available_tiers.append("working")
        if self.episodic_memory:
            available_tiers.append("episodic")
        if self.semantic_memory:
            available_tiers.append("semantic")
        
        if not memory_tiers:
            return available_tiers
        
        # Filter to only include valid tiers
        valid_tiers = [tier for tier in memory_tiers if tier in available_tiers]
        
        # Log warning if some requested tiers are not available
        if len(valid_tiers) < len(memory_tiers):
            invalid_tiers = set(memory_tiers) - set(valid_tiers)
            logger.warning(
                f"Requested memory tiers not available: {', '.join(invalid_tiers)}"
            )
        
        return valid_tiers
    
    async def _retrieve_from_tier(
        self, tier_name: str, query: str, options: RetrievalOptions
    ) -> list[ContextItem]:
        """
        Retrieve context items from a specific memory tier.
        
        Args:
            tier_name: Name of the memory tier to retrieve from
            query: The query string
            options: Retrieval configuration options
            
        Returns:
            List of ContextItem objects from the specified tier
            
        Raises:
            MemoryAccessError: If access to the memory tier fails
        """
        logger.debug(f"Retrieving from {tier_name} memory for query: '{query}'")
        
        try:
            if tier_name == "working" and self.working_memory:
                memory_items = await self._retrieve_from_working_memory(query, options)
            elif tier_name == "episodic" and self.episodic_memory:
                memory_items = await self._retrieve_from_episodic_memory(query, options)
            elif tier_name == "semantic" and self.semantic_memory:
                memory_items = await self._retrieve_from_semantic_memory(query, options)
            else:
                logger.error(f"Invalid memory tier: {tier_name}")
                return []
            
            # Convert memory items to context items with tier information
            context_items = [
                self._memory_item_to_context_item(item, tier_name)
                for item in memory_items
            ]
            
            logger.debug(f"Retrieved {len(context_items)} items from {tier_name} memory")
            return context_items
            
        except Exception as e:
            logger.error(f"Error accessing {tier_name} memory: {str(e)}", exc_info=True)
            raise MemoryAccessError(f"Failed to access {tier_name} memory: {str(e)}")
    
    async def _retrieve_from_working_memory(
        self, query: str, options: RetrievalOptions
    ) -> list[MemoryItem]:
        """
        Retrieve items from working memory.
        
        Args:
            query: The query string
            options: Retrieval configuration options
            
        Returns:
            List of MemoryItem objects from working memory
        """
        if options.strategy == RetrievalStrategy.SEMANTIC:
            return await self.working_memory.search_by_similarity(
                query, limit=options.max_items, threshold=options.min_relevance_score
            )
        elif options.strategy == RetrievalStrategy.RECENCY:
            return await self.working_memory.get_recent_items(limit=options.max_items)
        elif options.strategy == RetrievalStrategy.IMPORTANCE:
            return await self.working_memory.get_important_items(limit=options.max_items)
        else:  # HYBRID or ADAPTIVE
            # For hybrid, we'll get more items than needed and rank them later
            recent_items = await self.working_memory.get_recent_items(
                limit=options.max_items * 2
            )
            similar_items = await self.working_memory.search_by_similarity(
                query, limit=options.max_items * 2
            )
            # Combine and remove duplicates (based on item ID)
            combined = {item.id: item for item in recent_items + similar_items}
            return list(combined.values())
    
    async def _retrieve_from_episodic_memory(
        self, query: str, options: RetrievalOptions
    ) -> list[MemoryItem]:
        """
        Retrieve items from episodic memory.
        
        Args:
            query: The query string
            options: Retrieval configuration options
            
        Returns:
            List of MemoryItem objects from episodic memory
        """
        if options.strategy == RetrievalStrategy.SEMANTIC:
            return await self.episodic_memory.search_episodes(
                query, limit=options.max_items, threshold=options.min_relevance_score
            )
        elif options.strategy == RetrievalStrategy.RECENCY:
            return await self.episodic_memory.get_recent_episodes(limit=options.max_items)
        elif options.strategy == RetrievalStrategy.IMPORTANCE:
            return await self.episodic_memory.get_important_episodes(limit=options.max_items)
        else:  # HYBRID or ADAPTIVE
            # For hybrid, get episodes based on multiple criteria
            semantic_results = await self.episodic_memory.search_episodes(
                query, limit=options.max_items
            )
            temporal_results = await self.episodic_memory.get_recent_episodes(
                limit=options.max_items
            )
            # Combine and remove duplicates
            combined = {item.id: item for item in semantic_results + temporal_results}
            return list(combined.values())
    
    async def _retrieve_from_semantic_memory(
        self, query: str, options: RetrievalOptions
    ) -> list[MemoryItem]:
        """
        Retrieve items from semantic memory.
        
        Args:
            query: The query string
            options: Retrieval configuration options
            
        Returns:
            List of MemoryItem objects from semantic memory
        """
        # Semantic memory primarily uses semantic search
        return await self.semantic_memory.search_concepts(
            query, limit=options.max_items, threshold=options.min_relevance_score
        )
    
    def _memory_item_to_context_item(
        self, memory_item: MemoryItem, tier_name: str
    ) -> ContextItem:
        """
        Convert a memory item to a context item.
        
        Args:
            memory_item: The memory item to convert
            tier_name: The name of the memory tier
            
        Returns:
            A ContextItem object
        """
        # Calculate a base relevance score (will be refined later)
        base_relevance = getattr(memory_item, "relevance", 0.5)
        
        return ContextItem(
            id=memory_item.id,
            content=memory_item.content,
            metadata={
                "source": f"{tier_name}_memory",
                "timestamp": memory_item.timestamp,
                "importance": getattr(memory_item, "importance", 0.5),
                "original_item": memory_item,
            },
            relevance=RelevanceScore(
                score=base_relevance,
                semantic_score=getattr(memory_item, "semantic_score", None),
                recency_score=getattr(memory_item, "recency_score", None),
                importance_score=getattr(memory_item, "importance", None),
            ),
        )
    
    def _rank_and_filter_items(
        self, items: list[ContextItem], query: str, options: RetrievalOptions
    ) -> list[ContextItem]:
        """
        Rank and filter context items based on relevance to the query.
        
        Args:
            items: List of context items to rank
            query: The original query string
            options: Retrieval configuration options
            
        Returns:
            Filtered and ranked list of context items
        """
        if not items:
            return []
        
        # Calculate composite relevance scores for each item
        for item in items:
            self._calculate_composite_relevance(item, query, options)
        
        # Sort by composite relevance score
        sorted_items = sorted(
            items, key=lambda x: x.relevance.score, reverse=True
        )
        
        # Filter by minimum relevance threshold
        filtered_items = [
            item for item in sorted_items 
            if item.relevance.score >= options.min_relevance_score
        ]
        
        # Limit to max items
        return filtered_items[:options.max_items]
    
    def _calculate_composite_relevance(
        self, item: ContextItem, query: str, options: RetrievalOptions
    ) -> None:
        """
        Calculate a composite relevance score for an item based on multiple factors.
        
        Args:
            item: The context item to score
            query: The original query string
            options: Retrieval configuration options
            
        This method modifies the item in place, updating its relevance scores.
        """
        # Extract individual scores with defaults
        semantic_score = item.relevance.semantic_score or 0.0
        
        # Calculate recency score based on timestamp
        current_time = time.time()
        item_time = item.metadata.get("timestamp", current_time)
        time_diff_hours = (current_time - item_time) / 3600  # Convert to hours
        recency_score = max(0.0, 1.0 - (time_diff_hours * options.time_decay_factor))
        item.relevance.recency_score = recency_score
        
        # Get importance score
        importance_score = item.metadata.get("importance", 0.5)
        item.relevance.importance_score = importance_score
        
        # Calculate composite score based on strategy
        if options.strategy == RetrievalStrategy.SEMANTIC:
            composite_score = semantic_score
        elif options.strategy == RetrievalStrategy.RECENCY:
            composite_score = recency_score
        elif options.strategy == RetrievalStrategy.IMPORTANCE:
            composite_score = importance_score
        else:  # HYBRID or ADAPTIVE
            # Weighted combination of all factors
            composite_score = (
                options.semantic_weight * semantic_score +
                options.recency_weight * recency_score +
                options.importance_weight * importance_score
            )
        
        # Update the item's relevance score
        item.relevance.score = max(0.0, min(1.0, composite_score))  # Clamp to [0,1]

    async def retrieve_context_by_id(
        self, item_id: str, memory_tiers: Optional[list[str]] = None
    ) -> Optional[ContextItem]:
        """
        Retrieve a specific context item by its ID.
        
        Args:
            item_id: The ID of the item to retrieve
            memory_tiers: Optional list of memory tiers to search
            
        Returns:
            The context item if found, None otherwise
            
        Raises:
            ContextRetrievalError: If retrieval fails
        """
        logger.debug(f"Retrieving context item by ID: {item_id}")
        
        if not item_id:
            raise InvalidParameterError("Item ID must be provided")
        
        # Determine which memory tiers to search
        tiers_to_search = self._resolve_memory_tiers(memory_tiers)
        
        try:
            for tier_name in tiers_to_search:
                if tier_name == "working" and self.working_memory:
                    item = await self.working_memory.get_item(item_id)
                elif tier_name == "episodic" and self.episodic_memory:
                    item = await self.episodic_memory.get_episode(item_id)
                elif tier_name == "semantic" and self.semantic_memory:
                    item = await self.semantic_memory.get_concept(item_id)
                else:
                    continue
                
                if item:
                    return self._memory_item_to_context_item(item, tier_name)
            
            logger.debug(f"No item found with ID: {item_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving item by ID: {str(e)}", exc_info=True)
            raise ContextRetrievalError(f"Failed to retrieve item by ID: {str(e)}")