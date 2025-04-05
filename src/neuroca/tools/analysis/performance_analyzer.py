"""
Performance Analyzer for NeuroCognitive Architecture (NCA)

This module provides comprehensive performance analysis tools for the NCA system.
It enables monitoring, profiling, and analyzing various performance metrics across
the system components, with a focus on memory operations, cognitive processes,
and LLM integration points.

Features:
- Component-level performance profiling
- Memory operation latency tracking
- Throughput analysis for cognitive processes
- Resource utilization monitoring
- Performance bottleneck identification
- Historical performance data analysis
- Visualization of performance metrics

Usage:
    # Basic usage with default configuration
    analyzer = PerformanceAnalyzer()
    
    # Start profiling a specific operation
    with analyzer.profile("memory_retrieval"):
        result = memory_system.retrieve(query)
    
    # Get performance report
    report = analyzer.generate_report()
    
    # Analyze specific metrics
    memory_latency = analyzer.get_metric("memory_retrieval.latency")
    
    # Export performance data
    analyzer.export_data("performance_data.json")
"""

import datetime
import json
import logging
import os
import statistics
import threading
import time
import uuid
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

import matplotlib.pyplot as plt
import psutil

# Configure logger
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """
    Represents a single performance metric measurement.
    
    Attributes:
        name: Name of the metric
        value: Measured value
        unit: Unit of measurement (ms, MB, %, etc.)
        timestamp: When the measurement was taken
        component: System component being measured
        tags: Additional metadata tags for filtering and grouping
    """
    name: str
    value: float
    unit: str
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)
    component: str = ""
    tags: dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert metric to dictionary format for serialization."""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


@dataclass
class ProfileResult:
    """
    Contains the results of a profiling operation.
    
    Attributes:
        operation: Name of the profiled operation
        start_time: When the operation started
        end_time: When the operation completed
        duration_ms: Duration in milliseconds
        component: System component being profiled
        metadata: Additional contextual information
        memory_usage: Memory usage during operation (if tracked)
        cpu_usage: CPU usage during operation (if tracked)
    """
    operation: str
    start_time: datetime.datetime
    end_time: datetime.datetime
    duration_ms: float
    component: str
    metadata: dict[str, Any] = field(default_factory=dict)
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert profile result to dictionary format for serialization."""
        result = asdict(self)
        result['start_time'] = self.start_time.isoformat()
        result['end_time'] = self.end_time.isoformat()
        return result


