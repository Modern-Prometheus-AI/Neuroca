def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        stm_storage: Optional[STMStorage] = None,
        # Support for tier-specific storage types (new API)
        stm_storage_type: Optional[BackendType] = None,
        mtm_storage_type: BackendType = BackendType.REDIS,
        ltm_storage_type: BackendType = BackendType.SQL,
        vector_storage_type: BackendType = BackendType.VECTOR,
        working_buffer_size: int = 20,
        embedding_dimension: int = 768,
        ):
        """
        Initialize the Memory Manager.
        
        Args:
            config: Configuration for the memory system
            stm_storage: Optional STM storage instance (created if not provided)
            stm_storage_type: Optional storage type for STM (new API support)
            mtm_storage_type: Storage backend type for MTM
            ltm_storage_type: Storage backend type for LTM
            vector_storage_type: Storage backend type for vector search
            working_buffer_size: Size of the working memory buffer
            embedding_dimension: Dimension of embedding vectors
        """
        # If stm_storage_type is provided instead of stm_storage instance, handle it
        if stm_storage_type and not stm_storage:
            # Convert BackendType.MEMORY to in-memory storage for compatibility
            if stm_storage_type == BackendType.MEMORY:
                # Create an in-memory STM storage
                from neuroca.memory.backends.memory import InMemoryBackend
                stm_storage = InMemoryBackend(tier=MemoryTier.STM, config={})
