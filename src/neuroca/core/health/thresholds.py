"""
Threshold Management for NeuroCognitive Architecture Health Monitoring.

This module provides a comprehensive framework for defining, validating, and managing
thresholds for various health metrics within the NeuroCognitive Architecture system.
Thresholds are used to determine when health metrics indicate potential issues that
require attention, intervention, or adaptation within the system.

The module supports:
- Multiple threshold types (absolute, relative, adaptive)
- Threshold validation and enforcement
- Threshold crossing detection and notification
- Threshold persistence and retrieval
- Dynamic threshold adjustment based on system behavior

Usage Examples:
    # Create a simple threshold
    cpu_threshold = AbsoluteThreshold(
        metric_name="cpu_usage",
        warning_level=70.0,
        critical_level=90.0,
        units="%"
    )
    
    # Check if a value crosses the threshold
    status = cpu_threshold.check_value(85.0)
    if status == ThresholdStatus.WARNING:
        logger.warning(f"CPU usage approaching critical levels: {status.detail}")
        
    # Create an adaptive threshold that adjusts based on historical data
    memory_threshold = AdaptiveThreshold(
        metric_name="memory_usage",
        base_warning_level=75.0,
        base_critical_level=95.0,
        adaptation_window=timedelta(hours=24),
        adaptation_factor=0.1
    )
"""

import enum
import json
import logging
import math
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional

# Configure module logger
logger = logging.getLogger(__name__)