class PerformanceAnalyzer:
    """
    Main performance analysis tool for the NCA system.
    
    This class provides methods for profiling operations, collecting metrics,
    analyzing performance data, and generating reports.
    """
    
    def __init__(self, config: Optional[dict[str, Any]] = None):
        """
        Initialize the performance analyzer with optional configuration.
        
        Args:
            config: Configuration dictionary with the following options:
                - storage_path: Where to store performance data
                - auto_save: Whether to automatically save metrics
                - save_interval: How often to save metrics (in seconds)
                - track_memory: Whether to track memory usage
                - track_cpu: Whether to track CPU usage
                - components: List of components to track
                - log_level: Logging level for the analyzer
        """
        self.config = {
            'storage_path': 'data/performance',
            'auto_save': True,
            'save_interval': 300,  # 5 minutes
            'track_memory': True,
            'track_cpu': True,
            'components': [],  # Empty means track all
            'log_level': logging.INFO,
        }
        
        if config:
            self.config.update(config)
        
        # Configure logging
        logger.setLevel(self.config['log_level'])
        
        # Initialize storage
        self.metrics: list[PerformanceMetric] = []
        self.profile_results: list[ProfileResult] = []
        self._ensure_storage_path()
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Session identifier
        self.session_id = str(uuid.uuid4())
        self.start_time = datetime.datetime.now()
        
        # Auto-save setup
        self._stop_auto_save = threading.Event()
        if self.config['auto_save']:
            self._start_auto_save()
            
        logger.info(f"Performance analyzer initialized with session ID: {self.session_id}")
    
    def _ensure_storage_path(self) -> None:
        """Ensure the storage directory exists."""
        path = Path(self.config['storage_path'])
        path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Storage path ensured: {path}")
    
    def _start_auto_save(self) -> None:
        """Start the auto-save background thread."""
        def auto_save_worker():
            while not self._stop_auto_save.wait(self.config['save_interval']):
                try:
                    self.save_data()
                except Exception as e:
                    logger.error(f"Error in auto-save: {str(e)}")
        
        self._auto_save_thread = threading.Thread(
            target=auto_save_worker, 
            daemon=True,
            name="PerformanceAnalyzerAutoSave"
        )
        self._auto_save_thread.start()
        logger.debug("Auto-save thread started")
    
    @contextmanager
    def profile(self, operation: str, component: str = "", metadata: Optional[dict[str, Any]] = None) -> Generator[None, None, None]:
        """
        Context manager for profiling an operation.
        
        Args:
            operation: Name of the operation being profiled
            component: System component being profiled
            metadata: Additional contextual information
            
        Yields:
            None
            
        Example:
            with analyzer.profile("memory_retrieval", "working_memory"):
                result = memory.retrieve(query)
        """
        if not metadata:
            metadata = {}
            
        # Capture initial resource usage if configured
        initial_memory = psutil.Process().memory_info().rss / (1024 * 1024) if self.config['track_memory'] else None
        psutil.Process().cpu_percent() if self.config['track_cpu'] else None
        
        start_time = datetime.datetime.now()
        start_timestamp = time.time()
        
        try:
            yield
        finally:
            end_time = datetime.datetime.now()
            duration_ms = (time.time() - start_timestamp) * 1000
            
            # Capture final resource usage if configured
            final_memory = psutil.Process().memory_info().rss / (1024 * 1024) if self.config['track_memory'] else None
            final_cpu = psutil.Process().cpu_percent() if self.config['track_cpu'] else None
            
            memory_usage = final_memory - initial_memory if initial_memory is not None and final_memory is not None else None
            cpu_usage = final_cpu if final_cpu is not None else None
            
            result = ProfileResult(
                operation=operation,
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_ms,
                component=component,
                metadata=metadata,
                memory_usage=memory_usage,
                cpu_usage=cpu_usage
            )
            
            with self._lock:
                self.profile_results.append(result)
                
                # Also add as metrics for consistency
                self.add_metric(f"{operation}.duration", duration_ms, "ms", component)
                if memory_usage is not None:
                    self.add_metric(f"{operation}.memory_delta", memory_usage, "MB", component)
                if cpu_usage is not None:
                    self.add_metric(f"{operation}.cpu_usage", cpu_usage, "%", component)
            
            logger.debug(f"Profiled {operation}: {duration_ms:.2f}ms")
    
    def add_metric(self, name: str, value: float, unit: str, component: str = "", tags: Optional[dict[str, str]] = None) -> None:
        """
        Add a performance metric measurement.
        
        Args:
            name: Name of the metric
            value: Measured value
            unit: Unit of measurement
            component: System component being measured
            tags: Additional metadata tags
            
        Example:
            analyzer.add_metric("memory_usage", 256.5, "MB", "working_memory")
        """
        if not tags:
            tags = {}
            
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.datetime.now(),
            component=component,
            tags=tags
        )
        
        with self._lock:
            self.metrics.append(metric)
        
        logger.debug(f"Added metric {name}: {value} {unit}")
    
    def get_metrics(self, 
                   name: Optional[str] = None, 
                   component: Optional[str] = None, 
                   start_time: Optional[datetime.datetime] = None,
                   end_time: Optional[datetime.datetime] = None,
                   tags: Optional[dict[str, str]] = None) -> list[PerformanceMetric]:
        """
        Get metrics matching the specified filters.
        
        Args:
            name: Filter by metric name
            component: Filter by component
            start_time: Filter by start time
            end_time: Filter by end time
            tags: Filter by tags
            
        Returns:
            List of matching metrics
        """
        with self._lock:
            filtered_metrics = self.metrics.copy()
        
        if name:
            filtered_metrics = [m for m in filtered_metrics if m.name == name]
        
        if component:
            filtered_metrics = [m for m in filtered_metrics if m.component == component]
        
        if start_time:
            filtered_metrics = [m for m in filtered_metrics if m.timestamp >= start_time]
        
        if end_time:
            filtered_metrics = [m for m in filtered_metrics if m.timestamp <= end_time]
        
        if tags:
            filtered_metrics = [
                m for m in filtered_metrics 
                if all(m.tags.get(k) == v for k, v in tags.items())
            ]
        
        return filtered_metrics
    
    def get_metric_values(self, name: str, **kwargs) -> list[float]:
        """
        Get values for a specific metric.
        
        Args:
            name: Metric name
            **kwargs: Additional filters to pass to get_metrics
            
        Returns:
            List of metric values
        """
        metrics = self.get_metrics(name=name, **kwargs)
        return [m.value for m in metrics]
    
    def get_metric_statistics(self, name: str, **kwargs) -> dict[str, float]:
        """
        Calculate statistics for a specific metric.
        
        Args:
            name: Metric name
            **kwargs: Additional filters to pass to get_metrics
            
        Returns:
            Dictionary with statistics (min, max, mean, median, std_dev)
        """
        values = self.get_metric_values(name, **kwargs)
        
        if not values:
            return {
                'count': 0,
                'min': None,
                'max': None,
                'mean': None,
                'median': None,
                'std_dev': None
            }
        
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'std_dev': statistics.stdev(values) if len(values) > 1 else 0
        }
    
    def get_profile_results(self, 
                           operation: Optional[str] = None,
                           component: Optional[str] = None,
                           start_time: Optional[datetime.datetime] = None,
                           end_time: Optional[datetime.datetime] = None) -> list[ProfileResult]:
        """
        Get profile results matching the specified filters.
        
        Args:
            operation: Filter by operation name
            component: Filter by component
            start_time: Filter by start time
            end_time: Filter by end time
            
        Returns:
            List of matching profile results
        """
        with self._lock:
            filtered_results = self.profile_results.copy()
        
        if operation:
            filtered_results = [r for r in filtered_results if r.operation == operation]
        
        if component:
            filtered_results = [r for r in filtered_results if r.component == component]
        
        if start_time:
            filtered_results = [r for r in filtered_results if r.start_time >= start_time]
        
        if end_time:
            filtered_results = [r for r in filtered_results if r.end_time <= end_time]
        
        return filtered_results
    
    def generate_report(self, 
                       components: Optional[list[str]] = None,
                       operations: Optional[list[str]] = None,
                       start_time: Optional[datetime.datetime] = None,
                       end_time: Optional[datetime.datetime] = None) -> dict[str, Any]:
        """
        Generate a comprehensive performance report.
        
        Args:
            components: List of components to include (None for all)
            operations: List of operations to include (None for all)
            start_time: Start time for the report period
            end_time: End time for the report period
            
        Returns:
            Dictionary with performance report data
        """
        if not start_time:
            start_time = self.start_time
        
        if not end_time:
            end_time = datetime.datetime.now()
        
        # Get relevant profile results
        results = self.get_profile_results(
            component=components[0] if components and len(components) == 1 else None,
            operation=operations[0] if operations and len(operations) == 1 else None,
            start_time=start_time,
            end_time=end_time
        )
        
        # Filter by components and operations if multiple specified
        if components and len(components) > 1:
            results = [r for r in results if r.component in components]
        
        if operations and len(operations) > 1:
            results = [r for r in results if r.operation in operations]
        
        # Group by operation and component
        operation_stats = {}
        component_stats = {}
        
        for result in results:
            # Group by operation
            if result.operation not in operation_stats:
                operation_stats[result.operation] = []
            operation_stats[result.operation].append(result.duration_ms)
            
            # Group by component
            if result.component:
                if result.component not in component_stats:
                    component_stats[result.component] = []
                component_stats[result.component].append(result.duration_ms)
        
        # Calculate statistics
        operation_metrics = {}
        for operation, durations in operation_stats.items():
            operation_metrics[operation] = {
                'count': len(durations),
                'min_ms': min(durations),
                'max_ms': max(durations),
                'avg_ms': statistics.mean(durations),
                'median_ms': statistics.median(durations),
                'std_dev_ms': statistics.stdev(durations) if len(durations) > 1 else 0,
                'total_ms': sum(durations)
            }
        
        component_metrics = {}
        for component, durations in component_stats.items():
            component_metrics[component] = {
                'count': len(durations),
                'min_ms': min(durations),
                'max_ms': max(durations),
                'avg_ms': statistics.mean(durations),
                'median_ms': statistics.median(durations),
                'std_dev_ms': statistics.stdev(durations) if len(durations) > 1 else 0,
                'total_ms': sum(durations)
            }
        
        # Get memory and CPU metrics if available
        memory_metrics = self.get_metrics(name="memory_usage", start_time=start_time, end_time=end_time)
        cpu_metrics = self.get_metrics(name="cpu_usage", start_time=start_time, end_time=end_time)
        
        memory_values = [m.value for m in memory_metrics]
        cpu_values = [m.value for m in cpu_metrics]
        
        # Build the report
        report = {
            'session_id': self.session_id,
            'report_period': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'duration_seconds': (end_time - start_time).total_seconds()
            },
            'operations': operation_metrics,
            'components': component_metrics,
            'summary': {
                'total_operations': len(results),
                'unique_operations': len(operation_metrics),
                'unique_components': len(component_metrics),
                'slowest_operation': max(operation_metrics.items(), key=lambda x: x[1]['avg_ms'])[0] if operation_metrics else None,
                'fastest_operation': min(operation_metrics.items(), key=lambda x: x[1]['avg_ms'])[0] if operation_metrics else None,
            }
        }
        
        # Add memory and CPU stats if available
        if memory_values:
            report['memory'] = {
                'min_mb': min(memory_values),
                'max_mb': max(memory_values),
                'avg_mb': statistics.mean(memory_values),
                'latest_mb': memory_values[-1]
            }
        
        if cpu_values:
            report['cpu'] = {
                'min_percent': min(cpu_values),
                'max_percent': max(cpu_values),
                'avg_percent': statistics.mean(cpu_values),
                'latest_percent': cpu_values[-1]
            }
        
        return report
    
    def save_data(self, filename: Optional[str] = None) -> str:
        """
        Save collected performance data to disk.
        
        Args:
            filename: Custom filename (default: auto-generated based on timestamp)
            
        Returns:
            Path to the saved file
        """
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_{self.session_id}_{timestamp}.json"
        
        filepath = os.path.join(self.config['storage_path'], filename)
        
        with self._lock:
            data = {
                'session_id': self.session_id,
                'start_time': self.start_time.isoformat(),
                'save_time': datetime.datetime.now().isoformat(),
                'metrics': [m.to_dict() for m in self.metrics],
                'profile_results': [r.to_dict() for r in self.profile_results]
            }
        
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Performance data saved to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to save performance data: {str(e)}")
            raise
    
    def load_data(self, filepath: str) -> dict[str, Any]:
        """
        Load performance data from a file.
        
        Args:
            filepath: Path to the performance data file
            
        Returns:
            Dictionary with loaded performance data
        """
        try:
            with open(filepath) as f:
                data = json.load(f)
            logger.info(f"Performance data loaded from {filepath}")
            return data
        except Exception as e:
            logger.error(f"Failed to load performance data: {str(e)}")
            raise
    
    def visualize_metrics(self, 
                         metric_names: list[str], 
                         components: Optional[list[str]] = None,
                         start_time: Optional[datetime.datetime] = None,
                         end_time: Optional[datetime.datetime] = None,
                         output_file: Optional[str] = None) -> None:
        """
        Visualize performance metrics.
        
        Args:
            metric_names: List of metric names to visualize
            components: List of components to include (None for all)
            start_time: Start time for visualization
            end_time: End time for visualization
            output_file: Path to save the visualization (None for display)
            
        Example:
            analyzer.visualize_metrics(
                ["memory_retrieval.duration", "memory_storage.duration"],
                components=["working_memory", "long_term_memory"],
                output_file="memory_performance.png"
            )
        """
        if not start_time:
            start_time = self.start_time
        
        if not end_time:
            end_time = datetime.datetime.now()
        
        plt.figure(figsize=(12, 8))
        
        for metric_name in metric_names:
            # Get metrics for this name
            metrics = self.get_metrics(
                name=metric_name,
                start_time=start_time,
                end_time=end_time
            )
            
            # Filter by components if specified
            if components:
                metrics = [m for m in metrics if m.component in components]
            
            if not metrics:
                logger.warning(f"No data found for metric: {metric_name}")
                continue
            
            # Extract timestamps and values
            timestamps = [m.timestamp for m in metrics]
            values = [m.value for m in metrics]
            
            # Plot the data
            plt.plot(timestamps, values, label=f"{metric_name} ({metrics[0].unit})")
        
        plt.title("Performance Metrics")
        plt.xlabel("Time")
        plt.ylabel("Value")
        plt.legend()
        plt.grid(True)
        
        if output_file:
            plt.savefig(output_file)
            logger.info(f"Visualization saved to {output_file}")
        else:
            plt.show()
    
    def visualize_operation_comparison(self, 
                                      operations: list[str],
                                      components: Optional[list[str]] = None,
                                      metric: str = "duration_ms",
                                      output_file: Optional[str] = None) -> None:
        """
        Create a comparison visualization of different operations.
        
        Args:
            operations: List of operations to compare
            components: List of components to include (None for all)
            metric: Metric to compare (duration_ms, memory_usage, cpu_usage)
            output_file: Path to save the visualization (None for display)
        """
        results = []
        
        for operation in operations:
            profile_results = self.get_profile_results(operation=operation)
            
            if components:
                profile_results = [r for r in profile_results if r.component in components]
            
            if not profile_results:
                logger.warning(f"No data found for operation: {operation}")
                continue
            
            if metric == "duration_ms":
                values = [r.duration_ms for r in profile_results]
                unit = "ms"
            elif metric == "memory_usage":
                values = [r.memory_usage for r in profile_results if r.memory_usage is not None]
                unit = "MB"
            elif metric == "cpu_usage":
                values = [r.cpu_usage for r in profile_results if r.cpu_usage is not None]
                unit = "%"
            else:
                raise ValueError(f"Unknown metric: {metric}")
            
            if not values:
                logger.warning(f"No {metric} data for operation: {operation}")
                continue
            
            results.append((operation, values))
        
        if not results:
            logger.error("No data available for visualization")
            return
        
        plt.figure(figsize=(12, 8))
        
        # Create box plots
        plt.boxplot([values for _, values in results], labels=[op for op, _ in results])
        
        plt.title(f"Operation Comparison - {metric}")
        plt.xlabel("Operation")
        plt.ylabel(f"{metric} ({unit})")
        plt.grid(True)
        
        if output_file:
            plt.savefig(output_file)
            logger.info(f"Visualization saved to {output_file}")
        else:
            plt.show()
    
    def track_system_resources(self, interval: float = 1.0, duration: float = 60.0) -> None:
        """
        Track system resources (CPU, memory) for a specified duration.
        
        Args:
            interval: Sampling interval in seconds
            duration: Total tracking duration in seconds
        """
        end_time = time.time() + duration
        
        logger.info(f"Starting system resource tracking for {duration} seconds")
        
        while time.time() < end_time:
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.add_metric("cpu_usage", cpu_percent, "%", "system")
            
            # Get memory usage
            memory = psutil.virtual_memory()
            self.add_metric("memory_usage", memory.used / (1024 * 1024), "MB", "system")
            self.add_metric("memory_percent", memory.percent, "%", "system")
            
            # Get process-specific info
            process = psutil.Process()
            self.add_metric("process_cpu", process.cpu_percent(interval=0.1), "%", "process")
            self.add_metric("process_memory", process.memory_info().rss / (1024 * 1024), "MB", "process")
            
            # Sleep until next sample
            time.sleep(interval)
        
        logger.info("System resource tracking completed")
    
    def identify_bottlenecks(self, threshold_ms: float = 100.0) -> list[dict[str, Any]]:
        """
        Identify performance bottlenecks based on operation duration.
        
        Args:
            threshold_ms: Duration threshold to consider as a bottleneck (ms)
            
        Returns:
            List of bottleneck operations with statistics
        """
        bottlenecks = []
        
        # Group profile results by operation
        operation_results = {}
        for result in self.profile_results:
            if result.operation not in operation_results:
                operation_results[result.operation] = []
            operation_results[result.operation].append(result)
        
        # Analyze each operation
        for operation, results in operation_results.items():
            durations = [r.duration_ms for r in results]
            avg_duration = statistics.mean(durations)
            
            if avg_duration >= threshold_ms:
                bottlenecks.append({
                    'operation': operation,
                    'avg_duration_ms': avg_duration,
                    'max_duration_ms': max(durations),
                    'min_duration_ms': min(durations),
                    'std_dev_ms': statistics.stdev(durations) if len(durations) > 1 else 0,
                    'count': len(durations),
                    'components': list({r.component for r in results if r.component})
                })
        
        # Sort by average duration (descending)
        bottlenecks.sort(key=lambda x: x['avg_duration_ms'], reverse=True)
        
        return bottlenecks
    
    def clear_data(self) -> None:
        """Clear all collected performance data."""
        with self._lock:
            self.metrics = []
            self.profile_results = []
        logger.info("Performance data cleared")
    
    def __enter__(self) -> 'PerformanceAnalyzer':
        """Support for context manager usage."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Clean up resources when exiting context."""
        self.shutdown()
    
    def shutdown(self) -> None:
        """Shut down the analyzer and clean up resources."""
        if self.config['auto_save']:
            self._stop_auto_save.set()
            if hasattr(self, '_auto_save_thread'):
                self._auto_save_thread.join(timeout=5.0)
        
        # Save final data
        try:
            self.save_data()
        except Exception as e:
            logger.error(f"Error saving final performance data: {str(e)}")
        
        logger.info(f"Performance analyzer shutdown complete. Session: {self.session_id}")


