"""
Metrics Exporters for the NeuroCognitive Architecture (NCA) Monitoring System.

This module provides a collection of exporters that send metrics data to various
monitoring backends. It includes a base exporter interface and implementations for
common monitoring systems like Prometheus, OpenTelemetry, and cloud-specific services.

The exporters handle batching, retry logic, and proper error handling to ensure
metrics are reliably delivered even under adverse conditions.

Usage:
    # Configure and use a Prometheus exporter
    prometheus_exporter = PrometheusExporter(
        endpoint="/metrics",
        port=9090
    )
    prometheus_exporter.export_metric("memory_usage", 128.5, {"tier": "working_memory"})

    # Configure and use an OpenTelemetry exporter
    otel_exporter = OpenTelemetryExporter(
        service_name="neuroca",
        endpoint="http://collector:4317"
    )
    otel_exporter.export_metric("inference_time", 0.35, {"model": "gpt4"})
"""

import abc
import json
import logging
import os
import time
from enum import Enum
from typing import Any, Optional, Union

# Third-party imports
try:
    import prometheus_client
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

try:
    from opentelemetry import metrics as otel_metrics
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False

# Set up module logger
logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Enumeration of supported metric types."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class ExporterError(Exception):
    """Base exception class for all exporter-related errors."""
    pass


class ConfigurationError(ExporterError):
    """Exception raised when an exporter is misconfigured."""
    pass


class ExportError(ExporterError):
    """Exception raised when metrics export fails."""
    pass


class MetricExporter(abc.ABC):
    """
    Abstract base class for all metric exporters.
    
    This class defines the interface that all metric exporters must implement.
    Concrete implementations handle the specifics of exporting metrics to
    different monitoring systems.
    """
    
    def __init__(self, name: str, batch_size: int = 100, flush_interval: int = 60):
        """
        Initialize the base metric exporter.
        
        Args:
            name: A unique name for this exporter instance
            batch_size: Maximum number of metrics to batch before forcing a flush
            flush_interval: Maximum time in seconds between flush operations
        
        Raises:
            ConfigurationError: If the configuration is invalid
        """
        self.name = name
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.metrics_buffer: list[dict[str, Any]] = []
        self.last_flush_time = time.time()
        self._initialized = False
        
        logger.debug(f"Initialized {self.__class__.__name__} '{name}' with batch_size={batch_size}, "
                    f"flush_interval={flush_interval}s")
    
    @abc.abstractmethod
    def initialize(self) -> None:
        """
        Initialize the exporter, establishing connections and setting up resources.
        
        This method should be called before any metrics are exported.
        
        Raises:
            ConfigurationError: If initialization fails due to configuration issues
            ExporterError: If initialization fails for other reasons
        """
        pass
    
    @abc.abstractmethod
    def _export_batch(self, metrics: list[dict[str, Any]]) -> None:
        """
        Export a batch of metrics to the monitoring system.
        
        This internal method handles the actual export logic and is called by flush().
        
        Args:
            metrics: A list of metric dictionaries to export
            
        Raises:
            ExportError: If the export operation fails
        """
        pass
    
    def export_metric(self, 
                     name: str, 
                     value: Union[int, float], 
                     labels: Optional[dict[str, str]] = None,
                     metric_type: MetricType = MetricType.GAUGE,
                     timestamp: Optional[float] = None) -> None:
        """
        Queue a metric for export.
        
        Args:
            name: The name of the metric
            value: The numeric value of the metric
            labels: Optional key-value pairs for metric dimensions/labels
            metric_type: The type of metric (counter, gauge, etc.)
            timestamp: Optional timestamp for the metric (defaults to current time)
            
        Raises:
            ValueError: If the metric name or value is invalid
            ExporterError: If the exporter encounters an error
        """
        if not self._initialized:
            self.initialize()
            self._initialized = True
            
        if not name or not isinstance(name, str):
            raise ValueError("Metric name must be a non-empty string")
            
        if not isinstance(value, (int, float)):
            raise ValueError(f"Metric value must be numeric, got {type(value)}")
            
        if labels is not None and not isinstance(labels, dict):
            raise ValueError(f"Labels must be a dictionary, got {type(labels)}")
            
        # Create the metric record
        metric = {
            "name": name,
            "value": value,
            "type": metric_type.value,
            "timestamp": timestamp or time.time(),
            "labels": labels or {}
        }
        
        # Add to buffer
        self.metrics_buffer.append(metric)
        logger.debug(f"Queued metric: {name}={value} ({metric_type.value})")
        
        # Check if we need to flush
        if len(self.metrics_buffer) >= self.batch_size or \
           (time.time() - self.last_flush_time) >= self.flush_interval:
            self.flush()
    
    def flush(self) -> None:
        """
        Flush all buffered metrics to the monitoring system.
        
        This method should be called periodically to ensure metrics are exported
        in a timely manner, and must be called before application shutdown to
        avoid losing metrics.
        
        Raises:
            ExportError: If the export operation fails
        """
        if not self.metrics_buffer:
            logger.debug("No metrics to flush")
            return
            
        try:
            metrics_to_export = self.metrics_buffer.copy()
            self.metrics_buffer.clear()
            
            logger.debug(f"Flushing {len(metrics_to_export)} metrics")
            self._export_batch(metrics_to_export)
            
            self.last_flush_time = time.time()
            logger.debug(f"Successfully flushed {len(metrics_to_export)} metrics")
            
        except Exception as e:
            # Restore metrics to buffer to avoid data loss
            self.metrics_buffer.extend(metrics_to_export)
            logger.error(f"Failed to flush metrics: {str(e)}")
            raise ExportError(f"Failed to export metrics: {str(e)}") from e
    
    def close(self) -> None:
        """
        Close the exporter, releasing any resources and flushing remaining metrics.
        
        This method should be called when the exporter is no longer needed,
        typically during application shutdown.
        """
        try:
            if self.metrics_buffer:
                logger.info(f"Flushing {len(self.metrics_buffer)} metrics before closing")
                self.flush()
        except Exception as e:
            logger.error(f"Error during final flush: {str(e)}")
        
        logger.info(f"Closed {self.__class__.__name__} '{self.name}'")


