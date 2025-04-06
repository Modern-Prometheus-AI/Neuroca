"""
Performance Benchmarking Module for NeuroCognitive Architecture (NCA)

This module provides comprehensive benchmarking tools to measure and analyze the 
performance of various components of the NCA system. It includes utilities for:
- Memory access and manipulation benchmarks
- Processing speed measurements
- Resource utilization tracking
- Comparative performance analysis
- Benchmark result persistence and visualization

Usage:
    from neuroca.tests.performance.benchmarks import run_benchmark_suite
    
    # Run all benchmarks
    results = run_benchmark_suite()
    
    # Run specific benchmark
    memory_results = run_benchmark('memory_access')
    
    # Run benchmark with custom parameters
    custom_results = run_benchmark('llm_integration', 
                                  iterations=100, 
                                  payload_size=1024)
"""

import datetime
import json
import logging
import os
import statistics
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from functools import wraps
from pathlib import Path
from typing import Any, Optional

import matplotlib.pyplot as plt
import pandas as pd
import psutil

# Configure logging
logger = logging.getLogger(__name__)

# Constants
DEFAULT_ITERATIONS = 50
DEFAULT_WARMUP_ITERATIONS = 5
BENCHMARK_RESULTS_DIR = Path("benchmark_results")


@dataclass
class BenchmarkResult:
    """Data class to store benchmark results."""
    name: str
    execution_times: list[float]
    start_time: datetime.datetime
    end_time: datetime.datetime
    parameters: dict[str, Any] = field(default_factory=dict)
    memory_usage: dict[str, float] = field(default_factory=dict)
    cpu_usage: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @property
    def mean_execution_time(self) -> float:
        """Calculate the mean execution time."""
        return statistics.mean(self.execution_times)
    
    @property
    def median_execution_time(self) -> float:
        """Calculate the median execution time."""
        return statistics.median(self.execution_times)
    
    @property
    def std_deviation(self) -> float:
        """Calculate the standard deviation of execution times."""
        return statistics.stdev(self.execution_times) if len(self.execution_times) > 1 else 0
    
    @property
    def min_execution_time(self) -> float:
        """Get the minimum execution time."""
        return min(self.execution_times)
    
    @property
    def max_execution_time(self) -> float:
        """Get the maximum execution time."""
        return max(self.execution_times)
    
    @property
    def total_duration(self) -> float:
        """Calculate the total benchmark duration in seconds."""
        return (self.end_time - self.start_time).total_seconds()
    
    def to_dict(self) -> dict[str, Any]:
        """Convert the benchmark result to a dictionary."""
        result = asdict(self)
        # Add computed properties
        result.update({
            "mean_execution_time": self.mean_execution_time,
            "median_execution_time": self.median_execution_time,
            "std_deviation": self.std_deviation,
            "min_execution_time": self.min_execution_time,
            "max_execution_time": self.max_execution_time,
            "total_duration": self.total_duration
        })
        # Convert datetime objects to ISO format strings
        result["start_time"] = self.start_time.isoformat()
        result["end_time"] = self.end_time.isoformat()
        return result
    
    def save(self, directory: Optional[Path] = None) -> Path:
        """Save benchmark results to a JSON file."""
        if directory is None:
            directory = BENCHMARK_RESULTS_DIR
        
        directory.mkdir(exist_ok=True, parents=True)
        
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        filename = f"{self.name}_{timestamp}.json"
        filepath = directory / filename
        
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        
        logger.info(f"Benchmark results saved to {filepath}")
        return filepath


@contextmanager
def measure_time() -> float:
    """Context manager to measure execution time."""
    start_time = time.perf_counter()
    try:
        yield
    finally:
        end_time = time.perf_counter()
        end_time - start_time


