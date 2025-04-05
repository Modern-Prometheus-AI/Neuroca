"""
Health Check System for NeuroCognitive Architecture

This module provides a comprehensive health check system for monitoring the operational
status of various components within the NeuroCognitive Architecture. It implements
a flexible, extensible framework for defining, registering, and executing health checks
across the system.

The health check system supports:
- Component-level health checks (memory systems, LLM integrations, etc.)
- System-wide health status aggregation
- Customizable health check severity levels
- Detailed health check reporting
- Asynchronous health check execution
- Health check history and trending

Usage:
    # Register a health check
    memory_check = MemorySystemCheck(component="working_memory")
    health_registry.register(memory_check)
    
    # Run all health checks
    results = health_registry.run_all()
    
    # Get system health status
    status = health_registry.get_system_status()
"""

import asyncio
import datetime
import enum
import inspect
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

# Configure logger
logger = logging.getLogger(__name__)


class HealthStatus(enum.Enum):
    """
    Enumeration of possible health statuses for components and the overall system.
    """
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthCheckSeverity(enum.Enum):
    """
    Enumeration of health check severity levels to prioritize issues.
    """
    CRITICAL = "critical"  # System cannot function without this component
    HIGH = "high"          # Major functionality is impacted
    MEDIUM = "medium"      # Some functionality is impacted
    LOW = "low"            # Minor or cosmetic issues


@dataclass
class HealthCheckResult:
    """
    Data class representing the result of a health check execution.
    
    Attributes:
        check_id: Unique identifier for the health check
        component: The component being checked
        status: The health status determined by the check
        details: Additional details about the check result
        timestamp: When the check was performed
        duration_ms: How long the check took to execute
        severity: The severity level of this health check
        metadata: Additional contextual information
    """
    check_id: str
    component: str
    status: HealthStatus
    details: str = ""
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)
    duration_ms: float = 0.0
    severity: HealthCheckSeverity = HealthCheckSeverity.MEDIUM
    metadata: dict[str, Any] = field(default_factory=dict)