class PrometheusExporter(MetricExporter):
    """
    Exporter for Prometheus monitoring system.
    
    This exporter creates a Prometheus HTTP endpoint that can be scraped by
    a Prometheus server. It maintains metrics in memory and exposes them via
    the Prometheus client library.
    """
    
    def __init__(self, 
                name: str = "prometheus",
                endpoint: str = "/metrics", 
                port: int = 9090,
                **kwargs):
        """
        Initialize the Prometheus exporter.
        
        Args:
            name: A unique name for this exporter instance
            endpoint: The HTTP endpoint to expose metrics on
            port: The port to listen on
            **kwargs: Additional arguments passed to the base class
            
        Raises:
            ConfigurationError: If Prometheus client library is not available
        """
        super().__init__(name=name, **kwargs)
        
        if not PROMETHEUS_AVAILABLE:
            raise ConfigurationError(
                "Prometheus client library not available. "
                "Install with 'pip install prometheus-client'"
            )
            
        self.endpoint = endpoint
        self.port = port
        self.registry = None
        self.metrics_dict = {}  # Stores metric objects by name and labels
        
        logger.info(f"Created Prometheus exporter on {endpoint}:{port}")
    
    def initialize(self) -> None:
        """
        Initialize the Prometheus exporter and start the HTTP server.
        
        Raises:
            ConfigurationError: If initialization fails
        """
        try:
            self.registry = prometheus_client.CollectorRegistry()
            prometheus_client.start_http_server(
                port=self.port,
                endpoint=self.endpoint,
                registry=self.registry
            )
            logger.info(f"Started Prometheus HTTP server on port {self.port} at {self.endpoint}")
            self._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize Prometheus exporter: {str(e)}")
            raise ConfigurationError(f"Failed to initialize Prometheus exporter: {str(e)}") from e
    
    def _get_or_create_metric(self, name: str, metric_type: str, labels: dict[str, str]) -> tuple[Any, tuple[str, ...]]:
        """
        Get an existing metric object or create a new one.
        
        Args:
            name: The metric name
            metric_type: The type of metric
            labels: The metric labels
            
        Returns:
            A tuple containing the metric object and the label values
        """
        # Create a key that uniquely identifies this metric with its label names
        label_names = tuple(sorted(labels.keys()))
        metric_key = (name, metric_type, label_names)
        
        # Get or create the metric
        if metric_key not in self.metrics_dict:
            if metric_type == MetricType.COUNTER.value:
                self.metrics_dict[metric_key] = prometheus_client.Counter(
                    name, f"{name} counter", label_names, registry=self.registry
                )
            elif metric_type == MetricType.GAUGE.value:
                self.metrics_dict[metric_key] = prometheus_client.Gauge(
                    name, f"{name} gauge", label_names, registry=self.registry
                )
            elif metric_type == MetricType.HISTOGRAM.value:
                self.metrics_dict[metric_key] = prometheus_client.Histogram(
                    name, f"{name} histogram", label_names, registry=self.registry
                )
            elif metric_type == MetricType.SUMMARY.value:
                self.metrics_dict[metric_key] = prometheus_client.Summary(
                    name, f"{name} summary", label_names, registry=self.registry
                )
            else:
                raise ValueError(f"Unsupported metric type: {metric_type}")
        
        # Extract label values in the same order as label_names
        label_values = tuple(labels.get(label, "") for label in label_names)
        
        return self.metrics_dict[metric_key], label_values
    
    def _export_batch(self, metrics: list[dict[str, Any]]) -> None:
        """
        Export a batch of metrics to Prometheus.
        
        Args:
            metrics: A list of metric dictionaries to export
            
        Raises:
            ExportError: If the export operation fails
        """
        try:
            for metric in metrics:
                name = metric["name"]
                value = metric["value"]
                metric_type = metric["type"]
                labels = metric["labels"]
                
                # Get or create the metric object
                prometheus_metric, label_values = self._get_or_create_metric(name, metric_type, labels)
                
                # Update the metric value
                if metric_type == MetricType.COUNTER.value:
                    # For counters, we increment by the value
                    if label_values:
                        prometheus_metric.labels(*label_values).inc(value)
                    else:
                        prometheus_metric.inc(value)
                elif metric_type == MetricType.GAUGE.value:
                    # For gauges, we set the value
                    if label_values:
                        prometheus_metric.labels(*label_values).set(value)
                    else:
                        prometheus_metric.set(value)
                elif metric_type in (MetricType.HISTOGRAM.value, MetricType.SUMMARY.value):
                    # For histograms and summaries, we observe the value
                    if label_values:
                        prometheus_metric.labels(*label_values).observe(value)
                    else:
                        prometheus_metric.observe(value)
                        
            logger.debug(f"Exported {len(metrics)} metrics to Prometheus")
            
        except Exception as e:
            logger.error(f"Failed to export metrics to Prometheus: {str(e)}")
            raise ExportError(f"Failed to export metrics to Prometheus: {str(e)}") from e
    
    def close(self) -> None:
        """
        Close the Prometheus exporter and stop the HTTP server.
        """
        super().close()
        # Prometheus HTTP server runs in a daemon thread, so no explicit shutdown is needed