@contextmanager
def measure_resources():
    """Context manager to measure CPU and memory usage."""
    process = psutil.Process(os.getpid())
    
    # Measure before
    mem_before = process.memory_info().rss / 1024 / 1024  # MB
    cpu_percent_before = process.cpu_percent()
    
    yield
    
    # Measure after
    mem_after = process.memory_info().rss / 1024 / 1024  # MB
    cpu_percent_after = process.cpu_percent()
    
    return {
        "memory_usage_mb": mem_after - mem_before,
        "cpu_percent": cpu_percent_after - cpu_percent_before
    }


def benchmark(func=None, *, iterations=DEFAULT_ITERATIONS, warmup=DEFAULT_WARMUP_ITERATIONS, 
              parameters=None, metadata=None):
    """
    Decorator to benchmark a function.
    
    Args:
        func: The function to benchmark
        iterations: Number of iterations to run
        warmup: Number of warmup iterations (not included in results)
        parameters: Additional parameters to include in the benchmark result
        metadata: Additional metadata to include in the benchmark result
    
    Returns:
        Decorated function that returns a BenchmarkResult
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            logger.info(f"Starting benchmark: {func_name}")
            
            # Initialize result data
            execution_times = []
            memory_usage = {}
            cpu_usage = {}
            start_time = datetime.datetime.now()
            
            # Perform warmup iterations
            logger.debug(f"Performing {warmup} warmup iterations")
            for _ in range(warmup):
                func(*args, **kwargs)
            
            # Perform benchmark iterations
            logger.info(f"Running {iterations} benchmark iterations")
            for i in range(iterations):
                # Measure execution time
                iteration_start = time.perf_counter()
                
                # Measure resource usage
                process = psutil.Process(os.getpid())
                mem_before = process.memory_info().rss / 1024 / 1024  # MB
                cpu_before = process.cpu_percent(interval=None)
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Measure resource usage after execution
                mem_after = process.memory_info().rss / 1024 / 1024  # MB
                cpu_after = process.cpu_percent(interval=None)
                
                # Record measurements
                iteration_end = time.perf_counter()
                execution_time = iteration_end - iteration_start
                execution_times.append(execution_time)
                
                memory_usage[f"iteration_{i}"] = mem_after - mem_before
                cpu_usage[f"iteration_{i}"] = cpu_after - cpu_before
                
                logger.debug(f"Iteration {i+1}/{iterations}: {execution_time:.6f}s")
            
            end_time = datetime.datetime.now()
            
            # Create benchmark result
            benchmark_result = BenchmarkResult(
                name=func_name,
                execution_times=execution_times,
                start_time=start_time,
                end_time=end_time,
                parameters=parameters or {},
                memory_usage=memory_usage,
                cpu_usage=cpu_usage,
                metadata=metadata or {}
            )
            
            # Log summary
            logger.info(f"Benchmark complete: {func_name}")
            logger.info(f"Mean execution time: {benchmark_result.mean_execution_time:.6f}s")
            logger.info(f"Median execution time: {benchmark_result.median_execution_time:.6f}s")
            logger.info(f"Min/Max execution time: {benchmark_result.min_execution_time:.6f}s / {benchmark_result.max_execution_time:.6f}s")
            
            return result, benchmark_result
        
        return wrapper
    
    if func is None:
        return decorator
    return decorator(func)


def run_benchmark(benchmark_name: str, **kwargs) -> BenchmarkResult:
    """
    Run a specific benchmark by name.
    
    Args:
        benchmark_name: Name of the benchmark to run
        **kwargs: Additional parameters to pass to the benchmark
    
    Returns:
        BenchmarkResult object containing the results
    
    Raises:
        ValueError: If the benchmark name is not recognized
    """
    benchmark_registry = {
        "memory_access": benchmark_memory_access,
        "memory_tier_comparison": benchmark_memory_tier_comparison,
        "llm_integration": benchmark_llm_integration,
        "cognitive_processing": benchmark_cognitive_processing,
        "system_throughput": benchmark_system_throughput
    }
    
    if benchmark_name not in benchmark_registry:
        raise ValueError(f"Unknown benchmark: {benchmark_name}. Available benchmarks: {list(benchmark_registry.keys())}")
    
    logger.info(f"Running benchmark: {benchmark_name}")
    _, result = benchmark_registry[benchmark_name](**kwargs)
    return result


def run_benchmark_suite(benchmarks: Optional[list[str]] = None, 
                        save_results: bool = True,
                        generate_report: bool = True) -> dict[str, BenchmarkResult]:
    """
    Run a suite of benchmarks and collect their results.
    
    Args:
        benchmarks: List of benchmark names to run. If None, runs all benchmarks.
        save_results: Whether to save results to disk
        generate_report: Whether to generate a report of the results
    
    Returns:
        Dictionary mapping benchmark names to their results
    """
    available_benchmarks = [
        "memory_access",
        "memory_tier_comparison",
        "llm_integration",
        "cognitive_processing",
        "system_throughput"
    ]
    
    benchmarks_to_run = benchmarks or available_benchmarks
    
    # Validate benchmark names
    for benchmark in benchmarks_to_run:
        if benchmark not in available_benchmarks:
            raise ValueError(f"Unknown benchmark: {benchmark}. Available benchmarks: {available_benchmarks}")
    
    logger.info(f"Running benchmark suite with {len(benchmarks_to_run)} benchmarks")
    
    results = {}
    for benchmark_name in benchmarks_to_run:
        try:
            result = run_benchmark(benchmark_name)
            results[benchmark_name] = result
            
            if save_results:
                result.save()
                
        except Exception as e:
            logger.error(f"Error running benchmark {benchmark_name}: {str(e)}")
            logger.exception(e)
    
    if generate_report and results:
        generate_benchmark_report(results)
    
    return results


def generate_benchmark_report(results: dict[str, BenchmarkResult], 
                             output_dir: Optional[Path] = None) -> Path:
    """
    Generate a comprehensive report from benchmark results.
    
    Args:
        results: Dictionary mapping benchmark names to their results
        output_dir: Directory to save the report. If None, uses BENCHMARK_RESULTS_DIR.
    
    Returns:
        Path to the generated report
    """
    if output_dir is None:
        output_dir = BENCHMARK_RESULTS_DIR
    
    output_dir.mkdir(exist_ok=True, parents=True)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = output_dir / f"benchmark_report_{timestamp}.html"
    
    # Create a DataFrame for easier analysis
    data = []
    for name, result in results.items():
        row = {
            "Benchmark": name,
            "Mean (s)": result.mean_execution_time,
            "Median (s)": result.median_execution_time,
            "Min (s)": result.min_execution_time,
            "Max (s)": result.max_execution_time,
            "Std Dev": result.std_deviation,
            "Total Duration (s)": result.total_duration,
        }
        data.append(row)
    
    df = pd.DataFrame(data)
    
    # Generate HTML report
    with open(report_path, 'w') as f:
        f.write("<html><head><title>NeuroCognitive Architecture Benchmark Report</title>")
        f.write("<style>body{font-family:Arial,sans-serif;margin:20px;}")
        f.write("table{border-collapse:collapse;width:100%;}")
        f.write("th,td{border:1px solid #ddd;padding:8px;text-align:left;}")
        f.write("th{background-color:#f2f2f2;}")
        f.write("tr:nth-child(even){background-color:#f9f9f9;}")
        f.write("h1,h2{color:#333;}</style></head><body>")
        f.write("<h1>NeuroCognitive Architecture Benchmark Report</h1>")
        f.write(f"<p>Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")
        
        # Summary table
        f.write("<h2>Summary</h2>")
        f.write(df.to_html(index=False))
        
        # Individual benchmark details
        f.write("<h2>Detailed Results</h2>")
        for name, result in results.items():
            f.write(f"<h3>{name}</h3>")
            f.write("<table>")
            for key, value in result.to_dict().items():
                if key == "execution_times":
                    continue  # Skip the raw execution times
                f.write(f"<tr><th>{key}</th><td>{value}</td></tr>")
            f.write("</table>")
            
            # Add execution time distribution plot
            plt.figure(figsize=(10, 6))
            plt.hist(result.execution_times, bins=20, alpha=0.7)
            plt.title(f"{name} - Execution Time Distribution")
            plt.xlabel("Execution Time (s)")
            plt.ylabel("Frequency")
            plt.grid(True, alpha=0.3)
            
            plot_path = output_dir / f"{name}_distribution_{timestamp}.png"
            plt.savefig(plot_path)
            plt.close()
            
            f.write(f"<img src='{plot_path.name}' alt='Execution Time Distribution' width='800'>")
        
        f.write("</body></html>")
    
    logger.info(f"Benchmark report generated at {report_path}")
    return report_path


def compare_benchmarks(benchmark_results: list[BenchmarkResult], 
                      metric: str = "mean_execution_time",
                      output_path: Optional[Path] = None) -> Optional[Path]:
    """
    Compare multiple benchmark results and generate a comparison visualization.
    
    Args:
        benchmark_results: List of benchmark results to compare
        metric: The metric to compare (e.g., "mean_execution_time", "median_execution_time")
        output_path: Path to save the comparison visualization. If None, displays the plot.
    
    Returns:
        Path to the saved visualization if output_path is provided, None otherwise
    """
    if not benchmark_results:
        raise ValueError("No benchmark results provided for comparison")
    
    # Extract data for comparison
    names = [result.name for result in benchmark_results]
    values = []
    
    for result in benchmark_results:
        if metric == "mean_execution_time":
            values.append(result.mean_execution_time)
        elif metric == "median_execution_time":
            values.append(result.median_execution_time)
        elif metric == "min_execution_time":
            values.append(result.min_execution_time)
        elif metric == "max_execution_time":
            values.append(result.max_execution_time)
        elif metric == "std_deviation":
            values.append(result.std_deviation)
        else:
            raise ValueError(f"Unknown metric: {metric}")
    
    # Create comparison plot
    plt.figure(figsize=(12, 8))
    bars = plt.bar(names, values, alpha=0.7)
    
    # Add value labels on top of bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.001,
                f'{height:.6f}',
                ha='center', va='bottom', rotation=0)
    
    plt.title(f"Benchmark Comparison - {metric.replace('_', ' ').title()}")
    plt.xlabel("Benchmark")
    plt.ylabel(f"{metric.replace('_', ' ').title()} (seconds)")
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path)
        plt.close()
        return output_path
    else:
        plt.show()
        plt.close()
        return None


# Example benchmark implementations
@benchmark
def benchmark_memory_access(data_size: int = 1000000, access_pattern: str = "sequential"):
    """
    Benchmark memory access patterns.
    
    Args:
        data_size: Size of the data to access
        access_pattern: Pattern of access ("sequential", "random", "strided")
    
    Returns:
        Benchmark results
    """
    logger.info(f"Running memory access benchmark with data_size={data_size}, pattern={access_pattern}")
    
    # Create test data
    data = list(range(data_size))
    result = 0
    
    if access_pattern == "sequential":
        # Sequential access
        for i in range(data_size):
            result += data[i]
    elif access_pattern == "random":
        # Random access
        import random
        indices = [random.randint(0, data_size-1) for _ in range(data_size)]
        for idx in indices:
            result += data[idx]
    elif access_pattern == "strided":
        # Strided access
        stride = 16
        for i in range(0, data_size, stride):
            result += data[i]
    else:
        raise ValueError(f"Unknown access pattern: {access_pattern}")
    
    return result


@benchmark
def benchmark_memory_tier_comparison(tier_type: str = "all", operation: str = "read", data_size: int = 10000):
    """
    Benchmark and compare different memory tiers.
    
    Args:
        tier_type: Type of memory tier to benchmark ("working", "episodic", "semantic", "all")
        operation: Operation to benchmark ("read", "write", "search")
        data_size: Size of the data to use
    
    Returns:
        Benchmark results
    """
    logger.info(f"Running memory tier comparison benchmark: {tier_type}, {operation}, {data_size}")
    
    # This is a placeholder implementation
    # In a real implementation, this would interact with the actual memory tiers
    
    # Simulate different memory tier operations
    if tier_type == "working" or tier_type == "all":
        # Working memory operations (fastest)
        data = {i: f"value_{i}" for i in range(data_size)}
        if operation == "read":
            for i in range(data_size):
                _ = data.get(i)
        elif operation == "write":
            for i in range(data_size):
                data[i] = f"new_value_{i}"
        elif operation == "search":
            for i in range(data_size):
                _ = i in data
    
    if tier_type == "episodic" or tier_type == "all":
        # Episodic memory operations (medium)
        # Simulate with a more complex data structure
        data = [{"id": i, "timestamp": time.time(), "content": f"episode_{i}"} for i in range(data_size)]
        if operation == "read":
            for i in range(data_size):
                _ = data[i]
        elif operation == "write":
            for i in range(data_size):
                data[i] = {"id": i, "timestamp": time.time(), "content": f"new_episode_{i}"}
        elif operation == "search":
            for i in range(data_size):
                _ = next((item for item in data if item["id"] == i), None)
    
    if tier_type == "semantic" or tier_type == "all":
        # Semantic memory operations (slowest but most structured)
        # Simulate with a graph-like structure
        nodes = {i: {"connections": list(range(max(0, i-5), min(data_size, i+5)))} for i in range(data_size)}
        if operation == "read":
            for i in range(data_size):
                _ = nodes.get(i)
        elif operation == "write":
            for i in range(data_size):
                nodes[i] = {"connections": list(range(max(0, i-3), min(data_size, i+3)))}
        elif operation == "search":
            for i in range(data_size // 10):  # Reduce iterations for search as it's more complex
                target = i * 10
                visited = set()
                queue = [0]
                while queue:
                    node = queue.pop(0)
                    if node == target:
                        break
                    if node not in visited:
                        visited.add(node)
                        queue.extend([conn for conn in nodes[node]["connections"] if conn not in visited])
    
    return {"tier_type": tier_type, "operation": operation, "data_size": data_size}


@benchmark
def benchmark_llm_integration(model_size: str = "small", query_complexity: str = "medium", batch_size: int = 1):
    """
    Benchmark LLM integration performance.
    
    Args:
        model_size: Size of the model to simulate ("small", "medium", "large")
        query_complexity: Complexity of the queries ("simple", "medium", "complex")
        batch_size: Number of queries to process in a batch
    
    Returns:
        Benchmark results
    """
    logger.info(f"Running LLM integration benchmark: {model_size}, {query_complexity}, batch_size={batch_size}")
    
    # This is a placeholder implementation
    # In a real implementation, this would interact with actual LLM integrations
    
    # Simulate different model sizes with different processing times
    if model_size == "small":
        base_processing_time = 0.01
    elif model_size == "medium":
        base_processing_time = 0.05
    elif model_size == "large":
        base_processing_time = 0.1
    else:
        raise ValueError(f"Unknown model size: {model_size}")
    
    # Simulate different query complexities
    if query_complexity == "simple":
        complexity_factor = 1
    elif query_complexity == "medium":
        complexity_factor = 2
    elif query_complexity == "complex":
        complexity_factor = 4
    else:
        raise ValueError(f"Unknown query complexity: {query_complexity}")
    
    # Simulate processing
    processing_time = base_processing_time * complexity_factor * batch_size
    time.sleep(processing_time)  # Simulate the processing time
    
    return {
        "model_size": model_size,
        "query_complexity": query_complexity,
        "batch_size": batch_size,
        "simulated_processing_time": processing_time
    }


@benchmark
def benchmark_cognitive_processing(complexity: str = "medium", parallel: bool = False, iterations: int = 100):
    """
    Benchmark cognitive processing capabilities.
    
    Args:
        complexity: Complexity of the cognitive processing ("simple", "medium", "complex")
        parallel: Whether to simulate parallel processing
        iterations: Number of processing iterations
    
    Returns:
        Benchmark results
    """
    logger.info(f"Running cognitive processing benchmark: {complexity}, parallel={parallel}, iterations={iterations}")
    
    # This is a placeholder implementation
    # In a real implementation, this would interact with actual cognitive processing components
    
    # Simulate different complexities
    if complexity == "simple":
        operations_per_iteration = 10
    elif complexity == "medium":
        operations_per_iteration = 100
    elif complexity == "complex":
        operations_per_iteration = 1000
    else:
        raise ValueError(f"Unknown complexity: {complexity}")
    
    result = 0
    
    if parallel and complexity != "simple":
        # Simulate parallel processing
        from concurrent.futures import ThreadPoolExecutor
        
        def process_chunk(chunk_size):
            chunk_result = 0
            for _ in range(chunk_size):
                # Simulate some computation
                chunk_result += sum(i * i for i in range(100))
            return chunk_result
        
        # Divide work into chunks
        chunk_size = operations_per_iteration // 4
        chunks = [chunk_size] * 4
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            chunk_results = list(executor.map(process_chunk, chunks))
            result = sum(chunk_results)
    else:
        # Sequential processing
        for _ in range(iterations):
            for _ in range(operations_per_iteration):
                # Simulate some computation
                result += sum(i * i for i in range(100))
    
    return {
        "complexity": complexity,
        "parallel": parallel,
        "iterations": iterations,
        "result": result
    }


@benchmark
def benchmark_system_throughput(load_level: str = "medium", duration: int = 5, concurrent_operations: int = 10):
    """
    Benchmark overall system throughput under different loads.
    
    Args:
        load_level: Level of system load to simulate ("light", "medium", "heavy")
        duration: Duration of the benchmark in seconds
        concurrent_operations: Number of concurrent operations to simulate
    
    Returns:
        Benchmark results
    """
    logger.info(f"Running system throughput benchmark: {load_level}, {duration}s, {concurrent_operations} concurrent ops")
    
    # This is a placeholder implementation
    # In a real implementation, this would interact with actual system components
    
    # Simulate different load levels
    if load_level == "light":
        operations_per_second = 10
    elif load_level == "medium":
        operations_per_second = 50
    elif load_level == "heavy":
        operations_per_second = 200
    else:
        raise ValueError(f"Unknown load level: {load_level}")
    
    total_operations = operations_per_second * duration
    operations_completed = 0
    start_time = time.time()
    
    if concurrent_operations > 1:
        # Simulate concurrent operations
        from concurrent.futures import ThreadPoolExecutor
        
        def perform_operation(op_id):
            # Simulate a single operation
            time.sleep(0.01)  # Small delay to simulate work
            return op_id
        
        with ThreadPoolExecutor(max_workers=concurrent_operations) as executor:
            # Submit all operations
            futures = [executor.submit(perform_operation, i) for i in range(total_operations)]
            
            # Wait for all operations to complete or timeout
            end_time = start_time + duration
            for future in futures:
                if time.time() < end_time:
                    try:
                        future.result(timeout=max(0.1, end_time - time.time()))
                        operations_completed += 1
                    except Exception as e:
                        logger.warning(f"Operation failed: {str(e)}")
                else:
                    break
    else:
        # Sequential operations
        while time.time() - start_time < duration and operations_completed < total_operations:
            # Simulate a single operation
            time.sleep(0.01)  # Small delay to simulate work
            operations_completed += 1
    
    actual_duration = time.time() - start_time
    throughput = operations_completed / actual_duration if actual_duration > 0 else 0
    
    return {
        "load_level": load_level,
        "target_duration": duration,
        "actual_duration": actual_duration,
        "concurrent_operations": concurrent_operations,
        "operations_completed": operations_completed,
        "throughput_ops_per_second": throughput
    }


if __name__ == "__main__":
    # Configure logging when run directly
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run all benchmarks
    results = run_benchmark_suite()
    
    # Print summary
    print("\nBenchmark Summary:")
    for name, result in results.items():
        print(f"{name}: Mean={result.mean_execution_time:.6f}s, Median={result.median_execution_time:.6f}s")