"""
Performance benchmarks for the memory system.

This module contains benchmarks for various components of the memory system,
including storage backends, memory tiers, and cross-tier operations.
"""

import time
import random
import string
import pytest
import statistics
from typing import List, Dict, Any, Callable, Optional, Tuple
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

from neuroca.memory.models.memory_item import MemoryItem, MemoryMetadata
from neuroca.memory.backends.factory.backend_type import BackendType
from neuroca.memory.backends.factory.storage_factory import StorageBackendFactory
from neuroca.memory.tiers.stm.core import ShortTermMemory
from neuroca.memory.tiers.mtm.core import MediumTermMemory
from neuroca.memory.tiers.ltm.core import LongTermMemory
from neuroca.memory.manager.memory_manager import MemoryManager


def generate_random_memories(count: int, avg_content_length: int = 100) -> List[MemoryItem]:
    """Generate a list of random memories for benchmark testing."""
    memories = []
    
    for i in range(count):
        # Generate random content with varying length
        content_length = max(10, int(random.gauss(avg_content_length, avg_content_length // 4)))
        content = ''.join(random.choices(
            string.ascii_letters + string.digits + ' .,:;!?-', 
            k=content_length
        ))
        
        # Generate random tags
        num_tags = random.randint(1, 5)
        tags = ['tag' + str(random.randint(1, 20)) for _ in range(num_tags)]
        
        # Create memory with random metadata
        memory = MemoryItem(
            content=content,
            metadata=MemoryMetadata(
                importance=random.random(),
                relevance=random.random(),
                source="benchmark",
                tags=tags
            )
        )
        
        memories.append(memory)
    
    return memories


def time_operation(operation: Callable, *args, **kwargs) -> Tuple[float, Any]:
    """
    Time an operation and return both time taken and result.
    
    Args:
        operation: Function to time
        *args, **kwargs: Arguments to pass to the operation
        
    Returns:
        Tuple of (time_taken, result)
    """
    start_time = time.time()
    result = operation(*args, **kwargs)
    end_time = time.time()
    
    return (end_time - start_time), result


class MemorySystemBenchmark:
    """Benchmark class for the memory system."""
    
    def __init__(self, base_output_dir: str = "reports/benchmarks"):
        """
        Initialize the benchmark.
        
        Args:
            base_output_dir: Directory to store benchmark results
        """
        self.base_output_dir = Path(base_output_dir)
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
        
        self.results = {}
    
    def benchmark_backend_operations(
        self, 
        backend_type: BackendType,
        memory_counts: List[int] = [100, 1000, 10000],
        iterations: int = 3,
        batch_sizes: List[int] = [10, 100, 1000]
    ) -> Dict[str, Any]:
        """
        Benchmark basic operations for a specific backend type.
        
        Args:
            backend_type: Type of backend to benchmark
            memory_counts: List of memory counts to test
            iterations: Number of iterations for each test
            batch_sizes: List of batch sizes to test for batch operations
            
        Returns:
            Dictionary with benchmark results
        """
        print(f"\nBenchmarking {backend_type.name} backend...")
        results = {
            "backend_type": backend_type.name,
            "single_ops": {},
            "batch_ops": {},
            "search_ops": {}
        }
        
        for count in memory_counts:
            print(f"  Testing with {count} memories...")
            
            # Generate test data
            memories = generate_random_memories(count)
            
            # Initialize backend
            backend = StorageBackendFactory.create_backend(backend_type)
            
            # Benchmark single operations
            single_times = {
                "add": [],
                "get": [],
                "update": [],
                "delete": []
            }
            
            # Test add operation
            memory_ids = []
            for i in range(iterations):
                times = []
                for memory in memories:
                    time_taken, memory_id = time_operation(backend.add, memory)
                    times.append(time_taken)
                    if i == 0:  # Only store IDs from first iteration
                        memory_ids.append(memory_id)
                
                # Calculate average for this iteration
                single_times["add"].append(sum(times) / len(times))
                
                # Clean up for next iteration if not the last one
                if i < iterations - 1:
                    backend.clear()
            
            # Test get operation (using last iteration's data)
            times = []
            for memory_id in memory_ids:
                time_taken, _ = time_operation(backend.get, memory_id)
                times.append(time_taken)
            single_times["get"].append(sum(times) / len(times))
            
            # Test update operation
            times = []
            for i, memory_id in enumerate(memory_ids):
                updated_memory = memories[i].clone()
                updated_memory.content += " (updated)"
                time_taken, _ = time_operation(backend.update, memory_id, updated_memory)
                times.append(time_taken)
            single_times["update"].append(sum(times) / len(times))
            
            # Test delete operation
            times = []
            for memory_id in memory_ids:
                time_taken, _ = time_operation(backend.delete, memory_id)
                times.append(time_taken)
            single_times["delete"].append(sum(times) / len(times))
            
            # Calculate averages and store in results
            results["single_ops"][count] = {
                op: {
                    "mean": statistics.mean(times),
                    "min": min(times),
                    "max": max(times),
                    "total": sum(times)
                }
                for op, times in single_times.items()
            }
            
            # Benchmark batch operations
            batch_times = {
                "add_batch": {},
                "get_batch": {},
                "delete_batch": {}
            }
            
            # Test with different batch sizes
            for batch_size in batch_sizes:
                if batch_size > count:
                    continue  # Skip if batch size larger than memory count
                
                print(f"    Testing batch size {batch_size}...")
                
                batch_times["add_batch"][batch_size] = []
                batch_times["get_batch"][batch_size] = []
                batch_times["delete_batch"][batch_size] = []
                
                # Test add_batch
                for _ in range(iterations):
                    # Clear backend
                    backend.clear()
                    
                    # Create batches
                    batches = [memories[i:i+batch_size] for i in range(0, len(memories), batch_size)]
                    
                    add_times = []
                    batch_ids = []
                    
                    for batch in batches:
                        time_taken, ids = time_operation(backend.add_batch, batch)
                        add_times.append(time_taken)
                        batch_ids.append(ids)
                    
                    avg_time = sum(add_times) / len(add_times)
                    batch_times["add_batch"][batch_size].append(avg_time)
                    
                    # Flatten batch_ids for get_batch and delete_batch tests
                    memory_ids = [id for sublist in batch_ids for id in sublist]
                    
                    # Test get_batch
                    get_batches = [memory_ids[i:i+batch_size] for i in range(0, len(memory_ids), batch_size)]
                    get_times = []
                    
                    for batch in get_batches:
                        time_taken, _ = time_operation(backend.get_batch, batch)
                        get_times.append(time_taken)
                    
                    avg_time = sum(get_times) / len(get_times)
                    batch_times["get_batch"][batch_size].append(avg_time)
                    
                    # Test delete_batch
                    delete_batches = [memory_ids[i:i+batch_size] for i in range(0, len(memory_ids), batch_size)]
                    delete_times = []
                    
                    for batch in delete_batches:
                        time_taken, _ = time_operation(backend.delete_batch, batch)
                        delete_times.append(time_taken)
                    
                    avg_time = sum(delete_times) / len(delete_times)
                    batch_times["delete_batch"][batch_size].append(avg_time)
            
            # Calculate averages and store in results
            results["batch_ops"][count] = {
                op: {
                    bs: {
                        "mean": statistics.mean(times),
                        "min": min(times),
                        "max": max(times),
                        "total": sum(times)
                    }
                    for bs, times in sizes.items()
                }
                for op, sizes in batch_times.items()
            }
            
            # Benchmark search operations if backend supports it
            if hasattr(backend, 'search') and callable(getattr(backend, 'search')):
                search_times = []
                
                # Add memories again for search test
                backend.clear()
                backend.add_batch(memories)
                
                # Generate search queries from random memories
                search_queries = [
                    " ".join(memory.content.split(" ")[:3])  # First 3 words
                    for memory in random.sample(memories, min(10, len(memories)))
                ]
                
                # Test search
                for query in search_queries:
                    time_taken, results_set = time_operation(backend.search, query, limit=10)
                    search_times.append(time_taken)
                
                results["search_ops"][count] = {
                    "mean": statistics.mean(search_times),
                    "min": min(search_times),
                    "max": max(search_times),
                    "total": sum(search_times)
                }
            
            # Clean up
            backend.clear()
        
        # Store results
        self.results[f"backend_{backend_type.name}"] = results
        
        # Generate plots
        self._plot_backend_results(backend_type, results)
        
        return results
    
    def benchmark_tier_operations(
        self,
        iterations: int = 3,
        memory_counts: List[int] = [100, 1000, 5000]
    ) -> Dict[str, Any]:
        """
        Benchmark memory tier operations.
        
        Args:
            iterations: Number of iterations for each test
            memory_counts: List of memory counts to test
            
        Returns:
            Dictionary with benchmark results
        """
        print("\nBenchmarking memory tier operations...")
        results = {
            "stm": {},
            "mtm": {},
            "ltm": {},
            "consolidation": {}
        }
        
        for count in memory_counts:
            print(f"  Testing with {count} memories...")
            
            # Generate test data
            memories = generate_random_memories(count)
            
            # Benchmark each tier separately
            for tier_name in ["stm", "mtm", "ltm"]:
                print(f"    Testing {tier_name.upper()} tier...")
                
                # Initialize appropriate tier
                if tier_name == "stm":
                    tier = ShortTermMemory(
                        backend=StorageBackendFactory.create_backend(BackendType.MEMORY)
                    )
                elif tier_name == "mtm":
                    tier = MediumTermMemory(
                        backend=StorageBackendFactory.create_backend(BackendType.MEMORY)
                    )
                else:  # ltm
                    tier = LongTermMemory(
                        backend=StorageBackendFactory.create_backend(BackendType.MEMORY)
                    )
                
                tier.initialize()
                
                try:
                    # Benchmark operations for this tier
                    tier_times = {
                        "store": [],
                        "get": [],
                        "search": [],
                        "delete": []
                    }
                    
                    # Test store operation
                    memory_ids = []
                    for _ in range(iterations):
                        times = []
                        current_ids = []
                        for memory in memories:
                            time_taken, memory_id = time_operation(tier.store, memory)
                            times.append(time_taken)
                            current_ids.append(memory_id)
                        
                        tier_times["store"].append(sum(times) / len(times))
                        memory_ids = current_ids
                        
                        # Clean up for next iteration if not the last one
                        if _ < iterations - 1:
                            tier.clear()
                    
                    # Test get operation
                    times = []
                    for memory_id in memory_ids:
                        time_taken, _ = time_operation(tier.get, memory_id)
                        times.append(time_taken)
                    
                    tier_times["get"].append(sum(times) / len(times))
                    
                    # Test search operation (if supported)
                    if hasattr(tier, 'search') and callable(getattr(tier, 'search')):
                        search_times = []
                        
                        # Generate search queries from random memories
                        search_queries = [
                            " ".join(memory.content.split(" ")[:3])  # First 3 words
                            for memory in random.sample(memories, min(10, len(memories)))
                        ]
                        
                        # Test search
                        for query in search_queries:
                            time_taken, _ = time_operation(tier.search, query, limit=10)
                            search_times.append(time_taken)
                        
                        tier_times["search"].append(sum(search_times) / len(search_times))
                    
                    # Test delete operation
                    times = []
                    for memory_id in memory_ids:
                        time_taken, _ = time_operation(tier.delete, memory_id)
                        times.append(time_taken)
                    
                    tier_times["delete"].append(sum(times) / len(times))
                    
                    # Calculate averages and store in results
                    results[tier_name][count] = {
                        op: {
                            "mean": statistics.mean(times) if times else 0,
                            "min": min(times) if times else 0,
                            "max": max(times) if times else 0,
                            "total": sum(times) if times else 0
                        }
                        for op, times in tier_times.items() if times
                    }
                
                finally:
                    # Clean up
                    tier.shutdown()
            
            # Benchmark consolidation process
            print("    Testing consolidation...")
            
            # Set up memory manager with all tiers
            stm = ShortTermMemory(backend=StorageBackendFactory.create_backend(BackendType.MEMORY))
            mtm = MediumTermMemory(backend=StorageBackendFactory.create_backend(BackendType.MEMORY))
            ltm = LongTermMemory(backend=StorageBackendFactory.create_backend(BackendType.MEMORY))
            
            stm.initialize()
            mtm.initialize()
            ltm.initialize()
            
            manager = MemoryManager(stm=stm, mtm=mtm, ltm=ltm)
            manager.initialize()
            
            try:
                # Store memories in STM
                for memory in memories:
                    manager.store(memory)
                
                # Measure consolidation time
                time_taken, _ = time_operation(manager.consolidate)
                
                results["consolidation"][count] = {
                    "time": time_taken,
                    "memories": count,
                    "stm_after": manager.stm.count(),
                    "mtm_after": manager.mtm.count(),
                    "ltm_after": manager.ltm.count()
                }
            
            finally:
                # Clean up
                manager.shutdown()
                stm.shutdown()
                mtm.shutdown()
                ltm.shutdown()
        
        # Store results
        self.results["tier_operations"] = results
        
        # Generate plots
        self._plot_tier_results(results)
        
        return results
    
    def benchmark_memory_system(
        self,
        iterations: int = 3,
        memory_counts: List[int] = [100, 500, 1000],
        backend_types: List[BackendType] = [BackendType.MEMORY, BackendType.SQLITE]
    ) -> Dict[str, Any]:
        """
        Benchmark the full memory system.
        
        Args:
            iterations: Number of iterations for each test
            memory_counts: List of memory counts to test
            backend_types: List of backend types to test
            
        Returns:
            Dictionary with benchmark results
        """
        print("\nBenchmarking full memory system...")
        results = {}
        
        for backend_type in backend_types:
            print(f"  Testing with {backend_type.name} backend...")
            backend_results = {}
            
            for count in memory_counts:
                print(f"    Testing with {count} memories...")
                
                # Generate test data
                memories = generate_random_memories(count)
                
                # Set up memory manager with all tiers using the same backend type
                stm = ShortTermMemory(backend=StorageBackendFactory.create_backend(backend_type))
                mtm = MediumTermMemory(backend=StorageBackendFactory.create_backend(backend_type))
                ltm = LongTermMemory(backend=StorageBackendFactory.create_backend(backend_type))
                
                stm.initialize()
                mtm.initialize()
                ltm.initialize()
                
                manager = MemoryManager(stm=stm, mtm=mtm, ltm=ltm)
                manager.initialize()
                
                try:
                    system_times = {
                        "store": [],
                        "get": [],
                        "search": [],
                        "consolidate": []
                    }
                    
                    # Test store operation
                    for _ in range(iterations):
                        times = []
                        memory_ids = []
                        
                        for memory in memories:
                            time_taken, memory_id = time_operation(manager.store, memory)
                            times.append(time_taken)
                            memory_ids.append(memory_id)
                        
                        system_times["store"].append(sum(times) / len(times))
                        
                        # Get operation
                        times = []
                        for memory_id in memory_ids:
                            time_taken, _ = time_operation(manager.get, memory_id)
                            times.append(time_taken)
                        
                        system_times["get"].append(sum(times) / len(times))
                        
                        # Search operation
                        search_times = []
                        search_queries = [
                            " ".join(memory.content.split(" ")[:3])  # First 3 words
                            for memory in random.sample(memories, min(5, len(memories)))
                        ]
                        
                        for query in search_queries:
                            time_taken, _ = time_operation(manager.search, query)
                            search_times.append(time_taken)
                        
                        system_times["search"].append(sum(search_times) / len(search_times))
                        
                        # Consolidation operation
                        time_taken, _ = time_operation(manager.consolidate)
                        system_times["consolidate"].append(time_taken)
                        
                        # Reset for next iteration
                        if _ < iterations - 1:
                            manager.clear()
                    
                    # Calculate averages and store in results
                    backend_results[count] = {
                        op: {
                            "mean": statistics.mean(times),
                            "min": min(times),
                            "max": max(times),
                            "total": sum(times)
                        }
                        for op, times in system_times.items()
                    }
                
                finally:
                    # Clean up
                    manager.shutdown()
                    stm.shutdown()
                    mtm.shutdown()
                    ltm.shutdown()
            
            # Store results for this backend
            results[backend_type.name] = backend_results
        
        # Store overall results
        self.results["memory_system"] = results
        
        # Generate plots
        self._plot_system_results(results)
        
        return results
    
    def _plot_backend_results(self, backend_type: BackendType, results: Dict[str, Any]) -> None:
        """Generate plots for backend benchmark results."""
        output_dir = self.base_output_dir / f"backend_{backend_type.name}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        memory_counts = sorted(list(results["single_ops"].keys()))
        
        # Plot single operations
        plt.figure(figsize=(10, 6))
        
        for op in ["add", "get", "update", "delete"]:
            op_means = [results["single_ops"][count][op]["mean"] for count in memory_counts]
            plt.plot(memory_counts, op_means, marker='o', label=op)
        
        plt.xlabel("Number of Memories")
        plt.ylabel("Average Time (seconds)")
        plt.title(f"{backend_type.name} Backend: Single Operation Performance")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(output_dir / "single_ops.png")
        plt.close()
        
        # Plot batch operations
        for count in memory_counts:
            if count not in results["batch_ops"]:
                continue
                
            batch_sizes = []
            for op in ["add_batch", "get_batch", "delete_batch"]:
                if op in results["batch_ops"][count]:
                    batch_sizes.extend(list(results["batch_ops"][count][op].keys()))
            
            batch_sizes = sorted(list(set(batch_sizes)))
            
            if not batch_sizes:
                continue
            
            plt.figure(figsize=(10, 6))
            
            for op in ["add_batch", "get_batch", "delete_batch"]:
                if op not in results["batch_ops"][count]:
                    continue
                    
                op_means = [
                    results["batch_ops"][count][op].get(bs, {}).get("mean", 0) 
                    for bs in batch_sizes
                ]
                plt.plot(batch_sizes, op_means, marker='o', label=op)
            
            plt.xlabel("Batch Size")
            plt.ylabel("Average Time (seconds)")
            plt.title(f"{backend_type.name} Backend: Batch Operation Performance ({count} memories)")
            plt.legend()
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(output_dir / f"batch_ops_{count}.png")
            plt.close()
        
        # Plot search operations
        if "search_ops" in results and results["search_ops"]:
            plt.figure(figsize=(10, 6))
            
            search_counts = sorted(list(results["search_ops"].keys()))
            search_means = [results["search_ops"][count]["mean"] for count in search_counts]
            
            plt.plot(search_counts, search_means, marker='o')
            plt.xlabel("Number of Memories")
            plt.ylabel("Average Time (seconds)")
            plt.title(f"{backend_type.name} Backend: Search Performance")
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(output_dir / "search_ops.png")
            plt.close()
    
    def _plot_tier_results(self, results: Dict[str, Any]) -> None:
        """Generate plots for tier benchmark results."""
        output_dir = self.base_output_dir / "tiers"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Plot tier operations
        for tier_name in ["stm", "mtm", "ltm"]:
            if tier_name not in results or not results[tier_name]:
                continue
                
            memory_counts = sorted(list(results[tier_name].keys()))
            
            plt.figure(figsize=(10, 6))
            
            for op in ["store", "get", "search", "delete"]:
                op_means = []
                
                for count in memory_counts:
                    if op in results[tier_name][count]:
                        op_means.append(results[tier_name][count][op]["mean"])
                    else:
                        op_means.append(0)
                
                plt.plot(memory_counts, op_means, marker='o', label=op)
            
            plt.xlabel("Number of Memories")
            plt.ylabel("Average Time (seconds)")
            plt.title(f"{tier_name.upper()} Tier: Operation Performance")
            plt.legend()
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(output_dir / f"{tier_name}_ops.png")
            plt.close()
        
        # Plot consolidation
        if "consolidation" in results and results["consolidation"]:
            memory_counts = sorted(list(results["consolidation"].keys()))
            
            plt.figure(figsize=(10, 6))
            
            consolidation_times = [results["consolidation"][count]["time"] for count in memory_counts]
            plt.plot(memory_counts, consolidation_times, marker='o')
            
            plt.xlabel("Number of Memories")
            plt.ylabel("Time (seconds)")
            plt.title("Memory Consolidation Performance")
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(output_dir / "consolidation.png")
            plt.close()
            
            # Plot distribution after consolidation
            plt.figure(figsize=(10, 6))
            
            stm_after = [results["consolidation"][count]["stm_after"] for count in memory_counts]
            mtm_after = [results["consolidation"][count]["mtm_after"] for count in memory_counts]
            ltm_after = [results["consolidation"][count]["ltm_after"] for count in memory_counts]
            
            width = 0.25
            x = np.arange(len(memory_counts))
            
            plt.bar(x - width, stm_after, width, label='STM')
            plt.bar(x, mtm_after, width, label='MTM')
            plt.bar(x + width, ltm_after, width, label='LTM')
            
            plt.xlabel("Number of Memories")
            plt.ylabel("Count After Consolidation")
            plt.title("Memory Distribution After Consolidation")
            plt.xticks(x, memory_counts)
            plt.legend()
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(output_dir / "consolidation_distribution.png")
            plt.close()
    
    def _plot_system_results(self, results: Dict[str, Any]) -> None:
        """Generate plots for memory system benchmark results."""
        output_dir = self.base_output_dir / "system"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        backend_types = list(results.keys())
        operations = ["store", "get", "search", "consolidate"]
        
        # Plot by backend type
        for backend_type in backend_types:
            memory_counts = sorted(list(results[backend_type].keys()))
            
            plt.figure(figsize=(10, 6))
            
            for op in operations:
                op_means = [results[backend_type][count][op]["mean"] for count in memory_counts]
                plt.plot(memory_counts, op_means, marker='o', label=op)
            
            plt.xlabel("Number of Memories")
            plt.ylabel("Average Time (seconds)")
            plt.title(f"Memory System with {backend_type} Backend: Operation Performance")
            plt.legend()
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(output_dir / f"{backend_type}_ops.png")
            plt.close()
        
        # Plot by operation
        for op in operations:
            plt.figure(figsize=(10, 6))
            
            for backend_type in backend_types:
                memory_counts = sorted(list(results[backend_type].keys()))
                op_means = [results[backend_type][count][op]["mean"] for count in memory_counts]
                plt.plot(memory_counts, op_means, marker='o', label=backend_type)
            
            plt.xlabel("Number of Memories")
            plt.ylabel("Average Time (seconds)")
            plt.title(f"Memory System: {op} Operation Performance")
            plt.legend()
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(output_dir / f"{op}_by_backend.png")
            plt.close()
    
    def run_benchmarks(self, 
                      backend_types: List[BackendType] = [BackendType.MEMORY, BackendType.SQLITE],
                      memory_counts: List[int] = [100, 1000, 5000],
                      iterations: int = 3,
                      batch_sizes: List[int] = [10, 100, 1000]) -> Dict[str, Any]:
        """
        Run all benchmarks.
        
        Args:
            backend_types: List of backend types to benchmark
            memory_counts: List of memory counts to test
            iterations: Number of iterations for each test
            batch_sizes: List of batch sizes to test
            
        Returns:
            Dictionary with all benchmark results
        """
        # Backend operations
        for backend_type in backend_types:
            self.benchmark_backend_operations(
                backend_type,
                memory_counts=memory_counts,
                iterations=iterations,
                batch_sizes=batch_sizes
            )
        
        # Tier operations
        self.benchmark_tier_operations(
            iterations=iterations,
            memory_counts=memory_counts
        )
        
        # Full system
        self.benchmark_memory_system(
            iterations=iterations,
            memory_counts=memory_counts,
            backend_types=backend_types
        )
        
        return self.results
    
    def save_results(self, filename: str = "memory_benchmark_results.json") -> str:
        """Save benchmark results to a file."""
        import json
        
        output_path = self.base_output_dir / filename
        
        # Convert results to JSON-serializable format
        serializable_results = {}
        
        for key, value in self.results.items():
            if isinstance(value, dict):
                serializable_results[key] = value
            else:
                serializable_results[key] = str(value)
        
        with open(output_path, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        return str(output_path)


# Execute benchmarks when run