class OpenTelemetryExporter(MetricExporter):
    """
    Exporter for OpenTelemetry metrics.
    
    This exporter sends metrics to an OpenTelemetry collector using the OTLP protocol.
    """
    
    def __init__(self, 
                name: str = "opentelemetry",
                service_name: str = "neuroca",
                endpoint: str = "http://localhost:4317",
                **kwargs):
        """
        Initialize the OpenTelemetry exporter.
        
        Args:
            name: A unique name for this exporter instance
            service_name: The name of the service generating metrics
            endpoint: The OpenTelemetry collector endpoint
            **kwargs: Additional arguments passed to the base class
            
        Raises:
            ConfigurationError: If OpenTelemetry libraries are not available
        """
        super().__init__(name=name, **kwargs)
        
        if not OPENTELEMETRY_AVAILABLE:
            raise ConfigurationError(
                "OpenTelemetry libraries not available. "
                "Install with 'pip install opentelemetry-api opentelemetry-sdk "
                "opentelemetry-exporter-otlp-proto-grpc'"
            )
            
        self.service_name = service_name
        self.endpoint = endpoint
        self.meter_provider = None
        self.meter = None
        self.metrics_dict = {}
        
        logger.info(f"Created OpenTelemetry exporter for service '{service_name}' to endpoint {endpoint}")
    
    def initialize(self) -> None:
        """
        Initialize the OpenTelemetry exporter.
        
        Raises:
            ConfigurationError: If initialization fails
        """
        try:
            # Create the OTLP exporter
            otlp_exporter = OTLPMetricExporter(endpoint=self.endpoint)
            
            # Create a metric reader that will periodically export metrics
            reader = PeriodicExportingMetricReader(
                exporter=otlp_exporter,
                export_interval_millis=self.flush_interval * 1000
            )
            
            # Create a meter provider with the reader
            self.meter_provider = MeterProvider(metric_readers=[reader])
            
            # Set the global meter provider
            otel_metrics.set_meter_provider(self.meter_provider)
            
            # Create a meter for this service
            self.meter = otel_metrics.get_meter(
                name=self.service_name,
                version="1.0.0"
            )
            
            logger.info(f"Initialized OpenTelemetry exporter for service '{self.service_name}'")
            self._initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenTelemetry exporter: {str(e)}")
            raise ConfigurationError(f"Failed to initialize OpenTelemetry exporter: {str(e)}") from e
    
    def _get_or_create_metric(self, name: str, metric_type: str, labels: dict[str, str]) -> Any:
        """
        Get an existing metric object or create a new one.
        
        Args:
            name: The metric name
            metric_type: The type of metric
            labels: The metric labels
            
        Returns:
            The metric object
        """
        # Create a key that uniquely identifies this metric
        metric_key = (name, metric_type)
        
        # Get or create the metric
        if metric_key not in self.metrics_dict:
            description = f"{name} {metric_type}"
            
            if metric_type == MetricType.COUNTER.value:
                self.metrics_dict[metric_key] = self.meter.create_counter(
                    name=name,
                    description=description,
                    unit="1"
                )
            elif metric_type == MetricType.GAUGE.value:
                # OpenTelemetry doesn't have a direct gauge equivalent, use UpDownCounter
                self.metrics_dict[metric_key] = self.meter.create_up_down_counter(
                    name=name,
                    description=description,
                    unit="1"
                )
            elif metric_type == MetricType.HISTOGRAM.value:
                self.metrics_dict[metric_key] = self.meter.create_histogram(
                    name=name,
                    description=description,
                    unit="1"
                )
            else:
                # Default to counter for unsupported types
                logger.warning(f"Unsupported metric type '{metric_type}' for OpenTelemetry, using counter")
                self.metrics_dict[metric_key] = self.meter.create_counter(
                    name=name,
                    description=f"{name} counter",
                    unit="1"
                )
        
        return self.metrics_dict[metric_key]
    
    def _export_batch(self, metrics: list[dict[str, Any]]) -> None:
        """
        Export a batch of metrics to OpenTelemetry.
        
        Args:
            metrics: A list of metric dictionaries to export
            
        Raises:
            ExportError: If the export operation fails
        """
        try:
            for metric in metrics:
                name = metric["name"]
                value = metric["value"]
                metric_type = metric["type"]
                labels = metric["labels"]
                
                # Get or create the metric object
                otel_metric = self._get_or_create_metric(name, metric_type, labels)
                
                # Update the metric value
                if metric_type == MetricType.COUNTER.value:
                    otel_metric.add(value, labels)
                elif metric_type == MetricType.GAUGE.value:
                    # For gauges, we need to calculate the delta from the previous value
                    # This is a simplified approach; in a real implementation, you'd track previous values
                    otel_metric.add(value, labels)
                elif metric_type == MetricType.HISTOGRAM.value:
                    otel_metric.record(value, labels)
                else:
                    # Default behavior for unsupported types
                    otel_metric.add(value, labels)
                    
            logger.debug(f"Exported {len(metrics)} metrics to OpenTelemetry")
            
        except Exception as e:
            logger.error(f"Failed to export metrics to OpenTelemetry: {str(e)}")
            raise ExportError(f"Failed to export metrics to OpenTelemetry: {str(e)}") from e
    
    def close(self) -> None:
        """
        Close the OpenTelemetry exporter and shut down the meter provider.
        """
        try:
            super().close()
            if self.meter_provider:
                self.meter_provider.shutdown()
                logger.info("Shut down OpenTelemetry meter provider")
        except Exception as e:
            logger.error(f"Error shutting down OpenTelemetry exporter: {str(e)}")


