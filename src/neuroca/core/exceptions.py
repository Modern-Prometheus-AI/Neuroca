"""
Custom exceptions for the NCA system.

This module defines all custom exceptions used throughout the NCA system.
"""

class NCAError(Exception):
    """Base class for all NCA-specific exceptions."""
    
    def __init__(self, message: str = "An error occurred in the NCA system"):
        self.message = message
        super().__init__(self.message)


class ConfigurationError(NCAError):
    """Raised when there is an error in the system configuration."""
    
    def __init__(self, message: str = "Invalid configuration"):
        super().__init__(f"Configuration error: {message}")


class MemoryError(NCAError):
    """Base class for memory-related exceptions."""
    
    def __init__(self, message: str = "Memory operation failed"):
        super().__init__(f"Memory error: {message}")


class MemoryNotFoundError(MemoryError):
    """Raised when a requested memory cannot be found."""
    
    def __init__(self, memory_id: str):
        super().__init__(f"Memory not found: {memory_id}")


class MemoryStorageError(MemoryError):
    """Raised when there is an error storing or retrieving memories."""
    
    def __init__(self, message: str = "Failed to store or retrieve memory"):
        super().__init__(message)


class MemoryConsolidationError(MemoryError):
    """Raised when there is an error during memory consolidation."""
    
    def __init__(self, message: str = "Memory consolidation failed"):
        super().__init__(message)


class AuthenticationError(NCAError):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(f"Authentication error: {message}")


class AuthorizationError(NCAError):
    """Raised when a user is not authorized to perform an action."""
    
    def __init__(self, message: str = "Not authorized"):
        super().__init__(f"Authorization error: {message}")


class APIError(NCAError):
    """Raised when there is an error in the API layer."""
    
    def __init__(self, message: str = "API operation failed", status_code: int = 500):
        self.status_code = status_code
        super().__init__(f"API error: {message}")


class DatabaseError(NCAError):
    """Raised when there is a database-related error."""
    
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(f"Database error: {message}")


class IntegrationError(NCAError):
    """Raised when there is an error with an external integration."""
    
    def __init__(self, service: str, message: str = "Integration failed"):
        super().__init__(f"Integration error with {service}: {message}")


class ValidationError(NCAError):
    """Raised when data validation fails."""
    
    def __init__(self, field: str = None, message: str = "Validation failed"):
        msg = f"Validation error: {message}"
        if field:
            msg = f"Validation error for field '{field}': {message}"
        super().__init__(msg)


class ContextError(NCAError):
    """Raised for errors related to context management."""
    
    def __init__(self, message: str = "Context management error"):
        super().__init__(f"Context error: {message}")


class ContextLimitExceededError(ContextError):
    """Raised when context limits (e.g., token count) are exceeded."""
    
    def __init__(self, limit_type: str = "general", limit: int = 0, current: int = 0):
        message = f"Context limit exceeded for {limit_type}. Limit: {limit}, Current: {current}"
        super().__init__(message)
