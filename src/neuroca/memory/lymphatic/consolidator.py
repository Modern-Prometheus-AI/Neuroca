"""
Lymphatic Memory Consolidator Module

This module implements the memory consolidation process for the lymphatic memory system.
It handles the transformation of short-term memories into long-term storage by applying
various consolidation strategies including:
- Importance-based filtering
- Semantic clustering
- Temporal decay modeling
- Contextual association strengthening

The consolidator acts as the bridge between working memory and long-term storage,
implementing biologically-inspired processes that mimic how the human brain's
lymphatic system clears waste and consolidates important memories during rest periods.

Usage:
    consolidator = MemoryConsolidator(config)
    consolidated_memories = consolidator.consolidate(memories)
    consolidator.schedule_consolidation(memories, delay=3600)  # Schedule for later

Author: NeuroCognitive Architecture Team
"""

import asyncio
import heapq
import logging
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Any

from neuroca.config.settings import get_settings
from neuroca.core.exceptions import ConsolidationError
from neuroca.memory.models import ConsolidationMetrics, Memory
from neuroca.monitoring.metrics import record_metric, track_operation

# Configure logger
logger = logging.getLogger(__name__)


class ConsolidationStrategy:
    """Base class for memory consolidation strategies."""
    
    def __init__(self, config: dict[str, Any] = None):
        """
        Initialize the consolidation strategy.
        
        Args:
            config: Configuration parameters for the strategy
        """
        self.config = config or {}
        
    def apply(self, memories: list[Memory]) -> list[Memory]:
        """
        Apply the consolidation strategy to a list of memories.
        
        Args:
            memories: List of memories to consolidate
            
        Returns:
            List of consolidated memories
        """
        raise NotImplementedError("Consolidation strategies must implement apply()")


class ImportanceBasedStrategy(ConsolidationStrategy):
    """Consolidates memories based on their importance scores."""
    
    def apply(self, memories: list[Memory]) -> list[Memory]:
        """
        Filter memories based on importance threshold.
        
        Args:
            memories: List of memories to consolidate
            
        Returns:
            List of memories that meet the importance threshold
        """
        threshold = self.config.get("importance_threshold", 0.5)
        logger.debug(f"Applying importance-based filtering with threshold {threshold}")
        
        return [memory for memory in memories if memory.importance >= threshold]


class SemanticClusteringStrategy(ConsolidationStrategy):
    """Consolidates memories by clustering semantically related items."""
    
    def apply(self, memories: list[Memory]) -> list[Memory]:
        """
        Group semantically similar memories and create consolidated representations.
        
        Args:
            memories: List of memories to consolidate
            
        Returns:
            List of consolidated memories with semantic clusters
        """
        similarity_threshold = self.config.get("similarity_threshold", 0.7)
        logger.debug(f"Applying semantic clustering with threshold {similarity_threshold}")
        
        # In a real implementation, this would use embedding similarity
        # For now, we'll use a simplified approach based on tags/categories
        clusters = {}
        
        for memory in memories:
            key = frozenset(memory.tags) if hasattr(memory, 'tags') and memory.tags else "uncategorized"
            if key not in clusters:
                clusters[key] = []
            clusters[key].append(memory)
        
        # Create consolidated memories from clusters
        consolidated = []
        for _cluster_key, cluster_memories in clusters.items():
            if len(cluster_memories) <= 1:
                consolidated.extend(cluster_memories)
            else:
                # Create a consolidated memory from the cluster
                primary = max(cluster_memories, key=lambda m: m.importance)
                primary.related_memories = [m.id for m in cluster_memories if m.id != primary.id]
                primary.strength += 0.1 * len(cluster_memories)  # Strengthen based on cluster size
                consolidated.append(primary)
                
        return consolidated


