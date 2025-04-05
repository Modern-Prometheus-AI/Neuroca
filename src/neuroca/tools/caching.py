"""
NeuroCognitive Architecture (NCA) - Caching Module

This module provides caching capabilities for the NCA system, allowing for
optimization of repetitive operations and reduction of computational overhead.
It implements several caching strategies that can be used to improve performance
in different contexts.

The caching system is biologically inspired, mimicking the way the brain optimizes
frequently used neural pathways and reuses recently computed results.
"""

import functools
import hashlib
import json
import logging
import pickle
import threading
import time
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar, Union, cast

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)

# Type for decorated functions
T = TypeVar('T')
CacheKey = Union[str, tuple[Any, ...]]


@dataclass
class CacheEntry:
    """Data class representing a cache entry."""
    key: str
    value: Any
    expires_at: Optional[float] = None
    created_at: float = field(default_factory=time.time)
    last_accessed_at: float = field(default_factory=time.time)
    access_count: int = 0
    
    def is_expired(self) -> bool:
        """Check if this cache entry has expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def access(self) -> None:
        """Mark the entry as accessed."""
        self.last_accessed_at = time.time()
        self.access_count += 1


class CacheBackend(ABC):
    """Abstract base class for cache backend implementations."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional)
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if the key was deleted, False otherwise
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all entries from the cache."""
        pass
    
    @abstractmethod
    def get_stats(self) -> dict[str, Any]:
        """
        Get statistics about the cache.
        
        Returns:
            Dictionary of cache statistics
        """
        pass


class InMemoryCache(CacheBackend):
    """
    In-memory cache implementation with LRU eviction.
    
    This cache stores entries in memory and evicts the least recently used
    entries when the cache size exceeds the maximum capacity.
    """
    
    def __init__(self, max_size: int = 1000, eviction_policy: str = 'lru',
                 eviction_threshold: float = 0.9):
        """
        Initialize the in-memory cache.
        
        Args:
            max_size: Maximum number of entries to store in the cache
            eviction_policy: Policy to use when evicting entries ('lru', 'lfu', 'fifo')
            eviction_threshold: Threshold at which to start evicting entries (0.0-1.0)
        """
        self._cache: dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._eviction_policy = eviction_policy.lower()
        self._eviction_threshold = eviction_threshold
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        
        # Validate eviction policy
        if self._eviction_policy not in ('lru', 'lfu', 'fifo'):
            raise ValueError(f"Unknown eviction policy: {eviction_policy}")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._misses += 1
                return None
            
            if entry.is_expired():
                self._cache.pop(key)
                self._misses += 1
                return None
            
            entry.access()
            self._hits += 1
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional)
        """
        with self._lock:
            # Check if we need to evict entries
            self._maybe_evict()
            
            # Calculate expiration time
            expires_at = None
            if ttl is not None:
                expires_at = time.time() + ttl
            
            # Create and store the entry
            entry = CacheEntry(key=key, value=value, expires_at=expires_at)
            self._cache[key] = entry
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if the key was deleted, False otherwise
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all entries from the cache."""
        with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get statistics about the cache.
        
        Returns:
            Dictionary of cache statistics
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0
            
            return {
                "backend": "in_memory",
                "size": len(self._cache),
                "max_size": self._max_size,
                "usage_percent": len(self._cache) / self._max_size * 100,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "evictions": self._evictions,
                "eviction_policy": self._eviction_policy,
                "memory_usage_bytes": sum(
                    pickle.dumps(entry.value).__sizeof__() for entry in self._cache.values()
                )
            }
    
    def _maybe_evict(self) -> None:
        """Evict entries if the cache is full."""
        if len(self._cache) < self._max_size * self._eviction_threshold:
            return
        
        # Remove expired entries first
        expired_keys = [
            key for key, entry in self._cache.items() if entry.is_expired()
        ]
        for key in expired_keys:
            del self._cache[key]
            self._evictions += 1
        
        # If we still need to evict, use the configured policy
        if len(self._cache) >= self._max_size:
            if self._eviction_policy == 'lru':
                # Least Recently Used
                key_to_evict = min(
                    self._cache.keys(),
                    key=lambda k: self._cache[k].last_accessed_at
                )
            elif self._eviction_policy == 'lfu':
                # Least Frequently Used
                key_to_evict = min(
                    self._cache.keys(),
                    key=lambda k: self._cache[k].access_count
                )
            else:  # 'fifo'
                # First In First Out
                key_to_evict = min(
                    self._cache.keys(),
                    key=lambda k: self._cache[k].created_at
                )
            
            del self._cache[key_to_evict]
            self._evictions += 1


class FileCache(CacheBackend):
    """
    File-based cache implementation.
    
    This cache stores entries as files on disk, allowing for persistence
    between program runs. Entries are serialized using pickle.
    """
    
    def __init__(self, cache_dir: str = '.cache', max_size_mb: int = 100):
        """
        Initialize the file cache.
        
        Args:
            cache_dir: Directory to store cache files
            max_size_mb: Maximum total size of cache files in MB
        """
        self._cache_dir = Path(cache_dir)
        self._max_size_bytes = max_size_mb * 1024 * 1024
        self._hit_miss_path = self._cache_dir / 'hit_miss_stats.json'
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._lock = threading.RLock()
        
        # Create cache directory if it doesn't exist
        if not self._cache_dir.exists():
            self._cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Load hit/miss stats if available
        self._load_hit_miss_stats()
    
    def _load_hit_miss_stats(self) -> None:
        """Load hit/miss statistics from disk."""
        if self._hit_miss_path.exists():
            try:
                with open(self._hit_miss_path) as f:
                    stats = json.load(f)
                    self._hits = stats.get('hits', 0)
                    self._misses = stats.get('misses', 0)
                    self._evictions = stats.get('evictions', 0)
            except (OSError, json.JSONDecodeError) as e:
                logger.warning(f"Failed to load cache hit/miss stats: {e}")
    
    def _save_hit_miss_stats(self) -> None:
        """Save hit/miss statistics to disk."""
        try:
            with open(self._hit_miss_path, 'w') as f:
                json.dump({
                    'hits': self._hits,
                    'misses': self._misses,
                    'evictions': self._evictions
                }, f)
        except OSError as e:
            logger.warning(f"Failed to save cache hit/miss stats: {e}")
    
    def _get_cache_path(self, key: str) -> Path:
        """
        Get the file path for a cache key.
        
        Args:
            key: Cache key
            
        Returns:
            Path to the cache file
        """
        # Hash the key to create a safe filename
        hashed_key = hashlib.md5(key.encode('utf-8')).hexdigest()
        return self._cache_dir / f"{hashed_key}.cache"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            with self._lock:
                self._misses += 1
                self._save_hit_miss_stats()
            return None
        
        try:
            with open(cache_path, 'rb') as f:
                entry = pickle.load(f)
            
            if entry.is_expired():
                cache_path.unlink(missing_ok=True)
                with self._lock:
                    self._misses += 1
                    self._save_hit_miss_stats()
                return None
            
            # Update access information
            entry.access()
            with open(cache_path, 'wb') as f:
                pickle.dump(entry, f)
            
            with self._lock:
                self._hits += 1
                self._save_hit_miss_stats()
            
            return entry.value
            
        except (OSError, pickle.UnpicklingError) as e:
            logger.warning(f"Failed to load cache entry {key}: {e}")
            with self._lock:
                self._misses += 1
                self._save_hit_miss_stats()
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional)
        """
        # Check if we need to evict entries
        self._maybe_evict()
        
        # Calculate expiration time
        expires_at = None
        if ttl is not None:
            expires_at = time.time() + ttl
        
        # Create and store the entry
        entry = CacheEntry(key=key, value=value, expires_at=expires_at)
        cache_path = self._get_cache_path(key)
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(entry, f)
        except (OSError, pickle.PicklingError) as e:
            logger.warning(f"Failed to save cache entry {key}: {e}")
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if the key was deleted, False otherwise
        """
        cache_path = self._get_cache_path(key)
        
        if cache_path.exists():
            try:
                cache_path.unlink()
                return True
            except OSError as e:
                logger.warning(f"Failed to delete cache entry {key}: {e}")
        
        return False
    
    def clear(self) -> None:
        """Clear all entries from the cache."""
        for cache_file in self._cache_dir.glob('*.cache'):
            try:
                cache_file.unlink()
            except OSError as e:
                logger.warning(f"Failed to delete cache file {cache_file}: {e}")
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get statistics about the cache.
        
        Returns:
            Dictionary of cache statistics
        """
        cache_files = list(self._cache_dir.glob('*.cache'))
        total_size_bytes = sum(f.stat().st_size for f in cache_files)
        
        # Count expired entries
        expired_count = 0
        for cache_file in cache_files:
            try:
                with open(cache_file, 'rb') as f:
                    entry = pickle.load(f)
                if entry.is_expired():
                    expired_count += 1
            except (OSError, pickle.UnpicklingError):
                # If we can't load the entry, count it as expired
                expired_count += 1
        
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0
        
        return {
            "backend": "file",
            "cache_dir": str(self._cache_dir),
            "size": len(cache_files),
            "expired": expired_count,
            "total_size_bytes": total_size_bytes,
            "total_size_mb": total_size_bytes / (1024 * 1024),
            "max_size_bytes": self._max_size_bytes,
            "max_size_mb": self._max_size_bytes / (1024 * 1024),
            "usage_percent": (total_size_bytes / self._max_size_bytes) * 100 if self._max_size_bytes > 0 else 0,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "evictions": self._evictions
        }
    
    def _maybe_evict(self) -> None:
        """Evict entries if the cache is too large."""
        # Get all cache files with their sizes and timestamps
        cache_files = []
        for cache_file in self._cache_dir.glob('*.cache'):
            try:
                stat = cache_file.stat()
                cache_files.append((cache_file, stat.st_size, stat.st_mtime))
            except OSError:
                pass
        
        # Calculate total size
        total_size = sum(size for _, size, _ in cache_files)
        
        # If we're under the limit, no need to evict
        if total_size <= self._max_size_bytes:
            return
        
        # Sort by modification time (oldest first)
        cache_files.sort(key=lambda x: x[2])
        
        # Delete files until we're under the limit
        for cache_file, size, _ in cache_files:
            try:
                cache_file.unlink()
                total_size -= size
                with self._lock:
                    self._evictions += 1
                    self._save_hit_miss_stats()
                
                if total_size <= self._max_size_bytes * 0.8:  # Add some buffer
                    break
            except OSError:
                pass