class ThresholdStatus(enum.Enum):
    """
    Enumeration of possible threshold status values.
    
    Represents the current status of a metric relative to its defined thresholds.
    """
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class ThresholdResult:
    """
    Represents the result of a threshold check.
    
    Contains the status, the value that was checked, and additional details
    about the threshold crossing.
    """
    status: ThresholdStatus
    value: float
    threshold_name: str
    detail: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert the threshold result to a dictionary for serialization."""
        result = asdict(self)
        result["status"] = self.status.value
        result["timestamp"] = self.timestamp.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'ThresholdResult':
        """Create a ThresholdResult instance from a dictionary."""
        status = ThresholdStatus(data.pop("status"))
        timestamp = datetime.fromisoformat(data.pop("timestamp"))
        return cls(status=status, timestamp=timestamp, **data)


class Threshold(ABC):
    """
    Abstract base class for all threshold types.
    
    Defines the common interface and functionality for threshold implementations.
    """
    
    def __init__(
        self,
        metric_name: str,
        description: str = "",
        units: str = "",
        enabled: bool = True
    ):
        """
        Initialize a threshold.
        
        Args:
            metric_name: The name of the metric this threshold applies to
            description: Optional description of the threshold's purpose
            units: The units of measurement for the metric (e.g., "%", "MB", "ms")
            enabled: Whether this threshold is currently active
        """
        self.metric_name = metric_name
        self.description = description
        self.units = units
        self.enabled = enabled
        self.last_check: Optional[ThresholdResult] = None
        
        logger.debug(f"Initialized {self.__class__.__name__} for metric '{metric_name}'")
    
    @abstractmethod
    def check_value(self, value: float) -> ThresholdResult:
        """
        Check if a value crosses the threshold.
        
        Args:
            value: The metric value to check against the threshold
            
        Returns:
            A ThresholdResult object indicating the status and details
        """
        pass
    
    def to_dict(self) -> dict[str, Any]:
        """Convert the threshold to a dictionary for serialization."""
        result = {
            "type": self.__class__.__name__,
            "metric_name": self.metric_name,
            "description": self.description,
            "units": self.units,
            "enabled": self.enabled,
        }
        
        if self.last_check:
            result["last_check"] = self.last_check.to_dict()
            
        return result
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'Threshold':
        """
        Create a Threshold instance from a dictionary.
        
        This method should be implemented by subclasses to handle their specific
        attributes. The base implementation handles common attributes.
        """
        raise NotImplementedError("Subclasses must implement from_dict")


class AbsoluteThreshold(Threshold):
    """
    A threshold with fixed warning and critical levels.
    
    This is the simplest form of threshold, where the warning and critical
    levels are fixed values.
    """
    
    def __init__(
        self,
        metric_name: str,
        warning_level: float,
        critical_level: float,
        description: str = "",
        units: str = "",
        enabled: bool = True,
        is_lower_bound: bool = False
    ):
        """
        Initialize an absolute threshold.
        
        Args:
            metric_name: The name of the metric this threshold applies to
            warning_level: The value at which a warning status is triggered
            critical_level: The value at which a critical status is triggered
            description: Optional description of the threshold's purpose
            units: The units of measurement for the metric
            enabled: Whether this threshold is currently active
            is_lower_bound: If True, values below the threshold are concerning;
                           if False, values above the threshold are concerning
        
        Raises:
            ValueError: If warning and critical levels are inconsistent with is_lower_bound
        """
        super().__init__(metric_name, description, units, enabled)
        
        # Validate threshold levels based on whether this is a lower or upper bound
        if is_lower_bound and warning_level < critical_level:
            raise ValueError(
                f"For lower bound thresholds, warning_level ({warning_level}) must be "
                f"greater than or equal to critical_level ({critical_level})"
            )
        elif not is_lower_bound and warning_level > critical_level:
            raise ValueError(
                f"For upper bound thresholds, warning_level ({warning_level}) must be "
                f"less than or equal to critical_level ({critical_level})"
            )
        
        self.warning_level = warning_level
        self.critical_level = critical_level
        self.is_lower_bound = is_lower_bound
        
        logger.debug(
            f"Created {self.__class__.__name__} for '{metric_name}': "
            f"warning={warning_level}{units}, critical={critical_level}{units}, "
            f"{'lower' if is_lower_bound else 'upper'} bound"
        )
    
    def check_value(self, value: float) -> ThresholdResult:
        """
        Check if a value crosses the threshold.
        
        Args:
            value: The metric value to check against the threshold
            
        Returns:
            A ThresholdResult object indicating the status and details
        """
        if not self.enabled:
            result = ThresholdResult(
                status=ThresholdStatus.UNKNOWN,
                value=value,
                threshold_name=self.metric_name,
                detail="Threshold check disabled"
            )
            self.last_check = result
            return result
        
        if math.isnan(value):
            result = ThresholdResult(
                status=ThresholdStatus.UNKNOWN,
                value=value,
                threshold_name=self.metric_name,
                detail="Value is NaN"
            )
            self.last_check = result
            return result
        
        # Determine status based on whether this is a lower or upper bound
        if self.is_lower_bound:
            if value <= self.critical_level:
                status = ThresholdStatus.CRITICAL
                detail = (f"Value {value}{self.units} is below critical level "
                          f"({self.critical_level}{self.units})")
            elif value <= self.warning_level:
                status = ThresholdStatus.WARNING
                detail = (f"Value {value}{self.units} is below warning level "
                          f"({self.warning_level}{self.units})")
            else:
                status = ThresholdStatus.NORMAL
                detail = (f"Value {value}{self.units} is above warning level "
                          f"({self.warning_level}{self.units})")
        else:
            if value >= self.critical_level:
                status = ThresholdStatus.CRITICAL
                detail = (f"Value {value}{self.units} exceeds critical level "
                          f"({self.critical_level}{self.units})")
            elif value >= self.warning_level:
                status = ThresholdStatus.WARNING
                detail = (f"Value {value}{self.units} exceeds warning level "
                          f"({self.warning_level}{self.units})")
            else:
                status = ThresholdStatus.NORMAL
                detail = (f"Value {value}{self.units} is below warning level "
                          f"({self.warning_level}{self.units})")
        
        result = ThresholdResult(
            status=status,
            value=value,
            threshold_name=self.metric_name,
            detail=detail
        )
        self.last_check = result
        
        if status != ThresholdStatus.NORMAL:
            logger.info(f"Threshold crossed for {self.metric_name}: {detail}")
        
        return result
    
    def to_dict(self) -> dict[str, Any]:
        """Convert the threshold to a dictionary for serialization."""
        result = super().to_dict()
        result.update({
            "warning_level": self.warning_level,
            "critical_level": self.critical_level,
            "is_lower_bound": self.is_lower_bound
        })
        return result
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'AbsoluteThreshold':
        """Create an AbsoluteThreshold instance from a dictionary."""
        last_check_data = data.pop("last_check", None)
        threshold = cls(**{k: v for k, v in data.items() if k != "type"})
        
        if last_check_data:
            threshold.last_check = ThresholdResult.from_dict(last_check_data)
            
        return threshold


class RelativeThreshold(Threshold):
    """
    A threshold defined relative to a baseline value.
    
    This threshold type is useful for metrics where the absolute value
    varies widely, but deviations from a baseline are significant.
    """
    
    def __init__(
        self,
        metric_name: str,
        baseline: float,
        warning_percent: float,
        critical_percent: float,
        description: str = "",
        units: str = "",
        enabled: bool = True,
        is_lower_bound: bool = False
    ):
        """
        Initialize a relative threshold.
        
        Args:
            metric_name: The name of the metric this threshold applies to
            baseline: The baseline value to compare against
            warning_percent: The percentage deviation that triggers a warning
            critical_percent: The percentage deviation that triggers a critical alert
            description: Optional description of the threshold's purpose
            units: The units of measurement for the metric
            enabled: Whether this threshold is currently active
            is_lower_bound: If True, values below the threshold are concerning;
                           if False, values above the threshold are concerning
                           
        Raises:
            ValueError: If baseline is zero or if warning and critical percentages are inconsistent
        """
        super().__init__(metric_name, description, units, enabled)
        
        if baseline == 0:
            raise ValueError("Baseline cannot be zero for relative thresholds")
        
        # Validate threshold percentages
        if is_lower_bound and warning_percent > critical_percent:
            raise ValueError(
                f"For lower bound thresholds, warning_percent ({warning_percent}) must be "
                f"less than or equal to critical_percent ({critical_percent})"
            )
        elif not is_lower_bound and warning_percent < critical_percent:
            raise ValueError(
                f"For upper bound thresholds, warning_percent ({warning_percent}) must be "
                f"greater than or equal to critical_percent ({critical_percent})"
            )
        
        self.baseline = baseline
        self.warning_percent = warning_percent
        self.critical_percent = critical_percent
        self.is_lower_bound = is_lower_bound
        
        logger.debug(
            f"Created {self.__class__.__name__} for '{metric_name}': "
            f"baseline={baseline}{units}, warning={warning_percent}%, "
            f"critical={critical_percent}%, {'lower' if is_lower_bound else 'upper'} bound"
        )
    
    def check_value(self, value: float) -> ThresholdResult:
        """
        Check if a value crosses the threshold.
        
        Args:
            value: The metric value to check against the threshold
            
        Returns:
            A ThresholdResult object indicating the status and details
        """
        if not self.enabled:
            result = ThresholdResult(
                status=ThresholdStatus.UNKNOWN,
                value=value,
                threshold_name=self.metric_name,
                detail="Threshold check disabled"
            )
            self.last_check = result
            return result
        
        if math.isnan(value) or math.isnan(self.baseline):
            result = ThresholdResult(
                status=ThresholdStatus.UNKNOWN,
                value=value,
                threshold_name=self.metric_name,
                detail="Value or baseline is NaN"
            )
            self.last_check = result
            return result
        
        # Calculate percentage deviation from baseline
        percent_change = ((value - self.baseline) / abs(self.baseline)) * 100
        
        # Determine status based on whether this is a lower or upper bound
        if self.is_lower_bound:
            if percent_change <= -self.critical_percent:
                status = ThresholdStatus.CRITICAL
                detail = (f"Value {value}{self.units} is {abs(percent_change):.2f}% below baseline "
                          f"({self.baseline}{self.units}), exceeding critical threshold of {self.critical_percent}%")
            elif percent_change <= -self.warning_percent:
                status = ThresholdStatus.WARNING
                detail = (f"Value {value}{self.units} is {abs(percent_change):.2f}% below baseline "
                          f"({self.baseline}{self.units}), exceeding warning threshold of {self.warning_percent}%")
            else:
                status = ThresholdStatus.NORMAL
                detail = (f"Value {value}{self.units} is within normal range of baseline "
                          f"({self.baseline}{self.units})")
        else:
            if percent_change >= self.critical_percent:
                status = ThresholdStatus.CRITICAL
                detail = (f"Value {value}{self.units} is {percent_change:.2f}% above baseline "
                          f"({self.baseline}{self.units}), exceeding critical threshold of {self.critical_percent}%")
            elif percent_change >= self.warning_percent:
                status = ThresholdStatus.WARNING
                detail = (f"Value {value}{self.units} is {percent_change:.2f}% above baseline "
                          f"({self.baseline}{self.units}), exceeding warning threshold of {self.warning_percent}%")
            else:
                status = ThresholdStatus.NORMAL
                detail = (f"Value {value}{self.units} is within normal range of baseline "
                          f"({self.baseline}{self.units})")
        
        result = ThresholdResult(
            status=status,
            value=value,
            threshold_name=self.metric_name,
            detail=detail
        )
        self.last_check = result
        
        if status != ThresholdStatus.NORMAL:
            logger.info(f"Threshold crossed for {self.metric_name}: {detail}")
        
        return result
    
    def to_dict(self) -> dict[str, Any]:
        """Convert the threshold to a dictionary for serialization."""
        result = super().to_dict()
        result.update({
            "baseline": self.baseline,
            "warning_percent": self.warning_percent,
            "critical_percent": self.critical_percent,
            "is_lower_bound": self.is_lower_bound
        })
        return result
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'RelativeThreshold':
        """Create a RelativeThreshold instance from a dictionary."""
        last_check_data = data.pop("last_check", None)
        threshold = cls(**{k: v for k, v in data.items() if k != "type"})
        
        if last_check_data:
            threshold.last_check = ThresholdResult.from_dict(last_check_data)
            
        return threshold


class AdaptiveThreshold(Threshold):
    """
    A threshold that adapts based on historical data.
    
    This threshold type adjusts its warning and critical levels based on
    the observed behavior of the metric over time, making it useful for
    metrics with seasonal or cyclical patterns.
    """
    
    def __init__(
        self,
        metric_name: str,
        base_warning_level: float,
        base_critical_level: float,
        adaptation_window: timedelta,
        adaptation_factor: float = 0.1,
        description: str = "",
        units: str = "",
        enabled: bool = True,
        is_lower_bound: bool = False,
        history_size: int = 100
    ):
        """
        Initialize an adaptive threshold.
        
        Args:
            metric_name: The name of the metric this threshold applies to
            base_warning_level: The initial warning level
            base_critical_level: The initial critical level
            adaptation_window: The time window over which to adapt the threshold
            adaptation_factor: How quickly the threshold adapts (0-1)
            description: Optional description of the threshold's purpose
            units: The units of measurement for the metric
            enabled: Whether this threshold is currently active
            is_lower_bound: If True, values below the threshold are concerning
            history_size: Maximum number of historical values to store
            
        Raises:
            ValueError: If adaptation_factor is not between 0 and 1 or if
                       warning and critical levels are inconsistent
        """
        super().__init__(metric_name, description, units, enabled)
        
        # Validate threshold levels
        if is_lower_bound and base_warning_level < base_critical_level:
            raise ValueError(
                f"For lower bound thresholds, base_warning_level ({base_warning_level}) must be "
                f"greater than or equal to base_critical_level ({base_critical_level})"
            )
        elif not is_lower_bound and base_warning_level > base_critical_level:
            raise ValueError(
                f"For upper bound thresholds, base_warning_level ({base_warning_level}) must be "
                f"less than or equal to base_critical_level ({base_critical_level})"
            )
        
        if not 0 <= adaptation_factor <= 1:
            raise ValueError(f"Adaptation factor must be between 0 and 1, got {adaptation_factor}")
        
        self.base_warning_level = base_warning_level
        self.base_critical_level = base_critical_level
        self.current_warning_level = base_warning_level
        self.current_critical_level = base_critical_level
        self.adaptation_window = adaptation_window
        self.adaptation_factor = adaptation_factor
        self.is_lower_bound = is_lower_bound
        self.history: list[tuple[datetime, float]] = []
        self.history_size = history_size
        self.last_adaptation: Optional[datetime] = None
        
        logger.debug(
            f"Created {self.__class__.__name__} for '{metric_name}': "
            f"base_warning={base_warning_level}{units}, "
            f"base_critical={base_critical_level}{units}, "
            f"adaptation_window={adaptation_window}, "
            f"adaptation_factor={adaptation_factor}, "
            f"{'lower' if is_lower_bound else 'upper'} bound"
        )
    
    def add_to_history(self, value: float) -> None:
        """
        Add a value to the historical data.
        
        Args:
            value: The metric value to add to history
        """
        now = datetime.now()
        self.history.append((now, value))
        
        # Trim history if it exceeds the maximum size
        if len(self.history) > self.history_size:
            self.history = self.history[-self.history_size:]
        
        # Adapt thresholds if enough time has passed since last adaptation
        if (self.last_adaptation is None or 
                now - self.last_adaptation >= self.adaptation_window):
            self._adapt_thresholds()
    
    def _adapt_thresholds(self) -> None:
        """
        Adapt thresholds based on historical data.
        
        This method calculates new warning and critical levels based on
        the observed values in the adaptation window.
        """
        now = datetime.now()
        window_start = now - self.adaptation_window
        
        # Filter history to only include values within the adaptation window
        window_history = [value for timestamp, value in self.history 
                         if timestamp >= window_start]
        
        if not window_history:
            logger.debug(f"No historical data available for {self.metric_name} adaptation")
            return
        
        # Calculate statistics from the window
        avg_value = sum(window_history) / len(window_history)
        
        # Adapt thresholds based on the average value
        if self.is_lower_bound:
            # For lower bound, we want to detect when values drop too low
            # So we adapt by moving thresholds down if the average is lower
            adaptation = self.adaptation_factor * (avg_value - self.current_warning_level)
            new_warning = max(self.current_warning_level + adaptation, self.base_warning_level * 0.5)
            new_critical = max(self.current_critical_level + adaptation, self.base_critical_level * 0.5)
            
            # Ensure warning level remains above critical level
            if new_warning < new_critical:
                new_warning = new_critical
        else:
            # For upper bound, we want to detect when values rise too high
            # So we adapt by moving thresholds up if the average is higher
            adaptation = self.adaptation_factor * (avg_value - self.current_warning_level)
            new_warning = min(self.current_warning_level + adaptation, self.base_warning_level * 2)
            new_critical = min(self.current_critical_level + adaptation, self.base_critical_level * 2)
            
            # Ensure warning level remains below critical level
            if new_warning > new_critical:
                new_warning = new_critical
        
        logger.debug(
            f"Adapting thresholds for {self.metric_name}: "
            f"warning: {self.current_warning_level:.2f} -> {new_warning:.2f}, "
            f"critical: {self.current_critical_level:.2f} -> {new_critical:.2f}"
        )
        
        self.current_warning_level = new_warning
        self.current_critical_level = new_critical
        self.last_adaptation = now
    
    def check_value(self, value: float) -> ThresholdResult:
        """
        Check if a value crosses the threshold and update history.
        
        Args:
            value: The metric value to check against the threshold
            
        Returns:
            A ThresholdResult object indicating the status and details
        """
        if not self.enabled:
            result = ThresholdResult(
                status=ThresholdStatus.UNKNOWN,
                value=value,
                threshold_name=self.metric_name,
                detail="Threshold check disabled"
            )
            self.last_check = result
            return result
        
        if math.isnan(value):
            result = ThresholdResult(
                status=ThresholdStatus.UNKNOWN,
                value=value,
                threshold_name=self.metric_name,
                detail="Value is NaN"
            )
            self.last_check = result
            return result
        
        # Add value to history for future adaptation
        self.add_to_history(value)
        
        # Determine status based on whether this is a lower or upper bound
        if self.is_lower_bound:
            if value <= self.current_critical_level:
                status = ThresholdStatus.CRITICAL
                detail = (f"Value {value}{self.units} is below adaptive critical level "
                          f"({self.current_critical_level:.2f}{self.units})")
            elif value <= self.current_warning_level:
                status = ThresholdStatus.WARNING
                detail = (f"Value {value}{self.units} is below adaptive warning level "
                          f"({self.current_warning_level:.2f}{self.units})")
            else:
                status = ThresholdStatus.NORMAL
                detail = (f"Value {value}{self.units} is above adaptive warning level "
                          f"({self.current_warning_level:.2f}{self.units})")
        else:
            if value >= self.current_critical_level:
                status = ThresholdStatus.CRITICAL
                detail = (f"Value {value}{self.units} exceeds adaptive critical level "
                          f"({self.current_critical_level:.2f}{self.units})")
            elif value >= self.current_warning_level:
                status = ThresholdStatus.WARNING
                detail = (f"Value {value}{self.units} exceeds adaptive warning level "
                          f"({self.current_warning_level:.2f}{self.units})")
            else:
                status = ThresholdStatus.NORMAL
                detail = (f"Value {value}{self.units} is below adaptive warning level "
                          f"({self.current_warning_level:.2f}{self.units})")
        
        result = ThresholdResult(
            status=status,
            value=value,
            threshold_name=self.metric_name,
            detail=detail
        )
        self.last_check = result
        
        if status != ThresholdStatus.NORMAL:
            logger.info(f"Adaptive threshold crossed for {self.metric_name}: {detail}")
        
        return result
    
    def to_dict(self) -> dict[str, Any]:
        """Convert the threshold to a dictionary for serialization."""
        result = super().to_dict()
        result.update({
            "base_warning_level": self.base_warning_level,
            "base_critical_level": self.base_critical_level,
            "current_warning_level": self.current_warning_level,
            "current_critical_level": self.current_critical_level,
            "adaptation_window_seconds": self.adaptation_window.total_seconds(),
            "adaptation_factor": self.adaptation_factor,
            "is_lower_bound": self.is_lower_bound,
            "history_size": self.history_size,
            "history": [(ts.isoformat(), val) for ts, val in self.history],
        })
        
        if self.last_adaptation:
            result["last_adaptation"] = self.last_adaptation.isoformat()
            
        return result
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'AdaptiveThreshold':
        """Create an AdaptiveThreshold instance from a dictionary."""
        # Extract and convert special fields
        adaptation_window = timedelta(seconds=data.pop("adaptation_window_seconds"))
        history_data = data.pop("history", [])
        last_adaptation = data.pop("last_adaptation", None)
        last_check_data = data.pop("last_check", None)
        
        # Create the threshold instance
        threshold = cls(
            adaptation_window=adaptation_window,
            **{k: v for k, v in data.items() if k not in ["type", "current_warning_level", "current_critical_level"]}
        )
        
        # Restore current levels
        if "current_warning_level" in data:
            threshold.current_warning_level = data["current_warning_level"]
        if "current_critical_level" in data:
            threshold.current_critical_level = data["current_critical_level"]
        
        # Restore history
        threshold.history = [(datetime.fromisoformat(ts), val) for ts, val in history_data]
        
        # Restore last adaptation timestamp
        if last_adaptation:
            threshold.last_adaptation = datetime.fromisoformat(last_adaptation)
        
        # Restore last check result
        if last_check_data:
            threshold.last_check = ThresholdResult.from_dict(last_check_data)
            
        return threshold


class ThresholdRegistry:
    """
    Registry for managing and accessing thresholds.
    
    Provides a centralized way to register, retrieve, and persist thresholds
    across the system.
    """
    
    def __init__(self):
        """Initialize an empty threshold registry."""
        self._thresholds: dict[str, Threshold] = {}
        logger.debug("Initialized ThresholdRegistry")
    
    def register(self, threshold: Threshold) -> None:
        """
        Register a threshold in the registry.
        
        Args:
            threshold: The threshold to register
            
        Raises:
            ValueError: If a threshold with the same name already exists
        """
        if threshold.metric_name in self._thresholds:
            raise ValueError(f"Threshold for metric '{threshold.metric_name}' already registered")
        
        self._thresholds[threshold.metric_name] = threshold
        logger.debug(f"Registered threshold for metric '{threshold.metric_name}'")
    
    def unregister(self, metric_name: str) -> None:
        """
        Remove a threshold from the registry.
        
        Args:
            metric_name: The name of the metric whose threshold should be removed
            
        Raises:
            KeyError: If no threshold exists for the specified metric
        """
        if metric_name not in self._thresholds:
            raise KeyError(f"No threshold registered for metric '{metric_name}'")
        
        del self._thresholds[metric_name]
        logger.debug(f"Unregistered threshold for metric '{metric_name}'")
    
    def get(self, metric_name: str) -> Threshold:
        """
        Get a threshold by metric name.
        
        Args:
            metric_name: The name of the metric whose threshold to retrieve
            
        Returns:
            The threshold for the specified metric
            
        Raises:
            KeyError: If no threshold exists for the specified metric
        """
        if metric_name not in self._thresholds:
            raise KeyError(f"No threshold registered for metric '{metric_name}'")
        
        return self._thresholds[metric_name]
    
    def check_value(self, metric_name: str, value: float) -> ThresholdResult:
        """
        Check a value against a registered threshold.
        
        Args:
            metric_name: The name of the metric to check
            value: The value to check against the threshold
            
        Returns:
            A ThresholdResult object indicating the status and details
            
        Raises:
            KeyError: If no threshold exists for the specified metric
        """
        threshold = self.get(metric_name)
        return threshold.check_value(value)
    
    def list_metrics(self) -> list[str]:
        """
        Get a list of all registered metric names.
        
        Returns:
            A list of metric names with registered thresholds
        """
        return list(self._thresholds.keys())
    
    def save_to_file(self, filepath: str) -> None:
        """
        Save all thresholds to a JSON file.
        
        Args:
            filepath: The path to the file where thresholds should be saved
            
        Raises:
            IOError: If the file cannot be written
        """
        try:
            data = {
                metric_name: threshold.to_dict()
                for metric_name, threshold in self._thresholds.items()
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"Saved {len(data)} thresholds to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save thresholds to {filepath}: {str(e)}")
            raise
    
    def load_from_file(self, filepath: str) -> None:
        """
        Load thresholds from a JSON file.
        
        Args:
            filepath: The path to the file from which to load thresholds
            
        Raises:
            IOError: If the file cannot be read
            ValueError: If the file contains invalid threshold data
        """
        try:
            with open(filepath) as f:
                data = json.load(f)
            
            # Clear existing thresholds
            self._thresholds.clear()
            
            # Create threshold objects from the loaded data
            for metric_name, threshold_data in data.items():
                threshold_type = threshold_data.get("type")
                if threshold_type == "AbsoluteThreshold":
                    threshold = AbsoluteThreshold.from_dict(threshold_data)
                elif threshold_type == "RelativeThreshold":
                    threshold = RelativeThreshold.from_dict(threshold_data)
                elif threshold_type == "AdaptiveThreshold":
                    threshold = AdaptiveThreshold.from_dict(threshold_data)
                else:
                    logger.warning(f"Unknown threshold type '{threshold_type}' for metric '{metric_name}'")
                    continue
                
                self._thresholds[metric_name] = threshold
                
            logger.info(f"Loaded {len(self._thresholds)} thresholds from {filepath}")
        except Exception as e:
            logger.error(f"Failed to load thresholds from {filepath}: {str(e)}")
            raise


# Create a global registry instance
registry = ThresholdRegistry()


def create_absolute_threshold(
    metric_name: str,
    warning_level: float,
    critical_level: float,
    description: str = "",
    units: str = "",
    enabled: bool = True,
    is_lower_bound: bool = False,
    register: bool = True
) -> AbsoluteThreshold:
    """
    Create and optionally register an absolute threshold.
    
    Args:
        metric_name: The name of the metric this threshold applies to
        warning_level: The value at which a warning status is triggered
        critical_level: The value at which a critical status is triggered
        description: Optional description of the threshold's purpose
        units: The units of measurement for the metric
        enabled: Whether this threshold is currently active
        is_lower_bound: If True, values below the threshold are concerning
        register: Whether to register the threshold in the global registry
        
    Returns:
        The created threshold
        
    Raises:
        ValueError: If warning and critical levels are inconsistent
    """
    threshold = AbsoluteThreshold(
        metric_name=metric_name,
        warning_level=warning_level,
        critical_level=critical_level,
        description=description,
        units=units,
        enabled=enabled,
        is_lower_bound=is_lower_bound
    )
    
    if register:
        registry.register(threshold)
        
    return threshold


def create_relative_threshold(
    metric_name: str,
    baseline: float,
    warning_percent: float,
    critical_percent: float,
    description: str = "",
    units: str = "",
    enabled: bool = True,
    is_lower_bound: bool = False,
    register: bool = True
) -> RelativeThreshold:
    """
    Create and optionally register a relative threshold.
    
    Args:
        metric_name: The name of the metric this threshold applies to
        baseline: The baseline value to compare against
        warning_percent: The percentage deviation that triggers a warning
        critical_percent: The percentage deviation that triggers a critical alert
        description: Optional description of the threshold's purpose
        units: The units of measurement for the metric
        enabled: Whether this threshold is currently active
        is_lower_bound: If True, values below the threshold are concerning
        register: Whether to register the threshold in the global registry
        
    Returns:
        The created threshold
        
    Raises:
        ValueError: If baseline is zero or if warning and critical percentages are inconsistent
    """
    threshold = RelativeThreshold(
        metric_name=metric_name,
        baseline=baseline,
        warning_percent=warning_percent,
        critical_percent=critical_percent,
        description=description,
        units=units,
        enabled=enabled,
        is_lower_bound=is_lower_bound
    )
    
    if register:
        registry.register(threshold)
        
    return threshold


def create_adaptive_threshold(
    metric_name: str,
    base_warning_level: float,
    base_critical_level: float,
    adaptation_window: timedelta,
    adaptation_factor: float = 0.1,
    description: str = "",
    units: str = "",
    enabled: bool = True,
    is_lower_bound: bool = False,
    history_size: int = 100,
    register: bool = True
) -> AdaptiveThreshold:
    """
    Create and optionally register an adaptive threshold.
    
    Args:
        metric_name: The name of the metric this threshold applies to
        base_warning_level: The initial warning level
        base_critical_level: The initial critical level
        adaptation_window: The time window over which to adapt the threshold
        adaptation_factor: How quickly the threshold adapts (0-1)
        description: Optional description of the threshold's purpose
        units: The units of measurement for the metric
        enabled: Whether this threshold is currently active
        is_lower_bound: If True, values below the threshold are concerning
        history_size: Maximum number of historical values to store
        register: Whether to register the threshold in the global registry
        
    Returns:
        The created threshold
        
    Raises:
        ValueError: If adaptation_factor is not between 0 and 1 or if
                   warning and critical levels are inconsistent
    """
    threshold = AdaptiveThreshold(
        metric_name=metric_name,
        base_warning_level=base_warning_level,
        base_critical_level=base_critical_level,
        adaptation_window=adaptation_window,
        adaptation_factor=adaptation_factor,
        description=description,
        units=units,
        enabled=enabled,
        is_lower_bound=is_lower_bound,
        history_size=history_size
    )
    
    if register:
        registry.register(threshold)
        
    return threshold


def check_value(metric_name: str, value: float) -> ThresholdResult:
    """
    Check a value against a registered threshold.
    
    Convenience function that uses the global registry.
    
    Args:
        metric_name: The name of the metric to check
        value: The value to check against the threshold
        
    Returns:
        A ThresholdResult object indicating the status and details
        
    Raises:
        KeyError: If no threshold exists for the specified metric
    """
    return registry.check_value(metric_name, value)