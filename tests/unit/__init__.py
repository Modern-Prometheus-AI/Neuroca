"""
Unit Tests Package for NeuroCognitive Architecture (NCA)

This package contains all unit tests for the NeuroCognitive Architecture system.
Unit tests focus on testing individual components in isolation, mocking external
dependencies as needed.

The unit test suite is organized to mirror the main package structure, with test
modules corresponding to the modules they test.

Usage:
    Tests can be run using pytest:
    
    # Run all unit tests
    pytest neuroca/tests/unit
    
    # Run specific test module
    pytest neuroca/tests/unit/memory/test_working_memory.py
    
    # Run with coverage
    pytest neuroca/tests/unit --cov=neuroca

Test Organization:
    - Each module in the main package should have a corresponding test module
    - Test files should be named with the 'test_' prefix
    - Test classes should be named with the 'Test' prefix
    - Test methods should be named with the 'test_' prefix

Fixtures:
    Common test fixtures are defined in conftest.py files at appropriate levels
    of the test hierarchy to promote reuse and maintainability.

Notes:
    - Unit tests should be fast, isolated, and not depend on external resources
    - Use mocking for external dependencies
    - Focus on testing one specific functionality per test
    - Aim for high code coverage but prioritize testing critical paths and edge cases
"""

# Version information
__version__ = '0.1.0'

# Package exports
# Intentionally empty as this is a test package and doesn't need to export anything

# This allows running the tests as a module
if __name__ == '__main__':
    import sys

    import pytest
    sys.exit(pytest.main())

"""
Unit tests for the NeuroCognitive Architecture components.

These tests verify individual components in isolation to ensure
they meet their functional and biological requirements.
"""