class RedisCache(CacheBackend):
    """
    Redis-based cache implementation.
    
    This cache uses Redis for storage, allowing for distributed caching
    across multiple processes or machines.
    """
    
    def __init__(self, redis_url: str = 'redis://localhost:6379/0',
                 prefix: str = 'neuroca:cache:'):
        """
        Initialize the Redis cache.
        
        Args:
            redis_url: Redis connection URL
            prefix: Prefix for cache keys
        """
        if not REDIS_AVAILABLE:
            raise ImportError("Redis package is not installed. "
                              "Install it with 'pip install redis'.")
        
        self._redis = redis.from_url(redis_url)
        self._prefix = prefix
        self._stats_key = f"{self._prefix}stats"
        
        # Initialize stats
        if not self._redis.exists(self._stats_key):
            self._redis.hset(self._stats_key, mapping={
                'hits': 0,
                'misses': 0,
                'evictions': 0
            })
    
    def _get_redis_key(self, key: str) -> str:
        """
        Get the full Redis key with prefix.
        
        Args:
            key: Cache key
            
        Returns:
            Full Redis key
        """
        return f"{self._prefix}{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        redis_key = self._get_redis_key(key)
        
        # Get the value from Redis
        value = self._redis.get(redis_key)
        
        if value is None:
            # Increment miss counter
            self._redis.hincrby(self._stats_key, 'misses', 1)
            return None
        
        try:
            # Deserialize the value
            entry = pickle.loads(value)
            
            # No need to check expiration, Redis handles that
            
            # Increment hit counter
            self._redis.hincrby(self._stats_key, 'hits', 1)
            
            return entry
        except pickle.UnpicklingError as e:
            logger.warning(f"Failed to deserialize cache entry {key}: {e}")
            self._redis.hincrby(self._stats_key, 'misses', 1)
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional)
        """
        redis_key = self._get_redis_key(key)
        
        try:
            # Serialize the value
            serialized = pickle.dumps(value)
            
            # Store in Redis
            if ttl is not None:
                self._redis.setex(redis_key, int(ttl), serialized)
            else:
                self._redis.set(redis_key, serialized)
        except (pickle.PicklingError, redis.RedisError) as e:
            logger.warning(f"Failed to store cache entry {key}: {e}")
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if the key was deleted, False otherwise
        """
        redis_key = self._get_redis_key(key)
        
        try:
            # Delete from Redis
            result = self._redis.delete(redis_key)
            return result > 0
        except redis.RedisError as e:
            logger.warning(f"Failed to delete cache entry {key}: {e}")
            return False
    
    def clear(self) -> None:
        """Clear all entries from the cache."""
        try:
            # Find all keys with the prefix
            pattern = f"{self._prefix}*"
            for key in self._redis.scan_iter(match=pattern):
                if key != self._stats_key:  # Don't delete the stats
                    self._redis.delete(key)
        except redis.RedisError as e:
            logger.warning(f"Failed to clear cache: {e}")
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get statistics about the cache.
        
        Returns:
            Dictionary of cache statistics
        """
        try:
            # Count keys
            pattern = f"{self._prefix}*"
            size = sum(1 for _ in self._redis.scan_iter(match=pattern)) - 1  # Exclude stats key
            
            # Get hit/miss stats
            stats = self._redis.hgetall(self._stats_key)
            hits = int(stats.get(b'hits', 0))
            misses = int(stats.get(b'misses', 0))
            evictions = int(stats.get(b'evictions', 0))
            
            total_requests = hits + misses
            hit_rate = hits / total_requests if total_requests > 0 else 0
            
            memory_usage = self._redis.memory_usage(self._prefix)
            
            return {
                "backend": "redis",
                "prefix": self._prefix,
                "size": size,
                "hits": hits,
                "misses": misses,
                "hit_rate": hit_rate,
                "evictions": evictions,
                "memory_usage_bytes": memory_usage
            }
        except redis.RedisError as e:
            logger.warning(f"Failed to get cache stats: {e}")
            return {
                "backend": "redis",
                "prefix": self._prefix,
                "error": str(e)
            }


class Cache:
    """
    Main cache interface for the NCA system.
    
    This class provides a unified interface to different cache backends
    and offers high-level caching functionality.
    """
    
    def __init__(self, backend: Optional[CacheBackend] = None, 
                 default_ttl: Optional[float] = None):
        """
        Initialize the cache.
        
        Args:
            backend: Cache backend to use (default: InMemoryCache)
            default_ttl: Default time to live for cache entries (optional)
        """
        self._backend = backend or InMemoryCache()
        self._default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        return self._backend.get(key)
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional, defaults to self._default_ttl)
        """
        self._backend.set(key, value, ttl or self._default_ttl)
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if the key was deleted, False otherwise
        """
        return self._backend.delete(key)
    
    def clear(self) -> None:
        """Clear all entries from the cache."""
        self._backend.clear()
    
    def get_or_set(self, key: str, value_func: Callable[[], Any], 
                  ttl: Optional[float] = None) -> Any:
        """
        Get a value from the cache, or set it if not found.
        
        Args:
            key: Cache key
            value_func: Function to call to get the value if not in cache
            ttl: Time to live in seconds (optional, defaults to self._default_ttl)
            
        Returns:
            Cached or computed value
        """
        value = self.get(key)
        if value is None:
            value = value_func()
            self.set(key, value, ttl or self._default_ttl)
        return value
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get statistics about the cache.
        
        Returns:
            Dictionary of cache statistics
        """
        return self._backend.get_stats()


