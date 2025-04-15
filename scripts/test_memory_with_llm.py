#!/usr/bin/env python3
"""
Test script for the Neuroca memory system with LLM integration.

This script demonstrates how to use the memory system to create a conversational agent
that can remember previous interactions and use those memories in context.
"""

import asyncio
import os
import json
import time
from typing import Dict, List, Any, Optional
import uuid

from neuroca.memory.backends import BackendType
from neuroca.memory.manager.core import MemoryManager
from neuroca.memory.models.memory_item import MemoryItem
from neuroca.memory.models.search import MemorySearchOptions, MemorySearchResult # Import MemorySearchResult

# Uncomment to use OpenAI API. Add your API key to .env first.
try:
    import openai
    from dotenv import load_dotenv
    OPENAI_AVAILABLE = True
except ImportError:
    print("OpenAI package not available. Install with: pip install openai python-dotenv")
    OPENAI_AVAILABLE = False

class ConversationalAgent:
    """A simple conversational agent that uses the memory system to remember context."""
    
    def __init__(self, use_sqlite: bool = False):
        """Initialize the agent with memory system."""
        self.conversation_history = []
        self.memory_manager = None
        self.backend_type = BackendType.SQLITE if use_sqlite else BackendType.MEMORY
        self.conversation_id = str(uuid.uuid4())
        
        # OpenAI setup if available
        if OPENAI_AVAILABLE:
            load_dotenv()
            openai.api_key = os.getenv("OPENAI_API_KEY")
            if not openai.api_key:
                print("Warning: OPENAI_API_KEY not found in .env file")
    
    async def initialize(self):
        """Initialize the memory system."""
        print(f"Initializing memory system with {self.backend_type} backend...")
        self.memory_manager = MemoryManager(
            config={
                "stm": {"default_ttl": 3600},  # 1 hour TTL for STM memories
                "mtm": {"max_capacity": 1000},
                "ltm": {"maintenance_interval": 86400}  # 24 hours
            },
            mtm_storage_type=self.backend_type,
            ltm_storage_type=self.backend_type,
            vector_storage_type=BackendType.MEMORY  # Use in-memory for vector storage
        )
        
        await self.memory_manager.initialize()
        print("Memory system initialized successfully!")
    
    async def shutdown(self):
        """Shutdown the memory system."""
        if self.memory_manager:
            print("Shutting down memory system...")
            await self.memory_manager.shutdown()
            print("Memory system shut down successfully!")
    
    async def store_memory(self, content: str, source: str, importance: float = 0.7):
        """Store a new memory in the system."""
        memory_id = await self.memory_manager.add_memory(
            content=content,
            summary=f"From {source}: {content[:30]}...",
            importance=importance,
            tags=[source, "conversation"],
            metadata={
                "conversation_id": self.conversation_id,
                "timestamp": time.time(),
                "source": source
            },
            initial_tier="stm"  # Start in short-term memory
        )
        
        print(f"Added memory with ID: {memory_id}")
        return memory_id

    # Corrected indentation for this method
    async def retrieve_relevant_memories(self, query: str, limit: int = 5) -> List[MemorySearchResult]: # Return MemorySearchResult objects
        """Retrieve memories relevant to the current conversation."""
        try: # Ensure try is correctly indented
            search_results_obj = await self.memory_manager.search_memories( # Ensure this call is correctly indented
                query=query,
                limit=limit,
                min_relevance=0.3 # Only retrieve somewhat relevant memories
            )

            print(f"Retrieved {len(search_results_obj.results)} relevant memories")
            return search_results_obj.results # Return the list of MemorySearchResult objects
        except Exception as e: # Ensure except is aligned with try
            print(f"Error during memory retrieval: {e}")
            return [] # Return empty list on error

    async def process_message(self, user_message: str) -> str:
        """Process a user message and generate a response."""
        # Store the user's message in memory
        await self.store_memory(user_message, "user")
        
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": user_message})
        
        # Retrieve relevant memories
        relevant_memories = await self.retrieve_relevant_memories(user_message)
        
        # Format memories for context
        memory_context = ""
        if relevant_memories: # relevant_memories is now List[MemorySearchResult]
            memory_context = "Relevant previous information:\n"
            # Sort by relevance before formatting (highest first)
            relevant_memories.sort(key=lambda r: r.relevance, reverse=True)
            for i, search_result in enumerate(relevant_memories):
                # Access text via search_result.memory.get_text()
                memory_content = search_result.memory.get_text()
                memory_context += f"{i+1}. (Relevance: {search_result.relevance:.2f}) {memory_content}\n"

        # Generate response using OpenAI if available
        response = ""
        if OPENAI_AVAILABLE and openai.api_key:
            try:
                system_message = f"""You are a helpful assistant with memory capabilities. 
                You can remember previous parts of the conversation.
                
                {memory_context if memory_context else "No relevant memories found."}
                
                Base your response on the conversation history and relevant memories."""
                
                messages = [
                    {"role": "system", "content": system_message},
                    *self.conversation_history
                ]

                completion = openai.chat.completions.create(
                    model="gpt-4o", # Changed model name to gpt-4o
                    messages=messages,
                    # temperature=0.7, # Keeping temperature commented out for now
                    max_completion_tokens=500
                )

                # Debugging: Print the message object structure
                if completion.choices and completion.choices[0].message:
                    print(f"DEBUG: Message object: {completion.choices[0].message}")
                    response = completion.choices[0].message.content
                    if not response: # Check if content is empty
                         print("DEBUG: Response content is empty.")
                         response = "[Model returned empty content]" # Placeholder for empty response
                    else:
                         print(f"Generated response using OpenAI API")
                else:
                    print("DEBUG: No valid choices or message found in completion.")
                    response = "[Error retrieving model response]"

            except Exception as e:
                print(f"Error using OpenAI API: {e}")
                response = f"I'd respond to '{user_message}' here, but there was an issue with the OpenAI API. Using memory system with {self.backend_type} backend."
        else:
            # Fallback response without OpenAI
            response = f"I'd respond to '{user_message}' here. I've stored your message in my {self.backend_type} memory system."
            if memory_context:
                response += f"\n\nI remember: {memory_context}"
        
        # Store the assistant's response in memory
        await self.store_memory(response, "assistant")
        
        # Add to conversation history
        self.conversation_history.append({"role": "assistant", "content": response})
        
        return response

