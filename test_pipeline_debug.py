"""
Debug test for the summarization pipeline to identify where it hangs
"""

import asyncio
import tempfile
import pytest
from pathlib import Path
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from neuroca.analysis.summarization_engine import create_summarization_engine

@pytest.mark.asyncio
async def test_pipeline_step_by_step():
    """Test each step of the pipeline individually to find where it hangs"""
    
    print("\n🔍 Starting step-by-step pipeline debug test")
    
    # Use current workspace as test target
    workspace_path = str(Path(__file__).parent)
    
    try:
        print("✅ Step 0: Creating summarization engine...")
        engine = await create_summarization_engine(
            workspace_path=workspace_path,
            repos=["test-repo"],
            context_window=50000  # Smaller context for faster testing
        )
        print("✅ Engine created successfully")
        
        print("✅ Step 1: Testing scope configuration...")
        assert engine.scope is not None
        print(f"   - Repos: {engine.scope.repos}")
        print(f"   - Context window: {engine.scope.target_llm_profile['context_window']}")
        print("✅ Step 2: Testing environment preparation...")
        await engine._prepare_environment()
        print("   - Environment prep completed")
        
        print("✅ Step 3: Testing static analysis (limited)...")
        # Test the actual static analysis method
        try:
            await engine._static_analysis()
            print("   - Static analysis completed")
        except Exception as e:
            print(f"   - Static analysis failed: {e}")
            # Let's test just file enumeration which is simpler
            print("   - Trying just file enumeration...")
            try:
                await engine._enumerate_files()
                print("   - File enumeration completed")
            except Exception as e2:
                print(f"   - File enumeration also failed: {e2}")
        
        print("✅ Static analysis step completed")
        
        print("✅ Step 4: Testing metadata packaging...")
        await engine._package_metadata()
        print("   - Metadata packaging completed")
        
        print("✅ Step 5: Testing chunking (limited)...")
        chunks = await engine._chunk_and_summarize()
        print(f"   - Created {len(chunks)} chunks")
        
        print("✅ All basic steps completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed at step: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Run the test directly
    asyncio.run(test_pipeline_step_by_step())