def create_key_from_args(*args: Any, **kwargs: Any) -> str:
    """
    Create a cache key from function arguments.
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Cache key as a string
    """
    # Sort kwargs for consistent key generation
    sorted_kwargs = sorted(kwargs.items())
    
    # Create a tuple of all arguments
    key_parts = (args, sorted_kwargs)
    
    # Hash the pickled representation for a stable key
    key = hashlib.md5(pickle.dumps(key_parts)).hexdigest()
    
    return key


def cached(cache_instance: Optional[Cache] = None, ttl: Optional[float] = None,
          key_prefix: Optional[str] = None):
    """
    Decorator to cache function results.
    
    Args:
        cache_instance: Cache instance to use
        ttl: Time to live in seconds
        key_prefix: Prefix for cache keys
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Create default cache if none provided
        nonlocal cache_instance
        if cache_instance is None:
            cache_instance = Cache()
        
        # Get the function's qualified name for the key prefix
        nonlocal key_prefix
        if key_prefix is None:
            key_prefix = f"{func.__module__}.{func.__qualname__}"
        
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Create the cache key
            arg_key = create_key_from_args(*args, **kwargs)
            cache_key = f"{key_prefix}:{arg_key}"
            
            # Check the cache
            cached_value = cache_instance.get(cache_key)
            if cached_value is not None:
                return cast(T, cached_value)
            
            # Call the function and cache the result
            result = func(*args, **kwargs)
            cache_instance.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    
    return decorator


def timed_lru_cache(maxsize: int = 128, ttl: float = 300, typed: bool = False):
    """
    Decorator for an LRU cache with time-based expiration.
    
    This combines functools.lru_cache with time-based expiration.
    
    Args:
        maxsize: Maximum cache size
        ttl: Time to live in seconds
        typed: Whether to consider argument types in the cache key
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Create an LRU cache for the function
        cached_func = functools.lru_cache(maxsize=maxsize, typed=typed)(func)
        
        # Create a dictionary to store timestamps
        timestamps: dict[CacheKey, float] = {}
        lock = threading.RLock()
        
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Create a consistent key for the timestamps dict
            key = args
            if kwargs:
                key = args + tuple(sorted(kwargs.items()))
            
            # Check if the entry has expired
            with lock:
                timestamp = timestamps.get(key)
                current_time = time.time()
                
                if timestamp is not None and current_time - timestamp > ttl:
                    # Expired, clear the cache entry
                    cached_func.cache_clear()
                    timestamps.clear()
                
                # Call the cached function
                result = cached_func(*args, **kwargs)
                
                # Update the timestamp
                timestamps[key] = current_time
                
                return result
        
        # Add cache_info and cache_clear methods
        wrapper.cache_info = cached_func.cache_info
        wrapper.cache_clear = cached_func.cache_clear
        
        return wrapper
    
    return decorator