class HealthCheck(ABC):
    """
    Abstract base class for all health checks in the system.
    
    This class defines the interface that all health checks must implement
    and provides common functionality for health check execution.
    """
    
    def __init__(self, 
                 check_id: Optional[str] = None, 
                 component: str = "unknown",
                 severity: HealthCheckSeverity = HealthCheckSeverity.MEDIUM,
                 timeout_seconds: float = 10.0,
                 metadata: Optional[dict[str, Any]] = None):
        """
        Initialize a health check.
        
        Args:
            check_id: Unique identifier for this check (defaults to class name)
            component: Name of the component being checked
            severity: Severity level of this health check
            timeout_seconds: Maximum time allowed for check execution
            metadata: Additional contextual information
        """
        self.check_id = check_id or self.__class__.__name__
        self.component = component
        self.severity = severity
        self.timeout_seconds = timeout_seconds
        self.metadata = metadata or {}
        self._last_result: Optional[HealthCheckResult] = None
        
    @abstractmethod
    def check(self) -> HealthCheckResult:
        """
        Execute the health check and return a result.
        
        This method must be implemented by all concrete health check classes.
        
        Returns:
            HealthCheckResult: The result of the health check
            
        Raises:
            HealthCheckTimeoutError: If the check exceeds the timeout period
            HealthCheckExecutionError: If an error occurs during check execution
        """
        pass
    
    def execute(self) -> HealthCheckResult:
        """
        Execute the health check with timing and error handling.
        
        Returns:
            HealthCheckResult: The result of the health check
        """
        start_time = time.time()
        
        try:
            # Execute the check with timeout
            result = self._execute_with_timeout()
            
        except HealthCheckTimeoutError as e:
            logger.warning(f"Health check {self.check_id} timed out after {self.timeout_seconds}s")
            result = HealthCheckResult(
                check_id=self.check_id,
                component=self.component,
                status=HealthStatus.UNHEALTHY,
                details=f"Health check timed out: {str(e)}",
                severity=self.severity,
                metadata=self.metadata
            )
            
        except Exception as e:
            logger.exception(f"Error executing health check {self.check_id}")
            result = HealthCheckResult(
                check_id=self.check_id,
                component=self.component,
                status=HealthStatus.UNHEALTHY,
                details=f"Health check execution error: {str(e)}",
                severity=self.severity,
                metadata=self.metadata
            )
            
        finally:
            # Calculate duration and add to result
            duration_ms = (time.time() - start_time) * 1000
            result.duration_ms = duration_ms
            
        # Store the last result
        self._last_result = result
        return result
    
    def _execute_with_timeout(self) -> HealthCheckResult:
        """
        Execute the health check with a timeout.
        
        Returns:
            HealthCheckResult: The result of the health check
            
        Raises:
            HealthCheckTimeoutError: If the check exceeds the timeout period
        """
        if inspect.iscoroutinefunction(self.check):
            # Handle async health checks
            return asyncio.run(self._execute_async_with_timeout())
        
        # For synchronous checks, we'll use a simple approach
        # In a more sophisticated implementation, we might use threading
        result = self.check()
        return result
    
    async def _execute_async_with_timeout(self) -> HealthCheckResult:
        """
        Execute an async health check with a timeout.
        
        Returns:
            HealthCheckResult: The result of the health check
            
        Raises:
            HealthCheckTimeoutError: If the check exceeds the timeout period
        """
        try:
            result = await asyncio.wait_for(self.check(), timeout=self.timeout_seconds)
            return result
        except asyncio.TimeoutError:
            raise HealthCheckTimeoutError(
                f"Health check {self.check_id} timed out after {self.timeout_seconds} seconds"
            )
    
    @property
    def last_result(self) -> Optional[HealthCheckResult]:
        """Get the most recent result of this health check."""
        return self._last_result


class HealthCheckTimeoutError(Exception):
    """Exception raised when a health check exceeds its timeout period."""
    pass


class HealthCheckExecutionError(Exception):
    """Exception raised when a health check encounters an error during execution."""
    pass


