"""
NeuroCognitive Architecture (NCA) - Performance Profiling Module

This module provides tools for profiling the performance of the NCA system.
It allows for detailed measurement of operation execution times, memory usage,
and resource consumption across different components of the system.

The profiling data can be used to identify bottlenecks, optimize performance,
and ensure the system operates within acceptable latency bounds under load.
"""

import cProfile
import functools
import io
import json
import logging
import os
import pstats
import threading
import time
import tracemalloc
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

import numpy as np
import psutil

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class ProfileResult:
    """Data class to store the results of a profiling operation."""
    operation_name: str
    execution_time: float  # in seconds
    memory_usage: Optional[int] = None  # in bytes
    cpu_usage: Optional[float] = None  # in percentage
    call_count: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    children: list['ProfileResult'] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert the profile result to a dictionary."""
        result = {
            "operation_name": self.operation_name,
            "execution_time": self.execution_time,
            "execution_time_ms": self.execution_time * 1000,  # for human readability
            "call_count": self.call_count,
            "avg_execution_time": self.execution_time / self.call_count
        }
        
        if self.memory_usage is not None:
            result["memory_usage"] = self.memory_usage
            result["memory_usage_mb"] = self.memory_usage / (1024 * 1024)  # for human readability
            
        if self.cpu_usage is not None:
            result["cpu_usage"] = self.cpu_usage
            
        if self.metadata:
            result["metadata"] = self.metadata
            
        if self.children:
            result["children"] = [child.to_dict() for child in self.children]
            
        return result


@dataclass
class ProfileMetrics:
    """Collection of metrics from multiple profiling operations."""
    results: list[ProfileResult] = field(default_factory=list)
    
    def add_result(self, result: ProfileResult) -> None:
        """Add a profile result to the metrics."""
        self.results.append(result)
    
    def get_result(self, operation_name: str) -> Optional[ProfileResult]:
        """Get a profile result by operation name."""
        for result in self.results:
            if result.operation_name == operation_name:
                return result
        return None
    
    def summarize(self) -> dict[str, Any]:
        """Generate a summary of the profiling metrics."""
        if not self.results:
            return {"message": "No profiling data available."}
        
        total_time = sum(r.execution_time for r in self.results)
        avg_time = total_time / len(self.results)
        max_time = max(r.execution_time for r in self.results)
        min_time = min(r.execution_time for r in self.results)
        
        # Calculate memory usage statistics if available
        memory_results = [r for r in self.results if r.memory_usage is not None]
        memory_stats = {}
        if memory_results:
            total_memory = sum(r.memory_usage for r in memory_results)
            avg_memory = total_memory / len(memory_results)
            max_memory = max(r.memory_usage for r in memory_results)
            min_memory = min(r.memory_usage for r in memory_results)
            memory_stats = {
                "total_memory_bytes": total_memory,
                "total_memory_mb": total_memory / (1024 * 1024),
                "avg_memory_bytes": avg_memory,
                "avg_memory_mb": avg_memory / (1024 * 1024),
                "max_memory_bytes": max_memory,
                "max_memory_mb": max_memory / (1024 * 1024),
                "min_memory_bytes": min_memory,
                "min_memory_mb": min_memory / (1024 * 1024)
            }
            
        # Calculate CPU usage statistics if available
        cpu_results = [r for r in self.results if r.cpu_usage is not None]
        cpu_stats = {}
        if cpu_results:
            avg_cpu = sum(r.cpu_usage for r in cpu_results) / len(cpu_results)
            max_cpu = max(r.cpu_usage for r in cpu_results)
            min_cpu = min(r.cpu_usage for r in cpu_results)
            cpu_stats = {
                "avg_cpu_percent": avg_cpu,
                "max_cpu_percent": max_cpu,
                "min_cpu_percent": min_cpu
            }
        
        return {
            "operation_count": len(self.results),
            "time_stats": {
                "total_seconds": total_time,
                "avg_seconds": avg_time,
                "max_seconds": max_time,
                "min_seconds": min_time,
                "total_ms": total_time * 1000,
                "avg_ms": avg_time * 1000,
                "max_ms": max_time * 1000,
                "min_ms": min_time * 1000
            },
            "memory_stats": memory_stats,
            "cpu_stats": cpu_stats,
            "operations": sorted(
                [r.to_dict() for r in self.results],
                key=lambda x: x["execution_time"],
                reverse=True
            )
        }
    
    def to_json(self, pretty: bool = True) -> str:
        """Convert the metrics to a JSON string."""
        indent = 2 if pretty else None
        return json.dumps(self.summarize(), indent=indent)
    
    def save_to_file(self, file_path: str, pretty: bool = True) -> None:
        """Save the metrics to a JSON file."""
        with open(file_path, 'w') as f:
            f.write(self.to_json(pretty))
        logger.info(f"Profiling metrics saved to {file_path}")


class Profiler:
    """
    Profiler for measuring execution time, memory usage, and CPU consumption.
    
    This class provides methods for profiling operations in the NCA system.
    It supports both decorator-based and context manager-based profiling.
    """
    
    def __init__(self):
        """Initialize the profiler."""
        self.metrics = ProfileMetrics()
        self._active_profiles: dict[str, dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._profile_stack: list[str] = []
        self._trace_memory = False
        
    def reset(self) -> None:
        """Reset the profiler, clearing all gathered metrics."""
        with self._lock:
            self.metrics = ProfileMetrics()
            self._active_profiles = {}
            self._profile_stack = []
            self._trace_memory = False
    
    def start_memory_tracing(self) -> None:
        """Start tracing memory allocations."""
        tracemalloc.start()
        self._trace_memory = True
        logger.debug("Memory tracing started")
    
    def stop_memory_tracing(self) -> None:
        """Stop tracing memory allocations."""
        if self._trace_memory:
            tracemalloc.stop()
            self._trace_memory = False
            logger.debug("Memory tracing stopped")
    
    def profile(self, operation_name: Optional[str] = None, 
                trace_memory: bool = False, 
                track_cpu: bool = False,
                metadata: Optional[dict[str, Any]] = None):
        """
        Decorator for profiling a function.
        
        Args:
            operation_name: Name of the operation being profiled. Defaults to function name.
            trace_memory: Whether to trace memory allocations during execution.
            track_cpu: Whether to track CPU usage during execution.
            metadata: Additional metadata to attach to the profile result.
        
        Returns:
            Decorated function.
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                nonlocal operation_name
                if operation_name is None:
                    operation_name = func.__name__
                
                with self.profile_operation(
                    operation_name=operation_name,
                    trace_memory=trace_memory,
                    track_cpu=track_cpu,
                    metadata=metadata
                ):
                    return func(*args, **kwargs)
            return wrapper
        return decorator
    
    @contextmanager
    def profile_operation(self, operation_name: str, 
                         trace_memory: bool = False, 
                         track_cpu: bool = False,
                         metadata: Optional[dict[str, Any]] = None):
        """
        Context manager for profiling an operation.
        
        Args:
            operation_name: Name of the operation being profiled.
            trace_memory: Whether to trace memory allocations during execution.
            track_cpu: Whether to track CPU usage during execution.
            metadata: Additional metadata to attach to the profile result.
        """
        self._start_profiling(operation_name, trace_memory, track_cpu, metadata)
        try:
            yield
        finally:
            self._stop_profiling(operation_name)
    
    def _start_profiling(self, operation_name: str, 
                        trace_memory: bool, 
                        track_cpu: bool,
                        metadata: Optional[dict[str, Any]]) -> None:
        """Start profiling an operation."""
        with self._lock:
            profile_data = {
                "start_time": time.time(),
                "metadata": metadata or {},
                "trace_memory": trace_memory,
                "track_cpu": track_cpu,
                "parent": self._profile_stack[-1] if self._profile_stack else None
            }
            
            # Start memory tracing if requested
            if trace_memory and not self._trace_memory:
                tracemalloc.start()
                self._trace_memory = True
                profile_data["memory_snapshot_start"] = tracemalloc.take_snapshot()
            elif trace_memory and self._trace_memory:
                profile_data["memory_snapshot_start"] = tracemalloc.take_snapshot()
            
            # Start CPU tracking if requested
            if track_cpu:
                process = psutil.Process(os.getpid())
                profile_data["cpu_percent_start"] = process.cpu_percent(interval=0.1)
            
            self._active_profiles[operation_name] = profile_data
            self._profile_stack.append(operation_name)
    
    def _stop_profiling(self, operation_name: str) -> None:
        """Stop profiling an operation and record the results."""
        with self._lock:
            end_time = time.time()
            
            if operation_name not in self._active_profiles:
                logger.warning(f"Attempted to stop profiling for operation '{operation_name}' "
                              f"which was not started")
                return
            
            if self._profile_stack and self._profile_stack[-1] == operation_name:
                self._profile_stack.pop()
            else:
                # Profile stack is out of order, try to find and remove the operation
                try:
                    self._profile_stack.remove(operation_name)
                except ValueError:
                    logger.warning(f"Operation '{operation_name}' not found in profile stack")
            
            profile_data = self._active_profiles[operation_name]
            start_time = profile_data["start_time"]
            execution_time = end_time - start_time
            memory_usage = None
            cpu_usage = None
            
            # Calculate memory usage if tracking was requested
            if profile_data.get("trace_memory"):
                if "memory_snapshot_start" in profile_data:
                    memory_snapshot_end = tracemalloc.take_snapshot()
                    memory_stats = memory_snapshot_end.compare_to(profile_data["memory_snapshot_start"], 'lineno')
                    memory_usage = sum(stat.size_diff for stat in memory_stats if stat.size_diff > 0)
                    
                    # If no more active memory traces, stop tracemalloc
                    active_memory_traces = any(
                        p.get("trace_memory", False) for p in self._active_profiles.values()
                        if p != profile_data
                    )
                    if not active_memory_traces and self._trace_memory:
                        tracemalloc.stop()
                        self._trace_memory = False
            
            # Calculate CPU usage if tracking was requested
            if profile_data.get("track_cpu"):
                process = psutil.Process(os.getpid())
                cpu_usage = process.cpu_percent(interval=0.1)
            
            # Create the profile result
            result = ProfileResult(
                operation_name=operation_name,
                execution_time=execution_time,
                memory_usage=memory_usage,
                cpu_usage=cpu_usage,
                metadata=profile_data["metadata"]
            )
            
            # Add the result to its parent if it has one
            parent_name = profile_data.get("parent")
            if parent_name and parent_name in self._active_profiles:
                if "children" not in self._active_profiles[parent_name]:
                    self._active_profiles[parent_name]["children"] = []
                self._active_profiles[parent_name]["children"].append(result)
            else:
                # Otherwise add it to the top-level metrics
                self.metrics.add_result(result)
            
            # Remove the profile data for this operation
            del self._active_profiles[operation_name]
    
    def detailed_function_profile(self, func: Callable, *args, **kwargs) -> tuple[Any, pstats.Stats]:
        """
        Perform a detailed profile of a function using cProfile.
        
        Args:
            func: The function to profile.
            *args: Arguments to pass to the function.
            **kwargs: Keyword arguments to pass to the function.
            
        Returns:
            A tuple containing (function_result, profile_stats).
        """
        pr = cProfile.Profile()
        pr.enable()
        result = func(*args, **kwargs)
        pr.disable()
        
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats()
        
        return result, ps
    
    def summarize(self) -> dict[str, Any]:
        """Generate a summary of the profiling metrics."""
        return self.metrics.summarize()
    
    def save_to_file(self, file_path: str) -> None:
        """Save the profiling metrics to a file."""
        self.metrics.save_to_file(file_path)


