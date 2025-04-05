"""
Metrics Collectors for NeuroCognitive Architecture (NCA)

This module provides a collection of metric collectors that gather various
performance, resource usage, and operational metrics from the NCA system.
These collectors are designed to be used with the monitoring subsystem to
provide comprehensive observability of the NCA's operation.

The module implements a plugin-based architecture where different collectors
can be registered and used based on configuration. Each collector follows
a common interface but specializes in collecting specific types of metrics.

Available collectors include:
- SystemMetricsCollector: Collects system-level metrics (CPU, memory, disk)
- MemoryTierMetricsCollector: Collects metrics specific to NCA memory tiers
- LLMIntegrationMetricsCollector: Collects metrics related to LLM interactions
- PerformanceMetricsCollector: Collects performance-related metrics
- CustomMetricsCollector: Allows for collection of user-defined metrics

Usage:
    # Create a collector
    system_collector = SystemMetricsCollector()
    
    # Collect metrics
    metrics = system_collector.collect()
    
    # Register with a registry
    registry = MetricsRegistry()
    registry.register("system", system_collector)
"""

import abc
import logging
import os
import platform
import time
from typing import Any, Optional, Union

import psutil

from neuroca.config import settings
from neuroca.core.exceptions import MetricsCollectionError
from neuroca.monitoring.metrics.models import (
    Metric,
    MetricLabel,
    MetricType,
    MetricUnit,
    MetricValue,
)

# Configure logger
logger = logging.getLogger(__name__)


class BaseMetricsCollector(abc.ABC):
    """
    Abstract base class for all metrics collectors.
    
    This class defines the interface that all metrics collectors must implement.
    It provides common functionality for collecting, validating, and formatting
    metrics data.
    
    Attributes:
        name (str): Name of the collector
        enabled (bool): Whether the collector is enabled
        collection_interval (float): Time in seconds between collections
        last_collection_time (float): Timestamp of the last collection
        metrics_prefix (str): Prefix to add to all metric names
    """
    
    def __init__(
        self,
        name: str,
        enabled: bool = True,
        collection_interval: float = 60.0,
        metrics_prefix: str = "neuroca",
    ):
        """
        Initialize a new metrics collector.
        
        Args:
            name: Unique name for this collector
            enabled: Whether this collector is enabled by default
            collection_interval: Time in seconds between metric collections
            metrics_prefix: Prefix to add to all metric names
        """
        self.name = name
        self.enabled = enabled
        self.collection_interval = collection_interval
        self.last_collection_time = 0.0
        self.metrics_prefix = metrics_prefix
        
        logger.debug(f"Initialized {self.__class__.__name__} with name '{name}'")
    
    @abc.abstractmethod
    def collect(self) -> list[Metric]:
        """
        Collect metrics and return them as a list.
        
        This method must be implemented by all concrete collector classes.
        
        Returns:
            List of collected metrics
            
        Raises:
            MetricsCollectionError: If metrics collection fails
        """
        pass
    
    def should_collect(self) -> bool:
        """
        Determine if metrics should be collected based on the collection interval.
        
        Returns:
            True if enough time has passed since the last collection, False otherwise
        """
        if not self.enabled:
            return False
            
        current_time = time.time()
        if current_time - self.last_collection_time >= self.collection_interval:
            return True
        return False
    
    def format_metric_name(self, name: str) -> str:
        """
        Format a metric name with the appropriate prefix.
        
        Args:
            name: Base name of the metric
            
        Returns:
            Formatted metric name with prefix
        """
        return f"{self.metrics_prefix}.{self.name}.{name}"
    
    def create_metric(
        self,
        name: str,
        value: Union[int, float, str, bool],
        metric_type: MetricType,
        unit: Optional[MetricUnit] = None,
        labels: Optional[dict[str, str]] = None,
        description: Optional[str] = None,
        timestamp: Optional[float] = None,
    ) -> Metric:
        """
        Create a new metric with the given parameters.
        
        Args:
            name: Name of the metric (will be prefixed)
            value: Value of the metric
            metric_type: Type of the metric (counter, gauge, etc.)
            unit: Unit of measurement
            labels: Additional labels to attach to the metric
            description: Human-readable description of the metric
            timestamp: Custom timestamp (defaults to current time)
            
        Returns:
            A new Metric object
        """
        metric_name = self.format_metric_name(name)
        metric_value = MetricValue(value=value)
        metric_labels = []
        
        if labels:
            metric_labels = [MetricLabel(name=k, value=v) for k, v in labels.items()]
        
        return Metric(
            name=metric_name,
            value=metric_value,
            type=metric_type,
            unit=unit,
            labels=metric_labels,
            description=description or f"{name} metric",
            timestamp=timestamp or time.time(),
        )


