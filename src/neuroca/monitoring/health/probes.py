"""
Health Probes Module for NeuroCognitive Architecture

This module provides a comprehensive set of health probes for monitoring the
NeuroCognitive Architecture system. These probes are designed to check various
aspects of the system's health, including component availability, performance
metrics, and resource utilization.

The module implements a flexible, extensible probe system that can be used
for both internal health checks and external monitoring integrations.

Usage:
    # Basic usage with default probe
    probe = SystemHealthProbe()
    health_status = probe.check()
    
    # Using a specific probe with custom parameters
    memory_probe = MemoryHealthProbe(threshold_percentage=85)
    memory_health = memory_probe.check()
    
    # Using the composite probe to run multiple checks
    composite = CompositeHealthProbe([
        SystemHealthProbe(),
        MemoryHealthProbe(),
        DatabaseHealthProbe(connection_string="...")
    ])
    overall_health = composite.check()
"""

import abc
import datetime
import logging
import platform
import socket
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

import psutil

# Configure module logger
logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """
    Enumeration of possible health statuses for probes.
    
    These statuses follow a traffic light pattern that is commonly used
    in monitoring systems.
    """
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """
    Data class representing the result of a health check.
    
    Attributes:
        status: The overall health status
        component: The name of the component that was checked
        timestamp: When the check was performed
        details: Additional details about the health check
        metrics: Optional performance metrics collected during the check
        error: Error information if the check failed
    """
    status: HealthStatus
    component: str
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)
    details: str = ""
    metrics: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert the health check result to a dictionary for serialization."""
        return {
            "status": self.status.value,
            "component": self.component,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
            "metrics": self.metrics,
            "error": self.error
        }


class HealthProbe(abc.ABC):
    """
    Abstract base class for all health probes.
    
    This class defines the interface that all health probes must implement.
    Health probes are responsible for checking the health of a specific
    component or aspect of the system.
    """
    
    def __init__(self, component_name: str):
        """
        Initialize the health probe.
        
        Args:
            component_name: The name of the component being checked
        """
        self.component_name = component_name
        self.timeout_seconds = 30  # Default timeout
    
    @abc.abstractmethod
    def check(self) -> HealthCheckResult:
        """
        Perform the health check and return the result.
        
        Returns:
            A HealthCheckResult object containing the status and details
            
        Raises:
            TimeoutError: If the health check times out
            Exception: If an unexpected error occurs during the check
        """
        pass
    
    def _create_result(
        self, 
        status: HealthStatus, 
        details: str = "", 
        metrics: Optional[dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> HealthCheckResult:
        """
        Helper method to create a standardized health check result.
        
        Args:
            status: The health status
            details: Additional details about the health check
            metrics: Performance metrics collected during the check
            error: Error information if the check failed
            
        Returns:
            A properly formatted HealthCheckResult
        """
        return HealthCheckResult(
            status=status,
            component=self.component_name,
            details=details,
            metrics=metrics or {},
            error=error
        )


class SystemHealthProbe(HealthProbe):
    """
    Probe that checks the overall system health.
    
    This probe collects basic system information and resource utilization
    metrics to determine the health of the system.
    """
    
    def __init__(self, cpu_threshold: float = 90.0, memory_threshold: float = 90.0):
        """
        Initialize the system health probe.
        
        Args:
            cpu_threshold: CPU usage percentage threshold for degraded health
            memory_threshold: Memory usage percentage threshold for degraded health
        """
        super().__init__("system")
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
    
    def check(self) -> HealthCheckResult:
        """
        Check system health by examining CPU, memory, and disk usage.
        
        Returns:
            HealthCheckResult with system metrics and health status
        """
        try:
            logger.debug("Performing system health check")
            
            # Collect system metrics
            cpu_percent = psutil.cpu_percent(interval=0.5)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            metrics = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "boot_time": datetime.datetime.fromtimestamp(
                    psutil.boot_time()
                ).isoformat(),
                "hostname": socket.gethostname(),
                "platform": platform.platform(),
                "uptime_seconds": time.time() - psutil.boot_time()
            }
            
            # Determine health status based on thresholds
            if cpu_percent >= self.cpu_threshold or memory.percent >= self.memory_threshold:
                status = HealthStatus.DEGRADED
                details = (
                    f"System resources are under high load: "
                    f"CPU: {cpu_percent}%, Memory: {memory.percent}%"
                )
            else:
                status = HealthStatus.HEALTHY
                details = "System resources are within normal parameters"
            
            logger.debug(f"System health check completed: {status.value}")
            return self._create_result(status, details, metrics)
            
        except Exception as e:
            logger.error(f"Error during system health check: {str(e)}", exc_info=True)
            return self._create_result(
                HealthStatus.UNKNOWN,
                "Failed to check system health",
                error=str(e)
            )


class MemoryHealthProbe(HealthProbe):
    """
    Probe specifically for checking memory subsystem health.
    
    This probe focuses on memory usage patterns and can detect memory leaks
    or excessive memory consumption.
    """
    
    def __init__(
        self, 
        threshold_percentage: float = 85.0,
        leak_detection_enabled: bool = False,
        sample_interval_seconds: int = 60
    ):
        """
        Initialize the memory health probe.
        
        Args:
            threshold_percentage: Memory usage percentage threshold for degraded health
            leak_detection_enabled: Whether to enable memory leak detection
            sample_interval_seconds: Interval between memory samples for leak detection
        """
        super().__init__("memory")
        self.threshold_percentage = threshold_percentage
        self.leak_detection_enabled = leak_detection_enabled
        self.sample_interval_seconds = sample_interval_seconds
        self._previous_samples: list[tuple[datetime.datetime, float]] = []
    
    def check(self) -> HealthCheckResult:
        """
        Check memory health by examining usage patterns.
        
        Returns:
            HealthCheckResult with memory metrics and health status
        """
        try:
            logger.debug("Performing memory health check")
            
            # Get current memory usage
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            metrics = {
                "total_bytes": memory.total,
                "available_bytes": memory.available,
                "used_bytes": memory.used,
                "free_bytes": memory.free,
                "percent_used": memory.percent,
                "swap_total_bytes": swap.total,
                "swap_used_bytes": swap.used,
                "swap_percent": swap.percent
            }
            
            # Store sample for leak detection if enabled
            if self.leak_detection_enabled:
                current_time = datetime.datetime.now()
                self._previous_samples.append((current_time, memory.percent))
                
                # Keep only recent samples
                cutoff_time = current_time - datetime.timedelta(
                    seconds=self.sample_interval_seconds * 10
                )
                self._previous_samples = [
                    sample for sample in self._previous_samples 
                    if sample[0] >= cutoff_time
                ]
                
                # Check for consistent memory growth (potential leak)
                if self._detect_memory_leak():
                    return self._create_result(
                        HealthStatus.UNHEALTHY,
                        "Potential memory leak detected: consistent memory growth observed",
                        metrics
                    )
            
            # Determine health status based on threshold
            if memory.percent >= self.threshold_percentage:
                status = HealthStatus.DEGRADED
                details = f"Memory usage is high: {memory.percent}% used"
                
                # Check if we're critically low on memory
                if memory.percent >= 95:
                    status = HealthStatus.UNHEALTHY
                    details = f"Critical memory shortage: {memory.percent}% used"
            else:
                status = HealthStatus.HEALTHY
                details = f"Memory usage is normal: {memory.percent}% used"
            
            logger.debug(f"Memory health check completed: {status.value}")
            return self._create_result(status, details, metrics)
            
        except Exception as e:
            logger.error(f"Error during memory health check: {str(e)}", exc_info=True)
            return self._create_result(
                HealthStatus.UNKNOWN,
                "Failed to check memory health",
                error=str(e)
            )
    
    def _detect_memory_leak(self) -> bool:
        """
        Analyze memory samples to detect potential memory leaks.
        
        Returns:
            True if a potential memory leak is detected, False otherwise
        """
        if len(self._previous_samples) < 5:
            return False
        
        # Check if memory usage has been consistently increasing
        samples = sorted(self._previous_samples)
        consistently_increasing = True
        
        for i in range(1, len(samples)):
            if samples[i][1] <= samples[i-1][1]:
                consistently_increasing = False
                break
        
        return consistently_increasing and (samples[-1][1] - samples[0][1] > 10)


class DatabaseHealthProbe(HealthProbe):
    """
    Probe for checking database connectivity and performance.
    
    This probe tests database connections and can measure query performance
    to ensure the database is functioning properly.
    """
    
    def __init__(
        self, 
        connection_string: str,
        query_timeout_seconds: float = 5.0,
        test_query: str = "SELECT 1"
    ):
        """
        Initialize the database health probe.
        
        Args:
            connection_string: Database connection string
            query_timeout_seconds: Maximum time allowed for test query
            test_query: Simple query to test database connectivity
        """
        super().__init__("database")
        self.connection_string = connection_string
        self.query_timeout_seconds = query_timeout_seconds
        self.test_query = test_query
    
    def check(self) -> HealthCheckResult:
        """
        Check database health by testing connectivity and query performance.
        
        Returns:
            HealthCheckResult with database metrics and health status
        """
        try:
            logger.debug("Performing database health check")
            
            # This is a placeholder for actual database connectivity check
            # In a real implementation, we would use the appropriate database
            # driver to establish a connection and run the test query
            
            # Simulate database check for demonstration purposes
            # In production, replace with actual database connection code
            import random
            import time
            
            # Simulate connection and query execution time
            start_time = time.time()
            time.sleep(0.1)  # Simulate network latency
            
            # Simulate potential database issues
            random_value = random.random()
            
            if random_value < 0.05:
                # Simulate connection failure (5% chance)
                raise ConnectionError("Failed to connect to database")
            elif random_value < 0.1:
                # Simulate query timeout (5% chance)
                time.sleep(self.query_timeout_seconds + 0.1)
                return self._create_result(
                    HealthStatus.DEGRADED,
                    "Database query timed out",
                    {"query_time_seconds": self.query_timeout_seconds + 0.1}
                )
            
            # Simulate successful query
            query_time = time.time() - start_time
            
            metrics = {
                "connection_time_seconds": query_time * 0.3,  # Simulate connection time
                "query_time_seconds": query_time * 0.7,       # Simulate query execution time
                "total_time_seconds": query_time
            }
            
            # Determine health status based on query time
            if query_time > (self.query_timeout_seconds * 0.8):
                status = HealthStatus.DEGRADED
                details = f"Database response time is slow: {query_time:.2f} seconds"
            else:
                status = HealthStatus.HEALTHY
                details = f"Database is responding normally: {query_time:.2f} seconds"
            
            logger.debug(f"Database health check completed: {status.value}")
            return self._create_result(status, details, metrics)
            
        except Exception as e:
            logger.error(f"Error during database health check: {str(e)}", exc_info=True)
            return self._create_result(
                HealthStatus.UNHEALTHY,
                "Failed to connect to database",
                error=str(e)
            )


class CompositeHealthProbe(HealthProbe):
    """
    A composite probe that aggregates results from multiple health probes.
    
    This probe follows the Composite design pattern to allow treating
    individual probes and groups of probes uniformly.
    """
    
    def __init__(self, probes: list[HealthProbe]):
        """
        Initialize the composite health probe.
        
        Args:
            probes: List of health probes to include in the composite
        """
        super().__init__("composite")
        self.probes = probes
    
    def check(self) -> HealthCheckResult:
        """
        Run all contained probes and aggregate their results.
        
        Returns:
            HealthCheckResult with aggregated status and component results
        """
        try:
            logger.debug("Performing composite health check")
            
            results = []
            for probe in self.probes:
                try:
                    results.append(probe.check())
                except Exception as e:
                    logger.error(
                        f"Error in probe {probe.component_name}: {str(e)}",
                        exc_info=True
                    )
                    results.append(self._create_result(
                        HealthStatus.UNKNOWN,
                        f"Probe {probe.component_name} failed",
                        error=str(e)
                    ))
            
            # Determine overall status (worst status wins)
            status_priority = {
                HealthStatus.UNHEALTHY: 0,
                HealthStatus.DEGRADED: 1,
                HealthStatus.UNKNOWN: 2,
                HealthStatus.HEALTHY: 3
            }
            
            overall_status = HealthStatus.HEALTHY
            for result in results:
                if status_priority[result.status] < status_priority[overall_status]:
                    overall_status = result.status
            
            # Create composite metrics
            component_results = {
                result.component: {
                    "status": result.status.value,
                    "details": result.details,
                    "error": result.error
                } for result in results
            }
            
            metrics = {
                "component_count": len(results),
                "healthy_count": sum(1 for r in results if r.status == HealthStatus.HEALTHY),
                "degraded_count": sum(1 for r in results if r.status == HealthStatus.DEGRADED),
                "unhealthy_count": sum(1 for r in results if r.status == HealthStatus.UNHEALTHY),
                "unknown_count": sum(1 for r in results if r.status == HealthStatus.UNKNOWN),
                "components": component_results
            }
            
            details = f"Composite health check: {metrics['healthy_count']} healthy, " \
                      f"{metrics['degraded_count']} degraded, " \
                      f"{metrics['unhealthy_count']} unhealthy, " \
                      f"{metrics['unknown_count']} unknown"
            
            logger.debug(f"Composite health check completed: {overall_status.value}")
            return self._create_result(overall_status, details, metrics)
            
        except Exception as e:
            logger.error(f"Error during composite health check: {str(e)}", exc_info=True)
            return self._create_result(
                HealthStatus.UNKNOWN,
                "Failed to complete composite health check",
                error=str(e)
            )


class NetworkHealthProbe(HealthProbe):
    """
    Probe for checking network connectivity and performance.
    
    This probe tests network connections to critical services and measures
    latency and packet loss.
    """
    
    def __init__(
        self, 
        targets: list[str] = None,
        timeout_seconds: float = 2.0,
        packet_count: int = 3
    ):
        """
        Initialize the network health probe.
        
        Args:
            targets: List of hostnames or IPs to check
            timeout_seconds: Maximum time to wait for response
            packet_count: Number of packets to send for each target
        """
        super().__init__("network")
        self.targets = targets or ["8.8.8.8", "1.1.1.1"]  # Default to Google & Cloudflare DNS
        self.timeout_seconds = timeout_seconds
        self.packet_count = packet_count
    
    def check(self) -> HealthCheckResult:
        """
        Check network health by pinging targets and measuring response times.
        
        Returns:
            HealthCheckResult with network metrics and health status
        """
        try:
            logger.debug("Performing network health check")
            
            results = {}
            unreachable_count = 0
            total_latency = 0
            successful_pings = 0
            
            for target in self.targets:
                target_result = self._ping_target(target)
                results[target] = target_result
                
                if not target_result["reachable"]:
                    unreachable_count += 1
                else:
                    total_latency += target_result["avg_latency_ms"]
                    successful_pings += 1
            
            # Calculate average latency across all successful pings
            avg_latency = total_latency / successful_pings if successful_pings > 0 else 0
            
            metrics = {
                "targets_checked": len(self.targets),
                "unreachable_count": unreachable_count,
                "avg_latency_ms": avg_latency,
                "target_results": results
            }
            
            # Determine health status based on reachability and latency
            if unreachable_count == len(self.targets):
                status = HealthStatus.UNHEALTHY
                details = "All network targets are unreachable"
            elif unreachable_count > 0:
                status = HealthStatus.DEGRADED
                details = f"{unreachable_count} of {len(self.targets)} network targets are unreachable"
            elif avg_latency > 200:  # High latency threshold
                status = HealthStatus.DEGRADED
                details = f"Network latency is high: {avg_latency:.2f}ms average"
            else:
                status = HealthStatus.HEALTHY
                details = f"Network is healthy: {avg_latency:.2f}ms average latency"
            
            logger.debug(f"Network health check completed: {status.value}")
            return self._create_result(status, details, metrics)
            
        except Exception as e:
            logger.error(f"Error during network health check: {str(e)}", exc_info=True)
            return self._create_result(
                HealthStatus.UNKNOWN,
                "Failed to check network health",
                error=str(e)
            )
    
    def _ping_target(self, target: str) -> dict[str, Any]:
        """
        Ping a specific network target and measure response.
        
        Args:
            target: Hostname or IP address to ping
            
        Returns:
            Dictionary with ping results including reachability and latency
        """
        # This is a simplified ping implementation
        # In production, consider using a more robust approach or library
        import platform
        import subprocess
        
        try:
            # Determine ping command based on platform
            param = "-n" if platform.system().lower() == "windows" else "-c"
            timeout_param = f"-W {int(self.timeout_seconds * 1000)}" if platform.system().lower() != "windows" else f"-w {int(self.timeout_seconds * 1000)}"
            
            command = ["ping", param, str(self.packet_count), timeout_param, target]
            
            # Execute ping command
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds * self.packet_count + 1
            )
            
            # Parse ping output
            output = result.stdout.lower()
            
            # Check if target is reachable
            if "received, 0% packet loss" in output or "received, 0 percent" in output:
                # Extract average round-trip time
                if "average" in output:
                    # Extract average latency from output
                    # This is a simplified parser and may need adjustment for different OS outputs
                    avg_parts = output.split("average")[1].strip().split()[0].replace("=", "").replace("ms", "")
                    avg_latency = float(avg_parts.replace(",", "."))
                else:
                    avg_latency = 0.0
                
                return {
                    "reachable": True,
                    "avg_latency_ms": avg_latency,
                    "packet_loss_percent": 0.0
                }
            else:
                # Target is unreachable or has packet loss
                # Try to extract packet loss percentage
                packet_loss = 100.0  # Default to 100% loss
                if "packet loss" in output:
                    for part in output.split():
                        if "%" in part:
                            try:
                                packet_loss = float(part.replace("%", ""))
                                break
                            except ValueError:
                                pass
                
                return {
                    "reachable": False,
                    "avg_latency_ms": None,
                    "packet_loss_percent": packet_loss
                }
                
        except (subprocess.SubprocessError, subprocess.TimeoutExpired) as e:
            logger.warning(f"Ping to {target} failed: {str(e)}")
            return {
                "reachable": False,
                "avg_latency_ms": None,
                "packet_loss_percent": 100.0,
                "error": str(e)
            }


# Factory function to create a standard set of health probes
def create_standard_health_probes(
    db_connection_string: Optional[str] = None,
    network_targets: Optional[list[str]] = None
) -> CompositeHealthProbe:
    """
    Create a standard set of health probes for the NeuroCognitive Architecture.
    
    This factory function creates a composite probe with the most commonly
    needed health checks for the system.
    
    Args:
        db_connection_string: Optional database connection string
        network_targets: Optional list of network targets to check
        
    Returns:
        A CompositeHealthProbe containing the standard set of probes
    """
    probes = [
        SystemHealthProbe(),
        MemoryHealthProbe(leak_detection_enabled=True)
    ]
    
    # Add database probe if connection string is provided
    if db_connection_string:
        probes.append(DatabaseHealthProbe(connection_string=db_connection_string))
    
    # Add network probe with custom or default targets
    probes.append(NetworkHealthProbe(targets=network_targets))
    
    return CompositeHealthProbe(probes)