# Utility functions for common performance analysis tasks

def analyze_performance_data(filepath: str) -> dict[str, Any]:
    """
    Analyze performance data from a saved file.
    
    Args:
        filepath: Path to the performance data file
        
    Returns:
        Dictionary with analysis results
    """
    analyzer = PerformanceAnalyzer()
    data = analyzer.load_data(filepath)
    
    # Convert metrics to PerformanceMetric objects
    metrics = []
    for metric_dict in data.get('metrics', []):
        metric = PerformanceMetric(
            name=metric_dict['name'],
            value=metric_dict['value'],
            unit=metric_dict['unit'],
            timestamp=datetime.datetime.fromisoformat(metric_dict['timestamp']),
            component=metric_dict['component'],
            tags=metric_dict['tags']
        )
        metrics.append(metric)
    
    # Convert profile results to ProfileResult objects
    profile_results = []
    for result_dict in data.get('profile_results', []):
        result = ProfileResult(
            operation=result_dict['operation'],
            start_time=datetime.datetime.fromisoformat(result_dict['start_time']),
            end_time=datetime.datetime.fromisoformat(result_dict['end_time']),
            duration_ms=result_dict['duration_ms'],
            component=result_dict['component'],
            metadata=result_dict['metadata'],
            memory_usage=result_dict.get('memory_usage'),
            cpu_usage=result_dict.get('cpu_usage')
        )
        profile_results.append(result)
    
    # Set the data in the analyzer
    with analyzer._lock:
        analyzer.metrics = metrics
        analyzer.profile_results = profile_results
    
    # Generate a report
    report = analyzer.generate_report()
    
    # Identify bottlenecks
    bottlenecks = analyzer.identify_bottlenecks()
    
    return {
        'report': report,
        'bottlenecks': bottlenecks,
        'session_info': {
            'id': data.get('session_id'),
            'start_time': data.get('start_time'),
            'save_time': data.get('save_time'),
            'metrics_count': len(metrics),
            'profile_results_count': len(profile_results)
        }
    }