class HealthCheckRegistry:
    """
    Registry for managing and executing health checks.
    
    This class provides functionality to register, unregister, and execute
    health checks, as well as to aggregate health check results into an
    overall system health status.
    """
    
    def __init__(self):
        """Initialize the health check registry."""
        self._checks: dict[str, HealthCheck] = {}
        self._check_history: dict[str, list[HealthCheckResult]] = {}
        self._history_limit: int = 100  # Maximum number of historical results to keep
    
    def register(self, check: HealthCheck) -> None:
        """
        Register a health check with the registry.
        
        Args:
            check: The health check to register
            
        Raises:
            ValueError: If a check with the same ID is already registered
        """
        if check.check_id in self._checks:
            raise ValueError(f"Health check with ID '{check.check_id}' is already registered")
        
        self._checks[check.check_id] = check
        self._check_history[check.check_id] = []
        logger.info(f"Registered health check: {check.check_id} for component {check.component}")
    
    def unregister(self, check_id: str) -> None:
        """
        Unregister a health check from the registry.
        
        Args:
            check_id: The ID of the health check to unregister
            
        Raises:
            KeyError: If no check with the given ID is registered
        """
        if check_id not in self._checks:
            raise KeyError(f"No health check with ID '{check_id}' is registered")
        
        del self._checks[check_id]
        del self._check_history[check_id]
        logger.info(f"Unregistered health check: {check_id}")
    
    def get_check(self, check_id: str) -> HealthCheck:
        """
        Get a registered health check by ID.
        
        Args:
            check_id: The ID of the health check to retrieve
            
        Returns:
            HealthCheck: The requested health check
            
        Raises:
            KeyError: If no check with the given ID is registered
        """
        if check_id not in self._checks:
            raise KeyError(f"No health check with ID '{check_id}' is registered")
        
        return self._checks[check_id]
    
    def run(self, check_id: str) -> HealthCheckResult:
        """
        Run a specific health check by ID.
        
        Args:
            check_id: The ID of the health check to run
            
        Returns:
            HealthCheckResult: The result of the health check
            
        Raises:
            KeyError: If no check with the given ID is registered
        """
        check = self.get_check(check_id)
        result = check.execute()
        
        # Store the result in history
        self._add_to_history(check_id, result)
        
        return result
    
    def run_all(self) -> dict[str, HealthCheckResult]:
        """
        Run all registered health checks.
        
        Returns:
            Dict[str, HealthCheckResult]: A dictionary mapping check IDs to results
        """
        results = {}
        
        for check_id, check in self._checks.items():
            try:
                result = check.execute()
                results[check_id] = result
                
                # Store the result in history
                self._add_to_history(check_id, result)
                
                logger.debug(f"Health check {check_id} completed with status: {result.status.value}")
                
            except Exception as e:
                logger.exception(f"Unexpected error running health check {check_id}")
                # Create a failure result
                result = HealthCheckResult(
                    check_id=check_id,
                    component=check.component,
                    status=HealthStatus.UNHEALTHY,
                    details=f"Unexpected error: {str(e)}",
                    severity=check.severity,
                    metadata=check.metadata
                )
                results[check_id] = result
                self._add_to_history(check_id, result)
        
        return results
    
    def run_for_component(self, component: str) -> dict[str, HealthCheckResult]:
        """
        Run all health checks for a specific component.
        
        Args:
            component: The name of the component to check
            
        Returns:
            Dict[str, HealthCheckResult]: A dictionary mapping check IDs to results
        """
        results = {}
        
        for check_id, check in self._checks.items():
            if check.component == component:
                try:
                    result = check.execute()
                    results[check_id] = result
                    self._add_to_history(check_id, result)
                    
                except Exception as e:
                    logger.exception(f"Unexpected error running health check {check_id}")
                    result = HealthCheckResult(
                        check_id=check_id,
                        component=check.component,
                        status=HealthStatus.UNHEALTHY,
                        details=f"Unexpected error: {str(e)}",
                        severity=check.severity,
                        metadata=check.metadata
                    )
                    results[check_id] = result
                    self._add_to_history(check_id, result)
        
        return results
    
    async def run_all_async(self) -> dict[str, HealthCheckResult]:
        """
        Run all registered health checks asynchronously.
        
        Returns:
            Dict[str, HealthCheckResult]: A dictionary mapping check IDs to results
        """
        tasks = []
        
        for check_id in self._checks:
            tasks.append(self._run_check_async(check_id))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        result_dict = {}
        for check_id, result in zip(self._checks.keys(), results):
            if isinstance(result, Exception):
                logger.exception(f"Async health check {check_id} failed", exc_info=result)
                # Create a failure result
                check = self._checks[check_id]
                error_result = HealthCheckResult(
                    check_id=check_id,
                    component=check.component,
                    status=HealthStatus.UNHEALTHY,
                    details=f"Async execution error: {str(result)}",
                    severity=check.severity,
                    metadata=check.metadata
                )
                result_dict[check_id] = error_result
                self._add_to_history(check_id, error_result)
            else:
                result_dict[check_id] = result
                self._add_to_history(check_id, result)
        
        return result_dict
    
    async def _run_check_async(self, check_id: str) -> HealthCheckResult:
        """
        Run a health check asynchronously.
        
        Args:
            check_id: The ID of the health check to run
            
        Returns:
            HealthCheckResult: The result of the health check
        """
        check = self._checks[check_id]
        return check.execute()
    
    def get_system_status(self) -> tuple[HealthStatus, dict[str, Any]]:
        """
        Get the overall system health status based on the most recent check results.
        
        The system status is determined by the most severe health check status:
        - If any CRITICAL check is UNHEALTHY, the system is UNHEALTHY
        - If any HIGH check is UNHEALTHY, the system is UNHEALTHY
        - If any MEDIUM check is UNHEALTHY, the system is DEGRADED
        - If any LOW check is UNHEALTHY, the system is DEGRADED
        - Otherwise, the system is HEALTHY
        
        Returns:
            Tuple[HealthStatus, Dict[str, Any]]: The overall system status and details
        """
        if not self._checks:
            return HealthStatus.UNKNOWN, {"details": "No health checks registered"}
        
        # Get the most recent result for each check
        latest_results = {}
        for check_id, check in self._checks.items():
            if check.last_result:
                latest_results[check_id] = check.last_result
        
        if not latest_results:
            return HealthStatus.UNKNOWN, {"details": "No health checks have been executed"}
        
        # Count checks by status and severity
        status_counts = {status: 0 for status in HealthStatus}
        critical_unhealthy = []
        high_unhealthy = []
        medium_unhealthy = []
        low_unhealthy = []
        
        for check_id, result in latest_results.items():
            status_counts[result.status] += 1
            
            if result.status == HealthStatus.UNHEALTHY:
                if result.severity == HealthCheckSeverity.CRITICAL:
                    critical_unhealthy.append(check_id)
                elif result.severity == HealthCheckSeverity.HIGH:
                    high_unhealthy.append(check_id)
                elif result.severity == HealthCheckSeverity.MEDIUM:
                    medium_unhealthy.append(check_id)
                elif result.severity == HealthCheckSeverity.LOW:
                    low_unhealthy.append(check_id)
        
        # Determine overall status
        overall_status = HealthStatus.HEALTHY
        details = {
            "total_checks": len(latest_results),
            "status_counts": {status.value: count for status, count in status_counts.items()},
            "unhealthy_checks": {
                "critical": critical_unhealthy,
                "high": high_unhealthy,
                "medium": medium_unhealthy,
                "low": low_unhealthy
            }
        }
        
        if critical_unhealthy or high_unhealthy:
            overall_status = HealthStatus.UNHEALTHY
            details["reason"] = "Critical or high severity checks failing"
        elif medium_unhealthy or low_unhealthy:
            overall_status = HealthStatus.DEGRADED
            details["reason"] = "Medium or low severity checks failing"
        
        return overall_status, details
    
    def get_component_status(self, component: str) -> tuple[HealthStatus, dict[str, Any]]:
        """
        Get the health status for a specific component.
        
        Args:
            component: The name of the component to check
            
        Returns:
            Tuple[HealthStatus, Dict[str, Any]]: The component status and details
        """
        # Find all checks for this component
        component_checks = {
            check_id: check for check_id, check in self._checks.items() 
            if check.component == component
        }
        
        if not component_checks:
            return HealthStatus.UNKNOWN, {"details": f"No health checks registered for component '{component}'"}
        
        # Get the most recent result for each check
        latest_results = {}
        for check_id, check in component_checks.items():
            if check.last_result:
                latest_results[check_id] = check.last_result
        
        if not latest_results:
            return HealthStatus.UNKNOWN, {"details": f"No health checks have been executed for component '{component}'"}
        
        # Apply the same logic as get_system_status but only for this component's checks
        status_counts = {status: 0 for status in HealthStatus}
        critical_unhealthy = []
        high_unhealthy = []
        medium_unhealthy = []
        low_unhealthy = []
        
        for check_id, result in latest_results.items():
            status_counts[result.status] += 1
            
            if result.status == HealthStatus.UNHEALTHY:
                if result.severity == HealthCheckSeverity.CRITICAL:
                    critical_unhealthy.append(check_id)
                elif result.severity == HealthCheckSeverity.HIGH:
                    high_unhealthy.append(check_id)
                elif result.severity == HealthCheckSeverity.MEDIUM:
                    medium_unhealthy.append(check_id)
                elif result.severity == HealthCheckSeverity.LOW:
                    low_unhealthy.append(check_id)
        
        # Determine overall status
        overall_status = HealthStatus.HEALTHY
        details = {
            "component": component,
            "total_checks": len(latest_results),
            "status_counts": {status.value: count for status, count in status_counts.items()},
            "unhealthy_checks": {
                "critical": critical_unhealthy,
                "high": high_unhealthy,
                "medium": medium_unhealthy,
                "low": low_unhealthy
            }
        }
        
        if critical_unhealthy or high_unhealthy:
            overall_status = HealthStatus.UNHEALTHY
            details["reason"] = "Critical or high severity checks failing"
        elif medium_unhealthy or low_unhealthy:
            overall_status = HealthStatus.DEGRADED
            details["reason"] = "Medium or low severity checks failing"
        
        return overall_status, details
    
    def _add_to_history(self, check_id: str, result: HealthCheckResult) -> None:
        """
        Add a health check result to the history.
        
        Args:
            check_id: The ID of the health check
            result: The result to add to history
        """
        history = self._check_history.get(check_id, [])
        history.append(result)
        
        # Trim history if it exceeds the limit
        if len(history) > self._history_limit:
            history = history[-self._history_limit:]
        
        self._check_history[check_id] = history
    
    def get_history(self, check_id: str) -> list[HealthCheckResult]:
        """
        Get the history of results for a specific health check.
        
        Args:
            check_id: The ID of the health check
            
        Returns:
            List[HealthCheckResult]: The history of results for the check
            
        Raises:
            KeyError: If no check with the given ID is registered
        """
        if check_id not in self._check_history:
            raise KeyError(f"No health check with ID '{check_id}' is registered")
        
        return self._check_history[check_id]
    
    def set_history_limit(self, limit: int) -> None:
        """
        Set the maximum number of historical results to keep for each check.
        
        Args:
            limit: The maximum number of results to keep
            
        Raises:
            ValueError: If the limit is not a positive integer
        """
        if not isinstance(limit, int) or limit <= 0:
            raise ValueError("History limit must be a positive integer")
        
        self._history_limit = limit
        
        # Trim existing histories if needed
        for check_id, history in self._check_history.items():
            if len(history) > limit:
                self._check_history[check_id] = history[-limit:]