class SystemMetricsCollector(BaseMetricsCollector):
    """
    Collector for system-level metrics such as CPU, memory, and disk usage.
    
    This collector gathers metrics about the host system where the NCA is running,
    providing insights into resource utilization and system health.
    
    Attributes:
        include_process_metrics (bool): Whether to include process-specific metrics
        process_id (int): Process ID to monitor (defaults to current process)
    """
    
    def __init__(
        self,
        name: str = "system",
        enabled: bool = True,
        collection_interval: float = 60.0,
        metrics_prefix: str = "neuroca",
        include_process_metrics: bool = True,
        process_id: Optional[int] = None,
    ):
        """
        Initialize a system metrics collector.
        
        Args:
            name: Name for this collector
            enabled: Whether this collector is enabled
            collection_interval: Time between collections in seconds
            metrics_prefix: Prefix for all metrics
            include_process_metrics: Whether to collect process-specific metrics
            process_id: Specific process ID to monitor (defaults to current process)
        """
        super().__init__(name, enabled, collection_interval, metrics_prefix)
        self.include_process_metrics = include_process_metrics
        self.process_id = process_id or os.getpid()
        self._process = psutil.Process(self.process_id)
        
        # System information labels that will be added to all metrics
        self.system_labels = {
            "hostname": platform.node(),
            "os": platform.system(),
            "os_version": platform.version(),
            "python_version": platform.python_version(),
        }
        
        logger.debug(f"SystemMetricsCollector initialized for process {self.process_id}")
    
    def collect(self) -> list[Metric]:
        """
        Collect system metrics including CPU, memory, disk, and network usage.
        
        Returns:
            List of system metrics
            
        Raises:
            MetricsCollectionError: If metrics collection fails
        """
        if not self.should_collect():
            return []
        
        try:
            metrics = []
            
            # Collect CPU metrics
            metrics.extend(self._collect_cpu_metrics())
            
            # Collect memory metrics
            metrics.extend(self._collect_memory_metrics())
            
            # Collect disk metrics
            metrics.extend(self._collect_disk_metrics())
            
            # Collect process metrics if enabled
            if self.include_process_metrics:
                metrics.extend(self._collect_process_metrics())
            
            self.last_collection_time = time.time()
            logger.debug(f"Collected {len(metrics)} system metrics")
            return metrics
            
        except Exception as e:
            error_msg = f"Failed to collect system metrics: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise MetricsCollectionError(error_msg) from e
    
    def _collect_cpu_metrics(self) -> list[Metric]:
        """
        Collect CPU-related metrics.
        
        Returns:
            List of CPU metrics
        """
        metrics = []
        
        # CPU usage percentage (per core and total)
        cpu_percent = psutil.cpu_percent(interval=0.1)
        metrics.append(
            self.create_metric(
                name="cpu.usage.percent",
                value=cpu_percent,
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.PERCENT,
                labels=self.system_labels,
                description="CPU usage percentage (all cores)",
            )
        )
        
        # Per-core CPU usage
        per_cpu_percent = psutil.cpu_percent(interval=0.1, percpu=True)
        for i, cpu_percent in enumerate(per_cpu_percent):
            core_labels = {**self.system_labels, "core": str(i)}
            metrics.append(
                self.create_metric(
                    name="cpu.core.usage.percent",
                    value=cpu_percent,
                    metric_type=MetricType.GAUGE,
                    unit=MetricUnit.PERCENT,
                    labels=core_labels,
                    description=f"CPU usage percentage for core {i}",
                )
            )
        
        # CPU load averages (1, 5, 15 minutes)
        if hasattr(psutil, "getloadavg"):  # Not available on Windows
            load1, load5, load15 = psutil.getloadavg()
            metrics.append(
                self.create_metric(
                    name="cpu.load.1min",
                    value=load1,
                    metric_type=MetricType.GAUGE,
                    labels=self.system_labels,
                    description="CPU load average (1 minute)",
                )
            )
            metrics.append(
                self.create_metric(
                    name="cpu.load.5min",
                    value=load5,
                    metric_type=MetricType.GAUGE,
                    labels=self.system_labels,
                    description="CPU load average (5 minutes)",
                )
            )
            metrics.append(
                self.create_metric(
                    name="cpu.load.15min",
                    value=load15,
                    metric_type=MetricType.GAUGE,
                    labels=self.system_labels,
                    description="CPU load average (15 minutes)",
                )
            )
        
        return metrics
    
    def _collect_memory_metrics(self) -> list[Metric]:
        """
        Collect memory-related metrics.
        
        Returns:
            List of memory metrics
        """
        metrics = []
        
        # Virtual memory metrics
        virtual_memory = psutil.virtual_memory()
        metrics.append(
            self.create_metric(
                name="memory.total",
                value=virtual_memory.total,
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.BYTES,
                labels=self.system_labels,
                description="Total physical memory",
            )
        )
        metrics.append(
            self.create_metric(
                name="memory.available",
                value=virtual_memory.available,
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.BYTES,
                labels=self.system_labels,
                description="Available memory",
            )
        )
        metrics.append(
            self.create_metric(
                name="memory.used",
                value=virtual_memory.used,
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.BYTES,
                labels=self.system_labels,
                description="Used memory",
            )
        )
        metrics.append(
            self.create_metric(
                name="memory.percent",
                value=virtual_memory.percent,
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.PERCENT,
                labels=self.system_labels,
                description="Memory usage percentage",
            )
        )
        
        # Swap memory metrics
        swap_memory = psutil.swap_memory()
        metrics.append(
            self.create_metric(
                name="swap.total",
                value=swap_memory.total,
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.BYTES,
                labels=self.system_labels,
                description="Total swap memory",
            )
        )
        metrics.append(
            self.create_metric(
                name="swap.used",
                value=swap_memory.used,
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.BYTES,
                labels=self.system_labels,
                description="Used swap memory",
            )
        )
        metrics.append(
            self.create_metric(
                name="swap.percent",
                value=swap_memory.percent,
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.PERCENT,
                labels=self.system_labels,
                description="Swap usage percentage",
            )
        )
        
        return metrics
    
    def _collect_disk_metrics(self) -> list[Metric]:
        """
        Collect disk-related metrics.
        
        Returns:
            List of disk metrics
        """
        metrics = []
        
        # Disk usage for each partition
        for partition in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                partition_labels = {
                    **self.system_labels,
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                }
                
                metrics.append(
                    self.create_metric(
                        name="disk.total",
                        value=usage.total,
                        metric_type=MetricType.GAUGE,
                        unit=MetricUnit.BYTES,
                        labels=partition_labels,
                        description=f"Total disk space on {partition.mountpoint}",
                    )
                )
                metrics.append(
                    self.create_metric(
                        name="disk.used",
                        value=usage.used,
                        metric_type=MetricType.GAUGE,
                        unit=MetricUnit.BYTES,
                        labels=partition_labels,
                        description=f"Used disk space on {partition.mountpoint}",
                    )
                )
                metrics.append(
                    self.create_metric(
                        name="disk.free",
                        value=usage.free,
                        metric_type=MetricType.GAUGE,
                        unit=MetricUnit.BYTES,
                        labels=partition_labels,
                        description=f"Free disk space on {partition.mountpoint}",
                    )
                )
                metrics.append(
                    self.create_metric(
                        name="disk.percent",
                        value=usage.percent,
                        metric_type=MetricType.GAUGE,
                        unit=MetricUnit.PERCENT,
                        labels=partition_labels,
                        description=f"Disk usage percentage on {partition.mountpoint}",
                    )
                )
            except (PermissionError, FileNotFoundError) as e:
                # Skip partitions we can't access
                logger.debug(f"Skipping disk metrics for {partition.mountpoint}: {str(e)}")
        
        # Disk I/O counters
        try:
            disk_io = psutil.disk_io_counters(perdisk=True)
            for disk_name, counters in disk_io.items():
                disk_labels = {**self.system_labels, "disk": disk_name}
                
                metrics.append(
                    self.create_metric(
                        name="disk.read.bytes",
                        value=counters.read_bytes,
                        metric_type=MetricType.COUNTER,
                        unit=MetricUnit.BYTES,
                        labels=disk_labels,
                        description=f"Total bytes read from disk {disk_name}",
                    )
                )
                metrics.append(
                    self.create_metric(
                        name="disk.write.bytes",
                        value=counters.write_bytes,
                        metric_type=MetricType.COUNTER,
                        unit=MetricUnit.BYTES,
                        labels=disk_labels,
                        description=f"Total bytes written to disk {disk_name}",
                    )
                )
                metrics.append(
                    self.create_metric(
                        name="disk.read.count",
                        value=counters.read_count,
                        metric_type=MetricType.COUNTER,
                        labels=disk_labels,
                        description=f"Total read operations on disk {disk_name}",
                    )
                )
                metrics.append(
                    self.create_metric(
                        name="disk.write.count",
                        value=counters.write_count,
                        metric_type=MetricType.COUNTER,
                        labels=disk_labels,
                        description=f"Total write operations on disk {disk_name}",
                    )
                )
        except (AttributeError, PermissionError) as e:
            logger.debug(f"Could not collect disk I/O metrics: {str(e)}")
        
        return metrics
    
    def _collect_process_metrics(self) -> list[Metric]:
        """
        Collect process-specific metrics.
        
        Returns:
            List of process metrics
        """
        metrics = []
        
        try:
            # Process information labels
            process_labels = {
                **self.system_labels,
                "pid": str(self.process_id),
                "process_name": self._process.name(),
            }
            
            # CPU usage
            process_cpu_percent = self._process.cpu_percent(interval=0.1)
            metrics.append(
                self.create_metric(
                    name="process.cpu.percent",
                    value=process_cpu_percent,
                    metric_type=MetricType.GAUGE,
                    unit=MetricUnit.PERCENT,
                    labels=process_labels,
                    description="Process CPU usage percentage",
                )
            )
            
            # Memory usage
            memory_info = self._process.memory_info()
            metrics.append(
                self.create_metric(
                    name="process.memory.rss",
                    value=memory_info.rss,
                    metric_type=MetricType.GAUGE,
                    unit=MetricUnit.BYTES,
                    labels=process_labels,
                    description="Process resident set size (RSS)",
                )
            )
            metrics.append(
                self.create_metric(
                    name="process.memory.vms",
                    value=memory_info.vms,
                    metric_type=MetricType.GAUGE,
                    unit=MetricUnit.BYTES,
                    labels=process_labels,
                    description="Process virtual memory size (VMS)",
                )
            )
            
            # Open file descriptors (not available on Windows)
            if hasattr(self._process, "num_fds"):
                metrics.append(
                    self.create_metric(
                        name="process.open_files",
                        value=self._process.num_fds(),
                        metric_type=MetricType.GAUGE,
                        labels=process_labels,
                        description="Number of open file descriptors",
                    )
                )
            
            # Thread count
            metrics.append(
                self.create_metric(
                    name="process.threads",
                    value=self._process.num_threads(),
                    metric_type=MetricType.GAUGE,
                    labels=process_labels,
                    description="Number of threads in the process",
                )
            )
            
            # Process uptime
            create_time = self._process.create_time()
            uptime = time.time() - create_time
            metrics.append(
                self.create_metric(
                    name="process.uptime",
                    value=uptime,
                    metric_type=MetricType.GAUGE,
                    unit=MetricUnit.SECONDS,
                    labels=process_labels,
                    description="Process uptime in seconds",
                )
            )
            
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            logger.warning(f"Failed to collect process metrics: {str(e)}")
        
        return metrics