def compare_performance_sessions(filepaths: list[str]) -> dict[str, Any]:
    """
    Compare performance data from multiple sessions.
    
    Args:
        filepaths: List of paths to performance data files
        
    Returns:
        Dictionary with comparison results
    """
    if len(filepaths) < 2:
        raise ValueError("At least two sessions are required for comparison")
    
    session_data = []
    for filepath in filepaths:
        analyzer = PerformanceAnalyzer()
        data = analyzer.load_data(filepath)
        
        # Generate a report for this session
        with analyzer._lock:
            # Convert metrics to PerformanceMetric objects
            metrics = []
            for metric_dict in data.get('metrics', []):
                metric = PerformanceMetric(
                    name=metric_dict['name'],
                    value=metric_dict['value'],
                    unit=metric_dict['unit'],
                    timestamp=datetime.datetime.fromisoformat(metric_dict['timestamp']),
                    component=metric_dict['component'],
                    tags=metric_dict['tags']
                )
                metrics.append(metric)
            
            # Convert profile results to ProfileResult objects
            profile_results = []
            for result_dict in data.get('profile_results', []):
                result = ProfileResult(
                    operation=result_dict['operation'],
                    start_time=datetime.datetime.fromisoformat(result_dict['start_time']),
                    end_time=datetime.datetime.fromisoformat(result_dict['end_time']),
                    duration_ms=result_dict['duration_ms'],
                    component=result_dict['component'],
                    metadata=result_dict['metadata'],
                    memory_usage=result_dict.get('memory_usage'),
                    cpu_usage=result_dict.get('cpu_usage')
                )
                profile_results.append(result)
            
            analyzer.metrics = metrics
            analyzer.profile_results = profile_results
        
        report = analyzer.generate_report()
        
        session_data.append({
            'session_id': data.get('session_id'),
            'start_time': data.get('start_time'),
            'save_time': data.get('save_time'),
            'report': report,
            'filepath': filepath
        })
    
    # Compare operations across sessions
    operations = set()
    for session in session_data:
        operations.update(session['report']['operations'].keys())
    
    operation_comparison = {}
    for operation in operations:
        operation_comparison[operation] = []
        for session in session_data:
            if operation in session['report']['operations']:
                stats = session['report']['operations'][operation]
                stats['session_id'] = session['session_id']
                operation_comparison[operation].append(stats)
    
    # Calculate improvement/regression percentages
    for operation, sessions in operation_comparison.items():
        if len(sessions) >= 2:
            # Sort by start_time
            sessions.sort(key=lambda x: session_data[next(i for i, s in enumerate(session_data) if s['session_id'] == x['session_id'])]['start_time'])
            
            for i in range(1, len(sessions)):
                prev_avg = sessions[i-1]['avg_ms']
                curr_avg = sessions[i]['avg_ms']
                
                if prev_avg > 0:
                    change_pct = ((curr_avg - prev_avg) / prev_avg) * 100
                    sessions[i]['change_from_previous_pct'] = change_pct
    
    return {
        'sessions': session_data,
        'operation_comparison': operation_comparison,
        'summary': {
            'session_count': len(session_data),
            'unique_operations': len(operations),
        }
    }