# Common health check implementations

class DatabaseHealthCheck(HealthCheck):
    """
    Health check for database connectivity and performance.
    """
    
    def __init__(self, 
                 db_connection: Any,
                 query: str = "SELECT 1",
                 component: str = "database",
                 check_id: Optional[str] = None,
                 severity: HealthCheckSeverity = HealthCheckSeverity.CRITICAL,
                 timeout_seconds: float = 5.0):
        """
        Initialize a database health check.
        
        Args:
            db_connection: Database connection object
            query: Query to execute for the health check
            component: Name of the database component
            check_id: Unique identifier for this check
            severity: Severity level of this health check
            timeout_seconds: Maximum time allowed for check execution
        """
        super().__init__(
            check_id=check_id or f"DatabaseCheck_{component}",
            component=component,
            severity=severity,
            timeout_seconds=timeout_seconds
        )
        self.db_connection = db_connection
        self.query = query
    
    def check(self) -> HealthCheckResult:
        """
        Execute the database health check.
        
        Returns:
            HealthCheckResult: The result of the health check
        """
        try:
            # Execute the query
            # Note: This is a simplified example. In a real implementation,
            # you would use the appropriate method for your database connection.
            cursor = self.db_connection.cursor()
            cursor.execute(self.query)
            cursor.fetchone()
            cursor.close()
            
            return HealthCheckResult(
                check_id=self.check_id,
                component=self.component,
                status=HealthStatus.HEALTHY,
                details="Database connection is healthy",
                severity=self.severity,
                metadata=self.metadata
            )
            
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return HealthCheckResult(
                check_id=self.check_id,
                component=self.component,
                status=HealthStatus.UNHEALTHY,
                details=f"Database connection failed: {str(e)}",
                severity=self.severity,
                metadata=self.metadata
            )