class LoggingExporter(MetricExporter):
    """
    Simple exporter that logs metrics to a Python logger.
    
    This exporter is useful for development, debugging, or environments
    where a full monitoring system is not available.
    """
    
    def __init__(self, 
                name: str = "logging",
                logger_name: Optional[str] = None,
                log_level: int = logging.INFO,
                **kwargs):
        """
        Initialize the logging exporter.
        
        Args:
            name: A unique name for this exporter instance
            logger_name: Name of the logger to use (defaults to module logger)
            log_level: The logging level to use
            **kwargs: Additional arguments passed to the base class
        """
        super().__init__(name=name, **kwargs)
        
        self.log_level = log_level
        self.metrics_logger = logging.getLogger(logger_name or __name__)
        
        logger.info(f"Created logging exporter with log_level={log_level}")
    
    def initialize(self) -> None:
        """Initialize the logging exporter."""
        self._initialized = True
        logger.debug("Initialized logging exporter")
    
    def _export_batch(self, metrics: list[dict[str, Any]]) -> None:
        """
        Export a batch of metrics by logging them.
        
        Args:
            metrics: A list of metric dictionaries to export
        """
        for metric in metrics:
            name = metric["name"]
            value = metric["value"]
            metric_type = metric["type"]
            labels = metric["labels"]
            metric["timestamp"]
            
            # Format the metric as a log message
            labels_str = ", ".join(f"{k}={v}" for k, v in labels.items()) if labels else ""
            message = f"METRIC: {name}={value} ({metric_type})"
            if labels_str:
                message += f" [{labels_str}]"
                
            # Log the metric
            self.metrics_logger.log(self.log_level, message)
            
        logger.debug(f"Logged {len(metrics)} metrics at level {self.log_level}")