class MemoryTierMetricsCollector(BaseMetricsCollector):
    """
    Collector for NCA memory tier metrics.
    
    This collector gathers metrics about the three memory tiers in the NCA:
    working memory, episodic memory, and semantic memory. It provides insights
    into memory usage, access patterns, and performance.
    """
    
    def __init__(
        self,
        name: str = "memory_tiers",
        enabled: bool = True,
        collection_interval: float = 30.0,
        metrics_prefix: str = "neuroca",
    ):
        """
        Initialize a memory tier metrics collector.
        
        Args:
            name: Name for this collector
            enabled: Whether this collector is enabled
            collection_interval: Time between collections in seconds
            metrics_prefix: Prefix for all metrics
        """
        super().__init__(name, enabled, collection_interval, metrics_prefix)
        
        # Common labels for all memory tier metrics
        self.memory_labels = {
            "component": "memory_system",
            "version": settings.get("memory.version", "unknown"),
        }
        
        logger.debug("MemoryTierMetricsCollector initialized")
    
    def collect(self) -> list[Metric]:
        """
        Collect metrics for all memory tiers.
        
        Returns:
            List of memory tier metrics
            
        Raises:
            MetricsCollectionError: If metrics collection fails
        """
        if not self.should_collect():
            return []
        
        try:
            metrics = []
            
            # Collect metrics for each memory tier
            metrics.extend(self._collect_working_memory_metrics())
            metrics.extend(self._collect_episodic_memory_metrics())
            metrics.extend(self._collect_semantic_memory_metrics())
            
            self.last_collection_time = time.time()
            logger.debug(f"Collected {len(metrics)} memory tier metrics")
            return metrics
            
        except Exception as e:
            error_msg = f"Failed to collect memory tier metrics: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise MetricsCollectionError(error_msg) from e
    
    def _collect_working_memory_metrics(self) -> list[Metric]:
        """
        Collect working memory metrics.
        
        Returns:
            List of working memory metrics
        """
        metrics = []
        
        # Working memory labels
        wm_labels = {**self.memory_labels, "tier": "working_memory"}
        
        # These metrics would typically come from the actual memory system
        # For now, we'll use placeholder values that would be replaced with real metrics
        
        # Working memory capacity and usage
        metrics.append(
            self.create_metric(
                name="memory.working.size",
                value=100,  # Placeholder value
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.COUNT,
                labels=wm_labels,
                description="Current number of items in working memory",
            )
        )
        
        metrics.append(
            self.create_metric(
                name="memory.working.capacity",
                value=150,  # Placeholder value
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.COUNT,
                labels=wm_labels,
                description="Maximum capacity of working memory",
            )
        )
        
        # Working memory operations
        metrics.append(
            self.create_metric(
                name="memory.working.reads",
                value=250,  # Placeholder value
                metric_type=MetricType.COUNTER,
                unit=MetricUnit.COUNT,
                labels=wm_labels,
                description="Total number of read operations from working memory",
            )
        )
        
        metrics.append(
            self.create_metric(
                name="memory.working.writes",
                value=120,  # Placeholder value
                metric_type=MetricType.COUNTER,
                unit=MetricUnit.COUNT,
                labels=wm_labels,
                description="Total number of write operations to working memory",
            )
        )
        
        # Working memory latency
        metrics.append(
            self.create_metric(
                name="memory.working.read_latency",
                value=0.005,  # Placeholder value in seconds
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.SECONDS,
                labels=wm_labels,
                description="Average read latency for working memory",
            )
        )
        
        metrics.append(
            self.create_metric(
                name="memory.working.write_latency",
                value=0.008,  # Placeholder value in seconds
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.SECONDS,
                labels=wm_labels,
                description="Average write latency for working memory",
            )
        )
        
        return metrics
    
    def _collect_episodic_memory_metrics(self) -> list[Metric]:
        """
        Collect episodic memory metrics.
        
        Returns:
            List of episodic memory metrics
        """
        metrics = []
        
        # Episodic memory labels
        em_labels = {**self.memory_labels, "tier": "episodic_memory"}
        
        # Episodic memory size and capacity
        metrics.append(
            self.create_metric(
                name="memory.episodic.size",
                value=5000,  # Placeholder value
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.COUNT,
                labels=em_labels,
                description="Current number of episodes in episodic memory",
            )
        )
        
        metrics.append(
            self.create_metric(
                name="memory.episodic.storage_bytes",
                value=25000000,  # Placeholder value
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.BYTES,
                labels=em_labels,
                description="Current storage size of episodic memory in bytes",
            )
        )
        
        # Episodic memory operations
        metrics.append(
            self.create_metric(
                name="memory.episodic.retrievals",
                value=350,  # Placeholder value
                metric_type=MetricType.COUNTER,
                unit=MetricUnit.COUNT,
                labels=em_labels,
                description="Total number of episode retrievals",
            )
        )
        
        metrics.append(
            self.create_metric(
                name="memory.episodic.stores",
                value=180,  # Placeholder value
                metric_type=MetricType.COUNTER,
                unit=MetricUnit.COUNT,
                labels=em_labels,
                description="Total number of episode stores",
            )
        )
        
        # Episodic memory performance
        metrics.append(
            self.create_metric(
                name="memory.episodic.retrieval_latency",
                value=0.12,  # Placeholder value in seconds
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.SECONDS,
                labels=em_labels,
                description="Average retrieval latency for episodic memory",
            )
        )
        
        metrics.append(
            self.create_metric(
                name="memory.episodic.store_latency",
                value=0.08,  # Placeholder value in seconds
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.SECONDS,
                labels=em_labels,
                description="Average store latency for episodic memory",
            )
        )
        
        # Episodic memory health
        metrics.append(
            self.create_metric(
                name="memory.episodic.retrieval_success_rate",
                value=0.95,  # Placeholder value (95%)
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.PERCENT,
                labels=em_labels,
                description="Success rate of episodic memory retrievals",
            )
        )
        
        return metrics
    
    def _collect_semantic_memory_metrics(self) -> list[Metric]:
        """
        Collect semantic memory metrics.
        
        Returns:
            List of semantic memory metrics
        """
        metrics = []
        
        # Semantic memory labels
        sm_labels = {**self.memory_labels, "tier": "semantic_memory"}
        
        # Semantic memory size and capacity
        metrics.append(
            self.create_metric(
                name="memory.semantic.concepts",
                value=50000,  # Placeholder value
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.COUNT,
                labels=sm_labels,
                description="Number of concepts in semantic memory",
            )
        )
        
        metrics.append(
            self.create_metric(
                name="memory.semantic.relationships",
                value=200000,  # Placeholder value
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.COUNT,
                labels=sm_labels,
                description="Number of relationships in semantic memory",
            )
        )
        
        metrics.append(
            self.create_metric(
                name="memory.semantic.storage_bytes",
                value=150000000,  # Placeholder value
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.BYTES,
                labels=sm_labels,
                description="Storage size of semantic memory in bytes",
            )
        )
        
        # Semantic memory operations
        metrics.append(
            self.create_metric(
                name="memory.semantic.queries",
                value=1200,  # Placeholder value
                metric_type=MetricType.COUNTER,
                unit=MetricUnit.COUNT,
                labels=sm_labels,
                description="Total number of semantic memory queries",
            )
        )
        
        metrics.append(
            self.create_metric(
                name="memory.semantic.updates",
                value=300,  # Placeholder value
                metric_type=MetricType.COUNTER,
                unit=MetricUnit.COUNT,
                labels=sm_labels,
                description="Total number of semantic memory updates",
            )
        )
        
        # Semantic memory performance
        metrics.append(
            self.create_metric(
                name="memory.semantic.query_latency",
                value=0.25,  # Placeholder value in seconds
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.SECONDS,
                labels=sm_labels,
                description="Average query latency for semantic memory",
            )
        )
        
        metrics.append(
            self.create_metric(
                name="memory.semantic.update_latency",
                value=0.15,  # Placeholder value in seconds
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.SECONDS,
                labels=sm_labels,
                description="Average update latency for semantic memory",
            )
        )
        
        return metrics


