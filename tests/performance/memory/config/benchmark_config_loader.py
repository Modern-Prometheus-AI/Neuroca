"""
Performance benchmarks for the configuration loader module.

This module contains benchmarks for measuring the performance of various
operations in the configuration loader, including loading, merging,
and accessing configuration values.
"""

import os
import time
import tempfile
import yaml
import statistics
import cProfile
import pstats
from pathlib import Path
from typing import Dict, Any, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from neuroca.memory.config.loader import (
    ConfigurationLoader,
    get_backend_config,
    get_config_value,
    _deep_copy_dict,
    _deep_merge_dicts
)


class ConfigLoaderBenchmarks:
    """Benchmarks for measuring the performance of the configuration loader."""
    
    def __init__(self, iterations: int = 100):
        """Initialize the benchmarks.
        
        Args:
            iterations: Number of iterations for each benchmark
        """
        self.iterations = iterations
        self.results: Dict[str, Dict[str, float]] = {}
    
    def setup_test_configs(self, config_sizes: List[int], config_dir: str) -> Dict[str, Dict[str, Any]]:
        """Create test configuration files of various sizes.
        
        Args:
            config_sizes: List of config sizes to create (number of entries)
            config_dir: Directory to create the configs in
            
        Returns:
            Dictionary mapping config names to their contents
        """
        configs = {}
        
        # Create base config
        base_config = {
            "common": {
                "cache": {
                    "enabled": True,
                    "max_size": 1000
                },
                "batch": {
                    "max_batch_size": 100
                }
            },
            "default_backend": "in_memory"
        }
        
        # Write base config
        base_path = Path(config_dir) / "base_config.yaml"
        with open(base_path, 'w') as f:
            yaml.dump(base_config, f)
        
        configs["base"] = base_config
        
        # Create test configs of different sizes
        for size in config_sizes:
            config_name = f"test_{size}"
            test_config = {"test_section": {}}
            
            # Add size entries
            for i in range(size):
                test_config["test_section"][f"key_{i}"] = f"value_{i}"
                
                # Add nested structure for every 10th entry
                if i % 10 == 0:
                    test_config["test_section"][f"nested_{i}"] = {
                        "nested_key_1": "nested_value_1",
                        "nested_key_2": "nested_value_2",
                        "nested_list": [1, 2, 3, 4, 5]
                    }
            
            # Write config
            config_path = Path(config_dir) / f"{config_name}_config.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(test_config, f)
            
            configs[config_name] = test_config
        
        return configs
    
    def benchmark_config_loading(self, config_dir: str, config_sizes: List[int]) -> Dict[str, float]:
        """Benchmark configuration loading performance.
        
        Args:
            config_dir: Directory containing the test configs
            config_sizes: List of config sizes to benchmark
            
        Returns:
            Dictionary of benchmark results
        """
        results = {}
        loader = ConfigurationLoader(config_dir)
        
        # First, load the base config for reference
        start_time = time.time()
        for _ in range(self.iterations):
            loader.load_config_file("base_config.yaml")
        base_time = (time.time() - start_time) / self.iterations
        results["base"] = base_time
        
        # Load each test config
        for size in config_sizes:
            config_name = f"test_{size}"
            filename = f"{config_name}_config.yaml"
            
            start_time = time.time()
            for _ in range(self.iterations):
                loader.load_config_file(filename)
            load_time = (time.time() - start_time) / self.iterations
            
            results[config_name] = load_time
        
        return results
    
    def benchmark_config_merging(self, config_dir: str, config_sizes: List[int]) -> Dict[str, float]:
        """Benchmark configuration merging performance.
        
        Args:
            config_dir: Directory containing the test configs
            config_sizes: List of config sizes to benchmark
            
        Returns:
            Dictionary of benchmark results
        """
        results = {}
        loader = ConfigurationLoader(config_dir)
        
        # Load base config once
        base_config = loader.load_config_file("base_config.yaml")
        
        # Merge with each test config
        for size in config_sizes:
            config_name = f"test_{size}"
            filename = f"{config_name}_config.yaml"
            test_config = loader.load_config_file(filename)
            
            start_time = time.time()
            for _ in range(self.iterations):
                merged = _deep_copy_dict(base_config)
                _deep_merge_dicts(merged, test_config)
            merge_time = (time.time() - start_time) / self.iterations
            
            results[config_name] = merge_time
        
        return results
    
    def benchmark_config_access(self, config_dir: str, config_sizes: List[int]) -> Dict[str, float]:
        """Benchmark configuration access performance.
        
        Args:
            config_dir: Directory containing the test configs
            config_sizes: List of config sizes to benchmark
            
        Returns:
            Dictionary of benchmark results
        """
        results = {}
        loader = ConfigurationLoader(config_dir)
        
        # Test each config size
        for size in config_sizes:
            config_name = f"test_{size}"
            loader.config_dir = config_dir
            loader.load_config(config_name)
            
            # Generate a list of paths to access
            access_paths = [
                "common.cache.enabled",
                "common.batch.max_batch_size",
                f"test_section.key_{size // 2}",
                f"test_section.nested_{size // 10}.nested_key_1",
                "nonexistent.path.with.default"
            ]
            
            # Benchmark access
            start_time = time.time()
            for _ in range(self.iterations):
                for path in access_paths:
                    loader.get_value(path, "default")
            access_time = (time.time() - start_time) / self.iterations
            
            results[config_name] = access_time
        
        return results
    
    def benchmark_concurrent_access(self, config_dir: str, thread_counts: List[int]) -> Dict[str, float]:
        """Benchmark concurrent configuration access performance.
        
        Args:
            config_dir: Directory containing the test configs
            thread_counts: List of thread counts to benchmark
            
        Returns:
            Dictionary of benchmark results
        """
        results = {}
        
        # Create a loader for every thread to ensure clean state
        def worker(tid: int) -> Tuple[int, float]:
            start_time = time.time()
            
            loader = ConfigurationLoader(config_dir)
            config = loader.load_config("test_100")
            
            # Access some values
            loader.get_value("common.cache.enabled")
            loader.get_value("test_section.key_50")
            loader.get_value(f"test_section.key_{tid % 100}")
            
            end_time = time.time()
            return tid, end_time - start_time
        
        # Test with each thread count
        for thread_count in thread_counts:
            total_times = []
            
            for _ in range(5):  # Run the concurrent test 5 times
                with ThreadPoolExecutor(max_workers=thread_count) as executor:
                    futures = [executor.submit(worker, i) for i in range(thread_count)]
                    
                    # Get all the times
                    for future in as_completed(futures):
                        _, thread_time = future.result()
                        total_times.append(thread_time)
            
            # Calculate statistics
            avg_time = statistics.mean(total_times)
            results[f"threads_{thread_count}"] = avg_time
        
        return results
    
    def run_all_benchmarks(self) -> Dict[str, Dict[str, float]]:
        """Run all benchmarks.
        
        Returns:
            Dictionary of benchmark results
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Config sizes to test
            config_sizes = [10, 100, 1000, 10000]
            thread_counts = [1, 2, 4, 8, 16]
            
            # Setup test configs
            self.setup_test_configs(config_sizes, temp_dir)
            
            # Run benchmarks
            self.results["loading"] = self.benchmark_config_loading(temp_dir, config_sizes)
            self.results["merging"] = self.benchmark_config_merging(temp_dir, config_sizes)
            self.results["access"] = self.benchmark_config_access(temp_dir, config_sizes)
            self.results["concurrent"] = self.benchmark_concurrent_access(temp_dir, thread_counts)
            
        return self.results
    
    def profile_config_loading(self, config_dir: str, config_size: int) -> pstats.Stats:
        """Profile the configuration loading process.
        
        Args:
            config_dir: Directory containing the test configs
            config_size: Size of the config to profile
            
        Returns:
            Profiling statistics
        """
        loader = ConfigurationLoader(config_dir)
        config_name = f"test_{config_size}"
        
        # Profile the loading process
        profiler = cProfile.Profile()
        profiler.enable()
        
        # Load the config several times
        for _ in range(10):
            loader.load_config(config_name)
            
        profiler.disable()
        
        return pstats.Stats(profiler)
    
    def print_results(self) -> None:
        """Print the benchmark results."""
        print("\n===== Configuration Loader Benchmark Results =====\n")
        
        for benchmark_name, benchmark_results in self.results.items():
            print(f"\n--- {benchmark_name.title()} Benchmark ---")
            print(f"{'Configuration':<20} {'Time (s)':<15}")
            print("-" * 35)
            
            for config_name, time_taken in benchmark_results.items():
                print(f"{config_name:<20} {time_taken:.6f}")
        
        print("\n===============================================\n")


def run_benchmarks() -> None:
    """Run all configuration loader benchmarks."""
    benchmarks = ConfigLoaderBenchmarks(iterations=100)
    results = benchmarks.run_all_benchmarks()
    benchmarks.print_results()
    
    # To investigate performance bottlenecks, this would typically be run in isolation
    # with tempfile.TemporaryDirectory() as temp_dir:
    #     config_sizes = [10, 100, 1000, 10000]
    #     benchmarks.setup_test_configs(config_sizes, temp_dir)
    #     stats = benchmarks.profile_config_loading(temp_dir, 10000)
    #     stats.sort_stats('cumulative').print_stats(20)


if __name__ == "__main__":
    run_benchmarks()