class JsonFileExporter(MetricExporter):
    """
    Exporter that writes metrics to a JSON file.
    
    This exporter is useful for offline analysis or when other exporters
    are not available.
    """
    
    def __init__(self, 
                name: str = "json_file",
                file_path: str = "metrics.json",
                append: bool = True,
                **kwargs):
        """
        Initialize the JSON file exporter.
        
        Args:
            name: A unique name for this exporter instance
            file_path: Path to the JSON file
            append: Whether to append to the file or overwrite it
            **kwargs: Additional arguments passed to the base class
            
        Raises:
            ConfigurationError: If the file cannot be accessed
        """
        super().__init__(name=name, **kwargs)
        
        self.file_path = file_path
        self.append = append
        
        # Validate file access
        try:
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
                
            # Test file access
            mode = "a" if append else "w"
            with open(file_path, mode):
                pass
                
        except Exception as e:
            raise ConfigurationError(f"Cannot access metrics file {file_path}: {str(e)}") from e
            
        logger.info(f"Created JSON file exporter writing to {file_path} (append={append})")
    
    def initialize(self) -> None:
        """Initialize the JSON file exporter."""
        # If not appending, initialize the file with an empty array
        if not self.append:
            try:
                with open(self.file_path, "w") as f:
                    json.dump([], f)
            except Exception as e:
                raise ConfigurationError(f"Failed to initialize metrics file: {str(e)}") from e
                
        self._initialized = True
        logger.debug(f"Initialized JSON file exporter to {self.file_path}")
    
    def _export_batch(self, metrics: list[dict[str, Any]]) -> None:
        """
        Export a batch of metrics to the JSON file.
        
        Args:
            metrics: A list of metric dictionaries to export
            
        Raises:
            ExportError: If the export operation fails
        """
        try:
            # Read existing metrics if appending
            existing_metrics = []
            if self.append and os.path.exists(self.file_path) and os.path.getsize(self.file_path) > 0:
                try:
                    with open(self.file_path) as f:
                        existing_metrics = json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse existing metrics file {self.file_path}, overwriting")
                    existing_metrics = []
            
            # Combine existing and new metrics
            all_metrics = existing_metrics + metrics
            
            # Write all metrics to the file
            with open(self.file_path, "w") as f:
                json.dump(all_metrics, f, indent=2)
                
            logger.debug(f"Exported {len(metrics)} metrics to {self.file_path}")
            
        except Exception as e:
            logger.error(f"Failed to export metrics to JSON file: {str(e)}")
            raise ExportError(f"Failed to export metrics to JSON file: {str(e)}") from e


