#!/usr/bin/env python3
"""
Working NeuroCognitive Architecture (NCA) LLM Client
===================================================

This client demonstrates the working parts of Neuroca's cognitive architecture,
using only available components and supported backends.

Features:
1. 3-Tier Memory System (STM → MTM → LTM) with in-memory backend
2. Basic Memory Operations (store, retrieve, search)
3. Session Management
4. Error Handling

Usage:
    python sandbox/working_nca_client.py
"""

import asyncio
import logging
import time
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

# Core NCA Imports - only what's available
from neuroca.memory.manager.core import MemoryManager
from neuroca.memory.models.memory_item import MemoryItem, MemoryContent, MemoryMetadata
from neuroca.memory.backends import BackendType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WorkingNCAClient:
    """
    Working NeuroCognitive Architecture LLM Client
    
    Demonstrates the functional parts of the NCA memory system:
    - Multi-tier memory management (STM/MTM/LTM)
    - Memory operations (store, retrieve, search)
    - Session tracking
    - Basic cognitive processing simulation
    """
    
    def __init__(self):
        """Initialize the working NCA client."""
        self.memory_manager: Optional[MemoryManager] = None
        
        # Client state
        self.session_id = f"nca_session_{int(time.time())}"
        self.conversation_history = []
        self.memory_stats = {
            "stm_count": 0,
            "mtm_count": 0,
            "ltm_count": 0,
            "total_operations": 0
        }
        
        print("🧠 Working NCA LLM Client Initialized")
        print(f"📝 Session ID: {self.session_id}")
    
    async def initialize(self):
        """Initialize NCA components using supported backends."""
        try:
            print("\n🔧 Initializing NCA Memory System...")
            
            # Initialize memory manager with in-memory backend (supported)
            print("  💾 Initializing Memory Manager with in-memory backend...")
            self.memory_manager = MemoryManager(
                stm_storage_type=BackendType.MEMORY,
                mtm_storage_type=BackendType.MEMORY,
                ltm_storage_type=BackendType.MEMORY,
                vector_storage_type=BackendType.MEMORY
            )
            
            await self.memory_manager.initialize()
            
            print("✅ NCA Memory System Initialized Successfully!")
            
            # Test basic functionality
            await self._test_memory_system()
            
        except Exception as e:
            logger.error(f"Failed to initialize NCA components: {str(e)}")
            print(f"❌ Initialization failed: {str(e)}")
            raise
    
    async def _test_memory_system(self):
        """Test that the memory system is working."""
        print("\n🧪 Testing Memory System...")
        
        try:
            # Test using the new memory manager API
            memory_id = await self.memory_manager.add_memory(
                content="Test memory item",
                summary="Test memory",
                importance=0.5,
                metadata={"test": True},
                tags=["test"]
            )
            print(f"  ✅ STM test successful: {memory_id}")
            
            # Test retrieval
            retrieved = await self.memory_manager.retrieve_memory(memory_id)
            print(f"  ✅ Memory retrieval successful: {retrieved}")
            
            self.memory_stats["stm_count"] += 1
            self.memory_stats["total_operations"] += 2
            
        except Exception as e:
            print(f"  ❌ Memory test failed: {str(e)}")
            raise
    
    async def process_user_input(self, user_input: str) -> Dict[str, Any]:
        """
        Process user input through a simplified cognitive pipeline.
        
        Args:
            user_input: The user's input text
            
        Returns:
            Dict containing the processed response and stats
        """
        start_time = time.time()
        
        print(f"\n🎤 Processing: '{user_input[:50]}...'")
        
        try:
            # Phase 1: Memory Retrieval
            print("  💭 Phase 1: Memory Retrieval")
            relevant_memories = await self._retrieve_memories(user_input)
            print(f"    → Found {len(relevant_memories)} relevant memories")
            
            # Phase 2: Context Building
            print("  📄 Phase 2: Context Building")
            context = await self._build_context(user_input, relevant_memories)
            
            # Phase 3: Response Generation
            print("  💬 Phase 3: Response Generation")
            response = await self._generate_response(user_input, context)
            
            # Phase 4: Memory Storage
            print("  💾 Phase 4: Memory Storage")
            await self._store_interaction(user_input, response)
            
            processing_time = time.time() - start_time
            
            # Build response package
            result = {
                "response": response,
                "processing_time": processing_time,
                "memories_found": len(relevant_memories),
                "memory_stats": self.memory_stats.copy(),
                "session_id": self.session_id,
                "conversation_turn": len(self.conversation_history)
            }
            
            print(f"✅ Processing Complete! ({processing_time:.2f}s)")
            return result
            
        except Exception as e:
            logger.error(f"Error processing user input: {str(e)}")
            return {
                "response": f"I encountered an error: {str(e)}",
                "error": str(e),
                "memory_stats": self.memory_stats.copy()
            }
    
    async def _retrieve_memories(self, query: str) -> List[Any]:
        """Retrieve relevant memories from all tiers."""
        try:
            memories = []
            
            # Search for memories
            try:
                results = await self.memory_manager.search_memories(
                    query=query,
                    limit=5
                )
                memories.extend(results)
            except Exception as e:
                print(f"    → Memory search failed: {str(e)}")
            
            return memories
            
        except Exception as e:
            logger.error(f"Error retrieving memories: {str(e)}")
            return []
    
    async def _build_context(self, user_input: str, memories: List[Any]) -> Dict[str, Any]:
        """Build context from memories and current state."""
        context = {
            "user_input": user_input,
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "conversation_turn": len(self.conversation_history) + 1,
            "relevant_memories": len(memories),
            "memory_stats": self.memory_stats.copy()
        }
        return context
    
    async def _generate_response(self, user_input: str, context: Dict[str, Any]) -> str:
        """Generate a response based on input and context."""
        # Simple response generation
        memory_context = ""
        if context["relevant_memories"] > 0:
            memory_context = f" (Found {context['relevant_memories']} related memories)"
        
        response = f"I understand you said: '{user_input}'{memory_context}. This is conversation turn {context['conversation_turn']} in session {self.session_id}."
        
        return response
    
    async def _store_interaction(self, user_input: str, response: str):
        """Store the interaction in memory."""
        try:
            # Store interaction using the memory manager API
            memory_id = await self.memory_manager.add_memory(
                content=f"User: {user_input}\nAssistant: {response}",
                summary=f"Conversation turn {len(self.conversation_history) + 1}",
                importance=0.7,
                metadata={
                    "conversation": True,
                    "session": self.session_id,
                    "turn_number": len(self.conversation_history) + 1,
                    "user_input_length": len(user_input),
                    "response_length": len(response)
                },
                tags=["conversation", self.session_id]
            )
            
            print(f"    → Stored interaction in memory: {memory_id}")
            
            # Update conversation history
            self.conversation_history.append({
                "user_input": user_input,
                "response": response,
                "memory_id": memory_id,
                "timestamp": datetime.now().isoformat()
            })
            
            self.memory_stats["stm_count"] += 1
            self.memory_stats["total_operations"] += 1
            
        except Exception as e:
            logger.error(f"Error storing interaction: {str(e)}")
    
    async def demonstrate_memory_features(self):
        """Demonstrate the memory system features."""
        print("\n🎪 NCA Memory System Demonstration")
        print("=" * 40)
        
        try:
            # 1. Memory Storage Demo
            print("\n1️⃣ Memory Storage Demo")
            await self._demo_memory_storage()
            
            # 2. Memory Retrieval Demo
            print("\n2️⃣ Memory Retrieval Demo")
            await self._demo_memory_retrieval()
            
            # 3. Memory Search Demo
            print("\n3️⃣ Memory Search Demo")
            await self._demo_memory_search()
            
            print("\n🎉 Memory System Demonstration Complete!")
            
        except Exception as e:
            logger.error(f"Error in demonstration: {str(e)}")
            print(f"❌ Demonstration failed: {str(e)}")
    
    async def _demo_memory_storage(self):
        """Demonstrate storing memories in different tiers."""
        print("  💾 Storing memories across different types...")
        
        # Working memory
        stm_id = await self.memory_manager.add_memory(
            content="Current task: demonstrate NCA capabilities",
            summary="Current task context",
            importance=0.8,
            tags=["working", "demo"]
        )
        print(f"    → Working Memory: {stm_id}")
        
        # Session information
        mtm_id = await self.memory_manager.add_memory(
            content="User is exploring NCA memory system",
            summary="Session context",
            importance=0.6,
            tags=["session", "demo"]
        )
        print(f"    → Session Memory: {mtm_id}")
        
        # Knowledge
        ltm_id = await self.memory_manager.add_memory(
            content="NCA provides 3-tier memory architecture for LLMs",
            summary="NCA core knowledge",
            importance=0.9,
            tags=["knowledge", "demo"]
        )
        print(f"    → Knowledge Memory: {ltm_id}")
        
        # Update stats
        self.memory_stats["stm_count"] += 1
        self.memory_stats["mtm_count"] += 1
        self.memory_stats["ltm_count"] += 1
        self.memory_stats["total_operations"] += 3
    
    async def _demo_memory_retrieval(self):
        """Demonstrate memory retrieval."""
        print("  🔍 Testing memory retrieval...")
        
        # Search for recent memories
        try:
            results = await self.memory_manager.search_memories(
                query="demo",
                limit=3
            )
            print(f"    → Found memories: {len(results)}")
            
            for i, memory in enumerate(results[:2]):
                print(f"    → Memory {i+1}: {str(memory)[:50]}...")
                
        except Exception as e:
            print(f"    → Retrieval test failed: {str(e)}")
    
    async def _demo_memory_search(self):
        """Demonstrate memory search."""
        print("  🔎 Testing memory search...")
        
        search_queries = ["NCA", "demonstrate", "memory"]
        
        for query in search_queries:
            try:
                results = await self.memory_manager.search_memories(query=query, limit=5)
                print(f"    → Search '{query}': {len(results)} results")
            except Exception as e:
                print(f"    → Search '{query}' failed: {str(e)}")
    
    async def interactive_session(self):
        """Run an interactive session with the user."""
        print("\n🎮 Starting Interactive NCA Session")
        print("Type 'quit' to exit, 'demo' for memory demo, 'stats' for statistics")
        print("-" * 60)
        
        while True:
            try:
                user_input = input("\n👤 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Goodbye! Thanks for exploring NCA!")
                    break
                elif user_input.lower() == 'demo':
                    await self.demonstrate_memory_features()
                    continue
                elif user_input.lower() == 'stats':
                    await self._show_stats()
                    continue
                elif not user_input:
                    continue
                
                # Process the input through cognitive pipeline
                result = await self.process_user_input(user_input)
                
                print(f"\n🧠 NCA: {result['response']}")
                
                # Show brief stats
                if result.get('processing_time'):
                    print(f"   💭 Processed in {result['processing_time']:.2f}s using {result.get('memories_found', 0)} memories")
                
            except KeyboardInterrupt:
                print("\n\n👋 Session interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                logger.error(f"Interactive session error: {str(e)}")
    
    async def _show_stats(self):
        """Show current memory statistics."""
        print("\n📊 NCA Memory Statistics:")
        print(f"  💾 STM Memories: {self.memory_stats['stm_count']}")
        print(f"  💾 MTM Memories: {self.memory_stats['mtm_count']}")
        print(f"  💾 LTM Memories: {self.memory_stats['ltm_count']}")
        print(f"  🔧 Total Operations: {self.memory_stats['total_operations']}")
        print(f"  💬 Conversation Turns: {len(self.conversation_history)}")
        print(f"  📝 Session ID: {self.session_id}")
    
    async def shutdown(self):
        """Gracefully shutdown the NCA client."""
        print("\n🔧 Shutting down NCA Client...")
        
        try:
            if self.memory_manager:
                await self.memory_manager.shutdown()
                print("  ✅ Memory Manager shutdown")
            
            # Save session summary
            session_summary = {
                "session_id": self.session_id,
                "conversation_turns": len(self.conversation_history),
                "memory_stats": self.memory_stats,
                "conversation_history": self.conversation_history
            }
            
            # Ensure we're in the right directory for saving
            session_file = f"session_{self.session_id}.json"
            with open(session_file, "w") as f:
                json.dump(session_summary, f, indent=2, default=str)
            
            print(f"  💾 Session summary saved: {session_file}")
            print("🏁 NCA Client shutdown complete!")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")
            print(f"❌ Shutdown error: {str(e)}")


async def main():
    """Main entry point for the working NCA client."""
    print("🚀 Starting Working NeuroCognitive Architecture (NCA) Client")
    print("=" * 60)
    
    client = WorkingNCAClient()
    
    try:
        # Initialize the client
        await client.initialize()
        
        # Run interactive session
        await client.interactive_session()
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        print(f"💥 Fatal error: {str(e)}")
    finally:
        # Always shutdown gracefully
        await client.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