class LLMIntegrationMetricsCollector(BaseMetricsCollector):
    """
    Collector for LLM integration metrics.
    
    This collector gathers metrics related to the integration with Large Language Models,
    including request counts, latencies, token usage, and error rates.
    """
    
    def __init__(
        self,
        name: str = "llm_integration",
        enabled: bool = True,
        collection_interval: float = 60.0,
        metrics_prefix: str = "neuroca",
    ):
        """
        Initialize an LLM integration metrics collector.
        
        Args:
            name: Name for this collector
            enabled: Whether this collector is enabled
            collection_interval: Time between collections in seconds
            metrics_prefix: Prefix for all metrics
        """
        super().__init__(name, enabled, collection_interval, metrics_prefix)
        
        # Common labels for all LLM metrics
        self.llm_labels = {
            "component": "llm_integration",
            "version": settings.get("llm.integration.version", "unknown"),
        }
        
        logger.debug("LLMIntegrationMetricsCollector initialized")
    
    def collect(self) -> list[Metric]:
        """
        Collect LLM integration metrics.
        
        Returns:
            List of LLM integration metrics
            
        Raises:
            MetricsCollectionError: If metrics collection fails
        """
        if not self.should_collect():
            return []
        
        try:
            metrics = []
            
            # Collect metrics for different LLM providers
            # In a real implementation, this would iterate through active providers
            providers = ["openai", "anthropic", "local"]  # Example providers
            
            for provider in providers:
                metrics.extend(self._collect_provider_metrics(provider))
            
            self.last_collection_time = time.time()
            logger.debug(f"Collected {len(metrics)} LLM integration metrics")
            return metrics
            
        except Exception as e:
            error_msg = f"Failed to collect LLM integration metrics: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise MetricsCollectionError(error_msg) from e
    
    def _collect_provider_metrics(self, provider: str) -> list[Metric]:
        """
        Collect metrics for a specific LLM provider.
        
        Args:
            provider: Name of the LLM provider
            
        Returns:
            List of provider-specific metrics
        """
        metrics = []
        
        # Provider-specific labels
        provider_labels = {**self.llm_labels, "provider": provider}
        
        # These metrics would typically come from the actual LLM integration
        # For now, we'll use placeholder values that would be replaced with real metrics
        
        # Request counts
        metrics.append(
            self.create_metric(
                name="llm.requests.total",
                value=500,  # Placeholder value
                metric_type=MetricType.COUNTER,
                unit=MetricUnit.COUNT,
                labels=provider_labels,
                description=f"Total number of requests to {provider}",
            )
        )
        
        metrics.append(
            self.create_metric(
                name="llm.requests.successful",
                value=480,  # Placeholder value
                metric_type=MetricType.COUNTER,
                unit=MetricUnit.COUNT,
                labels=provider_labels,
                description=f"Number of successful requests to {provider}",
            )
        )
        
        metrics.append(
            self.create_metric(
                name="llm.requests.failed",
                value=20,  # Placeholder value
                metric_type=MetricType.COUNTER,
                unit=MetricUnit.COUNT,
                labels=provider_labels,
                description=f"Number of failed requests to {provider}",
            )
        )
        
        # Latency metrics
        metrics.append(
            self.create_metric(
                name="llm.latency.avg",
                value=1.2,  # Placeholder value in seconds
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.SECONDS,
                labels=provider_labels,
                description=f"Average request latency for {provider}",
            )
        )
        
        metrics.append(
            self.create_metric(
                name="llm.latency.p95",
                value=2.5,  # Placeholder value in seconds
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.SECONDS,
                labels=provider_labels,
                description=f"95th percentile request latency for {provider}",
            )
        )
        
        metrics.append(
            self.create_metric(
                name="llm.latency.p99",
                value=4.0,  # Placeholder value in seconds
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.SECONDS,
                labels=provider_labels,
                description=f"99th percentile request latency for {provider}",
            )
        )
        
        # Token usage
        metrics.append(
            self.create_metric(
                name="llm.tokens.input",
                value=25000,  # Placeholder value
                metric_type=MetricType.COUNTER,
                unit=MetricUnit.COUNT,
                labels=provider_labels,
                description=f"Total input tokens sent to {provider}",
            )
        )
        
        metrics.append(
            self.create_metric(
                name="llm.tokens.output",
                value=120000,  # Placeholder value
                metric_type=MetricType.COUNTER,
                unit=MetricUnit.COUNT,
                labels=provider_labels,
                description=f"Total output tokens received from {provider}",
            )
        )
        
        # Cost metrics (if applicable)
        if provider in ["openai", "anthropic"]:  # Providers that charge per token
            metrics.append(
                self.create_metric(
                    name="llm.cost",
                    value=2.35,  # Placeholder value in USD
                    metric_type=MetricType.COUNTER,
                    unit=MetricUnit.USD,
                    labels=provider_labels,
                    description=f"Total cost of requests to {provider}",
                )
            )
        
        # Rate limiting metrics
        metrics.append(
            self.create_metric(
                name="llm.rate_limits.hit",
                value=5,  # Placeholder value
                metric_type=MetricType.COUNTER,
                unit=MetricUnit.COUNT,
                labels=provider_labels,
                description=f"Number of rate limit hits for {provider}",
            )
        )
        
        # Model-specific metrics
        models = self._get_models_for_provider(provider)
        for model in models:
            model_labels = {**provider_labels, "model": model}
            
            metrics.append(
                self.create_metric(
                    name="llm.model.requests",
                    value=100,  # Placeholder value
                    metric_type=MetricType.COUNTER,
                    unit=MetricUnit.COUNT,
                    labels=model_labels,
                    description=f"Number of requests to {model} model",
                )
            )
            
            metrics.append(
                self.create_metric(
                    name="llm.model.latency",
                    value=0.8,  # Placeholder value in seconds
                    metric_type=MetricType.GAUGE,
                    unit=MetricUnit.SECONDS,
                    labels=model_labels,
                    description=f"Average latency for {model} model",
                )
            )
        
        return metrics
    
    def _get_models_for_provider(self, provider: str) -> list[str]:
        """
        Get the list of models for a specific provider.
        
        Args:
            provider: Name of the LLM provider
            
        Returns:
            List of model names
        """
        # This would typically come from configuration or be determined dynamically
        provider_models = {
            "openai": ["gpt-4", "gpt-3.5-turbo"],
            "anthropic": ["claude-2", "claude-instant"],
            "local": ["llama-2-7b", "mistral-7b"],
        }
        
        return provider_models.get(provider, [])