@contextmanager
def cached_context(cache: Cache, key: str, ttl: Optional[float] = None):
    """
    Context manager for caching the result of a block of code.
    
    This is useful for caching the result of a block of code that
    doesn't fit neatly into a function.
    
    Args:
        cache: Cache instance to use
        key: Cache key
        ttl: Time to live in seconds
        
    Yields:
        Tuple of (cached_result, is_cached)
    """
    # Check the cache
    result = cache.get(key)
    if result is not None:
        yield result, True
    else:
        # Create a list to hold the result
        result_holder = []
        
        yield result_holder, False
        
        # Cache the result if available
        if result_holder:
            cache.set(key, result_holder[0], ttl)


# Create a global cache instance for easy access
global_cache = Cache()


# Memory-aware caching function
def cached_with_memory_awareness(memory_manager=None, threshold: float = 0.8, 
                                ttl: Optional[float] = None,
                                key_prefix: Optional[str] = None):
    """
    Decorator for caching function results with awareness of memory usage.
    
    This decorator works like `cached`, but will dynamically modify
    its caching behavior based on the system's memory usage. When memory
    usage exceeds the threshold, the cache will become more aggressive
    about evicting entries.
    
    Args:
        memory_manager: Memory manager instance to check for memory usage
        threshold: Memory usage threshold (0.0-1.0) above which to modify caching
        ttl: Time to live in seconds
        key_prefix: Prefix for cache keys
        
    Returns:
        Decorated function
    """
    cache_instance = Cache(InMemoryCache(eviction_threshold=threshold))
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Get the function's qualified name for the key prefix
        nonlocal key_prefix
        if key_prefix is None:
            key_prefix = f"{func.__module__}.{func.__qualname__}"
        
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Create the cache key
            arg_key = create_key_from_args(*args, **kwargs)
            cache_key = f"{key_prefix}:{arg_key}"
            
            # Check memory usage if we have a memory manager
            current_ttl = ttl
            if memory_manager is not None:
                try:
                    # Get current memory usage
                    memory_usage = memory_manager.get_memory_usage()
                    
                    # If memory usage is above threshold, reduce TTL
                    if memory_usage > threshold:
                        # The higher the memory usage, the shorter the TTL
                        usage_factor = (memory_usage - threshold) / (1 - threshold)
                        if current_ttl is not None:
                            current_ttl = current_ttl * (1 - usage_factor * 0.9)
                        
                        # If usage is very high, skip caching altogether
                        if memory_usage > 0.95:
                            return func(*args, **kwargs)
                except Exception as e:
                    logger.warning(f"Error checking memory usage: {e}")
            
            # Check the cache
            cached_value = cache_instance.get(cache_key)
            if cached_value is not None:
                return cast(T, cached_value)
            
            # Call the function and cache the result
            result = func(*args, **kwargs)
            cache_instance.set(cache_key, result, current_ttl)
            
            return result
        
        return wrapper
    
    return decorator
