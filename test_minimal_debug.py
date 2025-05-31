"""
Very basic test to identify the exact hanging point
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_step_by_step():
    """Test each individual method call"""
    
    print("🔍 Testing each step individually")
    
    try:
        print("✅ Step 0: Importing...")
        from neuroca.analysis.summarization_engine import create_summarization_engine
        print("   - Import successful")
        
        print("✅ Step 1: Creating engine...")
        workspace_path = str(Path(__file__).parent)
        engine = await create_summarization_engine(
            workspace_path=workspace_path,
            repos=["test-repo"],
            context_window=50000
        )
        print("   - Engine created")
        
        print("✅ Step 2: Testing _prepare_environment...")
        print("   - About to call _prepare_environment()")
        await engine._prepare_environment()
        print("   - _prepare_environment() completed")
        
        print("✅ All steps passed!")
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Starting test...")
    asyncio.run(test_step_by_step())
    print("Test finished.")