class PerformanceMetricsCollector(BaseMetricsCollector):
    """
    Collector for performance-related metrics.
    
    This collector gathers metrics related to the performance of various components
    of the NCA system, including response times, throughput, and resource efficiency.
    """
    
    def __init__(
        self,
        name: str = "performance",
        enabled: bool = True,
        collection_interval: float = 30.0,
        metrics_prefix: str = "neuroca",
    ):
        """
        Initialize a performance metrics collector.
        
        Args:
            name: Name for this collector
            enabled: Whether this collector is enabled
            collection_interval: Time between collections in seconds
            metrics_prefix: Prefix for all metrics
        """
        super().__init__(name, enabled, collection_interval, metrics_prefix)
        
        # Common labels for all performance metrics
        self.performance_labels = {
            "component": "performance",
            "version": settings.get("system.version", "unknown"),
        }
        
        logger.debug("PerformanceMetricsCollector initialized")
    
    def collect(self) -> list[Metric]:
        """
        Collect performance metrics.
        
        Returns:
            List of performance metrics
            
        Raises:
            MetricsCollectionError: If metrics collection fails
        """
        if not self.should_collect():
            return []
        
        try:
            metrics = []
            
            # Collect metrics for different components
            metrics.extend(self._collect_api_performance_metrics())
            metrics.extend(self._collect_processing_performance_metrics())
            metrics.extend(self._collect_memory_performance_metrics())
            
            self.last_collection_time = time.time()
            logger.debug(f"Collected {len(metrics)} performance metrics")
            return metrics
            
        except Exception as e:
            error_msg = f"Failed to collect performance metrics: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise MetricsCollectionError(error_msg) from e
    
    def _collect_api_performance_metrics(self) -> list[Metric]:
        """
        Collect API performance metrics.
        
        Returns:
            List of API performance metrics
        """
        metrics = []
        
        # API performance labels
        api_labels = {**self.performance_labels, "subsystem": "api"}
        
        # These metrics would typically come from actual API monitoring
        # For now, we'll use placeholder values that would be replaced with real metrics
        
        # Request rate
        metrics.append(
            self.create_metric(
                name="api.requests.rate",
                value=25.5,  # Placeholder value (requests per second)
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.RATE_PER_SECOND,
                labels=api_labels,
                description="API request rate per second",
            )
        )
        
        # Response time
        metrics.append(
            self.create_metric(
                name="api.response_time.avg",
                value=0.12,  # Placeholder value in seconds
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.SECONDS,
                labels=api_labels,
                description="Average API response time",
            )
        )
        
        metrics.append(
            self.create_metric(
                name="api.response_time.p95",
                value=0.25,  # Placeholder value in seconds
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.SECONDS,
                labels=api_labels,
                description="95th percentile API response time",
            )
        )
        
        # Error rate
        metrics.append(
            self.create_metric(
                name="api.error_rate",
                value=0.02,  # Placeholder value (2%)
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.PERCENT,
                labels=api_labels,
                description="API error rate",
            )
        )
        
        # Endpoint-specific metrics
        endpoints = ["query", "process", "memory", "health"]
        for endpoint in endpoints:
            endpoint_labels = {**api_labels, "endpoint": endpoint}
            
            metrics.append(
                self.create_metric(
                    name="api.endpoint.requests",
                    value=100,  # Placeholder value
                    metric_type=MetricType.COUNTER,
                    unit=MetricUnit.COUNT,
                    labels=endpoint_labels,
                    description=f"Total requests to {endpoint} endpoint",
                )
            )
            
            metrics.append(
                self.create_metric(
                    name="api.endpoint.response_time",
                    value=0.1,  # Placeholder value in seconds
                    metric_type=MetricType.GAUGE,
                    unit=MetricUnit.SECONDS,
                    labels=endpoint_labels,
                    description=f"Average response time for {endpoint} endpoint",
                )
            )
        
        return metrics
    
    def _collect_processing_performance_metrics(self) -> list[Metric]:
        """
        Collect processing performance metrics.
        
        Returns:
            List of processing performance metrics
        """
        metrics = []
        
        # Processing performance labels
        processing_labels = {**self.performance_labels, "subsystem": "processing"}
        
        # Processing throughput
        metrics.append(
            self.create_metric(
                name="processing.throughput",
                value=15.2,  # Placeholder value (tasks per second)
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.RATE_PER_SECOND,
                labels=processing_labels,
                description="Processing throughput (tasks per second)",
            )
        )
        
        # Processing latency
        metrics.append(
            self.create_metric(
                name="processing.latency.avg",
                value=0.35,  # Placeholder value in seconds
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.SECONDS,
                labels=processing_labels,
                description="Average processing latency",
            )
        )
        
        # Queue metrics
        metrics.append(
            self.create_metric(
                name="processing.queue.length",
                value=5,  # Placeholder value
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.COUNT,
                labels=processing_labels,
                description="Current processing queue length",
            )
        )
        
        metrics.append(
            self.create_metric(
                name="processing.queue.wait_time",
                value=0.2,  # Placeholder value in seconds
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.SECONDS,
                labels=processing_labels,
                description="Average wait time in processing queue",
            )
        )
        
        # Task-specific metrics
        task_types = ["reasoning", "memory_access", "planning", "perception"]
        for task_type in task_types:
            task_labels = {**processing_labels, "task_type": task_type}
            
            metrics.append(
                self.create_metric(
                    name="processing.task.count",
                    value=50,  # Placeholder value
                    metric_type=MetricType.COUNTER,
                    unit=MetricUnit.COUNT,
                    labels=task_labels,
                    description=f"Total {task_type} tasks processed",
                )
            )
            
            metrics.append(
                self.create_metric(
                    name="processing.task.duration",
                    value=0.15,  # Placeholder value in seconds
                    metric_type=MetricType.GAUGE,
                    unit=MetricUnit.SECONDS,
                    labels=task_labels,
                    description=f"Average duration of {task_type} tasks",
                )
            )
        
        return metrics
    
    def _collect_memory_performance_metrics(self) -> list[Metric]:
        """
        Collect memory performance metrics.
        
        Returns:
            List of memory performance metrics
        """
        metrics = []
        
        # Memory performance labels
        memory_labels = {**self.performance_labels, "subsystem": "memory"}
        
        # Memory access rate
        metrics.append(
            self.create_metric(
                name="memory.access.rate",
                value=45.8,  # Placeholder value (accesses per second)
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.RATE_PER_SECOND,
                labels=memory_labels,
                description="Memory access rate per second",
            )
        )
        
        # Memory access latency
        metrics.append(
            self.create_metric(
                name="memory.access.latency",
                value=0.05,  # Placeholder value in seconds
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.SECONDS,
                labels=memory_labels,
                description="Average memory access latency",
            )
        )
        
        # Memory operation breakdown
        operation_types = ["read", "write", "update", "delete"]
        for op_type in operation_types:
            op_labels = {**memory_labels, "operation": op_type}
            
            metrics.append(
                self.create_metric(
                    name="memory.operation.count",
                    value=200,  # Placeholder value
                    metric_type=MetricType.COUNTER,
                    unit=MetricUnit.COUNT,
                    labels=op_labels,
                    description=f"Total {op_type} operations on memory",
                )
            )
            
            metrics.append(
                self.create_metric(
                    name="memory.operation.latency",
                    value=0.03,  # Placeholder value in seconds
                    metric_type=MetricType.GAUGE,
                    unit=MetricUnit.SECONDS,
                    labels=op_labels,
                    description=f"Average latency of {op_type} operations",
                )
            )
        
        # Memory tier performance comparison
        memory_tiers = ["working", "episodic", "semantic"]
        for tier in memory_tiers:
            tier_labels = {**memory_labels, "tier": f"{tier}_memory"}
            
            metrics.append(
                self.create_metric(
                    name="memory.tier.access_rate",
                    value=15.0,  # Placeholder value (accesses per second)
                    metric_type=MetricType.GAUGE,
                    unit=MetricUnit.RATE_PER_SECOND,
                    labels=tier_labels,
                    description=f"Access rate for {tier} memory tier",
                )
            )
            
            metrics.append(
                self.create_metric(
                    name="memory.tier.latency",
                    value=0.08,  # Placeholder value in seconds
                    metric_type=MetricType.GAUGE,
                    unit=MetricUnit.SECONDS,
                    labels=tier_labels,
                    description=f"Average latency for {tier} memory tier",
                )
            )
        
        return metrics