class MemorySystemCheck(HealthCheck):
    """
    Health check for memory system components.
    """
    
    def __init__(self, 
                 memory_client: Any,
                 component: str = "memory_system",
                 check_id: Optional[str] = None,
                 severity: HealthCheckSeverity = HealthCheckSeverity.HIGH,
                 timeout_seconds: float = 5.0):
        """
        Initialize a memory system health check.
        
        Args:
            memory_client: Client for the memory system
            component: Name of the memory component
            check_id: Unique identifier for this check
            severity: Severity level of this health check
            timeout_seconds: Maximum time allowed for check execution
        """
        super().__init__(
            check_id=check_id or f"MemoryCheck_{component}",
            component=component,
            severity=severity,
            timeout_seconds=timeout_seconds
        )
        self.memory_client = memory_client
    
    def check(self) -> HealthCheckResult:
        """
        Execute the memory system health check.
        
        Returns:
            HealthCheckResult: The result of the health check
        """
        try:
            # Check memory system health
            # This is a placeholder - actual implementation would depend on the memory system
            is_healthy = self.memory_client.is_healthy()
            
            if is_healthy:
                return HealthCheckResult(
                    check_id=self.check_id,
                    component=self.component,
                    status=HealthStatus.HEALTHY,
                    details=f"Memory system {self.component} is healthy",
                    severity=self.severity,
                    metadata=self.metadata
                )
            else:
                return HealthCheckResult(
                    check_id=self.check_id,
                    component=self.component,
                    status=HealthStatus.UNHEALTHY,
                    details=f"Memory system {self.component} is unhealthy",
                    severity=self.severity,
                    metadata=self.metadata
                )
            
        except Exception as e:
            logger.error(f"Memory system health check failed: {str(e)}")
            return HealthCheckResult(
                check_id=self.check_id,
                component=self.component,
                status=HealthStatus.UNHEALTHY,
                details=f"Memory system check failed: {str(e)}",
                severity=self.severity,
                metadata=self.metadata
            )


