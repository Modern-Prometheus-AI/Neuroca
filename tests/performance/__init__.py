"""
Performance Testing Module for NeuroCognitive Architecture (NCA).

This module provides tools, utilities, and fixtures for conducting performance
tests on the NeuroCognitive Architecture system. It enables measuring and
analyzing the performance characteristics of various components, including:

- Memory tier access and retrieval speeds
- LLM integration response times
- Cognitive processing throughput
- System scalability under load
- Resource utilization metrics

The performance testing framework is designed to be used both in automated CI/CD
pipelines and for manual benchmarking during development.

Usage:
    from neuroca.tests.performance import (
        PerformanceTestCase,
        benchmark,
        measure_memory_usage,
        measure_response_time,
        load_test
    )

    # Example: Measuring function execution time
    @benchmark
    def test_memory_retrieval():
        # Test code here
        pass

    # Example: Creating a performance test case
    class MemoryTierPerformanceTest(PerformanceTestCase):
        def test_working_memory_throughput(self):
            with self.measure_time():
                # Test code here
                pass
"""

import functools
import logging
import time
import tracemalloc
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Optional

# Configure logging for performance tests
logger = logging.getLogger(__name__)

# Performance test constants
DEFAULT_ITERATIONS = 5
DEFAULT_WARMUP_ITERATIONS = 2
DEFAULT_COOLDOWN_SECONDS = 1.0
DEFAULT_TIMEOUT_SECONDS = 30.0