async def main():
    """Main function to demonstrate the agent."""
    # Create an agent with SQLite backend (more persistent)
    # Or use in-memory backend for faster testing (less persistent)
    use_sqlite = False  # Using in-memory backend for easier testing
    agent = ConversationalAgent(use_sqlite=use_sqlite)
    
    try:
        # Initialize the agent
        await agent.initialize()
        
        print("\n=== Conversational Memory Agent ===")
        print("Type 'exit' to end the conversation.")
        print("Backend: " + ("SQLite" if use_sqlite else "In-Memory"))
        print("OpenAI API: " + ("Available" if OPENAI_AVAILABLE and openai.api_key else "Not Available"))
        print("====================================\n")
        
        # Main conversation loop
        while True:
            user_input = input("\nYou: ")
            if user_input.lower() in ['exit', 'quit', 'bye']:
                break
            
            response = await agent.process_message(user_input)
            print(f"\nAgent: {response}")
            
            # Note: The memory manager runs maintenance tasks in the background automatically
            # We just simulate a message about it for demonstration purposes
            if agent.conversation_history and len(agent.conversation_history) % 10 == 0:
                print("\nMemory system is running maintenance tasks in the background.")
                print("These tasks include consolidation (STM → MTM → LTM) and memory decay.")
    
    finally:
        # Always shutdown properly
        await agent.shutdown()

if __name__ == "__main__":
    # Run the agent
    asyncio.run(main())
