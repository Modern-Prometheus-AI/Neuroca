#!/usr/bin/env python3
"""
LLM Brain Demo - How to give an LLM cognitive capabilities using NCA

This demonstrates how the Neuro-Cognitive Architecture (NCA) serves as a
development kit to give Large Language Models a persistent "brain" with:
- Multi-tier memory system
- Health dynamics
- Cognitive state management
- Context persistence across conversations
"""

import sys
sys.path.insert(0, 'src')
import json
from datetime import datetime

class LLMBrain:
    """
    A cognitive wrapper that gives LLMs brain-like capabilities using NCA.
    
    This class demonstrates how NCA serves as a development kit to enhance
    LLMs with persistent memory, health dynamics, and cognitive state.
    """
    
    def __init__(self, llm_name="Generic LLM"):
        """Initialize the LLM's cognitive brain using NCA components."""
        self.llm_name = llm_name
        self.session_start = datetime.now()
        
        # Initialize NCA components
        self._init_memory_system()
        self._init_health_system()
        self._init_cognitive_state()
        
        print(f"🧠 Brain initialized for {llm_name}")
        print(f"   Memory System: Active")
        print(f"   Health Monitoring: Active") 
        print(f"   Cognitive State: Healthy")
    
    def _init_memory_system(self):
        """Set up the multi-tier memory system for the LLM."""
        from neuroca.memory import MemorySystem
        
        self.memory = MemorySystem()
        
        # These would store different types of LLM context:
        # - Working Memory: Current conversation context
        # - Episodic Memory: Previous conversation sessions  
        # - Semantic Memory: Learned knowledge and patterns
        
        print("   ✓ Memory tiers configured")
    
    def _init_health_system(self):
        """Set up health dynamics for cognitive state monitoring."""
        from neuroca.core.health import HealthState
        
        self.health_states = HealthState
        self.current_health = "HEALTHY"  # Would use actual HealthState enum
        
        # Track cognitive load, token usage, response quality, etc.
        self.cognitive_metrics = {
            'tokens_processed': 0,
            'conversations': 0, 
            'cognitive_load': 0.0,
            'response_quality': 1.0
        }
        
        print("   ✓ Health monitoring configured")
    
    def _init_cognitive_state(self):
        """Initialize persistent cognitive state."""
        self.cognitive_state = {
            'personality_drift': 0.0,
            'learned_preferences': {},
            'conversation_context': [],
            'long_term_goals': [],
            'current_focus': None
        }
        
        print("   ✓ Cognitive state initialized")
    
    def process_input(self, user_input, context=None):
        """
        Process user input through the cognitive brain before LLM processing.
        
        This is where the magic happens - the LLM gets cognitive capabilities:
        - Context from previous conversations (episodic memory)
        - Learned patterns and knowledge (semantic memory) 
        - Current conversation state (working memory)
        - Health-based response modulation
        """
        
        print(f"\n🔄 Processing: '{user_input}'")
        
        # 1. Update working memory with current input
        self._update_working_memory(user_input, context)
        
        # 2. Retrieve relevant memories
        relevant_context = self._retrieve_memories(user_input)
        
        # 3. Check cognitive health and adjust processing
        processing_mode = self._check_cognitive_health()
        
        # 4. Generate enhanced context for LLM
        enhanced_context = self._generate_enhanced_context(
            user_input, relevant_context, processing_mode
        )
        
        # 5. Simulate LLM response (in real usage, this would call actual LLM)
        llm_response = self._simulate_llm_response(enhanced_context)
        
        # 6. Store response in memory for future use
        self._store_response_memory(user_input, llm_response)
        
        # 7. Update cognitive metrics
        self._update_cognitive_metrics()
        
        return llm_response
    
    def _update_working_memory(self, input_text, context):
        """Add current input to working memory."""
        # In real implementation, this would use NCA memory components
        self.cognitive_state['conversation_context'].append({
            'timestamp': datetime.now().isoformat(),
            'input': input_text,
            'context': context
        })
        
        # Keep working memory bounded (like human working memory)
        if len(self.cognitive_state['conversation_context']) > 7:
            self.cognitive_state['conversation_context'].pop(0)
        
        print("   ✓ Working memory updated")
    
    def _retrieve_memories(self, query):
        """Retrieve relevant memories based on input query."""
        # This would use NCA's memory retrieval systems
        # For demo, we simulate finding relevant past conversations
        
        relevant = []
        for item in self.cognitive_state['conversation_context']:
            if any(word in item['input'].lower() for word in query.lower().split()):
                relevant.append(item)
        
        print(f"   ✓ Retrieved {len(relevant)} relevant memories")
        return relevant
    
    def _check_cognitive_health(self):
        """Check cognitive health and determine processing mode."""
        load = self.cognitive_metrics['cognitive_load']
        
        if load < 0.3:
            mode = "OPTIMAL"
        elif load < 0.7:
            mode = "MODERATE"
        else:
            mode = "STRESSED"
        
        print(f"   ✓ Cognitive health: {mode} (load: {load:.2f})")
        return mode
    
    def _generate_enhanced_context(self, input_text, memories, health_mode):
        """Generate enhanced context for the LLM including cognitive state."""
        
        context = {
            'user_input': input_text,
            'relevant_memories': memories,
            'cognitive_health': health_mode,
            'conversation_history': self.cognitive_state['conversation_context'][-3:],
            'learned_preferences': self.cognitive_state['learned_preferences'],
            'session_info': {
                'llm_name': self.llm_name,
                'session_duration': str(datetime.now() - self.session_start),
                'conversations': self.cognitive_metrics['conversations']
            }
        }
        
        print("   ✓ Enhanced context generated for LLM")
        return context
    
    def _simulate_llm_response(self, enhanced_context):
        """Simulate LLM response with cognitive enhancement."""
        
        # In real usage, this would be:
        # response = llm_api.generate(enhanced_context)
        
        # For demo, show how the enhanced context would improve responses
        input_text = enhanced_context['user_input']
        memories = enhanced_context['relevant_memories'] 
        health = enhanced_context['cognitive_health']
        
        response = f"[Cognitive Response] Based on our conversation history and my current {health.lower()} cognitive state, "
        
        if memories:
            response += f"I recall we discussed similar topics {len(memories)} times before. "
        
        response += f"My response to '{input_text}': This is where the actual LLM would generate a contextually-aware, memory-informed response."
        
        print("   ✓ LLM response generated with cognitive enhancement")
        return response
    
    def _store_response_memory(self, input_text, response):
        """Store the interaction in long-term memory."""
        # This would use NCA's memory consolidation systems
        
        memory_entry = {
            'timestamp': datetime.now().isoformat(),
            'input': input_text,
            'response': response,
            'cognitive_state': self.current_health
        }
        
        # In real implementation, this would trigger memory consolidation
        print("   ✓ Interaction stored in long-term memory")
    
    def _update_cognitive_metrics(self):
        """Update cognitive health metrics."""
        self.cognitive_metrics['conversations'] += 1
        self.cognitive_metrics['tokens_processed'] += 100  # Simulated
        
        # Simulate cognitive load (would be based on actual processing)
        self.cognitive_metrics['cognitive_load'] = min(
            0.9, 
            self.cognitive_metrics['conversations'] * 0.1
        )
        
        print("   ✓ Cognitive metrics updated")
    
    def get_brain_status(self):
        """Get current status of the LLM's cognitive brain."""
        return {
            'llm_name': self.llm_name,
            'session_duration': str(datetime.now() - self.session_start),
            'cognitive_health': self.current_health,
            'metrics': self.cognitive_metrics,
            'memory_items': len(self.cognitive_state['conversation_context']),
            'nca_components': {
                'memory_system': 'Active',
                'health_monitoring': 'Active',
                'cognitive_state': 'Tracking'
            }
        }

