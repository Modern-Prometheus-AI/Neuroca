"""
Test to count files that would actually be processed
"""

import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def count_files_to_process():
    """Count files that would be processed by the static analysis"""
    
    workspace_path = Path(__file__).parent
    
    # Default exclusion patterns from the code
    default_exclude_patterns = [
        "*.log", "*.tmp", "node_modules/", "__pycache__/", 
        ".git/", "*.pyc", "*.pyo", ".DS_Store"
    ]
    
    # Better exclusion patterns for this workspace
    better_exclude_patterns = [
        "*.log", "*.tmp", "node_modules/", "__pycache__/", 
        ".git/", "*.pyc", "*.pyo", ".DS_Store",
        "nca_env/", "venv/", "env/",  # Virtual environments
        "docs/site/", "site/",        # Generated docs
        "logs/", "*.log",             # Log files
        "coverage/", "htmlcov/",      # Coverage reports
        ".pytest_cache/", ".tox/",    # Test caches
        "build/", "dist/", "*.egg-info/",  # Build artifacts
        "*.pyc", "*.pyo", "*.pyd",    # Python compiled
        ".idea/", ".vscode/",         # IDE files
        "temp/", "tmp/", "cache/",    # Temp directories
    ]
    
    def should_exclude_file(file_path, exclude_patterns):
        """Check if file should be excluded"""
        relative_path = str(file_path.relative_to(workspace_path))
        
        for pattern in exclude_patterns:
            if file_path.match(pattern) or pattern.rstrip('/') in relative_path.split('/'):
                return True
        return False
    
    total_files = 0
    default_excluded = 0
    better_excluded = 0
    
    print("🔍 Analyzing file counts...")
    
    for file_path in workspace_path.rglob("*"):
        if file_path.is_file():
            total_files += 1
            
            if should_exclude_file(file_path, default_exclude_patterns):
                default_excluded += 1
            elif should_exclude_file(file_path, better_exclude_patterns):
                better_excluded += 1
    
    default_processed = total_files - default_excluded
    better_processed = total_files - default_excluded - better_excluded
    
    print(f"📊 File Analysis Results:")
    print(f"   Total files in workspace: {total_files:,}")
    print(f"   Files excluded by default patterns: {default_excluded:,}")
    print(f"   Files that would be processed (default): {default_processed:,}")
    print(f"   Additional files excluded by better patterns: {better_excluded:,}")
    print(f"   Files that would be processed (better): {better_processed:,}")
    print(f"   Reduction: {((default_processed - better_processed) / default_processed * 100):.1f}%")
    
    return default_processed, better_processed

if __name__ == "__main__":
    count_files_to_process()
