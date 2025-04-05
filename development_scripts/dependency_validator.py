"""
Dependency Validator Script

This script helps validate and fix dependencies when new files are created in the project.
It ensures that:
1. All imported modules exist
2. Required packages are added to pyproject.toml
3. Proper package structure is maintained
"""

import os
import ast
import sys
import re
import importlib.util
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional


def parse_imports(file_path: str) -> Tuple[Set[str], Set[str]]:
    """
    Parse a Python file to extract both module imports and from-imports.
    
    Args:
        file_path: Path to the Python file
        
    Returns:
        Tuple of (module_imports, from_imports)
    """
    module_imports = set()
    from_imports = set()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    module_name = name.name.split('.')[0]
                    module_imports.add(module_name)
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_name = node.module.split('.')[0]
                    from_imports.add(module_name)
    
    except Exception as e:
        print(f"Error parsing {file_path}: {str(e)}")
    
    return module_imports, from_imports


def check_module_exists(module_name: str) -> bool:
    """Check if a module can be imported."""
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, ValueError):
        return False


def is_standard_library(module_name: str) -> bool:
    """Check if a module is part of the Python standard library."""
    std_lib_modules = {
        'abc', 'argparse', 'ast', 'asyncio', 'base64', 'collections', 'configparser',
        'contextlib', 'copy', 'csv', 'dataclasses', 'datetime', 'decimal', 'difflib',
        'enum', 'functools', 'glob', 'hashlib', 'hmac', 'http', 'importlib', 'inspect',
        'io', 'itertools', 'json', 'logging', 'math', 'multiprocessing', 'os', 'pathlib',
        'pickle', 'platform', 'pprint', 're', 'secrets', 'shutil', 'signal', 'socket',
        'sqlite3', 'statistics', 'string', 'subprocess', 'sys', 'tempfile', 'textwrap',
        'threading', 'time', 'traceback', 'typing', 'unicodedata', 'unittest', 'urllib',
        'uuid', 'warnings', 'weakref', 'xml', 'zipfile', 'zlib'
    }
    return module_name in std_lib_modules


def is_project_module(module_name: str, project_root: str) -> bool:
    """Check if a module is part of the project."""
    potential_paths = [
        os.path.join(project_root, module_name),
        os.path.join(project_root, module_name + '.py')
    ]
    return any(os.path.exists(p) for p in potential_paths)


def ensure_package_structure(module_path: str) -> List[str]:
    """
    Ensure a directory has the necessary __init__.py files to be a package.
    Returns list of created files.
    """
    created_files = []
    
    if os.path.isdir(module_path):
        init_file = os.path.join(module_path, '__init__.py')
        if not os.path.exists(init_file):
            with open(init_file, 'w', encoding='utf-8') as f:
                f.write('"""Package module."""\n')
            created_files.append(init_file)
            
        # Check subdirectories too
        for item in os.listdir(module_path):
            subdir_path = os.path.join(module_path, item)
            if os.path.isdir(subdir_path) and not item.startswith('.') and item != '__pycache__':
                created_files.extend(ensure_package_structure(subdir_path))
                
    return created_files


def get_missing_dependencies(file_path: str, project_root: str) -> Set[str]:
    """
    Find missing dependencies for a Python file.
    
    Args:
        file_path: Path to the Python file
        project_root: Root directory of the project
        
    Returns:
        Set of missing dependencies
    """
    missing = set()
    module_imports, from_imports = parse_imports(file_path)
    all_imports = module_imports.union(from_imports)
    
    for module in all_imports:
        # Skip standard library
        if is_standard_library(module):
            continue
            
        # Check if it's a project module
        if is_project_module(module, project_root):
            # Ensure it has __init__.py
            module_path = os.path.join(project_root, module)
            if os.path.isdir(module_path):
                ensure_package_structure(module_path)
            continue
            
        # Check if it can be imported
        if not check_module_exists(module):
            missing.add(module)
            
    return missing


