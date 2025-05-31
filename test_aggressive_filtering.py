#!/usr/bin/env python3
"""
Test more aggressive file filtering to reduce the file count for Step 3.
"""

import sys
import os
sys.path.insert(0, 'src')

from src.neuroca.analysis.summarization_engine import SummarizationEngine

def test_aggressive_filtering():
    """Test with more aggressive filtering to reduce file processing."""
    print("🔍 Testing aggressive file filtering...")
    
    # Create engine
    engine = SummarizationEngine(base_path=".")
    
    # Count files with current filtering
    print("\n📊 Current gitignore filtering:")
    current_files = list(engine._enumerate_files())
    print(f"   Files found: {len(current_files)}")
    
    # Test additional aggressive filters
    print("\n🔥 Testing aggressive filtering:")
    
    # Only process common source code files
    source_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', '.hpp', '.cs', '.go', '.rs', '.php', '.rb', '.swift', '.kt'}
    
    # Only process files under common source directories
    source_dirs = {'src', 'lib', 'app', 'components', 'utils', 'services', 'models', 'views', 'controllers'}
    
    aggressive_files = []
    for file_path in current_files:
        # Check extension
        _, ext = os.path.splitext(file_path)
        if ext not in source_extensions:
            continue
            
        # Check if it's in a source directory
        path_parts = file_path.replace('\\', '/').split('/')
        if not any(part in source_dirs for part in path_parts):
            continue
            
        # Skip test files for now
        if 'test' in file_path.lower() or 'spec' in file_path.lower():
            continue
            
        # Skip files larger than 1MB
        try:
            if os.path.getsize(file_path) > 1024 * 1024:
                continue
        except:
            continue
            
        aggressive_files.append(file_path)
    
    print(f"   Aggressive filtering: {len(aggressive_files)} files")
    print(f"   Reduction: {((len(current_files) - len(aggressive_files)) / len(current_files) * 100):.1f}%")
    
    # Show some examples
    print(f"\n📂 Sample filtered files (first 10):")
    for i, file_path in enumerate(aggressive_files[:10]):
        print(f"   {i+1}. {file_path}")
    
    if len(aggressive_files) > 10:
        print(f"   ... and {len(aggressive_files) - 10} more")

if __name__ == "__main__":
    test_aggressive_filtering()
