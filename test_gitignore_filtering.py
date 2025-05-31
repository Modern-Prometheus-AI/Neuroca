"""
Test to show the difference in file count with gitignore filtering
"""

import sys
from pathlib import Path
import fnmatch

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def load_gitignore_patterns(workspace_path: Path) -> list[str]:
    """Load .gitignore patterns"""
    gitignore_file = workspace_path / ".gitignore"
    patterns = []
    
    if gitignore_file.exists():
        with open(gitignore_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if line.startswith('/'):
                        line = line[1:]
                    patterns.append(line)
    
    # Add essential patterns
    essential_patterns = [
        "__pycache__", "*.pyc", "*.pyo", ".git", ".pytest_cache", 
        "node_modules", ".mypy_cache", ".ruff_cache"
    ]
    for pattern in essential_patterns:
        if pattern not in patterns:
            patterns.append(pattern)
            
    return patterns

def should_exclude_file(file_path: Path, workspace_path: Path, patterns: list[str]) -> bool:
    """Check if file should be excluded"""
    try:
        relative_path = file_path.relative_to(workspace_path)
        relative_path_str = str(relative_path)
        relative_path_posix = relative_path.as_posix()
        
        for pattern in patterns:
            if pattern.endswith('/'):
                pattern_for_dirs = pattern.rstrip('/')
                for parent in relative_path.parents:
                    if fnmatch.fnmatch(str(parent), pattern_for_dirs) or \
                       fnmatch.fnmatch(parent.as_posix(), pattern_for_dirs):
                        return True
            else:
                if fnmatch.fnmatch(relative_path_str, pattern) or \
                   fnmatch.fnmatch(relative_path_posix, pattern) or \
                   fnmatch.fnmatch(file_path.name, pattern):
                    return True
                
                for parent in relative_path.parents:
                    if fnmatch.fnmatch(str(parent), pattern) or \
                       fnmatch.fnmatch(parent.as_posix(), pattern):
                        return True
        
        # Size check
        try:
            if file_path.is_file() and file_path.stat().st_size > 50 * 1024 * 1024:
                return True
        except OSError:
            pass
            
        return False
    except ValueError:
        return True

def test_file_filtering():
    """Test the file filtering with gitignore patterns"""
    
    print("🔍 Testing file filtering with .gitignore patterns")
    
    workspace_path = Path(__file__).parent
    patterns = load_gitignore_patterns(workspace_path)
    
    print(f"✅ Loaded {len(patterns)} .gitignore patterns")
    print("   Sample patterns:")
    for pattern in patterns[:10]:
        print(f"     • {pattern}")
    if len(patterns) > 10:
        print(f"     ... and {len(patterns) - 10} more")
    
    print("\n📊 Counting files...")
    
    total_files = 0
    included_files = 0
    excluded_files = 0
    
    excluded_samples = []
    included_samples = []
    
    for file_path in workspace_path.rglob("*"):
        if file_path.is_file():
            total_files += 1
            
            if should_exclude_file(file_path, workspace_path, patterns):
                excluded_files += 1
                if len(excluded_samples) < 10:
                    excluded_samples.append(str(file_path.relative_to(workspace_path)))
            else:
                included_files += 1
                if len(included_samples) < 10:
                    included_samples.append(str(file_path.relative_to(workspace_path)))
    
    print(f"\n📈 Results:")
    print(f"   Total files found: {total_files:,}")
    print(f"   Files to analyze: {included_files:,}")
    print(f"   Files excluded: {excluded_files:,}")
    print(f"   Reduction: {((excluded_files / total_files) * 100):.1f}%")
    
    print(f"\n✅ Sample files to analyze:")
    for sample in included_samples:
        print(f"     • {sample}")
    
    print(f"\n❌ Sample excluded files:")
    for sample in excluded_samples:
        print(f"     • {sample}")
    
    print(f"\n🎯 Step 3 would now process {included_files:,} files instead of {total_files:,}")
    print(f"   Estimated time reduction: {((excluded_files / total_files) * 100):.1f}%")

if __name__ == "__main__":
    test_file_filtering()
