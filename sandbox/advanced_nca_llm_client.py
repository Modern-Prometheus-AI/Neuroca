#!/usr/bin/env python3
"""
Advanced NeuroCognitive Architecture (NCA) LLM Client
=====================================================

This client demonstrates the full power of Neuroca's cognitive architecture,
showcasing all major cognitive features:

1. 3-Tier Memory System (STM → MTM → LTM)
2. Cognitive Control (Attention, Goals, Planning, Decision Making)
3. Metacognitive Monitoring and Reflection
4. Memory Consolidation and Relationships
5. Context-Aware Processing
6. Health Monitoring and Self-Optimization

Usage:
    python sandbox/advanced_nca_llm_client.py
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import json

# Core NCA Imports
from neuroca.memory.manager.core import MemoryManager
from neuroca.memory.models.memory_item import MemoryItem, MemoryContent, MemoryMetadata
from neuroca.config.settings import Settings

# Cognitive Control Imports
try:
    from neuroca.core.cognitive_control.attention_manager import AttentionManager
    from neuroca.core.cognitive_control.goal_manager import GoalManager
    from neuroca.core.cognitive_control.decision_maker import DecisionMaker
    from neuroca.core.cognitive_control.metacognition import MetacognitiveMonitor
    from neuroca.core.cognitive_control.planner import CognitivePlanner
    from neuroca.core.cognitive_control.inhibitor import ResponseInhibitor
except ImportError as e:
    print(f"⚠️ Some cognitive control components not available: {e}")
    # Create minimal stubs for demo
    class AttentionManager:
        def __init__(self, *args, **kwargs): pass
        async def focus_on(self, *args, **kwargs): return "focused"
        async def get_current_focus(self): return {"focus": "demo"}
    
    class GoalManager:
        def __init__(self, *args, **kwargs): pass
        async def set_goal(self, *args, **kwargs): return "goal_set"
        async def get_active_goals(self): return []

    class DecisionMaker:
        def __init__(self, *args, **kwargs): pass
        async def make_decision(self, *args, **kwargs): return {"decision": "proceed", "confidence": 0.8}
    
    class MetacognitiveMonitor:
        def __init__(self, *args, **kwargs): pass
        async def reflect_on_performance(self, *args, **kwargs): return {"performance": "good"}
        async def log_error(self, *args, **kwargs): pass
    
    class CognitivePlanner:
        def __init__(self, *args, **kwargs): pass
        async def create_plan(self, *args, **kwargs): return {"plan": "demo_plan", "steps": []}
    
    class ResponseInhibitor:
        def __init__(self, *args, **kwargs): pass
        async def should_inhibit(self, *args, **kwargs): return False

# Integration Imports
try:
    from neuroca.integration.context.retrieval import ContextRetriever
    from neuroca.integration.context.injection import ContextInjector
except ImportError:
    print("⚠️ Context components not available - using minimal implementations")
    class ContextRetriever:
        def __init__(self, *args, **kwargs): pass
        async def retrieve_context(self, *args, **kwargs): return []
    
    class ContextInjector:
        def __init__(self, *args, **kwargs): pass
        async def inject_context(self, *args, **kwargs): return "context injected"

# Health Monitoring
try:
    from neuroca.core.health.monitor import HealthMonitor
except ImportError:
    print("⚠️ Health monitoring not available - using stub")
    class HealthMonitor:
        def __init__(self, *args, **kwargs): pass
        async def get_system_health(self): return {"status": "healthy", "score": 0.9}
        async def record_operation(self, *args, **kwargs): pass


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AdvancedNCAClient:
    """
    Advanced NeuroCognitive Architecture LLM Client
    
    This client demonstrates the full cognitive architecture with:
    - Multi-tier memory management
    - Cognitive control processes
    - Metacognitive monitoring
    - Context-aware processing
    - Health monitoring and optimization
    """
    
    def __init__(self):
        """Initialize the advanced NCA client."""
        self.memory_manager: Optional[MemoryManager] = None
        self.attention_manager: Optional[AttentionManager] = None
        self.goal_manager: Optional[GoalManager] = None
        self.decision_maker: Optional[DecisionMaker] = None
        self.metacognitive_monitor: Optional[MetacognitiveMonitor] = None
        self.cognitive_planner: Optional[CognitivePlanner] = None
        self.response_inhibitor: Optional[ResponseInhibitor] = None
        self.context_retriever: Optional[ContextRetriever] = None
        self.context_injector: Optional[ContextInjector] = None
        self.health_monitor: Optional[HealthMonitor] = None
        
        # Client state
        self.session_id = f"nca_session_{int(time.time())}"
        self.conversation_history = []
        self.cognitive_state = {
            "current_goals": [],
            "attention_focus": None,
            "working_memory_items": [],
            "recent_decisions": [],
            "performance_metrics": {}
        }
        
        print("🧠 Advanced NCA LLM Client Initialized")
        print(f"📝 Session ID: {self.session_id}")
    
    async def initialize(self):
        """Initialize all NCA components."""
        try:
            print("\n🔧 Initializing NCA Components...")
            
            # Initialize core memory system
            print("  💾 Initializing Memory Manager...")
            self.memory_manager = MemoryManager()
            await self.memory_manager.initialize()
            
            # Initialize cognitive control components
            print("  🎯 Initializing Attention Manager...")
            self.attention_manager = AttentionManager(
                memory_manager=self.memory_manager
            )
            
            print("  🎪 Initializing Goal Manager...")
            self.goal_manager = GoalManager(
                memory_manager=self.memory_manager
            )
            
            print("  🤔 Initializing Decision Maker...")
            self.decision_maker = DecisionMaker(
                memory_manager=self.memory_manager,
                attention_manager=self.attention_manager
            )
            
            print("  🔍 Initializing Metacognitive Monitor...")
            self.metacognitive_monitor = MetacognitiveMonitor(
                memory_manager=self.memory_manager
            )
            
            print("  📋 Initializing Cognitive Planner...")
            self.cognitive_planner = CognitivePlanner(
                memory_manager=self.memory_manager,
                goal_manager=self.goal_manager
            )
            
            print("  🛡️ Initializing Response Inhibitor...")
            self.response_inhibitor = ResponseInhibitor(
                memory_manager=self.memory_manager
            )
            
            # Initialize context components
            print("  📄 Initializing Context Systems...")
            self.context_retriever = ContextRetriever(
                working_memory=None,  # Will use memory manager
                episodic_memory=None,
                semantic_memory=None
            )
            
            self.context_injector = ContextInjector()
            
            # Initialize health monitoring
            print("  ❤️ Initializing Health Monitor...")
            self.health_monitor = HealthMonitor()
            
            print("✅ All NCA Components Initialized Successfully!")
            
        except Exception as e:
            logger.error(f"Failed to initialize NCA components: {str(e)}")
            print(f"❌ Initialization failed: {str(e)}")
            raise
    
    async def process_user_input(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process user input through the full NCA cognitive pipeline.
        
        Args:
            user_input: The user's input text
            context: Optional additional context
            
        Returns:
            Dict containing the processed response and cognitive state
        """
        start_time = time.time()
        context = context or {}
        
        print(f"\n🎤 Processing User Input: '{user_input[:50]}...'")
        
        try:
            # Phase 1: Attention and Focus
            print("  🎯 Phase 1: Attention Management")
            attention_result = await self.attention_manager.focus_on(
                stimulus=user_input,
                context=context
            )
            current_focus = await self.attention_manager.get_current_focus()
            self.cognitive_state["attention_focus"] = current_focus
            print(f"    → Focus: {current_focus}")
            
            # Phase 2: Memory Retrieval and Context
            print("  💭 Phase 2: Memory and Context Retrieval")
            relevant_memories = await self._retrieve_relevant_memories(user_input)
            context_data = await self._build_context(user_input, relevant_memories)
            self.cognitive_state["working_memory_items"] = relevant_memories[:5]  # Keep top 5
            print(f"    → Retrieved {len(relevant_memories)} relevant memories")
            
            # Phase 3: Goal Processing
            print("  🎪 Phase 3: Goal Management")
            await self._process_goals(user_input, context)
            active_goals = await self.goal_manager.get_active_goals()
            self.cognitive_state["current_goals"] = active_goals
            print(f"    → Active goals: {len(active_goals)}")
            
            # Phase 4: Planning
            print("  📋 Phase 4: Cognitive Planning")
            plan = await self.cognitive_planner.create_plan(
                goal_description=f"Respond to: {user_input}",
                context=context_data
            )
            print(f"    → Plan created: {plan.get('plan', 'default')}")
            
            # Phase 5: Decision Making
            print("  🤔 Phase 5: Decision Making")
            decision = await self.decision_maker.make_decision(
                situation=user_input,
                options=["respond", "ask_clarification", "defer"],
                context=context_data
            )
            self.cognitive_state["recent_decisions"].append(decision)
            print(f"    → Decision: {decision.get('decision', 'respond')} (confidence: {decision.get('confidence', 0.8):.2f})")
            
            # Phase 6: Response Inhibition Check
            print("  🛡️ Phase 6: Response Inhibition")
            should_inhibit = await self.response_inhibitor.should_inhibit(
                response_candidate=f"Response to: {user_input}",
                context=context_data
            )
            print(f"    → Inhibition check: {'BLOCKED' if should_inhibit else 'ALLOWED'}")
            
            # Phase 7: Generate Response
            print("  💬 Phase 7: Response Generation")
            if should_inhibit:
                response = "I need to think more carefully about this before responding."
            else:
                response = await self._generate_response(
                    user_input=user_input,
                    context_data=context_data,
                    plan=plan,
                    decision=decision
                )
            
            # Phase 8: Memory Storage
            print("  💾 Phase 8: Memory Storage")
            await self._store_interaction(user_input, response, context_data)
            
            # Phase 9: Metacognitive Reflection
            print("  🔍 Phase 9: Metacognitive Reflection")
            processing_time = time.time() - start_time
            reflection = await self.metacognitive_monitor.reflect_on_performance(
                task="process_user_input",
                performance_data={
                    "processing_time": processing_time,
                    "memories_retrieved": len(relevant_memories),
                    "decision_confidence": decision.get("confidence", 0.8),
                    "response_length": len(response)
                }
            )
            print(f"    → Reflection: {reflection.get('performance', 'good')}")
            
            # Phase 10: Health Monitoring
            print("  ❤️ Phase 10: Health Monitoring")
            await self.health_monitor.record_operation(
                operation="process_user_input",
                duration=processing_time,
                success=True
            )
            health_status = await self.health_monitor.get_system_health()
            
            # Build response package
            response_package = {
                "response": response,
                "cognitive_state": self.cognitive_state.copy(),
                "processing_time": processing_time,
                "health_status": health_status,
                "memories_accessed": len(relevant_memories),
                "decision": decision,
                "plan": plan,
                "attention_focus": current_focus,
                "reflection": reflection,
                "inhibited": should_inhibit
            }
            
            print(f"✅ Processing Complete! ({processing_time:.2f}s)")
            return response_package
            
        except Exception as e:
            # Metacognitive error handling
            await self.metacognitive_monitor.log_error(
                error_type="processing_error",
                error_details={"message": str(e), "input": user_input}
            )
            logger.error(f"Error processing user input: {str(e)}")
            return {
                "response": "I encountered an error while processing your request. Let me try a different approach.",
                "error": str(e),
                "cognitive_state": self.cognitive_state.copy()
            }
    
    async def _retrieve_relevant_memories(self, query: str) -> List[Dict[str, Any]]:
        """Retrieve relevant memories from all tiers."""
        try:
            # Search across all memory tiers
            memories = []
            
            # STM search
            stm_results = await self.memory_manager.search(
                query=query,
                tier="stm",
                limit=10
            )
            memories.extend([{"tier": "stm", "memory": m} for m in stm_results])
            
            # MTM search
            mtm_results = await self.memory_manager.search(
                query=query,
                tier="mtm",
                limit=15
            )
            memories.extend([{"tier": "mtm", "memory": m} for m in mtm_results])
            
            # LTM search
            ltm_results = await self.memory_manager.search(
                query=query,
                tier="ltm",
                limit=20
            )
            memories.extend([{"tier": "ltm", "memory": m} for m in ltm_results])
            
            # Sort by relevance and return top results
            memories.sort(key=lambda x: getattr(x["memory"], "relevance", 0.5), reverse=True)
            return memories[:25]  # Return top 25 most relevant
            
        except Exception as e:
            logger.error(f"Error retrieving memories: {str(e)}")
            return []
    
    async def _build_context(self, user_input: str, memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build rich context from memories and current state."""
        context = {
            "user_input": user_input,
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "conversation_turn": len(self.conversation_history) + 1,
            "relevant_memories": memories,
            "cognitive_state": self.cognitive_state.copy(),
            "memory_summary": {
                "stm_count": len([m for m in memories if m["tier"] == "stm"]),
                "mtm_count": len([m for m in memories if m["tier"] == "mtm"]),
                "ltm_count": len([m for m in memories if m["tier"] == "ltm"]),
                "total_relevance": sum(getattr(m["memory"], "relevance", 0.5) for m in memories)
            }
        }
        return context
    
    async def _process_goals(self, user_input: str, context: Dict[str, Any]):
        """Process and update goals based on user input."""
        try:
            # Check if user input suggests new goals
            if any(word in user_input.lower() for word in ["goal", "want", "need", "plan", "achieve"]):
                await self.goal_manager.set_goal(
                    description=f"Address user request: {user_input}",
                    priority="high",
                    context=context
                )
        except Exception as e:
            logger.error(f"Error processing goals: {str(e)}")
    
    async def _generate_response(self, user_input: str, context_data: Dict[str, Any], 
                                plan: Dict[str, Any], decision: Dict[str, Any]) -> str:
        """Generate a response based on all cognitive processing."""
        # This is a simplified response generator
        # In a real implementation, this would interface with an LLM
        
        memory_context = ""
        if context_data["relevant_memories"]:
            top_memory = context_data["relevant_memories"][0]["memory"]
            memory_context = f" (I recall: {getattr(top_memory, 'content', {}).get('text', 'previous context')})"
        
        confidence = decision.get("confidence", 0.8)
        confidence_phrase = "I'm confident" if confidence > 0.8 else "I think" if confidence > 0.6 else "I'm not entirely sure, but"
        
        response = f"{confidence_phrase} I can help with that.{memory_context} Based on my cognitive processing, here's my response to your input: '{user_input}'"
        
        return response
    
    async def _store_interaction(self, user_input: str, response: str, context_data: Dict[str, Any]):
        """Store the interaction in appropriate memory tiers."""
        try:
            # Store in STM (working memory)
            interaction_content = MemoryContent(
                text=f"User: {user_input}\nAssistant: {response}",
                summary=f"Conversation turn {context_data['conversation_turn']}",
                content_type="conversation"
            )
            
            interaction_metadata = MemoryMetadata(
                tags={"conversation": True, "session": self.session_id},
                source="nca_client",
                importance=0.7,
                additional_metadata={
                    "turn_number": context_data["conversation_turn"],
                    "processing_time": context_data.get("processing_time"),
                    "user_input_length": len(user_input),
                    "response_length": len(response)
                }
            )
            
            memory_item = MemoryItem(
                content=interaction_content,
                metadata=interaction_metadata,
                summary="Conversation interaction"
            )
            
            memory_id = await self.memory_manager.store(memory_item, tier="stm")
            print(f"    → Stored interaction in STM: {memory_id}")
            
            # Update conversation history
            self.conversation_history.append({
                "user_input": user_input,
                "response": response,
                "memory_id": memory_id,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error storing interaction: {str(e)}")
    
    async def demonstrate_cognitive_features(self):
        """Demonstrate all major cognitive features of the NCA."""
        print("\n🎪 NCA Cognitive Features Demonstration")
        print("=" * 50)
        
        try:
            # 1. Memory System Demo
            print("\n1️⃣ Multi-Tier Memory System Demo")
            await self._demo_memory_system()
            
            # 2. Cognitive Control Demo
            print("\n2️⃣ Cognitive Control Demo")
            await self._demo_cognitive_control()
            
            # 3. Metacognition Demo
            print("\n3️⃣ Metacognitive Monitoring Demo")
            await self._demo_metacognition()
            
            # 4. Context Processing Demo
            print("\n4️⃣ Context-Aware Processing Demo")
            await self._demo_context_processing()
            
            # 5. Health Monitoring Demo
            print("\n5️⃣ Health Monitoring Demo")
            await self._demo_health_monitoring()
            
            print("\n🎉 Cognitive Features Demonstration Complete!")
            
        except Exception as e:
            logger.error(f"Error in demonstration: {str(e)}")
            print(f"❌ Demonstration failed: {str(e)}")
    
    async def _demo_memory_system(self):
        """Demonstrate the 3-tier memory system."""
        print("  💾 Creating memories across all tiers...")
        
        # STM - Current working context
        stm_memory = MemoryItem(
            content=MemoryContent(text="User is asking about NCA capabilities", content_type="working_context"),
            metadata=MemoryMetadata(tags={"working": True}, importance=0.8),
            summary="Current conversation context"
        )
        stm_id = await self.memory_manager.store(stm_memory, tier="stm")
        print(f"    → STM: {stm_id}")
        
        # MTM - Recent important information
        mtm_memory = MemoryItem(
            content=MemoryContent(text="NCA provides cognitive architecture for LLMs", content_type="knowledge"),
            metadata=MemoryMetadata(tags={"knowledge": True}, importance=0.7),
            summary="NCA core concept"
        )
        mtm_id = await self.memory_manager.store(mtm_memory, tier="mtm")
        print(f"    → MTM: {mtm_id}")
        
        # LTM - Fundamental knowledge
        ltm_memory = MemoryItem(
            content=MemoryContent(text="Cognitive architectures model human cognition", content_type="fundamental"),
            metadata=MemoryMetadata(tags={"cognitive_science": True}, importance=0.9),
            summary="Cognitive architecture principles"
        )
        ltm_id = await self.memory_manager.store(ltm_memory, tier="ltm")
        print(f"    → LTM: {ltm_id}")
        
        # Demonstrate memory retrieval
        print("  🔍 Testing memory retrieval...")
        retrieved = await self.memory_manager.retrieve(stm_id)
        print(f"    → Retrieved: {retrieved.content.text[:30]}...")
    
    async def _demo_cognitive_control(self):
        """Demonstrate cognitive control components."""
        print("  🎯 Testing attention management...")
        focus_result = await self.attention_manager.focus_on("NCA demonstration")
        current_focus = await self.attention_manager.get_current_focus()
        print(f"    → Current focus: {current_focus}")
        
        print("  🎪 Testing goal management...")
        await self.goal_manager.set_goal("Demonstrate NCA capabilities", priority="high")
        goals = await self.goal_manager.get_active_goals()
        print(f"    → Active goals: {len(goals)}")
        
        print("  📋 Testing cognitive planning...")
        plan = await self.cognitive_planner.create_plan("Show NCA features")
        print(f"    → Plan: {plan.get('plan', 'generated')}")
        
        print("  🤔 Testing decision making...")
        decision = await self.decision_maker.make_decision(
            situation="User wants to see NCA demo",
            options=["full_demo", "quick_overview", "detailed_explanation"]
        )
        print(f"    → Decision: {decision.get('decision', 'proceed')}")
    
    async def _demo_metacognition(self):
        """Demonstrate metacognitive monitoring."""
        print("  🔍 Performing metacognitive reflection...")
        reflection = await self.metacognitive_monitor.reflect_on_performance(
            task="nca_demonstration",
            performance_data={"demo_step": 3, "user_engagement": "high"}
        )
        print(f"    → Reflection: {reflection.get('performance', 'good')}")
        
        print("  📊 Updating performance metrics...")
        self.cognitive_state["performance_metrics"] = {
            "tasks_completed": 3,
            "average_response_time": 0.5,
            "memory_efficiency": 0.85,
            "decision_accuracy": 0.9
        }
        print(f"    → Metrics updated: {len(self.cognitive_state['performance_metrics'])} metrics")
    
    async def _demo_context_processing(self):
        """Demonstrate context-aware processing."""
        print("  📄 Building rich context...")
        context = await self._build_context("What can NCA do?", [])
        print(f"    → Context elements: {len(context)} items")
        
        print("  🔗 Demonstrating context injection...")
        injected = await self.context_injector.inject_context(
            base_prompt="Explain NCA",
            context_items=["Memory tiers", "Cognitive control", "Metacognition"]
        )
        print(f"    → Context injected: {injected}")
    
    async def _demo_health_monitoring(self):
        """Demonstrate health monitoring."""
        print("  ❤️ Checking system health...")
        health = await self.health_monitor.get_system_health()
        print(f"    → Health status: {health.get('status', 'healthy')}")
        print(f"    → Health score: {health.get('score', 0.9):.2f}")
        
        print("  📊 Recording operation metrics...")
        await self.health_monitor.record_operation("demo_operation", 0.1, True)
        print("    → Operation recorded")
    
    async def interactive_session(self):
        """Run an interactive session with the user."""
        print("\n🎮 Starting Interactive NCA Session")
        print("Type 'quit' to exit, 'demo' for feature demo, 'status' for cognitive state")
        print("-" * 60)
        
        while True:
            try:
                user_input = input("\n👤 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Goodbye! Thanks for exploring NCA!")
                    break
                elif user_input.lower() == 'demo':
                    await self.demonstrate_cognitive_features()
                    continue
                elif user_input.lower() == 'status':
                    await self._show_cognitive_status()
                    continue
                elif not user_input:
                    continue
                
                # Process the input through full cognitive pipeline
                result = await self.process_user_input(user_input)
                
                print(f"\n🧠 NCA: {result['response']}")
                
                # Show brief cognitive summary
                if result.get('processing_time'):
                    print(f"   💭 Processed in {result['processing_time']:.2f}s using {result.get('memories_accessed', 0)} memories")
                
            except KeyboardInterrupt:
                print("\n\n👋 Session interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                logger.error(f"Interactive session error: {str(e)}")
    
    async def _show_cognitive_status(self):
        """Show current cognitive state."""
        print("\n🧠 Current Cognitive State:")
        print(f"  🎯 Attention: {self.cognitive_state.get('attention_focus', 'None')}")
        print(f"  🎪 Goals: {len(self.cognitive_state.get('current_goals', []))} active")
        print(f"  💭 Working Memory: {len(self.cognitive_state.get('working_memory_items', []))} items")
        print(f"  🤔 Recent Decisions: {len(self.cognitive_state.get('recent_decisions', []))}")
        print(f"  💬 Conversation History: {len(self.conversation_history)} turns")
        
        if self.cognitive_state.get('performance_metrics'):
            print(f"  📊 Performance Metrics:")
            for metric, value in self.cognitive_state['performance_metrics'].items():
                print(f"    • {metric}: {value}")
    
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
                "final_cognitive_state": self.cognitive_state,
                "session_duration": time.time()
            }
            
            with open(f"sandbox/session_{self.session_id}.json", "w") as f:
                json.dump(session_summary, f, indent=2, default=str)
            
            print(f"  💾 Session summary saved: session_{self.session_id}.json")
            print("🏁 NCA Client shutdown complete!")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")
            print(f"❌ Shutdown error: {str(e)}")


async def main():
    """Main entry point for the advanced NCA client."""
    print("🚀 Starting Advanced NeuroCognitive Architecture (NCA) LLM Client")
    print("=" * 60)
    
    client = AdvancedNCAClient()
    
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
