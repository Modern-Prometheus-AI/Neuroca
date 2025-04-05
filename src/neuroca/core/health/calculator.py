"""
Health Calculator Module for NeuroCognitive Architecture (NCA).

This module provides comprehensive functionality for calculating, monitoring, and
analyzing the health metrics of various components within the NCA system. It implements
algorithms for determining system vitality, cognitive load, memory efficiency,
and other critical health indicators that affect the performance and stability
of the NCA system.

The health calculations follow biologically-inspired models to simulate natural
cognitive processes and their degradation or optimization over time and usage.

Usage:
    from neuroca.core.health import calculator
    
    # Calculate overall system health
    system_health = calculator.calculate_system_health(system_state)
    
    # Calculate specific component health
    memory_health = calculator.calculate_memory_health(memory_metrics)
    
    # Get health trends over time
    health_trends = calculator.analyze_health_trends(historical_data)
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional

import numpy as np

from neuroca.core.exceptions import (
    ComponentNotFoundError,
    HealthCalculationError,
    InvalidMetricsError,
)
from neuroca.core.health.constants import (
    CRITICAL_THRESHOLD,
    DEFAULT_DECAY_RATE,
    DEFAULT_RECOVERY_RATE,
    MAX_HEALTH_VALUE,
    MIN_HEALTH_VALUE,
    OPTIMAL_THRESHOLD,
    WARNING_THRESHOLD,
)
from neuroca.core.health.models import (
    ComponentHealth,
    HealthStatus,
    HealthTrend,
    SystemHealth,
)

# Configure logger
logger = logging.getLogger(__name__)

@dataclass
class HealthParameters:
    """Parameters used for health calculations."""
    decay_rate: float = DEFAULT_DECAY_RATE
    recovery_rate: float = DEFAULT_RECOVERY_RATE
    weight_cognitive_load: float = 0.3
    weight_memory_efficiency: float = 0.25
    weight_response_time: float = 0.2
    weight_error_rate: float = 0.25


class HealthCalculator:
    """
    Core class for calculating health metrics of NCA components.
    
    This class provides methods to calculate various health indicators
    based on system metrics, usage patterns, and historical data.
    It implements biologically-inspired algorithms to model system health
    in a way that mimics natural cognitive processes.
    """
    
    def __init__(self, parameters: Optional[HealthParameters] = None):
        """
        Initialize the health calculator with specific parameters.
        
        Args:
            parameters: Custom parameters for health calculations.
                        If None, default parameters will be used.
        """
        self.parameters = parameters or HealthParameters()
        self._last_calculation_time = None
        logger.debug("HealthCalculator initialized with parameters: %s", self.parameters)
    
    def calculate_system_health(self, metrics: dict[str, Any]) -> SystemHealth:
        """
        Calculate the overall health of the NCA system.
        
        Args:
            metrics: Dictionary containing system metrics including:
                    - cognitive_load: Float between 0-1
                    - memory_usage: Dict with usage stats for each memory tier
                    - response_times: List of recent response times in ms
                    - error_rates: Dict with error counts by component
                    - uptime: System uptime in seconds
        
        Returns:
            SystemHealth object containing overall health score and component scores
            
        Raises:
            InvalidMetricsError: If required metrics are missing or invalid
            HealthCalculationError: If calculation fails due to unexpected errors
        """
        try:
            self._validate_system_metrics(metrics)
            current_time = time.time()
            
            # Calculate time-based decay if applicable
            if self._last_calculation_time:
                time_factor = self._calculate_time_factor(current_time)
            else:
                time_factor = 1.0
            
            # Calculate component health scores
            component_scores = {}
            
            # Calculate cognitive health
            cognitive_health = self._calculate_cognitive_health(
                metrics.get('cognitive_load', 0.5),
                time_factor
            )
            component_scores['cognitive'] = cognitive_health
            
            # Calculate memory health for each tier
            memory_health = self._calculate_memory_health(
                metrics.get('memory_usage', {}),
                time_factor
            )
            component_scores['memory'] = memory_health
            
            # Calculate processing health
            processing_health = self._calculate_processing_health(
                metrics.get('response_times', []),
                metrics.get('error_rates', {}),
                time_factor
            )
            component_scores['processing'] = processing_health
            
            # Calculate overall system health score (weighted average)
            overall_score = self._calculate_overall_health(component_scores)
            
            # Determine system health status based on overall score
            status = self._determine_health_status(overall_score)
            
            # Update last calculation time
            self._last_calculation_time = current_time
            
            # Create and return SystemHealth object
            system_health = SystemHealth(
                overall_score=overall_score,
                status=status,
                component_scores=component_scores,
                timestamp=datetime.now(),
                metrics_snapshot=metrics
            )
            
            logger.info(
                "System health calculated: %s (Score: %.2f)", 
                status.name, 
                overall_score
            )
            
            return system_health
            
        except (KeyError, ValueError, TypeError) as e:
            error_msg = f"Invalid metrics format: {str(e)}"
            logger.error(error_msg)
            raise InvalidMetricsError(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to calculate system health: {str(e)}"
            logger.exception(error_msg)
            raise HealthCalculationError(error_msg) from e
    
    def calculate_component_health(
        self, 
        component_id: str, 
        metrics: dict[str, Any]
    ) -> ComponentHealth:
        """
        Calculate health metrics for a specific component.
        
        Args:
            component_id: Identifier of the component
            metrics: Component-specific metrics
        
        Returns:
            ComponentHealth object with health score and status
            
        Raises:
            ComponentNotFoundError: If component_id is invalid
            InvalidMetricsError: If metrics are invalid for the component
        """
        try:
            logger.debug("Calculating health for component: %s", component_id)
            
            if not component_id:
                raise ComponentNotFoundError("Component ID cannot be empty")
            
            # Select calculation method based on component type
            if component_id.startswith("memory"):
                score = self._calculate_memory_health(metrics, 1.0)
            elif component_id.startswith("cognitive"):
                score = self._calculate_cognitive_health(
                    metrics.get('cognitive_load', 0.5), 
                    1.0
                )
            elif component_id.startswith("processing"):
                score = self._calculate_processing_health(
                    metrics.get('response_times', []),
                    metrics.get('error_rates', {}),
                    1.0
                )
            else:
                # Generic calculation for other components
                score = self._calculate_generic_component_health(metrics)
            
            status = self._determine_health_status(score)
            
            return ComponentHealth(
                component_id=component_id,
                health_score=score,
                status=status,
                timestamp=datetime.now(),
                metrics=metrics
            )
            
        except KeyError as e:
            error_msg = f"Missing required metrics for component {component_id}: {str(e)}"
            logger.error(error_msg)
            raise InvalidMetricsError(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to calculate health for component {component_id}: {str(e)}"
            logger.exception(error_msg)
            raise HealthCalculationError(error_msg) from e
    
    def analyze_health_trends(
        self, 
        historical_data: list[SystemHealth],
        time_window: Optional[timedelta] = None
    ) -> HealthTrend:
        """
        Analyze health trends over time based on historical health data.
        
        Args:
            historical_data: List of SystemHealth objects ordered by timestamp
            time_window: Optional time window to analyze (default: all available data)
        
        Returns:
            HealthTrend object containing trend analysis
            
        Raises:
            InvalidMetricsError: If historical data is invalid or insufficient
        """
        try:
            if not historical_data:
                raise InvalidMetricsError("Historical data cannot be empty")
            
            # Filter data by time window if specified
            if time_window:
                cutoff_time = datetime.now() - time_window
                filtered_data = [
                    data for data in historical_data 
                    if data.timestamp >= cutoff_time
                ]
            else:
                filtered_data = historical_data
            
            if not filtered_data:
                raise InvalidMetricsError(
                    "No data available within the specified time window"
                )
            
            # Extract timestamps and scores
            timestamps = [data.timestamp for data in filtered_data]
            scores = [data.overall_score for data in filtered_data]
            
            # Calculate trend metrics
            trend_slope = self._calculate_trend_slope(timestamps, scores)
            volatility = self._calculate_volatility(scores)
            
            # Determine if health is improving, stable, or declining
            if trend_slope > 0.01:
                trend_direction = "improving"
            elif trend_slope < -0.01:
                trend_direction = "declining"
            else:
                trend_direction = "stable"
            
            # Calculate component-specific trends
            component_trends = self._calculate_component_trends(filtered_data)
            
            # Create and return HealthTrend object
            trend = HealthTrend(
                direction=trend_direction,
                slope=trend_slope,
                volatility=volatility,
                component_trends=component_trends,
                start_time=timestamps[0],
                end_time=timestamps[-1],
                data_points=len(filtered_data)
            )
            
            logger.info(
                "Health trend analysis: %s (slope: %.4f, volatility: %.4f)",
                trend_direction,
                trend_slope,
                volatility
            )
            
            return trend
            
        except (TypeError, ValueError) as e:
            error_msg = f"Invalid historical data format: {str(e)}"
            logger.error(error_msg)
            raise InvalidMetricsError(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to analyze health trends: {str(e)}"
            logger.exception(error_msg)
            raise HealthCalculationError(error_msg) from e
    
    def predict_future_health(
        self, 
        current_health: SystemHealth,
        historical_data: list[SystemHealth],
        prediction_window: timedelta
    ) -> dict[datetime, float]:
        """
        Predict future health scores based on current health and historical trends.
        
        Args:
            current_health: Current system health
            historical_data: Historical health data
            prediction_window: Time window to predict into the future
            
        Returns:
            Dictionary mapping future timestamps to predicted health scores
            
        Raises:
            InvalidMetricsError: If input data is insufficient for prediction
        """
        try:
            if not historical_data or len(historical_data) < 3:
                raise InvalidMetricsError(
                    "Insufficient historical data for prediction (minimum 3 data points required)"
                )
            
            # Analyze trends from historical data
            trend = self.analyze_health_trends(historical_data)
            
            # Generate prediction points
            prediction_points = {}
            current_time = datetime.now()
            current_score = current_health.overall_score
            
            # Simple linear prediction based on trend slope
            # More sophisticated models could be implemented here
            num_points = 10  # Number of prediction points
            interval = prediction_window / num_points
            
            for i in range(1, num_points + 1):
                future_time = current_time + (interval * i)
                time_delta = (future_time - current_time).total_seconds() / 86400  # Convert to days
                
                # Apply trend slope and add some randomness based on volatility
                predicted_score = current_score + (trend.slope * time_delta)
                
                # Add small random variation based on historical volatility
                random_factor = np.random.normal(0, trend.volatility * 0.1)
                predicted_score += random_factor
                
                # Ensure score stays within valid range
                predicted_score = max(MIN_HEALTH_VALUE, min(MAX_HEALTH_VALUE, predicted_score))
                
                prediction_points[future_time] = predicted_score
            
            logger.info(
                "Health prediction generated for %s days with %d points",
                prediction_window.days,
                len(prediction_points)
            )
            
            return prediction_points
            
        except Exception as e:
            error_msg = f"Failed to predict future health: {str(e)}"
            logger.exception(error_msg)
            raise HealthCalculationError(error_msg) from e
    
    def _validate_system_metrics(self, metrics: dict[str, Any]) -> None:
        """
        Validate that the provided metrics contain all required fields.
        
        Args:
            metrics: Dictionary of system metrics
            
        Raises:
            InvalidMetricsError: If metrics are missing required fields or have invalid values
        """
        required_keys = ['cognitive_load', 'memory_usage', 'response_times']
        
        for key in required_keys:
            if key not in metrics:
                raise InvalidMetricsError(f"Missing required metric: {key}")
        
        # Validate cognitive_load is a float between 0-1
        cognitive_load = metrics.get('cognitive_load')
        if not isinstance(cognitive_load, (int, float)) or not 0 <= cognitive_load <= 1:
            raise InvalidMetricsError(
                f"cognitive_load must be a float between 0-1, got: {cognitive_load}"
            )
        
        # Validate memory_usage is a dictionary
        if not isinstance(metrics.get('memory_usage'), dict):
            raise InvalidMetricsError("memory_usage must be a dictionary")
        
        # Validate response_times is a list
        if not isinstance(metrics.get('response_times'), list):
            raise InvalidMetricsError("response_times must be a list")
    
    def _calculate_time_factor(self, current_time: float) -> float:
        """
        Calculate time-based factor for health decay/recovery.
        
        Args:
            current_time: Current timestamp
            
        Returns:
            Time factor to apply to health calculations
        """
        if not self._last_calculation_time:
            return 1.0
        
        time_diff = current_time - self._last_calculation_time
        # Convert to hours for more meaningful decay/recovery rates
        time_diff_hours = time_diff / 3600
        
        # Time factor is based on elapsed time, but capped to prevent extreme values
        return min(max(time_diff_hours, 0.01), 24.0)
    
    def _calculate_cognitive_health(self, cognitive_load: float, time_factor: float) -> float:
        """
        Calculate cognitive health based on cognitive load.
        
        Args:
            cognitive_load: Value between 0-1 representing cognitive load
            time_factor: Time-based factor for calculations
            
        Returns:
            Cognitive health score between 0-100
        """
        # Cognitive health is inversely related to cognitive load
        # Optimal cognitive load is around 0.4-0.6 (not too low, not too high)
        if 0.4 <= cognitive_load <= 0.6:
            # Optimal range
            base_score = 90.0
        elif cognitive_load < 0.4:
            # Too low (underutilized)
            base_score = 70.0 + (cognitive_load / 0.4) * 20.0
        else:
            # Too high (overloaded)
            base_score = 90.0 - ((cognitive_load - 0.6) / 0.4) * 70.0
        
        # Apply time-based recovery or decay
        if 0.4 <= cognitive_load <= 0.6:
            # Recovery when in optimal range
            adjusted_score = base_score + (self.parameters.recovery_rate * time_factor)
        else:
            # Decay when outside optimal range
            adjusted_score = base_score - (self.parameters.decay_rate * time_factor)
        
        return max(MIN_HEALTH_VALUE, min(MAX_HEALTH_VALUE, adjusted_score))
    
    def _calculate_memory_health(
        self, 
        memory_usage: dict[str, dict[str, float]], 
        time_factor: float
    ) -> float:
        """
        Calculate memory health based on usage metrics across memory tiers.
        
        Args:
            memory_usage: Dictionary with memory usage stats for each tier
            time_factor: Time-based factor for calculations
            
        Returns:
            Memory health score between 0-100
        """
        if not memory_usage:
            return 75.0  # Default score if no data
        
        tier_scores = []
        tier_weights = {
            'working': 0.5,    # Working memory is most critical
            'episodic': 0.3,   # Episodic memory is important
            'semantic': 0.2    # Semantic memory is most stable
        }
        
        for tier, metrics in memory_usage.items():
            if tier not in tier_weights:
                logger.warning("Unknown memory tier: %s", tier)
                continue
                
            # Extract usage percentage and fragmentation
            usage_pct = metrics.get('usage_percent', 0.0)
            fragmentation = metrics.get('fragmentation', 0.0)
            
            # Calculate tier score
            # Optimal usage is 30-70%
            if 0.3 <= usage_pct <= 0.7:
                usage_score = 100.0
            elif usage_pct < 0.3:
                # Underutilized
                usage_score = 70.0 + (usage_pct / 0.3) * 30.0
            else:
                # Overutilized
                usage_score = 100.0 - ((usage_pct - 0.7) / 0.3) * 70.0
            
            # Fragmentation penalty (0-30%)
            fragmentation_penalty = fragmentation * 30.0
            
            tier_score = usage_score - fragmentation_penalty
            tier_scores.append((tier_score, tier_weights.get(tier, 0.1)))
        
        if not tier_scores:
            return 75.0  # Default score if no valid tiers
        
        # Calculate weighted average
        weighted_sum = sum(score * weight for score, weight in tier_scores)
        total_weight = sum(weight for _, weight in tier_scores)
        
        base_score = weighted_sum / total_weight if total_weight > 0 else 75.0
        
        # Apply time-based decay/recovery based on overall memory health
        if base_score >= 80.0:
            # Healthy memory recovers slightly
            adjusted_score = base_score + (self.parameters.recovery_rate * 0.5 * time_factor)
        else:
            # Unhealthy memory decays
            adjusted_score = base_score - (self.parameters.decay_rate * time_factor)
        
        return max(MIN_HEALTH_VALUE, min(MAX_HEALTH_VALUE, adjusted_score))
    
    def _calculate_processing_health(
        self, 
        response_times: list[float],
        error_rates: dict[str, int],
        time_factor: float
    ) -> float:
        """
        Calculate processing health based on response times and error rates.
        
        Args:
            response_times: List of recent response times in ms
            error_rates: Dictionary with error counts by component
            time_factor: Time-based factor for calculations
            
        Returns:
            Processing health score between 0-100
        """
        # Calculate response time score
        if not response_times:
            response_time_score = 75.0  # Default if no data
        else:
            # Calculate average and variance
            avg_response_time = sum(response_times) / len(response_times)
            
            # Response time score (lower is better, but too low might indicate issues)
            if 50 <= avg_response_time <= 200:
                # Optimal range
                response_time_score = 100.0
            elif avg_response_time < 50:
                # Suspiciously fast
                response_time_score = 80.0 + (avg_response_time / 50.0) * 20.0
            else:
                # Too slow
                response_time_score = 100.0 - min(((avg_response_time - 200) / 800.0) * 80.0, 80.0)
        
        # Calculate error rate score
        total_errors = sum(error_rates.values())
        if total_errors == 0:
            error_score = 100.0
        else:
            # Error score decreases with more errors (exponential penalty)
            error_score = 100.0 * np.exp(-0.1 * total_errors)
        
        # Combine scores with weights
        base_score = (
            response_time_score * self.parameters.weight_response_time +
            error_score * self.parameters.weight_error_rate
        ) / (self.parameters.weight_response_time + self.parameters.weight_error_rate)
        
        # Apply time-based decay/recovery
        if base_score >= 80.0:
            # Healthy processing recovers
            adjusted_score = base_score + (self.parameters.recovery_rate * 0.7 * time_factor)
        else:
            # Unhealthy processing decays faster
            adjusted_score = base_score - (self.parameters.decay_rate * 1.2 * time_factor)
        
        return max(MIN_HEALTH_VALUE, min(MAX_HEALTH_VALUE, adjusted_score))
    
    def _calculate_generic_component_health(self, metrics: dict[str, Any]) -> float:
        """
        Calculate health for a generic component based on provided metrics.
        
        Args:
            metrics: Component-specific metrics
            
        Returns:
            Health score between 0-100
        """
        # Extract common health indicators if available
        utilization = metrics.get('utilization', 0.5)
        error_count = metrics.get('error_count', 0)
        performance = metrics.get('performance', 0.7)
        
        # Calculate base score
        utilization_score = 100.0 - abs(utilization - 0.5) * 100.0  # Optimal at 50%
        error_score = 100.0 * np.exp(-0.2 * error_count)  # Exponential penalty for errors
        performance_score = performance * 100.0  # Direct mapping
        
        # Combine scores with equal weights
        base_score = (utilization_score + error_score + performance_score) / 3.0
        
        return max(MIN_HEALTH_VALUE, min(MAX_HEALTH_VALUE, base_score))
    
    def _calculate_overall_health(self, component_scores: dict[str, float]) -> float:
        """
        Calculate overall system health from component scores.
        
        Args:
            component_scores: Dictionary mapping component names to health scores
            
        Returns:
            Overall health score between 0-100
        """
        if not component_scores:
            return 50.0  # Default score if no components
        
        # Define component weights
        weights = {
            'cognitive': self.parameters.weight_cognitive_load,
            'memory': self.parameters.weight_memory_efficiency,
            'processing': self.parameters.weight_response_time + self.parameters.weight_error_rate
        }
        
        # Calculate weighted average
        weighted_sum = 0.0
        total_weight = 0.0
        
        for component, score in component_scores.items():
            weight = weights.get(component, 0.1)  # Default weight for unknown components
            weighted_sum += score * weight
            total_weight += weight
        
        if total_weight == 0:
            return 50.0
            
        overall_score = weighted_sum / total_weight
        
        # Ensure score is within valid range
        return max(MIN_HEALTH_VALUE, min(MAX_HEALTH_VALUE, overall_score))
    
    def _determine_health_status(self, health_score: float) -> HealthStatus:
        """
        Determine health status category based on health score.
        
        Args:
            health_score: Health score between 0-100
            
        Returns:
            HealthStatus enum value
        """
        if health_score >= OPTIMAL_THRESHOLD:
            return HealthStatus.OPTIMAL
        elif health_score >= WARNING_THRESHOLD:
            return HealthStatus.HEALTHY
        elif health_score >= CRITICAL_THRESHOLD:
            return HealthStatus.WARNING
        else:
            return HealthStatus.CRITICAL
    
    def _calculate_trend_slope(
        self, 
        timestamps: list[datetime], 
        scores: list[float]
    ) -> float:
        """
        Calculate the slope of health trend over time.
        
        Args:
            timestamps: List of datetime objects
            scores: List of health scores
            
        Returns:
            Slope value (positive for improving, negative for declining)
        """
        if len(timestamps) < 2:
            return 0.0
        
        # Convert timestamps to seconds since first timestamp
        first_timestamp = timestamps[0]
        time_values = [(ts - first_timestamp).total_seconds() / 86400 for ts in timestamps]  # Convert to days
        
        # Simple linear regression
        n = len(time_values)
        sum_x = sum(time_values)
        sum_y = sum(scores)
        sum_xy = sum(x * y for x, y in zip(time_values, scores))
        sum_xx = sum(x * x for x in time_values)
        
        # Calculate slope
        try:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)
        except ZeroDivisionError:
            slope = 0.0
        
        return slope
    
    def _calculate_volatility(self, scores: list[float]) -> float:
        """
        Calculate the volatility (standard deviation) of health scores.
        
        Args:
            scores: List of health scores
            
        Returns:
            Volatility value
        """
        if len(scores) < 2:
            return 0.0
        
        return np.std(scores)
    
    def _calculate_component_trends(
        self, 
        historical_data: list[SystemHealth]
    ) -> dict[str, dict[str, float]]:
        """
        Calculate trends for individual components.
        
        Args:
            historical_data: List of SystemHealth objects
            
        Returns:
            Dictionary mapping component names to trend metrics
        """
        component_trends = {}
        
        # Get all unique component names
        all_components = set()
        for data in historical_data:
            all_components.update(data.component_scores.keys())
        
        # Calculate trend for each component
        for component in all_components:
            timestamps = []
            scores = []
            
            for data in historical_data:
                if component in data.component_scores:
                    timestamps.append(data.timestamp)
                    scores.append(data.component_scores[component])
            
            if len(scores) >= 2:
                slope = self._calculate_trend_slope(timestamps, scores)
                volatility = self._calculate_volatility(scores)
                
                component_trends[component] = {
                    'slope': slope,
                    'volatility': volatility,
                    'data_points': len(scores)
                }
        
        return component_trends


# Create a default instance for easy import and use
default_calculator = HealthCalculator()

# Convenience functions that use the default calculator

def calculate_system_health(metrics: dict[str, Any]) -> SystemHealth:
    """
    Calculate system health using the default calculator.
    
    Args:
        metrics: System metrics dictionary
        
    Returns:
        SystemHealth object
    """
    return default_calculator.calculate_system_health(metrics)

def calculate_component_health(
    component_id: str, 
    metrics: dict[str, Any]
) -> ComponentHealth:
    """
    Calculate component health using the default calculator.
    
    Args:
        component_id: Component identifier
        metrics: Component metrics
        
    Returns:
        ComponentHealth object
    """
    return default_calculator.calculate_component_health(component_id, metrics)

def analyze_health_trends(
    historical_data: list[SystemHealth],
    time_window: Optional[timedelta] = None
) -> HealthTrend:
    """
    Analyze health trends using the default calculator.
    
    Args:
        historical_data: List of historical SystemHealth objects
        time_window: Optional time window to analyze
        
    Returns:
        HealthTrend object
    """
    return default_calculator.analyze_health_trends(historical_data, time_window)

def predict_future_health(
    current_health: SystemHealth,
    historical_data: list[SystemHealth],
    prediction_window: timedelta
) -> dict[datetime, float]:
    """
    Predict future health using the default calculator.
    
    Args:
        current_health: Current system health
        historical_data: Historical health data
        prediction_window: Time window to predict
        
    Returns:
        Dictionary mapping future timestamps to predicted health scores
    """
    return default_calculator.predict_future_health(
        current_health, 
        historical_data, 
        prediction_window
    )