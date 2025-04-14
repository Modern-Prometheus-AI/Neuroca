"""
Unit tests for memory storage backends.

This module contains unit tests for the various storage backend implementations 
provided by the memory system. It tests the basic functionality of each backend
to ensure they properly implement the expected interfaces.
"""

import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

import pytest

from neuroca.memory.backends import (
    BackendType,
    MemoryTier,
    StorageBackendFactory,
    RedisStorageBackend,
    SQLStorageBackend,
    VectorStorageBackend,
)
from neuroca.memory.ltm.storage import MemoryItem, MemoryMetadata, MemoryStatus
from neuroca.memory.mtm.storage import MTMMemory, MemoryPriority


class TestStorageBackendFactory:
    """Test suite for the StorageBackendFactory class."""
    
    def test_create_stm_storage(self):
        """Test creating STM storage."""
        config = {"base_path": tempfile.mkdtemp(), "max_items": 100}
        storage = StorageBackendFactory.create_stm_storage(config)
        assert storage is not None
        # Clean up
        shutil.rmtree(config["base_path"])
    
    def test_create_mtm_storage_in_memory(self):
        """Test creating MTM storage with in-memory backend."""
        storage = StorageBackendFactory.create_mtm_storage(
            backend_type=BackendType.IN_MEMORY
        )
        assert storage is not None
    
    def test_create_ltm_storage_file(self):
        """Test creating LTM storage with file backend."""
        base_path = tempfile.mkdtemp()
        storage = StorageBackendFactory.create_ltm_storage(
            backend_type=BackendType.FILE,
            config={"base_path": base_path}
        )
        assert storage is not None
        # Clean up
        shutil.rmtree(base_path)
    
    def test_create_storage_generic(self):
        """Test creating storage with the generic method."""
        storage = StorageBackendFactory.create_storage(
            tier=MemoryTier.STM
        )
        assert storage is not None
        
        storage = StorageBackendFactory.create_storage(
            tier=MemoryTier.MTM,
            backend_type=BackendType.IN_MEMORY
        )
        assert storage is not None
        
        storage = StorageBackendFactory.create_storage(
            tier=MemoryTier.LTM,
            backend_type=BackendType.IN_MEMORY
        )
        assert storage is not None


@pytest.mark.asyncio
class TestRedisBackend:
    """
    Test suite for the Redis storage backend.
    
    These tests use a mocked Redis connection to avoid requiring an actual Redis server.
    """
    
    @pytest.fixture
    async def redis_backend(self):
        """Create a Redis backend with mocked connection."""
        with patch("neuroca.memory.backends.redis_backend.get_redis_connection") as mock_get_conn:
            # Mock Redis connection methods
            mock_conn = mock_get_conn.return_value
            mock_conn.ping.return_value = True
            mock_conn.set.return_value = True
            mock_conn.get.return_value = None
            mock_conn.sadd.return_value = 1
            mock_conn.srem.return_value = 1
            mock_conn.exists.return_value = 0
            mock_conn.smembers.return_value = set()
            
            # Create backend
            backend = RedisStorageBackend(namespace="test")
            await backend.initialize()
            yield backend
    
    async def test_store_and_retrieve(self, redis_backend):
        """Test storing and retrieving a memory item."""
        # Create a test memory
        memory = MTMMemory(
            id="test-memory",
            content={"text": "This is a test memory"},
            priority=MemoryPriority.MEDIUM,
            tags=["test", "memory"]
        )
        
        # Mock Redis get to return our memory data
        redis_backend._connection.get.return_value = {
            "id": "test-memory",
            "content": {"text": "This is a test memory"},
            "created_at": memory.created_at.isoformat(),
            "last_accessed": memory.last_accessed.isoformat(),
            "access_count": 0,
            "priority": MemoryPriority.MEDIUM.value,
            "status": "active",
            "tags": ["test", "memory"],
            "metadata": {}
        }
        redis_backend._connection.exists.return_value = 1
        
        # Store memory
        memory_id = await redis_backend.store(memory)
        assert memory_id == "test-memory"
        
        # Retrieve memory
        retrieved = await redis_backend.retrieve(memory_id)
        assert retrieved is not None
        
        # Delete memory
        await redis_backend.delete(memory_id)