class LLMIntegrationCheck(HealthCheck):
    """
    Health check for LLM integration components.
    """
    
    def __init__(self, 
                 llm_client: Any,
                 test_prompt: str = "Hello, world!",
                 component: str = "llm_integration",
                 check_id: Optional[str] = None,
                 severity: HealthCheckSeverity = HealthCheckSeverity.CRITICAL,
                 timeout_seconds: float = 10.0):
        """
        Initialize an LLM integration health check.
        
        Args:
            llm_client: Client for the LLM service
            test_prompt: Test prompt to send to the LLM
            component: Name of the LLM component
            check_id: Unique identifier for this check
            severity: Severity level of this health check
            timeout_seconds: Maximum time allowed for check execution
        """
        super().__init__(
            check_id=check_id or f"LLMCheck_{component}",
            component=component,
            severity=severity,
            timeout_seconds=timeout_seconds
        )
        self.llm_client = llm_client
        self.test_prompt = test_prompt
    
    async def check(self) -> HealthCheckResult:
        """
        Execute the LLM integration health check asynchronously.
        
        Returns:
            HealthCheckResult: The result of the health check
        """
        try:
            # Send a test prompt to the LLM
            # This is a placeholder - actual implementation would depend on the LLM client
            response = await self.llm_client.generate(self.test_prompt)
            
            if response and len(response) > 0:
                return HealthCheckResult(
                    check_id=self.check_id,
                    component=self.component,
                    status=HealthStatus.HEALTHY,
                    details=f"LLM integration {self.component} is responsive",
                    severity=self.severity,
                    metadata={"response_length": len(response)}
                )
            else:
                return HealthCheckResult(
                    check_id=self.check_id,
                    component=self.component,
                    status=HealthStatus.DEGRADED,
                    details=f"LLM integration {self.component} returned empty response",
                    severity=self.severity,
                    metadata={}
                )
            
        except Exception as e:
            logger.error(f"LLM integration health check failed: {str(e)}")
            return HealthCheckResult(
                check_id=self.check_id,
                component=self.component,
                status=HealthStatus.UNHEALTHY,
                details=f"LLM integration check failed: {str(e)}",
                severity=self.severity,
                metadata={}
            )