class CustomMetricsCollector(BaseMetricsCollector):
    """
    Collector for custom user-defined metrics.
    
    This collector allows users to define and collect custom metrics that are
    specific to their use case or application. It provides a flexible way to
    extend the monitoring system.
    """
    
    def __init__(
        self,
        name: str = "custom",
        enabled: bool = True,
        collection_interval: float = 60.0,
        metrics_prefix: str = "neuroca",
    ):
        """
        Initialize a custom metrics collector.
        
        Args:
            name: Name for this collector
            enabled: Whether this collector is enabled
            collection_interval: Time between collections in seconds
            metrics_prefix: Prefix for all metrics
        """
        super().__init__(name, enabled, collection_interval, metrics_prefix)
        
        # Storage for custom metrics
        self._custom_metrics: dict[str, dict[str, Any]] = {}
        
        logger.debug("CustomMetricsCollector initialized")
    
    def register_metric(
        self,
        name: str,
        metric_type: MetricType,
        description: str,
        unit: Optional[MetricUnit] = None,
        labels: Optional[dict[str, str]] = None,
    ) -> None:
        """
        Register a new custom metric.
        
        Args:
            name: Name of the metric (will be prefixed)
            metric_type: Type of the metric (counter, gauge, etc.)
            description: Human-readable description of the metric
            unit: Unit of measurement
            labels: Additional labels to attach to the metric
            
        Raises:
            ValueError: If a metric with the same name already exists
        """
        if name in self._custom_metrics:
            raise ValueError(f"Metric with name '{name}' already exists")
        
        self._custom_metrics[name] = {
            "type": metric_type,
            "description": description,
            "unit": unit,
            "labels": labels or {},
            "value": None,
            "last_updated": None,
        }
        
        logger.debug(f"Registered custom metric '{name}'")
    
    def update_metric(
        self,
        name: str,
        value: Union[int, float, str, bool],
        labels: Optional[dict[str, str]] = None,
    ) -> None:
        """
        Update the value of a custom metric.
        
        Args:
            name: Name of the metric to update
            value: New value for the metric
            labels: Additional or updated labels
            
        Raises:
            ValueError: If the metric does not exist
        """
        if name not in self._custom_metrics:
            raise ValueError(f"Metric with name '{name}' does not exist")
        
        self._custom_metrics[name]["value"] = value
        self._custom_metrics[name]["last_updated"] = time.time()
        
        if labels:
            self._custom_metrics[name]["labels"].update(labels)
        
        logger.debug(f"Updated custom metric '{name}' with value {value}")
    
    def collect(self) -> list[Metric]:
        """
        Collect all registered custom metrics.
        
        Returns:
            List of custom metrics
            
        Raises:
            MetricsCollectionError: If metrics collection fails
        """
        if not self.should_collect():
            return []
        
        try:
            metrics = []
            
            for name, metric_data in self._custom_metrics.items():
                # Skip metrics that haven't been updated
                if metric_data["value"] is None:
                    continue
                
                metrics.append(
                    self.create_metric(
                        name=name,
                        value=metric_data["value"],
                        metric_type=metric_data["type"],
                        unit=metric_data["unit"],
                        labels=metric_data["labels"],
                        description=metric_data["description"],
                        timestamp=metric_data["last_updated"],
                    )
                )
            
            self.last_collection_time = time.time()
            logger.debug(f"Collected {len(metrics)} custom metrics")
            return metrics
            
        except Exception as e:
            error_msg = f"Failed to collect custom metrics: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise MetricsCollectionError(error_msg) from e
    
    def reset_metric(self, name: str) -> None:
        """
        Reset a counter metric to zero.
        
        Args:
            name: Name of the metric to reset
            
        Raises:
            ValueError: If the metric does not exist or is not a counter
        """
        if name not in self._custom_metrics:
            raise ValueError(f"Metric with name '{name}' does not exist")
        
        if self._custom_metrics[name]["type"] != MetricType.COUNTER:
            raise ValueError(f"Metric '{name}' is not a counter and cannot be reset")
        
        self._custom_metrics[name]["value"] = 0
        self._custom_metrics[name]["last_updated"] = time.time()
        
        logger.debug(f"Reset counter metric '{name}' to zero")
    
    def increment_counter(self, name: str, value: float = 1.0) -> None:
        """
        Increment a counter metric by the specified value.
        
        Args:
            name: Name of the counter metric to increment
            value: Amount to increment by (default: 1.0)
            
        Raises:
            ValueError: If the metric does not exist or is not a counter
        """
        if name not in self._custom_metrics:
            raise ValueError(f"Metric with name '{name}' does not exist")
        
        if self._custom_metrics[name]["type"] != MetricType.COUNTER:
            raise ValueError(f"Metric '{name}' is not a counter and cannot be incremented")
        
        current_value = self._custom_metrics[name]["value"] or 0
        self._custom_metrics[name]["value"] = current_value + value
        self._custom_metrics[name]["last_updated"] = time.time()
        
        logger.debug(f"Incremented counter metric '{name}' by {value}")
    
    def remove_metric(self, name: str) -> None:
        """
        Remove a custom metric.
        
        Args:
            name: Name of the metric to remove
            
        Raises:
            ValueError: If the metric does not exist
        """
        if name not in self._custom_metrics:
            raise ValueError(f"Metric with name '{name}' does not exist")
        
        del self._custom_metrics[name]
        logger.debug(f"Removed custom metric '{name}'")


