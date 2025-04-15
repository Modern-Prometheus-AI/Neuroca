#!/usr/bin/env python3
"""
Basic test script for the Neuroca memory system.

This script demonstrates the minimum viable use of the memory system.
"""

import asyncio
import logging
from neuroca.memory.backends import BackendType
from neuroca.memory.manager.core import MemoryManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Test basic memory system functionality."""
    print("Initializing memory system...")
    
    # Create a memory manager with in-memory backend
    memory_manager = MemoryManager(
        config={
            "stm": {"default_ttl": 3600},  # 1 hour TTL
            "mtm": {"max_capacity": 1000},
            "ltm": {"maintenance_interval": 86400}  # 24 hours
        },
        mtm_storage_type=BackendType.MEMORY,
        ltm_storage_type=BackendType.MEMORY,
        vector_storage_type=BackendType.MEMORY
    )
    
    try:
        # Initialize the memory manager
        await memory_manager.initialize()
        print("Memory system initialized successfully!")
        
        # Add a memory
        print("\nAdding a memory...")
        memory_id = await memory_manager.add_memory(
            content="This is a test memory",
            summary="Test memory",
            importance=0.7,
            tags=["test", "example"],
            metadata={"source": "test script"},
            initial_tier="stm"
        )
        print(f"Added memory with ID: {memory_id}")
        
        # Retrieve the memory
        print("\nRetrieving the memory...")
        memory = await memory_manager.retrieve_memory(memory_id)
        print(f"Retrieved memory: {memory}")
        
        # Search for memories
        print("\nSearching for memories...")
        search_results = await memory_manager.search_memories(
            query="test memory",
            limit=5
        )
        # Access the 'results' attribute for the list of MemorySearchResult objects
        print(f"Found {len(search_results.results)} memories")
        for search_result in search_results.results:
            # Access attributes via the 'memory' attribute of MemorySearchResult
            print(f"- ID: {search_result.memory.id}, Text: {search_result.memory.get_text()}, Relevance: {search_result.relevance:.2f}, Tier: {search_result.tier}")

        # Wait a bit to allow background processes to run
        print("\nWaiting for 2 seconds to allow background processes to run...")
        await asyncio.sleep(2)
        
    finally:
        # Properly shut down
        print("\nShutting down memory system...")
        await memory_manager.shutdown()
        print("Memory system shut down successfully!")

if __name__ == "__main__":
    asyncio.run(main())
