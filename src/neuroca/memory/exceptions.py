"""
Memory System Exceptions

This module defines the exception hierarchy for the Neuroca memory system.
These exceptions provide standardized error handling and reporting across
all components of the memory system.

Exception Hierarchy:
- MemoryException (base)
  - InitializationError
    - StorageInitializationError
    - TierInitializationError
    - MemoryManagerInitializationError
  - OperationError
    - StorageOperationError
    - TierOperationError
    - MemoryManagerOperationError
  - ItemError
    - ItemNotFoundError
    - ItemExistsError
    - ItemValidationError
  - ConfigurationError
  - InvalidInputError
  - ResourceExhaustedError
  - TimeoutError
"""

class MemoryException(Exception):
    """Base exception for all memory system errors."""
    
    def __init__(self, message: str = None, *args, **kwargs):
        self.message = message or "An error occurred in the memory system"
        super().__init__(self.message, *args, **kwargs)


class StorageBackendError(MemoryException):
    """Base exception for all storage backend errors."""
    
    def __init__(self, backend_type: str = None, message: str = None, *args, **kwargs):
        backend_str = f" ({backend_type})" if backend_type else ""
        self.message = message or f"Storage backend error{backend_str}"
        super().__init__(self.message, *args, **kwargs)


#-----------------------------------------------------------------------
# Initialization Errors
#-----------------------------------------------------------------------

class InitializationError(MemoryException):
    """Base exception for initialization errors."""
    
    def __init__(self, message: str = None, *args, **kwargs):
        self.message = message or "Failed to initialize a memory system component"
        super().__init__(self.message, *args, **kwargs)


class StorageInitializationError(InitializationError):
    """Exception raised when a storage backend fails to initialize."""
    
    def __init__(self, backend_type: str = None, message: str = None, *args, **kwargs):
        backend_str = f" ({backend_type})" if backend_type else ""
        self.message = message or f"Failed to initialize storage backend{backend_str}"
        super().__init__(self.message, *args, **kwargs)


class TierInitializationError(InitializationError):
    """Exception raised when a memory tier fails to initialize."""
    
    def __init__(self, tier_name: str = None, message: str = None, *args, **kwargs):
        tier_str = f" ({tier_name})" if tier_name else ""
        self.message = message or f"Failed to initialize memory tier{tier_str}"
        super().__init__(self.message, *args, **kwargs)


class MemoryManagerInitializationError(InitializationError):
    """Exception raised when the memory manager fails to initialize."""
    
    def __init__(self, message: str = None, *args, **kwargs):
        self.message = message or "Failed to initialize memory manager"
        super().__init__(self.message, *args, **kwargs)


#-----------------------------------------------------------------------
# Operation Errors
#-----------------------------------------------------------------------

class OperationError(MemoryException):
    """Base exception for operation errors."""
    
    def __init__(self, operation: str = None, message: str = None, *args, **kwargs):
        op_str = f" during {operation}" if operation else ""
        self.message = message or f"Operation failed{op_str}"
        super().__init__(self.message, *args, **kwargs)


class StorageOperationError(OperationError):
    """Exception raised when a storage operation fails."""
    
    def __init__(self, operation: str = None, backend_type: str = None, 
                 message: str = None, *args, **kwargs):
        backend_str = f" in {backend_type} backend" if backend_type else ""
        op_str = f" ({operation})" if operation else ""
        self.message = message or f"Storage operation{op_str} failed{backend_str}"
        super().__init__(operation, self.message, *args, **kwargs)


class TierOperationError(OperationError):
    """Exception raised when a tier operation fails."""
    
    def __init__(self, operation: str = None, tier_name: str = None,
                 message: str = None, *args, **kwargs):
        tier_str = f" in {tier_name} tier" if tier_name else ""
        op_str = f" ({operation})" if operation else ""
        self.message = message or f"Tier operation{op_str} failed{tier_str}"
        super().__init__(operation, self.message, *args, **kwargs)


class MemoryManagerOperationError(OperationError):
    """Exception raised when a memory manager operation fails."""
    
    def __init__(self, operation: str = None, message: str = None, *args, **kwargs):
        op_str = f" ({operation})" if operation else ""
        self.message = message or f"Memory manager operation{op_str} failed"
        super().__init__(operation, self.message, *args, **kwargs)


#-----------------------------------------------------------------------
# Item Errors
#-----------------------------------------------------------------------

