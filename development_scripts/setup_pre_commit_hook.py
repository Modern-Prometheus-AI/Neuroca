#!/usr/bin/env python3
"""
Setup Script for Pre-Commit Hook

This script sets up a pre-commit hook that checks for dependency issues
before allowing code to be committed.
"""

import os
import sys
import stat
from pathlib import Path


PRE_COMMIT_HOOK_CONTENT = """#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

# Get the root directory of the git repository
git_root = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], 
                                  universal_newlines=True).strip()

# Path to the dependency validator script
validator_script = os.path.join(git_root, 'development_scripts', 'dependency_validator.py')

# Get staged Python files
staged_files_output = subprocess.check_output(
    ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'], 
    universal_newlines=True
)
staged_files = [f for f in staged_files_output.strip().split('\\n') if f.endswith('.py')]

if not staged_files:
    # No Python files to check
    sys.exit(0)

print("Checking dependencies in staged files...")
exit_code = 0

for file_path in staged_files:
    abs_path = os.path.join(git_root, file_path)
    result = subprocess.run(
        [sys.executable, validator_script, '--file', abs_path],
        capture_output=True,
        text=True
    )
    
    if 'Issues found' in result.stdout:
        print(f"\\n{file_path}:")
        print(result.stdout)
        exit_code = 1

if exit_code == 1:
    print("\\n❌ Dependency issues found. Please fix them before committing.")
    print("You can run: python development_scripts/dependency_validator.py --fix")
    sys.exit(1)
else:
    print("✅ All dependencies validated successfully.")
    sys.exit(0)
"""


def setup_pre_commit_hook():
    """Set up the pre-commit hook in the .git/hooks directory."""
    # Find the git directory
    try:
        git_root = os.popen('git rev-parse --show-toplevel').read().strip()
    except Exception:
        print("Error: This doesn't appear to be a git repository.")
        return False

    if not git_root:
        print("Error: Unable to find git repository root.")
        return False

    git_hooks_dir = os.path.join(git_root, '.git', 'hooks')
    pre_commit_path = os.path.join(git_hooks_dir, 'pre-commit')

    # Check if hooks directory exists
    if not os.path.exists(git_hooks_dir):
        print(f"Error: Git hooks directory not found at {git_hooks_dir}")
        return False

    # Check if pre-commit hook already exists
    if os.path.exists(pre_commit_path):
        overwrite = input("A pre-commit hook already exists. Overwrite? (y/N): ")
        if overwrite.lower() != 'y':
            print("Aborted.")
            return False

    # Write the pre-commit hook
    try:
        with open(pre_commit_path, 'w', encoding='utf-8') as f:
            f.write(PRE_COMMIT_HOOK_CONTENT)

        # Make it executable
        os.chmod(pre_commit_path, os.stat(pre_commit_path).st_mode | stat.S_IEXEC)
        print(f"✅ Pre-commit hook installed at {pre_commit_path}")
        return True
    except Exception as e:
        print(f"Error setting up pre-commit hook: {str(e)}")
        return False


def main():
    """Main function to run the setup script."""
    print("Setting up pre-commit hook for dependency validation...")
    result = setup_pre_commit_hook()
    if result:
        print("\nPre-commit hook setup complete!")
        print("\nThe hook will now check for dependency issues before each commit.")
        print("To validate all files in the project, run:")
        print("    python development_scripts/dependency_validator.py")
        print("\nTo fix dependency issues automatically, run:")
        print("    python development_scripts/dependency_validator.py --fix")
    else:
        print("\nFailed to set up pre-commit hook.")
        sys.exit(1)


if __name__ == "__main__":
    main() 