@pytest.mark.asyncio
class TestSQLBackend:
    """
    Test suite for the SQL storage backend.
    
    These tests use mocked database connection to avoid requiring an actual database.
    """
    
    @pytest.fixture
    async def sql_backend(self):
        """Create a SQL backend with mocked connection."""
        with patch("neuroca.memory.backends.sql_backend.get_postgres_connection") as mock_get_conn:
            # Mock connection and its methods
            mock_conn = mock_get_conn.return_value
            mock_conn.__aenter__.return_value = mock_conn
            mock_conn.__aexit__.return_value = None
            mock_conn.execute_query.return_value = []
            
            # Create backend
            backend = SQLStorageBackend(schema="test", table_name="test_memories")
            await backend.initialize()
            yield backend
    
    async def test_store_and_retrieve(self, sql_backend):
        """Test storing and retrieving a memory item."""
        # Create a test memory
        memory = MemoryItem(
            id="test-memory",
            content={"text": "This is a test memory"},
            summary="Test memory summary",
            metadata=MemoryMetadata(
                status=MemoryStatus.ACTIVE,
                tags=["test", "memory"],
                importance=0.8
            )
        )
        
        # Set up mock responses
        sql_backend._connection.execute_query.return_value = [{
            "id": "test-memory",
            "content": '{"text": "This is a test memory"}',
            "summary": "Test memory summary",
            "embedding": None,
            "metadata": '{"status": "active", "tags": ["test", "memory"], "importance": 0.8}',
            "created_at": memory.metadata.created_at if memory.metadata else None,
            "last_accessed": memory.metadata.created_at if memory.metadata else None,
            "access_count": 0,
            "decay_factor": 1.0,
            "source": None,
            "associations": None,
            "status": "active"
        }]
        
        # Store memory
        memory_id = await sql_backend.store(memory)
        assert memory_id == "test-memory"
        
        # Retrieve memory
        retrieved = await sql_backend.get(memory_id)
        assert retrieved is not None
        
        # Delete memory
        result = await sql_backend.delete(memory_id)
        assert result is True


@pytest.mark.asyncio
class TestVectorBackend:
    """
    Test suite for the Vector storage backend.
    """
    
    @pytest.fixture
    async def vector_backend(self):
        """Create a Vector backend."""
        # Create a temporary directory for the index
        temp_dir = tempfile.mkdtemp()
        index_path = os.path.join(temp_dir, "vector_index.json")
        
        # Create backend
        backend = VectorStorageBackend(
            dimension=3,  # Small dimension for testing
            similarity_threshold=0.5,
            index_path=index_path
        )
        await backend.initialize()
        yield backend
        
        # Clean up
        shutil.rmtree(temp_dir)
    
    async def test_store_and_retrieve(self, vector_backend):
        """Test storing and retrieving a memory item."""
        # Create a test memory with embedding
        memory = MemoryItem(
            id="test-memory",
            content={"text": "This is a test memory"},
            summary="Test memory summary",
            embedding=[0.1, 0.2, 0.3],  # Simple 3D vector
            metadata=MemoryMetadata(
                status=MemoryStatus.ACTIVE,
                tags=["test", "memory"],
                importance=0.8
            )
        )
        
        # Store memory
        memory_id = await vector_backend.store(memory)
        assert memory_id == "test-memory"
        
        # Retrieve memory
        retrieved = await vector_backend.get(memory_id)
        assert retrieved is not None
        assert retrieved.id == "test-memory"
        assert retrieved.embedding == [0.1, 0.2, 0.3]
        
        # Test vector search
        search_results = await vector_backend.search(
            query="test search",
            query_embedding=[0.1, 0.2, 0.3],  # Same vector should match
            limit=5
        )
        assert len(search_results) == 1
        assert search_results[0].id == "test-memory"
        
        # Delete memory
        result = await vector_backend.delete(memory_id)
        assert result is True
