#!/usr/bin/env python3
"""
Test more aggressive file filtering to reduce the file count for Step 3.
"""

import sys
import os
from pathlib import Path
import fnmatch
sys.path.insert(0, 'src')

def load_gitignore_patterns(workspace_path):
    """Load and parse .gitignore file patterns"""
    gitignore_file = Path(workspace_path) / ".gitignore"
    patterns = []
    
    if gitignore_file.exists():
        try:
            with open(gitignore_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        # Remove leading slash and convert to glob pattern
                        if line.startswith('/'):
                            line = line[1:]
                        patterns.append(line)
            print(f"Loaded {len(patterns)} patterns from .gitignore")
        except Exception as e:
            print(f"Could not read .gitignore: {e}")
    else:
        print("No .gitignore file found")
        
    # Add some essential patterns if not present
    essential_patterns = [
        "__pycache__", "*.pyc", "*.pyo", ".git", ".pytest_cache", 
        "node_modules", ".mypy_cache", ".ruff_cache"
    ]
    for pattern in essential_patterns:
        if pattern not in patterns:
            patterns.append(pattern)
            
    return patterns

def should_exclude_file(file_path, workspace_path, gitignore_patterns):
    """Check if file should be excluded based on .gitignore patterns"""
    try:
        relative_path = file_path.relative_to(workspace_path)
        relative_path_str = str(relative_path)
        relative_path_posix = relative_path.as_posix()  # Use forward slashes
        
        # Check against .gitignore patterns
        for pattern in gitignore_patterns:
            # Handle directory patterns (ending with /)
            if pattern.endswith('/'):
                pattern_for_dirs = pattern.rstrip('/')
                # Check if any parent directory matches
                for parent in relative_path.parents:
                    if fnmatch.fnmatch(str(parent), pattern_for_dirs) or \
                       fnmatch.fnmatch(parent.as_posix(), pattern_for_dirs):
                        return True
            else:
                # Check file and directory patterns
                if fnmatch.fnmatch(relative_path_str, pattern) or \
                   fnmatch.fnmatch(relative_path_posix, pattern) or \
                   fnmatch.fnmatch(file_path.name, pattern):
                    return True
                
                # Check if pattern matches any parent directory
                for parent in relative_path.parents:
                    if fnmatch.fnmatch(str(parent), pattern) or \
                       fnmatch.fnmatch(parent.as_posix(), pattern):
                        return True
        
        # Additional size-based exclusion for very large files
        try:
            if file_path.is_file() and file_path.stat().st_size > 50 * 1024 * 1024:  # 50MB
                return True
        except OSError:
            pass  # File might not be accessible
            
        return False
        
    except ValueError:
        # File is not relative to workspace (shouldn't happen)
        return True
    except Exception:
        return True  # Exclude on error to be safe

def test_aggressive_filtering():
    """Test with more aggressive filtering to reduce file processing."""
    print("🔍 Testing aggressive file filtering...")
    
    workspace_path = Path(".")
    gitignore_patterns = load_gitignore_patterns(workspace_path)
    
    # Count files with current gitignore filtering
    print("\n📊 Current gitignore filtering:")
    current_files = []
    for file_path in workspace_path.rglob("*"):
        if file_path.is_file() and not should_exclude_file(file_path, workspace_path, gitignore_patterns):
            current_files.append(file_path)
    
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
        path_parts = str(file_path).replace('\\', '/').split('/')
        if not any(part in source_dirs for part in path_parts):
            continue
            
        # Skip test files for now
        if 'test' in str(file_path).lower() or 'spec' in str(file_path).lower():
            continue
            
        # Skip files larger than 1MB
        try:
            if file_path.stat().st_size > 1024 * 1024:
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