@dataclass
class PerformanceMetric:
    """
    Data class for storing performance test metrics.
    
    Attributes:
        name: Name of the metric or test
        start_time: When the test started
        end_time: When the test completed
        duration_ms: Test duration in milliseconds
        memory_before_kb: Memory usage before test in KB
        memory_after_kb: Memory usage after test in KB
        memory_diff_kb: Memory usage difference in KB
        cpu_percent: CPU utilization percentage
        metadata: Additional test-specific metadata
    """
    name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    memory_before_kb: Optional[float] = None
    memory_after_kb: Optional[float] = None
    memory_diff_kb: Optional[float] = None
    cpu_percent: Optional[float] = None
    metadata: dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize default values for optional fields."""
        if self.metadata is None:
            self.metadata = {}
    
    def complete(self, end_time: datetime, memory_after_kb: float, cpu_percent: float) -> None:
        """
        Complete the performance metric with end results.
        
        Args:
            end_time: When the test completed
            memory_after_kb: Memory usage after test in KB
            cpu_percent: CPU utilization percentage
        """
        self.end_time = end_time
        self.memory_after_kb = memory_after_kb
        self.cpu_percent = cpu_percent
        
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            self.duration_ms = delta.total_seconds() * 1000
        
        if self.memory_before_kb is not None and self.memory_after_kb is not None:
            self.memory_diff_kb = self.memory_after_kb - self.memory_before_kb
    
    def to_dict(self) -> dict[str, Any]:
        """
        Convert the metric to a dictionary for serialization.
        
        Returns:
            Dict containing all metric data
        """
        return {
            "name": self.name,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "memory_before_kb": self.memory_before_kb,
            "memory_after_kb": self.memory_after_kb,
            "memory_diff_kb": self.memory_diff_kb,
            "cpu_percent": self.cpu_percent,
            "metadata": self.metadata
        }


class PerformanceTestCase:
    """
    Base class for performance test cases in the NCA system.
    
    This class provides utilities for measuring execution time, memory usage,
    and other performance characteristics of NCA components.
    
    Example:
        class MemoryTierPerformanceTest(PerformanceTestCase):
            def setup(self):
                self.memory_system = MemorySystem()
                
            def test_working_memory_access(self):
                with self.measure_time() as metric:
                    result = self.memory_system.working_memory.retrieve("test_key")
                    metric.metadata["result_size"] = len(result)
    """
    
    def __init__(self):
        """Initialize the performance test case with empty results."""
        self.results: list[PerformanceMetric] = []
    
    def setup(self) -> None:
        """Set up the test environment. Override in subclasses."""
        pass
    
    def teardown(self) -> None:
        """Clean up after tests. Override in subclasses."""
        pass
    
    @contextmanager
    def measure_time(self, name: Optional[str] = None) -> PerformanceMetric:
        """
        Context manager for measuring execution time and resource usage.
        
        Args:
            name: Name of the measurement. Defaults to the calling function name.
            
        Yields:
            PerformanceMetric: The metric object being populated
            
        Example:
            with self.measure_time("memory_retrieval") as metric:
                result = memory_system.retrieve(key)
                metric.metadata["result_size"] = len(result)
        """
        if name is None:
            # Get the calling function's name if not provided
            name = traceback.extract_stack()[-2][2]
        
        # Start tracking memory
        tracemalloc.start()
        memory_before = tracemalloc.get_traced_memory()[0] / 1024  # KB
        
        try:
            # Create and initialize the metric
            start_time = datetime.now()
            metric = PerformanceMetric(
                name=name,
                start_time=start_time,
                memory_before_kb=memory_before
            )
            
            # Yield the metric to the caller
            yield metric
            
            # Measure final state
            end_time = datetime.now()
            memory_after = tracemalloc.get_traced_memory()[0] / 1024  # KB
            
            # Try to get CPU usage if psutil is available
            cpu_percent = None
            try:
                import psutil
                cpu_percent = psutil.cpu_percent()
            except (ImportError, AttributeError):
                logger.debug("psutil not available for CPU measurement")
            
            # Complete the metric
            metric.complete(end_time, memory_after, cpu_percent)
            
            # Store the result
            self.results.append(metric)
            
            # Log the result
            logger.info(
                f"Performance test '{name}' completed: "
                f"{metric.duration_ms:.2f}ms, "
                f"memory change: {metric.memory_diff_kb:.2f}KB"
            )
            
        finally:
            # Stop memory tracking
            tracemalloc.stop()
    
    def run_benchmark(self, func: Callable, iterations: int = DEFAULT_ITERATIONS, 
                     warmup: int = DEFAULT_WARMUP_ITERATIONS,
                     cooldown: float = DEFAULT_COOLDOWN_SECONDS) -> list[PerformanceMetric]:
        """
        Run a benchmark test with multiple iterations.
        
        Args:
            func: Function to benchmark
            iterations: Number of test iterations
            warmup: Number of warmup iterations (not counted in results)
            cooldown: Cooldown time between iterations in seconds
            
        Returns:
            List of performance metrics for each iteration
            
        Raises:
            ValueError: If iterations or warmup are negative
        """
        if iterations < 0 or warmup < 0:
            raise ValueError("Iterations and warmup must be non-negative")
        
        name = func.__name__
        results = []
        
        logger.info(f"Starting benchmark '{name}' with {warmup} warmup and {iterations} measured iterations")
        
        # Warmup phase
        for i in range(warmup):
            logger.debug(f"Warmup iteration {i+1}/{warmup}")
            func()
            time.sleep(cooldown)
        
        # Measured iterations
        for i in range(iterations):
            logger.debug(f"Benchmark iteration {i+1}/{iterations}")
            with self.measure_time(f"{name}_iter_{i+1}") as metric:
                result = func()
                metric.metadata["iteration"] = i + 1
                if result is not None:
                    try:
                        metric.metadata["result"] = str(result)
                    except:
                        metric.metadata["result"] = "unprintable"
            
            results.append(self.results[-1])
            time.sleep(cooldown)
        
        return results
    
    def report_results(self) -> dict[str, Any]:
        """
        Generate a report of all test results.
        
        Returns:
            Dictionary containing test results and summary statistics
        """
        if not self.results:
            return {"status": "no_results", "results": []}
        
        # Group results by test name
        grouped_results = {}
        for result in self.results:
            if result.name not in grouped_results:
                grouped_results[result.name] = []
            grouped_results[result.name].append(result)
        
        # Calculate statistics for each group
        summary = {}
        for name, metrics in grouped_results.items():
            durations = [m.duration_ms for m in metrics if m.duration_ms is not None]
            memory_diffs = [m.memory_diff_kb for m in metrics if m.memory_diff_kb is not None]
            
            if durations:
                summary[name] = {
                    "count": len(metrics),
                    "duration": {
                        "min_ms": min(durations),
                        "max_ms": max(durations),
                        "avg_ms": sum(durations) / len(durations),
                    }
                }
                
                if memory_diffs:
                    summary[name]["memory"] = {
                        "min_kb": min(memory_diffs),
                        "max_kb": max(memory_diffs),
                        "avg_kb": sum(memory_diffs) / len(memory_diffs),
                    }
        
        return {
            "status": "success",
            "test_count": len(self.results),
            "summary": summary,
            "results": [r.to_dict() for r in self.results]
        }


def benchmark(func: Optional[Callable] = None, *, 
              iterations: int = DEFAULT_ITERATIONS,
              warmup: int = DEFAULT_WARMUP_ITERATIONS,
              cooldown: float = DEFAULT_COOLDOWN_SECONDS) -> Callable:
    """
    Decorator for benchmarking function performance.
    
    This decorator can be used with or without arguments:
    
    @benchmark
    def my_function():
        pass
        
    @benchmark(iterations=10, warmup=2)
    def my_function():
        pass
    
    Args:
        func: Function to benchmark
        iterations: Number of test iterations
        warmup: Number of warmup iterations
        cooldown: Cooldown time between iterations in seconds
        
    Returns:
        Decorated function that will run performance benchmarks
        
    Example:
        @benchmark(iterations=5)
        def test_memory_retrieval(key):
            return memory_system.retrieve(key)
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            test_case = PerformanceTestCase()
            
            # Define the function to benchmark with args
            def benchmarked_func():
                return fn(*args, **kwargs)
            
            # Run the benchmark
            test_case.run_benchmark(
                benchmarked_func, 
                iterations=iterations,
                warmup=warmup,
                cooldown=cooldown
            )
            
            # Get the actual function result (last run)
            result = fn(*args, **kwargs)
            
            # Attach the performance results to the return value if possible
            if hasattr(result, '__dict__'):
                result.__performance_results__ = test_case.report_results()
            
            return result
        
        return wrapper
    
    # Handle both @benchmark and @benchmark() syntax
    if func is None:
        return decorator
    return decorator(func)


