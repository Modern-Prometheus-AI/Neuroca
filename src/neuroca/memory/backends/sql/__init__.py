"""
SQL Backend Package

This package contains the modular components for the SQL storage backend
implementation that uses PostgreSQL for robust, persistent memory storage.

All components are re-exported from the package root for easier access.
"""

from neuroca.memory.backends.sql.core import SQLBackend
from neuroca.memory.backends.sql.components import (
    SQLConnection,
    SQLSchema,
    SQLCRUD,
    SQLSearch,
    SQLBatch,
    SQLStats
)

# Export classes
__all__ = [
    'SQLBackend',
    'SQLConnection',
    'SQLSchema',
    'SQLCRUD',
    'SQLSearch',
    'SQLBatch',
    'SQLStats'
]