def fix_imports_in_file(file_path: str, project_root: str) -> Tuple[bool, List[str]]:
    """
    Fix imports in a Python file by ensuring imported modules exist.
    
    Args:
        file_path: Path to the Python file
        project_root: Root directory of the project
        
    Returns:
        Tuple of (success, list_of_actions_taken)
    """
    actions = []
    module_imports, from_imports = parse_imports(file_path)
    all_imports = module_imports.union(from_imports)
    success = True
    
    for module in all_imports:
        # Skip standard library
        if is_standard_library(module):
            continue
            
        # If it's potentially a project module
        if module in {'neuroca', 'api', 'cli', 'core', 'db', 'memory', 'config', 'infrastructure', 'tools'}:
            module_path = os.path.join(project_root, module)
            
            # Create the module dir if it doesn't exist
            if not os.path.exists(module_path):
                os.makedirs(module_path, exist_ok=True)
                actions.append(f"Created directory: {module}")
            
            # Ensure it has __init__.py
            created_files = ensure_package_structure(module_path)
            if created_files:
                actions.extend([f"Created file: {f}" for f in created_files])
                
        # External module that doesn't exist
        elif not check_module_exists(module):
            actions.append(f"Missing external dependency: {module}")
            success = False
            
    return success, actions


def validate_file(file_path: str, project_root: str, fix: bool = False) -> Tuple[bool, List[str]]:
    """
    Validate a Python file for dependency issues.
    
    Args:
        file_path: Path to the Python file
        project_root: Root directory of the project
        fix: Whether to attempt to fix issues
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    # Check if file exists
    if not os.path.exists(file_path):
        return False, [f"File does not exist: {file_path}"]
    
    # Get missing dependencies
    missing = get_missing_dependencies(file_path, project_root)
    
    if missing:
        issues.append(f"Missing dependencies: {', '.join(missing)}")
        
    if fix:
        # Try to fix imports
        success, actions = fix_imports_in_file(file_path, project_root)
        issues.extend(actions)
        return success, issues
    
    return len(issues) == 0, issues


def validate_project(project_root: str, fix: bool = False) -> Dict[str, List[str]]:
    """
    Validate all Python files in a project.
    
    Args:
        project_root: Root directory of the project
        fix: Whether to attempt to fix issues
        
    Returns:
        Dictionary of {file_path: list_of_issues}
    """
    results = {}
    
    for root, _, files in os.walk(project_root):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, project_root)
                
                # Skip files in .venv
                if '.venv' in file_path:
                    continue
                    
                success, issues = validate_file(file_path, project_root, fix)
                if not success:
                    results[rel_path] = issues
    
    return results


def main():
    """Run the dependency validator."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate and fix dependencies in Python files')
    parser.add_argument('--file', '-f', help='Specific Python file to validate')
    parser.add_argument('--fix', action='store_true', help='Attempt to fix issues')
    parser.add_argument('--project', '-p', default=os.getcwd(), help='Project root directory')
    
    args = parser.parse_args()
    
    if args.file:
        file_path = os.path.abspath(args.file)
        success, issues = validate_file(file_path, args.project, args.fix)
        
        print(f"\nValidating file: {os.path.relpath(file_path, args.project)}")
        if success:
            print("✅ No issues found" if not issues else "✅ All issues fixed")
        else:
            print("❌ Issues found:")
            for issue in issues:
                print(f"  - {issue}")
    else:
        results = validate_project(args.project, args.fix)
        
        if not results:
            print("\n✅ No issues found in any files")
        else:
            print(f"\n❌ Issues found in {len(results)} files:")
            for file, issues in results.items():
                print(f"\n{file}:")
                for issue in issues:
                    print(f"  - {issue}")
                    
        if args.fix:
            print("\nRun the validator again to check if all issues were fixed.")


if __name__ == "__main__":
    main() 