class TemporalDecayStrategy(ConsolidationStrategy):
    """Applies temporal decay to memories based on their age."""
    
    def apply(self, memories: list[Memory]) -> list[Memory]:
        """
        Adjust memory strength based on age and decay parameters.
        
        Args:
            memories: List of memories to consolidate
            
        Returns:
            List of memories with adjusted strength values
        """
        decay_rate = self.config.get("decay_rate", 0.05)
        max_age_days = self.config.get("max_age_days", 30)
        logger.debug(f"Applying temporal decay with rate {decay_rate}")
        
        now = datetime.now()
        result = []
        
        for memory in memories:
            age_days = (now - memory.created_at).days if hasattr(memory, 'created_at') else 0
            
            # Apply decay formula: strength = original_strength * e^(-decay_rate * age)
            decay_factor = 1.0 - (decay_rate * min(age_days, max_age_days) / max_age_days)
            memory.strength *= max(0.1, decay_factor)  # Ensure strength doesn't go below 0.1
            
            # Filter out memories that have decayed too much
            if memory.strength >= self.config.get("min_strength", 0.2):
                result.append(memory)
            else:
                logger.debug(f"Memory {memory.id} decayed below threshold and was removed")
                
        return result


class MemoryConsolidator:
    """
    Main class responsible for memory consolidation processes.
    
    This class orchestrates the consolidation of memories from working memory
    into long-term storage using various biologically-inspired strategies.
    """
    
    def __init__(self, config: dict[str, Any] = None):
        """
        Initialize the memory consolidator with configuration.
        
        Args:
            config: Configuration dictionary for the consolidator
        """
        self.config = config or get_settings().memory.lymphatic.consolidation
        self.strategies = self._initialize_strategies()
        self._consolidation_queue = []
        self._queue_lock = threading.Lock()
        self._scheduler_thread = None
        self._running = False
        self.metrics = ConsolidationMetrics()
        
        logger.info("Memory consolidator initialized with %d strategies", len(self.strategies))
    
    def _initialize_strategies(self) -> list[ConsolidationStrategy]:
        """
        Initialize consolidation strategies based on configuration.
        
        Returns:
            List of configured consolidation strategy instances
        """
        strategies = []
        
        strategy_configs = self.config.get("strategies", {
            "importance": {"enabled": True, "importance_threshold": 0.5},
            "semantic": {"enabled": True, "similarity_threshold": 0.7},
            "temporal": {"enabled": True, "decay_rate": 0.05, "max_age_days": 30}
        })
        
        if strategy_configs.get("importance", {}).get("enabled", True):
            strategies.append(ImportanceBasedStrategy(strategy_configs.get("importance", {})))
            
        if strategy_configs.get("semantic", {}).get("enabled", True):
            strategies.append(SemanticClusteringStrategy(strategy_configs.get("semantic", {})))
            
        if strategy_configs.get("temporal", {}).get("enabled", True):
            strategies.append(TemporalDecayStrategy(strategy_configs.get("temporal", {})))
            
        return strategies
    
    @track_operation("memory_consolidation")
    def consolidate(self, memories: list[Memory]) -> list[Memory]:
        """
        Consolidate a list of memories by applying all enabled strategies.
        
        Args:
            memories: List of memories to consolidate
            
        Returns:
            List of consolidated memories
            
        Raises:
            ConsolidationError: If consolidation fails
        """
        if not memories:
            logger.warning("No memories provided for consolidation")
            return []
        
        logger.info(f"Starting consolidation of {len(memories)} memories")
        start_time = time.time()
        consolidated_memories = memories.copy()
        
        try:
            # Apply each strategy in sequence
            for strategy in self.strategies:
                strategy_start = time.time()
                consolidated_memories = strategy.apply(consolidated_memories)
                strategy_duration = time.time() - strategy_start
                
                logger.debug(
                    f"Applied {strategy.__class__.__name__}: {len(consolidated_memories)} memories remaining "
                    f"(took {strategy_duration:.2f}s)"
                )
                
                # Update metrics
                self.metrics.strategy_durations[strategy.__class__.__name__] = strategy_duration
                self.metrics.memories_after_strategy[strategy.__class__.__name__] = len(consolidated_memories)
            
            # Update final consolidation metrics
            self.metrics.total_input_memories += len(memories)
            self.metrics.total_output_memories += len(consolidated_memories)
            self.metrics.total_duration += (time.time() - start_time)
            self.metrics.consolidation_count += 1
            
            # Record metrics for monitoring
            record_metric("memory_consolidation.input_count", len(memories))
            record_metric("memory_consolidation.output_count", len(consolidated_memories))
            record_metric("memory_consolidation.duration", time.time() - start_time)
            
            logger.info(
                f"Consolidation complete: {len(memories)} → {len(consolidated_memories)} memories "
                f"(took {time.time() - start_time:.2f}s)"
            )
            
            return consolidated_memories
            
        except Exception as e:
            logger.error(f"Consolidation failed: {str(e)}", exc_info=True)
            raise ConsolidationError(f"Memory consolidation failed: {str(e)}") from e
    
    def schedule_consolidation(self, memories: list[Memory], delay: int = 3600) -> str:
        """
        Schedule memories for future consolidation.
        
        Args:
            memories: List of memories to consolidate
            delay: Delay in seconds before consolidation should occur
            
        Returns:
            str: ID of the scheduled consolidation task
        """
        if not memories:
            logger.warning("No memories provided for scheduled consolidation")
            return None
            
        scheduled_time = datetime.now() + timedelta(seconds=delay)
        task_id = str(uuid.uuid4())
        
        with self._queue_lock:
            heapq.heappush(
                self._consolidation_queue, 
                (scheduled_time.timestamp(), task_id, memories)
            )
            
        logger.info(
            f"Scheduled consolidation of {len(memories)} memories with ID {task_id} "
            f"for {scheduled_time.isoformat()}"
        )
        
        # Start the scheduler thread if not already running
        self._ensure_scheduler_running()
        
        return task_id
    
    def _ensure_scheduler_running(self):
        """Ensure the scheduler thread is running."""
        with self._queue_lock:
            if self._scheduler_thread is None or not self._scheduler_thread.is_alive():
                self._running = True
                self._scheduler_thread = threading.Thread(
                    target=self._scheduler_loop,
                    daemon=True,
                    name="memory-consolidation-scheduler"
                )
                self._scheduler_thread.start()
                logger.debug("Started memory consolidation scheduler thread")
    
    def _scheduler_loop(self):
        """Background thread that processes scheduled consolidations."""
        logger.info("Memory consolidation scheduler started")
        
        while self._running:
            try:
                now = time.time()
                
                # Check if there are any tasks ready to process
                with self._queue_lock:
                    if not self._consolidation_queue:
                        # No tasks, sleep for a bit
                        time.sleep(1)
                        continue
                        
                    # Peek at the next task
                    next_time, task_id, memories = self._consolidation_queue[0]
                    
                    if next_time <= now:
                        # Task is ready, remove it from the queue
                        heapq.heappop(self._consolidation_queue)
                    else:
                        # Not ready yet, sleep until it's time
                        sleep_time = min(next_time - now, 5)  # Sleep at most 5 seconds
                        time.sleep(sleep_time)
                        continue
                
                # Process the task outside the lock
                logger.info(f"Processing scheduled consolidation task {task_id} with {len(memories)} memories")
                try:
                    self.consolidate(memories)
                except Exception as e:
                    logger.error(f"Error in scheduled consolidation task {task_id}: {str(e)}", exc_info=True)
                    
            except Exception as e:
                logger.error(f"Error in consolidation scheduler: {str(e)}", exc_info=True)
                time.sleep(5)  # Sleep to avoid tight error loops
    
    def stop(self):
        """Stop the scheduler thread."""
        logger.info("Stopping memory consolidation scheduler")
        self._running = False
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            self._scheduler_thread.join(timeout=5)
            
    async def consolidate_async(self, memories: list[Memory]) -> list[Memory]:
        """
        Asynchronous version of the consolidate method.
        
        Args:
            memories: List of memories to consolidate
            
        Returns:
            List of consolidated memories
        """
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(executor, self.consolidate, memories)
    
    def get_metrics(self) -> dict[str, Any]:
        """
        Get current consolidation metrics.
        
        Returns:
            Dictionary of consolidation metrics
        """
        return self.metrics.to_dict()
    
    def reset_metrics(self):
        """Reset all consolidation metrics."""
        self.metrics = ConsolidationMetrics()
        logger.debug("Consolidation metrics reset")

    def __enter__(self):
        """Context manager entry."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.stop()