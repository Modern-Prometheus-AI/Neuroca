#!/usr/bin/env python3
"""
Simple import test for the summarization engine
"""

print("Starting import test...")
import sys
from pathlib import Path
print("Basic imports done...")

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    print("Testing imports...")
    from neuroca.analysis.summarization_engine import CodebaseSummarizationEngine
    print("✅ CodebaseSummarizationEngine imported successfully")
    
    from neuroca.analysis.summarization_engine import ScopeConfig
    print("✅ ScopeConfig imported successfully")
    
    from neuroca.analysis.summarization_engine import create_summarization_engine
    print("✅ create_summarization_engine imported successfully")
    
    print("🎉 All imports successful!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
    
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
