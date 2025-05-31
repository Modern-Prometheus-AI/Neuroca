"""
Test to isolate the hanging subprocess call
"""

import subprocess
import json
from pathlib import Path

def test_poetry_command():
    """Test the specific poetry command that might be hanging"""
    
    print("🔍 Testing poetry command directly")
    workspace_path = Path(__file__).parent
    
    print(f"Workspace path: {workspace_path}")
    print(f"pyproject.toml exists: {(workspace_path / 'pyproject.toml').exists()}")
    
    if (workspace_path / "pyproject.toml").exists():
        print("✅ Running poetry show --tree...")
        try:
            # Add timeout to the subprocess call
            result = subprocess.run(
                ["poetry", "show", "--tree"], 
                capture_output=True, 
                text=True, 
                cwd=workspace_path,
                timeout=10  # 10-second timeout
            )
            print(f"   - Poetry command completed")
            print(f"   - Return code: {result.returncode}")
            print(f"   - Output length: {len(result.stdout)} chars")
            if result.stderr:
                print(f"   - Stderr: {result.stderr[:200]}...")
        except subprocess.TimeoutExpired:
            print("   - ❌ Poetry command timed out after 10 seconds!")
        except subprocess.CalledProcessError as e:
            print(f"   - ❌ Poetry command failed: {e}")
        except FileNotFoundError:
            print("   - ❌ Poetry command not found")
        except Exception as e:
            print(f"   - ❌ Unexpected error: {e}")
    
    print("✅ Testing other commands...")
    
    # Test other commands that might hang
    commands = {
        "python": ["python", "--version"],
        "git": ["git", "--version"],
        "node": ["node", "--version"],
        "npm": ["npm", "--version"]
    }
    
    for tool, cmd in commands.items():
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            print(f"   - {tool}: OK ({result.stdout.strip()})")
        except subprocess.TimeoutExpired:
            print(f"   - {tool}: TIMEOUT")
        except FileNotFoundError:
            print(f"   - {tool}: NOT FOUND")
        except Exception as e:
            print(f"   - {tool}: ERROR ({e})")

if __name__ == "__main__":
    test_poetry_command()
