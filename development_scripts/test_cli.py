"""Test script for CLI functionality."""

import importlib
import sys

def test_cli_imports():
    """Test importing the CLI functionality."""
    print("Testing CLI imports...")
    
    # Test importing the cli.main module
    try:
        import cli.main
        print("✓ Successfully imported cli.main")
        
        # Test app attribute
        if hasattr(cli.main, "app"):
            print(f"✓ Found app object: {cli.main.app}")
        else:
            print("✗ app object not found in cli.main")
            
        # Test cli attribute
        if hasattr(cli.main, "cli"):
            print(f"✓ Found cli object: {cli.main.cli}")
        else:
            print("✗ cli object not found in cli.main")
    
    except ImportError as e:
        print(f"✗ Failed to import cli.main: {e}")
    
    # Print sys.path for debugging
    print("\nPython path:")
    for path in sys.path:
        print(f"  - {path}")
        
    # Print all found modules containing 'cli'
    print("\nModules containing 'cli':")
    modules = [m for m in sys.modules if 'cli' in m]
    for module in modules:
        print(f"  - {module}")

if __name__ == "__main__":
    test_cli_imports() 