@contextmanager
def measure_memory_usage(name: str = "memory_measurement") -> dict[str, Any]:
    """
    Context manager for measuring memory usage of a code block.
    
    Args:
        name: Name of the measurement
        
    Yields:
        Dictionary to store results
        
    Example:
        with measure_memory_usage("large_model_load") as results:
            model = load_large_model()
            results["model_size"] = model.size_mb
    """
    tracemalloc.start()
    start_snapshot = tracemalloc.take_snapshot()
    start_memory = tracemalloc.get_traced_memory()
    
    results = {
        "name": name,
        "start_time": datetime.now(),
        "start_memory_kb": start_memory[0] / 1024,
    }
    
    try:
        yield results
    finally:
        end_memory = tracemalloc.get_traced_memory()
        end_snapshot = tracemalloc.take_snapshot()
        end_time = datetime.now()
        
        results.update({
            "end_time": end_time,
            "duration_ms": (end_time - results["start_time"]).total_seconds() * 1000,
            "end_memory_kb": end_memory[0] / 1024,
            "peak_memory_kb": end_memory[1] / 1024,
            "memory_diff_kb": (end_memory[0] - start_memory[0]) / 1024,
        })
        
        # Get top memory differences
        top_stats = end_snapshot.compare_to(start_snapshot, 'lineno')
        results["top_memory_allocations"] = [
            {
                "file": str(stat.traceback.frame.filename),
                "line": stat.traceback.frame.lineno,
                "size_kb": stat.size / 1024,
                "size_diff_kb": stat.size_diff / 1024,
            }
            for stat in top_stats[:10]  # Top 10 allocations
        ]
        
        tracemalloc.stop()
        
        logger.info(
            f"Memory measurement '{name}' completed: "
            f"change: {results['memory_diff_kb']:.2f}KB, "
            f"peak: {results['peak_memory_kb']:.2f}KB"
        )


def measure_response_time(func: Callable, *args, **kwargs) -> tuple[Any, float]:
    """
    Measure the response time of a function call.
    
    Args:
        func: Function to measure
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
        
    Returns:
        Tuple containing (function_result, execution_time_ms)
        
    Example:
        result, time_ms = measure_response_time(
            llm_integration.generate_response, 
            prompt="Tell me about cognitive architectures"
        )
        print(f"Response generated in {time_ms:.2f}ms")
    """
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    execution_time_ms = (end_time - start_time) * 1000
    
    logger.debug(f"Function {func.__name__} executed in {execution_time_ms:.2f}ms")
    return result, execution_time_ms