def demo_llm_brain():
    """Demonstrate how NCA gives an LLM cognitive capabilities."""
    
    print("🤖 LLM Brain Development Kit Demo")
    print("=" * 50)
    print("Showing how NCA serves as a dev kit to give LLMs a brain...")
    
    # Create an LLM with a cognitive brain
    llm_brain = LLMBrain("GPT-4-with-NCA-Brain")
    
    # Simulate a conversation session
    print(f"\n📝 Conversation Session:")
    print("-" * 30)
    
    # First interaction
    response1 = llm_brain.process_input("Hello, can you help me with Python programming?")
    print(f"🤖 {response1}")
    
    # Second interaction (should reference memory)
    response2 = llm_brain.process_input("What about Python data structures?")
    print(f"🤖 {response2}")
    
    # Third interaction (cognitive load building)  
    response3 = llm_brain.process_input("Can we go back to the Python topic?")
    print(f"🤖 {response3}")
    
    # Show brain status
    print(f"\n🧠 Brain Status:")
    print("-" * 20)
    status = llm_brain.get_brain_status()
    print(json.dumps(status, indent=2))
    
    print(f"\n💡 Key Benefits of NCA Brain for LLMs:")
    print("  • Persistent memory across conversations")
    print("  • Context awareness from previous sessions")
    print("  • Cognitive health monitoring")
    print("  • Structured knowledge storage")
    print("  • Personality and preference learning")
    print("  • Multi-tier memory system (working/episodic/semantic)")
    
    print(f"\n🚀 Development Kit Capabilities:")
    print("  • Drop-in cognitive enhancement for any LLM")
    print("  • Modular architecture - use what you need")
    print("  • Extensible for domain-specific cognitive features")
    print("  • Research-grade cognitive modeling")
    print("  • Production-ready memory management")

if __name__ == "__main__":
    demo_llm_brain()
