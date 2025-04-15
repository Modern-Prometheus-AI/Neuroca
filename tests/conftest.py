"""
Global test configuration for the Neuroca memory system.

This module configures the Python path and sets up fixtures that are used
across all test modules.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path so imports can work correctly
# without needing to add the 'src.' prefix to every import
project_root = Path(__file__).parent.parent
src_dir = project_root / 'src'

# Make the 'neuroca' package directly importable
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Rest of conftest.py would go here (global fixtures, etc.)