class MetricsCollectorRegistry:
    """
    Registry for metrics collectors.
    
    This class manages a collection of metrics collectors and provides methods
    to register, retrieve, and collect metrics from all registered collectors.
    """
    
    def __init__(self):
        """Initialize a new metrics collector registry."""
        self._collectors: dict[str, BaseMetricsCollector] = {}
        logger.debug("MetricsCollectorRegistry initialized")
    
    def register(self, collector: BaseMetricsCollector) -> None:
        """
        Register a metrics collector.
        
        Args:
            collector: The collector to register
            
        Raises:
            ValueError: If a collector with the same name already exists
        """
        if collector.name in self._collectors:
            raise ValueError(f"Collector with name '{collector.name}' already exists")
        
        self._collectors[collector.name] = collector
        logger.debug(f"Registered collector '{collector.name}'")
    
    def unregister(self, name: str) -> None:
        """
        Unregister a metrics collector.
        
        Args:
            name: Name of the collector to unregister
            
        Raises:
            ValueError: If the collector does not exist
        """
        if name not in self._collectors:
            raise ValueError(f"Collector with name '{name}' does not exist")
        
        del self._collectors[name]
        logger.debug(f"Unregistered collector '{name}'")
    
    def get_collector(self, name: str) -> BaseMetricsCollector:
        """
        Get a collector by name.
        
        Args:
            name: Name of the collector to retrieve
            
        Returns:
            The requested collector
            
        Raises:
            ValueError: If the collector does not exist
        """
        if name not in self._collectors:
            raise ValueError(f"Collector with name '{name}' does not exist")
        
        return self._collectors[name]
    
    def collect_all(self) -> list[Metric]:
        """
        Collect metrics from all registered collectors.
        
        Returns:
            List of all collected metrics
        """
        all_metrics = []
        
        for name, collector in self._collectors.items():
            try:
                if collector.enabled:
                    metrics = collector.collect()
                    all_metrics.extend(metrics)
                    logger.debug(f"Collected {len(metrics)} metrics from '{name}'")
            except Exception as e:
                logger.error(f"Failed to collect metrics from '{name}': {str(e)}", exc_info=True)
        
        logger.info(f"Collected a total of {len(all_metrics)} metrics from all collectors")
        return all_metrics
    
    def get_collector_names(self) -> list[str]:
        """
        Get the names of all registered collectors.
        
        Returns:
            List of collector names
        """
        return list(self._collectors.keys())
    
    def enable_collector(self, name: str) -> None:
        """
        Enable a collector.
        
        Args:
            name: Name of the collector to enable
            
        Raises:
            ValueError: If the collector does not exist
        """
        collector = self.get_collector(name)
        collector.enabled = True
        logger.debug(f"Enabled collector '{name}'")
    
    def disable_collector(self, name: str) -> None:
        """
        Disable a collector.
        
        Args:
            name: Name of the collector to disable
            
        Raises:
            ValueError: If the collector does not exist
        """
        collector = self.get_collector(name)
        collector.enabled = False
        logger.debug(f"Disabled collector '{name}'")
    
    def set_collection_interval(self, name: str, interval: float) -> None:
        """
        Set the collection interval for a collector.
        
        Args:
            name: Name of the collector
            interval: New collection interval in seconds
            
        Raises:
            ValueError: If the collector does not exist or interval is invalid
        """
        if interval <= 0:
            raise ValueError("Collection interval must be positive")
        
        collector = self.get_collector(name)
        collector.collection_interval = interval
        logger.debug(f"Set collection interval for '{name}' to {interval} seconds")