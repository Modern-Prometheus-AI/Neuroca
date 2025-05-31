"""
Simple debug test to isolate the hanging issue
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_simple_creation():
    """Test just the engine creation step by step"""
    
    print("🔍 Testing engine creation step by step")
    
    try:
        print("✅ Step 0: Import test...")
        from neuroca.analysis.summarization_engine import ScopeConfig, CodebaseSummarizationEngine
        print("   - Imports successful")
        
        print("✅ Step 1: Create scope config...")
        scope = ScopeConfig(
            repos=["test-repo"],
            branches=["main"],
            target_llm_profile={
                "context_window": 50000,
                "input_limits": 40000,
                "accepted_formats": ["json", "markdown", "yaml"],
                "rate_limits": {"requests_per_minute": 60}
            }
        )
        print("   - Scope config created")
        
        print("✅ Step 2: Create engine...")
        workspace_path = str(Path(__file__).parent)
        engine = CodebaseSummarizationEngine(scope, workspace_path)
        print("   - Engine created successfully")
        
        print("✅ Step 3: Check engine attributes...")
        print(f"   - Workspace path: {engine.workspace_path}")
        print(f"   - Output dir: {engine.output_dir}")
        print(f"   - Scope repos: {engine.scope.repos}")
        
        print("✅ All steps completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Run the test directly
    asyncio.run(test_simple_creation())
