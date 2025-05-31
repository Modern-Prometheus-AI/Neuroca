"""
Test to measure Step 3 (static analysis) timing
"""

import asyncio
import time
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_step3_timing():
    """Test Step 3 static analysis with detailed timing"""
    
    print("🔍 Testing Step 3 (Static Analysis) timing")
    
    try:
        print("✅ Setup: Creating engine...")
        from neuroca.analysis.summarization_engine import create_summarization_engine
        
        workspace_path = str(Path(__file__).parent)
        engine = await create_summarization_engine(
            workspace_path=workspace_path,
            repos=["test-repo"],
            context_window=50000
        )
        print("   - Engine created")
        
        # Step 2 first (required)
        print("✅ Step 2: Environment preparation...")
        start_time = time.time()
        await engine._prepare_environment()
        step2_time = time.time() - start_time
        print(f"   - Step 2 completed in {step2_time:.2f} seconds")
        
        # Step 3: Static Analysis with timing
        print("✅ Step 3: Static analysis...")
        start_time = time.time()
        
        # Test the main static analysis
        await engine._static_analysis()
        
        step3_time = time.time() - start_time
        print(f"   - Step 3 completed in {step3_time:.2f} seconds")
        
        # Check what was analyzed
        print("✅ Analysis results:")
        print(f"   - Files analyzed: {len(engine.file_metadata)}")
        print(f"   - Components found: {len(engine.component_metadata)}")
        
        # Show some sample files analyzed
        if engine.file_metadata:
            print("   - Sample analyzed files:")
            for i, (file_path, metadata) in enumerate(list(engine.file_metadata.items())[:5]):
                print(f"     • {file_path} ({metadata.language}, {metadata.lines_of_code} LOC)")
                if i >= 4:  # Show only first 5
                    break
                    
        print(f"✅ Total Step 3 time: {step3_time:.2f} seconds")
        
        return step3_time
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("Starting Step 3 timing test...")
    result = asyncio.run(test_step3_timing())
    if result:
        print(f"\n📊 Final Result: Step 3 took {result:.2f} seconds")
    else:
        print("\n❌ Test failed")