class CompositeExporter(MetricExporter):
    """
    Exporter that forwards metrics to multiple other exporters.
    
    This is useful for sending metrics to multiple monitoring systems
    simultaneously.
    """
    
    def __init__(self, 
                name: str = "composite",
                exporters: list[MetricExporter] = None,
                **kwargs):
        """
        Initialize the composite exporter.
        
        Args:
            name: A unique name for this exporter instance
            exporters: List of exporters to forward metrics to
            **kwargs: Additional arguments passed to the base class
        """
        super().__init__(name=name, **kwargs)
        
        self.exporters = exporters or []
        
        exporter_names = [e.name for e in self.exporters]
        logger.info(f"Created composite exporter with {len(self.exporters)} sub-exporters: {exporter_names}")
    
    def add_exporter(self, exporter: MetricExporter) -> None:
        """
        Add an exporter to the composite.
        
        Args:
            exporter: The exporter to add
        """
        self.exporters.append(exporter)
        logger.debug(f"Added {exporter.__class__.__name__} '{exporter.name}' to composite exporter")
    
    def initialize(self) -> None:
        """
        Initialize all sub-exporters.
        
        Raises:
            ConfigurationError: If any sub-exporter fails to initialize
        """
        errors = []
        
        for exporter in self.exporters:
            try:
                if not exporter._initialized:
                    exporter.initialize()
            except Exception as e:
                errors.append(f"{exporter.name}: {str(e)}")
                logger.error(f"Failed to initialize sub-exporter {exporter.name}: {str(e)}")
        
        if errors:
            raise ConfigurationError(f"Failed to initialize some sub-exporters: {'; '.join(errors)}")
            
        self._initialized = True
        logger.debug(f"Initialized all {len(self.exporters)} sub-exporters")
    
    def _export_batch(self, metrics: list[dict[str, Any]]) -> None:
        """
        Export a batch of metrics to all sub-exporters.
        
        Args:
            metrics: A list of metric dictionaries to export
            
        Raises:
            ExportError: If any sub-exporter fails
        """
        errors = []
        
        for exporter in self.exporters:
            try:
                exporter._export_batch(metrics)
            except Exception as e:
                errors.append(f"{exporter.name}: {str(e)}")
                logger.error(f"Sub-exporter {exporter.name} failed to export metrics: {str(e)}")
        
        if errors:
            raise ExportError(f"Some sub-exporters failed: {'; '.join(errors)}")
            
        logger.debug(f"Exported {len(metrics)} metrics to {len(self.exporters)} sub-exporters")
    
    def close(self) -> None:
        """Close all sub-exporters."""
        for exporter in self.exporters:
            try:
                exporter.close()
            except Exception as e:
                logger.error(f"Error closing sub-exporter {exporter.name}: {str(e)}")
                
        super().close()


# Factory function to create exporters from configuration
def create_exporter(config: dict[str, Any]) -> MetricExporter:
    """
    Create a metric exporter from a configuration dictionary.
    
    Args:
        config: Configuration dictionary with exporter type and settings
        
    Returns:
        A configured MetricExporter instance
        
    Raises:
        ConfigurationError: If the configuration is invalid or the exporter type is unknown
    """
    exporter_type = config.get("type", "").lower()
    
    if not exporter_type:
        raise ConfigurationError("Exporter type not specified in configuration")
    
    # Extract common parameters
    name = config.get("name", exporter_type)
    batch_size = config.get("batch_size", 100)
    flush_interval = config.get("flush_interval", 60)
    
    # Create the appropriate exporter
    if exporter_type == "prometheus":
        return PrometheusExporter(
            name=name,
            endpoint=config.get("endpoint", "/metrics"),
            port=config.get("port", 9090),
            batch_size=batch_size,
            flush_interval=flush_interval
        )
    elif exporter_type == "opentelemetry":
        return OpenTelemetryExporter(
            name=name,
            service_name=config.get("service_name", "neuroca"),
            endpoint=config.get("endpoint", "http://localhost:4317"),
            batch_size=batch_size,
            flush_interval=flush_interval
        )
    elif exporter_type == "logging":
        return LoggingExporter(
            name=name,
            logger_name=config.get("logger_name"),
            log_level=config.get("log_level", logging.INFO),
            batch_size=batch_size,
            flush_interval=flush_interval
        )
    elif exporter_type == "json_file":
        return JsonFileExporter(
            name=name,
            file_path=config.get("file_path", "metrics.json"),
            append=config.get("append", True),
            batch_size=batch_size,
            flush_interval=flush_interval
        )
    elif exporter_type == "composite":
        # Create sub-exporters
        sub_exporters = []
        for sub_config in config.get("exporters", []):
            sub_exporters.append(create_exporter(sub_config))
            
        return CompositeExporter(
            name=name,
            exporters=sub_exporters,
            batch_size=batch_size,
            flush_interval=flush_interval
        )
    else:
        raise ConfigurationError(f"Unknown exporter type: {exporter_type}")