# Create a global instance for easy access
profiler = Profiler()


def measure_execution_time(func: Optional[Callable] = None, *, operation_name: Optional[str] = None):
    """
    Decorator to measure the execution time of a function.
    
    This is a simplified version of the profile decorator that only measures
    execution time without the overhead of memory and CPU tracking.
    
    Args:
        func: The function to measure.
        operation_name: Name of the operation. Defaults to function name.
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            name = operation_name or f.__name__
            start_time = time.time()
            result = f(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Create and add the profile result
            profile_result = ProfileResult(operation_name=name, execution_time=execution_time)
            profiler.metrics.add_result(profile_result)
            
            return result
        return wrapper
    
    if func is None:
        return decorator
    return decorator(func)


@contextmanager
def measure_operation(operation_name: str):
    """
    Context manager to measure the execution time of an operation.
    
    This is a simplified version of the profile_operation context manager
    that only measures execution time without the overhead of memory and CPU tracking.
    
    Args:
        operation_name: Name of the operation.
    """
    start_time = time.time()
    try:
        yield
    finally:
        execution_time = time.time() - start_time
        profile_result = ProfileResult(operation_name=operation_name, execution_time=execution_time)
        profiler.metrics.add_result(profile_result)


def run_profiled_load_test(func: Callable, num_threads: int = 4, iterations: int = 100) -> dict[str, Any]:
    """
    Run a load test on a function with profiling.
    
    Args:
        func: The function to test.
        num_threads: Number of threads to use for the test.
        iterations: Number of iterations to run per thread.
        
    Returns:
        Dictionary with load test results.
    """
    profiler.reset()
    errors = []
    
    def worker(iteration):
        try:
            with measure_operation(f"{func.__name__}_iteration_{iteration}"):
                return func()
        except Exception as e:
            errors.append((iteration, str(e)))
            return None
    
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker, i) for i in range(iterations)]
        [future.result() for future in futures]
    end_time = time.time()
    
    total_time = end_time - start_time
    operations_per_second = iterations / total_time
    
    # Calculate statistics on execution times
    execution_times = [
        r.execution_time for r in profiler.metrics.results 
        if r.operation_name.startswith(f"{func.__name__}_iteration_")
    ]
    
    if execution_times:
        avg_time = np.mean(execution_times)
        median_time = np.median(execution_times)
        p95_time = np.percentile(execution_times, 95)
        p99_time = np.percentile(execution_times, 99)
        min_time = np.min(execution_times)
        max_time = np.max(execution_times)
    else:
        avg_time = median_time = p95_time = p99_time = min_time = max_time = 0
    
    return {
        "function_name": func.__name__,
        "threads": num_threads,
        "iterations": iterations,
        "successful_iterations": iterations - len(errors),
        "errors": len(errors),
        "error_details": errors,
        "total_time_seconds": total_time,
        "operations_per_second": operations_per_second,
        "execution_time_stats": {
            "avg_seconds": avg_time,
            "median_seconds": median_time,
            "p95_seconds": p95_time,
            "p99_seconds": p99_time,
            "min_seconds": min_time,
            "max_seconds": max_time,
            "avg_ms": avg_time * 1000,
            "median_ms": median_time * 1000,
            "p95_ms": p95_time * 1000,
            "p99_ms": p99_time * 1000,
            "min_ms": min_time * 1000,
            "max_ms": max_time * 1000
        }
    }