class ItemError(MemoryException):
    """Base exception for memory item errors."""
    
    def __init__(self, item_id: str = None, message: str = None, *args, **kwargs):
        item_str = f" (ID: {item_id})" if item_id else ""
        self.message = message or f"Error with memory item{item_str}"
        super().__init__(self.message, *args, **kwargs)


class ItemNotFoundError(ItemError):
    """Exception raised when a memory item is not found."""
    
    def __init__(self, item_id: str = None, tier: str = None, 
                 message: str = None, *args, **kwargs):
        item_str = f" (ID: {item_id})" if item_id else ""
        tier_str = f" in {tier} tier" if tier else ""
        self.message = message or f"Memory item{item_str} not found{tier_str}"
        super().__init__(item_id, self.message, *args, **kwargs)


class ItemExistsError(ItemError):
    """Exception raised when attempting to create a memory item that already exists."""
    
    def __init__(self, item_id: str = None, tier: str = None,
                 message: str = None, *args, **kwargs):
        item_str = f" (ID: {item_id})" if item_id else ""
        tier_str = f" in {tier} tier" if tier else ""
        self.message = message or f"Memory item{item_str} already exists{tier_str}"
        super().__init__(item_id, self.message, *args, **kwargs)


class ItemValidationError(ItemError):
    """Exception raised when a memory item fails validation."""
    
    def __init__(self, item_id: str = None, reason: str = None,
                 message: str = None, *args, **kwargs):
        item_str = f" (ID: {item_id})" if item_id else ""
        reason_str = f": {reason}" if reason else ""
        self.message = message or f"Memory item{item_str} validation failed{reason_str}"
        super().__init__(item_id, self.message, *args, **kwargs)


#-----------------------------------------------------------------------
# Other Errors
#-----------------------------------------------------------------------

class ConfigurationError(MemoryException):
    """Exception raised when there is a configuration error."""
    
    def __init__(self, component: str = None, message: str = None, *args, **kwargs):
        comp_str = f" for {component}" if component else ""
        self.message = message or f"Invalid configuration{comp_str}"
        super().__init__(self.message, *args, **kwargs)


class InvalidInputError(MemoryException):
    """Exception raised when an operation receives invalid input."""
    
    def __init__(self, parameter: str = None, message: str = None, *args, **kwargs):
        param_str = f" for parameter '{parameter}'" if parameter else ""
        self.message = message or f"Invalid input{param_str}"
        super().__init__(self.message, *args, **kwargs)


class ResourceExhaustedError(MemoryException):
    """Exception raised when a resource is exhausted."""
    
    def __init__(self, resource: str = None, message: str = None, *args, **kwargs):
        res_str = f" ({resource})" if resource else ""
        self.message = message or f"Resource exhausted{res_str}"
        super().__init__(self.message, *args, **kwargs)


class TimeoutError(MemoryException):
    """Exception raised when an operation times out."""
    
    def __init__(self, operation: str = None, timeout_seconds: float = None,
                 message: str = None, *args, **kwargs):
        op_str = f" ({operation})" if operation else ""
        timeout_str = f" after {timeout_seconds} seconds" if timeout_seconds else ""
        self.message = message or f"Operation{op_str} timed out{timeout_str}"
        super().__init__(self.message, *args, **kwargs)


class InvalidTierError(MemoryException):
    """Exception raised when an invalid tier is specified."""
    
    def __init__(self, tier_name: str = None, valid_tiers: list = None,
                 message: str = None, *args, **kwargs):
        tier_str = f" '{tier_name}'" if tier_name else ""
        valid_str = f" (valid tiers: {', '.join(valid_tiers)})" if valid_tiers else ""
        self.message = message or f"Invalid memory tier{tier_str}{valid_str}"
        super().__init__(self.message, *args, **kwargs)


class TierNotFoundError(MemoryException):
    """Exception raised when a tier is not found."""
    
    def __init__(self, tier_name: str = None, message: str = None, *args, **kwargs):
        tier_str = f" '{tier_name}'" if tier_name else ""
        self.message = message or f"Memory tier not found{tier_str}"
        super().__init__(self.message, *args, **kwargs)


class UnsupportedOperationError(MemoryException):
    """Exception raised when an operation is not supported."""
    
    def __init__(self, operation: str = None, component: str = None,
                 message: str = None, *args, **kwargs):
        op_str = f" '{operation}'" if operation else ""
        comp_str = f" by {component}" if component else ""
        self.message = message or f"Operation{op_str} not supported{comp_str}"
        super().__init__(self.message, *args, **kwargs)
