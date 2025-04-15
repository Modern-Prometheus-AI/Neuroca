"""
Storage Backend Factory

This module provides the StorageBackendFactory class for creating storage backend instances.
The factory is responsible for creating the appropriate backend based on
configuration settings and ensures only one instance of each backend is created.
"""

import logging
from typing import Any, Dict, Optional, Type

from neuroca.memory.backends.base import BaseStorageBackend
from neuroca.memory.backends.factory.backend_type import BackendType
from neuroca.memory.backends.factory.memory_tier import MemoryTier
from neuroca.memory.backends.in_memory_backend import InMemoryBackend
from neuroca.memory.backends.sqlite_backend import SQLiteBackend
from neuroca.memory.exceptions import ConfigurationError


logger = logging.getLogger(__name__)


class StorageBackendFactory:
    """
    Factory for creating storage backend instances.
    
    This class is responsible for creating and configuring storage backend
    instances based on the provided configuration. It ensures that the
    appropriate backend is created for each memory tier.
    """
    
    # Registry of backend implementations
    _backend_registry: Dict[BackendType, Type[BaseStorageBackend]] = {
        BackendType.MEMORY: InMemoryBackend,
        BackendType.SQL: SQLiteBackend,
        # Other backends will be added when implemented
    }
    
    # Instances of created backends (for reuse)
    _instances: Dict[str, BaseStorageBackend] = {}
    
    @classmethod
    def create_storage(
        cls,
        tier: Optional[MemoryTier] = None,
        backend_type: Optional[BackendType] = None,
        config: Optional[Dict[str, Any]] = None,
        use_existing: bool = True,
        instance_name: Optional[str] = None,
    ) -> BaseStorageBackend:
        """
        Create and initialize a storage backend instance.
        
        Args:
            tier: Memory tier for which to create the backend (determines default backend type)
            backend_type: Explicit backend type to create (overrides tier default)
            config: Backend-specific configuration
            use_existing: Whether to reuse an existing instance if available
            instance_name: Optional name for the instance (for reuse identification)
            
        Returns:
            Initialized storage backend instance
            
        Raises:
            ConfigurationError: If the specified backend type is not supported
        """
        config = config or {}
        
        # Determine the backend type
        if backend_type is None:
            if tier is None:
                # Default to in-memory backend if neither tier nor type is specified
                backend_type = BackendType.MEMORY
            else:
                # Determine default backend type based on tier
                backend_type = cls._get_default_backend_for_tier(tier)
        
        # Get the backend class
        if backend_type not in cls._backend_registry:
            raise ConfigurationError(
                component="StorageBackendFactory",
                message=f"Unsupported backend type: {backend_type}. "
                f"Supported types: {list(cls._backend_registry.keys())}"
            )
        
        backend_class = cls._backend_registry[backend_type]
        
        # Generate instance name (for registry)
        if instance_name is None:
            if tier is not None:
                instance_name = f"{tier.value}_{backend_type.value}"
            else:
                instance_name = f"{backend_type.value}"
                
            # Add identifier based on selected config values if present
            if "database" in config:
                instance_name += f"_{config['database']}"
            elif "host" in config and "port" in config:
                instance_name += f"_{config['host']}_{config['port']}"
        
        # Check if instance already exists
        if use_existing and instance_name in cls._instances:
            logger.debug(f"Reusing existing backend instance: {instance_name}")
            return cls._instances[instance_name]
        
        # Create and initialize the backend instance
        logger.info(f"Creating new {backend_type.value} storage backend for {tier.value if tier else 'custom'} tier")
        backend = backend_class(config)
        
        # Store the instance for reuse
        cls._instances[instance_name] = backend
        
        return backend
    
    @classmethod
    def register_backend(cls, backend_type: BackendType, backend_class: Type[BaseStorageBackend]) -> None:
        """
        Register a new backend implementation.
        
        Args:
            backend_type: The backend type to register
            backend_class: The backend class implementation
        """
        cls._backend_registry[backend_type] = backend_class
        logger.info(f"Registered {backend_class.__name__} implementation for {backend_type.value} backend")
    
    @classmethod
    def get_registry(cls) -> Dict[BackendType, Type[BaseStorageBackend]]:
        """
        Get the current backend registry.
        
        Returns:
            Dictionary mapping backend types to their implementations
        """
        return cls._backend_registry.copy()
    
    @classmethod
    def get_existing_instances(cls) -> Dict[str, BaseStorageBackend]:
        """
        Get all existing backend instances.
        
        Returns:
            Dictionary mapping instance names to their instances
        """
        return cls._instances.copy()
    
    @classmethod
    def shutdown_all(cls) -> None:
        """
        Shutdown all created backend instances.
        """
        for instance_name, backend in list(cls._instances.items()):
            try:
                # Shutting down is an async operation, but we're calling it
                # in a synchronous context here for simplicity. In a real
                # implementation, this would need to be properly handled.
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        loop.create_task(backend.shutdown())
                    else:
                        loop.run_until_complete(backend.shutdown())
                except RuntimeError:
                    # If there's no event loop, create one
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(backend.shutdown())
                    loop.close()
                
                del cls._instances[instance_name]
                logger.info(f"Shutdown backend instance: {instance_name}")
            except Exception as e:
                logger.exception(f"Error shutting down backend instance {instance_name}: {str(e)}")
    
    @classmethod
    def _get_default_backend_for_tier(cls, tier: MemoryTier) -> BackendType:
        """
        Get the default backend type for a memory tier.
        
        Args:
            tier: The memory tier
            
        Returns:
            The default backend type for the tier
        """
        if tier == MemoryTier.STM:
            return BackendType.MEMORY  # In-memory for STM
        elif tier == MemoryTier.MTM:
            return BackendType.MEMORY  # In-memory for MTM (would be REDIS in production)
        elif tier == MemoryTier.LTM:
            # Use SQL backend for LTM in production
            # For development or testing, this can be overridden with an explicit backend_type
            import os
            env = os.environ.get("NEUROCA_ENV", "development")
            if env in ("production", "staging"):
                return BackendType.SQL  # SQLite for LTM in production
            else:
                return BackendType.MEMORY  # In-memory for development/testing
        else:
            return BackendType.MEMORY  # Default to in-memory