def load_test(func: Callable, concurrent_users: int, 
             requests_per_user: int, 
             timeout: float = DEFAULT_TIMEOUT_SECONDS) -> dict[str, Any]:
    """
    Perform a load test by simulating multiple concurrent users.
    
    Args:
        func: Function to test
        concurrent_users: Number of concurrent users to simulate
        requests_per_user: Number of requests per user
        timeout: Maximum time to wait for completion in seconds
        
    Returns:
        Dictionary with load test results
        
    Raises:
        ImportError: If required dependencies are not available
        TimeoutError: If the test exceeds the specified timeout
        
    Example:
        results = load_test(
            memory_system.retrieve,
            concurrent_users=10,
            requests_per_user=5
        )
        print(f"Average response time: {results['avg_response_time_ms']:.2f}ms")
    """
    try:
        import concurrent.futures
        import threading
    except ImportError:
        raise ImportError("concurrent.futures is required for load testing")
    
    results = {
        "start_time": datetime.now(),
        "concurrent_users": concurrent_users,
        "requests_per_user": requests_per_user,
        "total_requests": concurrent_users * requests_per_user,
        "successful_requests": 0,
        "failed_requests": 0,
        "response_times_ms": [],
        "errors": []
    }
    
    # Thread-safe collections for gathering results
    lock = threading.Lock()
    
    def user_task(user_id):
        user_results = {
            "user_id": user_id,
            "successful": 0,
            "failed": 0,
            "response_times_ms": []
        }
        
        for i in range(requests_per_user):
            try:
                start_time = time.time()
                func()
                end_time = time.time()
                
                response_time_ms = (end_time - start_time) * 1000
                
                with lock:
                    user_results["successful"] += 1
                    user_results["response_times_ms"].append(response_time_ms)
            except Exception as e:
                error_info = {
                    "user_id": user_id,
                    "request_num": i,
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }
                
                with lock:
                    user_results["failed"] += 1
                    results["errors"].append(error_info)
                
                logger.error(f"Load test error (User {user_id}, Request {i}): {str(e)}")
        
        return user_results
    
    # Execute the load test with a thread pool
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
        future_to_user = {
            executor.submit(user_task, user_id): user_id 
            for user_id in range(concurrent_users)
        }
        
        # Collect results with timeout
        try:
            for future in concurrent.futures.as_completed(future_to_user, timeout=timeout):
                user_id = future_to_user[future]
                try:
                    user_result = future.result()
                    
                    with lock:
                        results["successful_requests"] += user_result["successful"]
                        results["failed_requests"] += user_result["failed"]
                        results["response_times_ms"].extend(user_result["response_times_ms"])
                        
                except Exception as e:
                    with lock:
                        results["failed_requests"] += requests_per_user
                        results["errors"].append({
                            "user_id": user_id,
                            "error": str(e),
                            "traceback": traceback.format_exc()
                        })
        except concurrent.futures.TimeoutError:
            results["timeout"] = True
            results["timeout_seconds"] = timeout
            logger.error(f"Load test timed out after {timeout} seconds")
    
    # Calculate statistics
    results["end_time"] = datetime.now()
    results["duration_seconds"] = (results["end_time"] - results["start_time"]).total_seconds()
    
    if results["response_times_ms"]:
        results["min_response_time_ms"] = min(results["response_times_ms"])
        results["max_response_time_ms"] = max(results["response_times_ms"])
        results["avg_response_time_ms"] = sum(results["response_times_ms"]) / len(results["response_times_ms"])
        
        # Calculate percentiles
        sorted_times = sorted(results["response_times_ms"])
        results["percentiles"] = {
            "50th": sorted_times[int(len(sorted_times) * 0.5)],
            "90th": sorted_times[int(len(sorted_times) * 0.9)],
            "95th": sorted_times[int(len(sorted_times) * 0.95)],
            "99th": sorted_times[int(len(sorted_times) * 0.99)] if len(sorted_times) >= 100 else None
        }
    
    # Log summary
    logger.info(
        f"Load test completed: {results['successful_requests']}/{results['total_requests']} "
        f"successful requests, avg response time: "
        f"{results.get('avg_response_time_ms', 0):.2f}ms"
    )
    
    return results


# Version information
__version__ = "0.1.0"

# Export public API
__all__ = [
    "PerformanceMetric",
    "PerformanceTestCase",
    "benchmark",
    "measure_memory_usage",
    "measure_response_time",
    "load_test",
]