class ResourceUsageCheck(HealthCheck):
    """
    Health check for system resource usage (CPU, memory, disk).
    """
    
    def __init__(self, 
                 cpu_threshold: float = 90.0,
                 memory_threshold: float = 90.0,
                 disk_threshold: float = 90.0,
                 component: str = "system_resources",
                 check_id: Optional[str] = None,
                 severity: HealthCheckSeverity = HealthCheckSeverity.HIGH,
                 timeout_seconds: float = 5.0):
        """
        Initialize a resource usage health check.
        
        Args:
            cpu_threshold: CPU usage percentage threshold (0-100)
            memory_threshold: Memory usage percentage threshold (0-100)
            disk_threshold: Disk usage percentage threshold (0-100)
            component: Name of the component
            check_id: Unique identifier for this check
            severity: Severity level of this health check
            timeout_seconds: Maximum time allowed for check execution
        """
        super().__init__(
            check_id=check_id or f"ResourceCheck_{component}",
            component=component,
            severity=severity,
            timeout_seconds=timeout_seconds
        )
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.disk_threshold = disk_threshold
    
    def check(self) -> HealthCheckResult:
        """
        Execute the resource usage health check.
        
        Returns:
            HealthCheckResult: The result of the health check
        """
        try:
            # This is a placeholder - in a real implementation, you would use
            # a library like psutil to get actual resource usage
            
            # Simulate getting resource usage
            cpu_usage = 50.0  # Example value
            memory_usage = 60.0  # Example value
            disk_usage = 70.0  # Example value
            
            # Check against thresholds
            issues = []
            if cpu_usage > self.cpu_threshold:
                issues.append(f"CPU usage ({cpu_usage}%) exceeds threshold ({self.cpu_threshold}%)")
            
            if memory_usage > self.memory_threshold:
                issues.append(f"Memory usage ({memory_usage}%) exceeds threshold ({self.memory_threshold}%)")
            
            if disk_usage > self.disk_threshold:
                issues.append(f"Disk usage ({disk_usage}%) exceeds threshold ({self.disk_threshold}%)")
            
            # Determine status based on issues
            if issues:
                return HealthCheckResult(
                    check_id=self.check_id,
                    component=self.component,
                    status=HealthStatus.DEGRADED,
                    details="; ".join(issues),
                    severity=self.severity,
                    metadata={
                        "cpu_usage": cpu_usage,
                        "memory_usage": memory_usage,
                        "disk_usage": disk_usage
                    }
                )
            else:
                return HealthCheckResult(
                    check_id=self.check_id,
                    component=self.component,
                    status=HealthStatus.HEALTHY,
                    details="Resource usage within acceptable limits",
                    severity=self.severity,
                    metadata={
                        "cpu_usage": cpu_usage,
                        "memory_usage": memory_usage,
                        "disk_usage": disk_usage
                    }
                )
            
        except Exception as e:
            logger.error(f"Resource usage health check failed: {str(e)}")
            return HealthCheckResult(
                check_id=self.check_id,
                component=self.component,
                status=HealthStatus.UNKNOWN,
                details=f"Resource usage check failed: {str(e)}",
                severity=self.severity,
                metadata={}
            )


# Create a global health check registry
health_registry = HealthCheckRegistry()