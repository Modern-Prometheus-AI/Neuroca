"""
Memory Analyzer for NeuroCognitive Architecture

This module provides comprehensive tools for analyzing memory usage, patterns, and performance
across the three-tiered memory system of the NeuroCognitive Architecture. It enables:
- Memory usage statistics and visualization
- Memory access pattern analysis
- Performance bottleneck identification
- Memory health diagnostics
- Optimization recommendations

The analyzer supports both real-time monitoring and historical analysis through
integration with the monitoring subsystem and database storage.

Usage:
    from neuroca.tools.analysis.memory_analyzer import MemoryAnalyzer
    
    # Create analyzer instance
    analyzer = MemoryAnalyzer()
    
    # Get current memory usage snapshot
    memory_snapshot = analyzer.get_memory_snapshot()
    
    # Analyze memory access patterns
    access_patterns = analyzer.analyze_access_patterns(time_window="1h")
    
    # Generate optimization recommendations
    recommendations = analyzer.generate_recommendations()
"""

import datetime
import json
import logging
import os
from enum import Enum
from typing import Any, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

# Internal imports
from neuroca.config import settings
from neuroca.core.exceptions import AnalysisError, ConfigurationError
from neuroca.memory.models import MemoryTier
from neuroca.monitoring.metrics import MetricsCollector

# Configure logger
logger = logging.getLogger(__name__)


class AnalysisTimeframe(Enum):
    """Timeframes for memory analysis."""
    LAST_HOUR = "1h"
    LAST_DAY = "24h"
    LAST_WEEK = "7d"
    LAST_MONTH = "30d"
    CUSTOM = "custom"


class MemoryMetricType(Enum):
    """Types of memory metrics that can be analyzed."""
    USAGE = "usage"
    ACCESS_COUNT = "access_count"
    ACCESS_LATENCY = "access_latency"
    RETENTION_RATE = "retention_rate"
    RETRIEVAL_ACCURACY = "retrieval_accuracy"
    WRITE_OPERATIONS = "write_operations"
    READ_OPERATIONS = "read_operations"


class MemoryAnalyzer:
    """
    Comprehensive analyzer for the NCA memory system.
    
    This class provides tools to analyze memory usage, access patterns,
    performance metrics, and health indicators across all memory tiers.
    It can generate visualizations, reports, and optimization recommendations.
    """
    
    def __init__(
        self,
        metrics_collector: Optional[MetricsCollector] = None,
        config_path: Optional[str] = None,
        output_dir: Optional[str] = None
    ):
        """
        Initialize the Memory Analyzer.
        
        Args:
            metrics_collector: Optional custom metrics collector instance.
                If None, a default one will be created.
            config_path: Path to custom configuration file.
                If None, default configuration will be used.
            output_dir: Directory for saving analysis outputs.
                If None, the default directory from settings will be used.
                
        Raises:
            ConfigurationError: If configuration is invalid or inaccessible.
        """
        self.metrics_collector = metrics_collector or MetricsCollector()
        
        # Load configuration
        try:
            if config_path:
                with open(config_path) as f:
                    self.config = json.load(f)
            else:
                self.config = settings.MEMORY_ANALYZER_CONFIG
        except (FileNotFoundError, json.JSONDecodeError, AttributeError) as e:
            logger.error(f"Failed to load configuration: {str(e)}")
            raise ConfigurationError(f"Failed to load memory analyzer configuration: {str(e)}")
        
        # Set up output directory
        self.output_dir = output_dir or settings.ANALYSIS_OUTPUT_DIR
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize analysis cache
        self._cache = {}
        
        logger.debug("Memory Analyzer initialized successfully")
    
    def get_memory_snapshot(self, tier: Optional[MemoryTier] = None) -> dict[str, Any]:
        """
        Get current memory usage snapshot across all or specific memory tiers.
        
        Args:
            tier: Optional specific memory tier to analyze.
                If None, all tiers will be analyzed.
                
        Returns:
            Dict containing memory usage statistics.
            
        Raises:
            AnalysisError: If metrics collection fails.
        """
        logger.debug(f"Getting memory snapshot for tier: {tier or 'all'}")
        
        try:
            if tier:
                metrics = self.metrics_collector.get_memory_metrics(tier=tier)
            else:
                metrics = {}
                for t in MemoryTier:
                    metrics[t.name] = self.metrics_collector.get_memory_metrics(tier=t)
            
            # Add timestamp to the snapshot
            result = {
                "timestamp": datetime.datetime.now().isoformat(),
                "metrics": metrics
            }
            
            return result
        
        except Exception as e:
            error_msg = f"Failed to get memory snapshot: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise AnalysisError(error_msg)
    
    def analyze_access_patterns(
        self,
        time_window: str = "1h",
        tier: Optional[MemoryTier] = None,
        custom_start: Optional[datetime.datetime] = None,
        custom_end: Optional[datetime.datetime] = None
    ) -> dict[str, Any]:
        """
        Analyze memory access patterns over a specified time window.
        
        Args:
            time_window: Time window for analysis (e.g., "1h", "24h", "7d").
                Use "custom" for custom time range.
            tier: Optional specific memory tier to analyze.
                If None, all tiers will be analyzed.
            custom_start: Start time for custom time window.
                Required if time_window is "custom".
            custom_end: End time for custom time window.
                Required if time_window is "custom".
                
        Returns:
            Dict containing access pattern analysis results.
            
        Raises:
            AnalysisError: If analysis fails.
            ValueError: If invalid parameters are provided.
        """
        logger.debug(f"Analyzing access patterns for window: {time_window}, tier: {tier or 'all'}")
        
        # Validate custom timeframe parameters
        if time_window == AnalysisTimeframe.CUSTOM.value:
            if not custom_start or not custom_end:
                raise ValueError("Custom start and end times must be provided for custom timeframe")
            if custom_end <= custom_start:
                raise ValueError("Custom end time must be after start time")
        
        try:
            # Get access metrics from the metrics collector
            access_data = self.metrics_collector.get_access_metrics(
                time_window=time_window,
                tier=tier,
                custom_start=custom_start,
                custom_end=custom_end
            )
            
            # Process the raw access data
            patterns = self._process_access_patterns(access_data)
            
            # Add metadata to the results
            result = {
                "timestamp": datetime.datetime.now().isoformat(),
                "time_window": time_window,
                "tier": tier.name if tier else "all",
                "patterns": patterns
            }
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to analyze access patterns: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise AnalysisError(error_msg)
    
    def _process_access_patterns(self, access_data: dict[str, Any]) -> dict[str, Any]:
        """
        Process raw access data to extract meaningful patterns.
        
        Args:
            access_data: Raw access metrics data.
            
        Returns:
            Dict containing processed access patterns.
        """
        patterns = {}
        
        # Convert to pandas DataFrame for easier analysis
        df = pd.DataFrame(access_data)
        
        # Calculate temporal patterns (time of day, day of week)
        if 'timestamp' in df.columns:
            df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
            df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.dayofweek
            
            patterns['hourly_distribution'] = df.groupby('hour').size().to_dict()
            patterns['daily_distribution'] = df.groupby('day_of_week').size().to_dict()
        
        # Calculate access frequency by memory item
        if 'memory_id' in df.columns:
            patterns['item_frequency'] = df.groupby('memory_id').size().to_dict()
            
            # Find most frequently accessed items
            top_items = df['memory_id'].value_counts().head(10).to_dict()
            patterns['top_accessed_items'] = top_items
        
        # Calculate access type distribution
        if 'operation_type' in df.columns:
            patterns['operation_distribution'] = df.groupby('operation_type').size().to_dict()
        
        # Calculate sequential access patterns if possible
        if len(df) > 1 and 'memory_id' in df.columns and 'timestamp' in df.columns:
            df = df.sort_values('timestamp')
            df['next_memory_id'] = df['memory_id'].shift(-1)
            transitions = df.groupby(['memory_id', 'next_memory_id']).size()
            
            # Convert to dictionary with tuple keys
            transitions_dict = {f"{k[0]}->{k[1]}": v for k, v in transitions.items() if pd.notna(k[1])}
            patterns['sequential_patterns'] = transitions_dict
        
        return patterns
    
    def analyze_performance(
        self,
        time_window: str = "24h",
        tier: Optional[MemoryTier] = None,
        metrics: Optional[list[MemoryMetricType]] = None,
        custom_start: Optional[datetime.datetime] = None,
        custom_end: Optional[datetime.datetime] = None
    ) -> dict[str, Any]:
        """
        Analyze memory performance metrics over a specified time window.
        
        Args:
            time_window: Time window for analysis (e.g., "1h", "24h", "7d").
                Use "custom" for custom time range.
            tier: Optional specific memory tier to analyze.
                If None, all tiers will be analyzed.
            metrics: List of specific metrics to analyze.
                If None, all available metrics will be analyzed.
            custom_start: Start time for custom time window.
            custom_end: End time for custom time window.
                
        Returns:
            Dict containing performance analysis results.
            
        Raises:
            AnalysisError: If analysis fails.
        """
        logger.debug(f"Analyzing performance for window: {time_window}, tier: {tier or 'all'}")
        
        try:
            # Get performance metrics from the metrics collector
            if metrics:
                metric_names = [m.value for m in metrics]
            else:
                metric_names = [m.value for m in MemoryMetricType]
                
            perf_data = self.metrics_collector.get_performance_metrics(
                metrics=metric_names,
                time_window=time_window,
                tier=tier,
                custom_start=custom_start,
                custom_end=custom_end
            )
            
            # Process the raw performance data
            analysis = self._analyze_performance_metrics(perf_data)
            
            # Add metadata to the results
            result = {
                "timestamp": datetime.datetime.now().isoformat(),
                "time_window": time_window,
                "tier": tier.name if tier else "all",
                "metrics_analyzed": metric_names,
                "analysis": analysis
            }
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to analyze performance: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise AnalysisError(error_msg)
    
    def _analyze_performance_metrics(self, perf_data: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze raw performance metrics to extract insights.
        
        Args:
            perf_data: Raw performance metrics data.
            
        Returns:
            Dict containing performance analysis results.
        """
        analysis = {}
        
        for metric_name, metric_data in perf_data.items():
            # Skip if no data
            if not metric_data:
                analysis[metric_name] = {"status": "no_data"}
                continue
                
            # Convert to pandas Series for analysis
            if isinstance(metric_data, list) and all(isinstance(item, dict) for item in metric_data):
                # Extract timestamps and values
                timestamps = [item.get('timestamp') for item in metric_data]
                values = [item.get('value') for item in metric_data]
                
                # Create Series with timestamps as index
                s = pd.Series(values, index=pd.to_datetime(timestamps))
                s = s.sort_index()
            else:
                # Handle other data formats
                s = pd.Series(metric_data)
            
            # Calculate basic statistics
            metric_analysis = {
                "mean": float(s.mean()) if not s.empty else None,
                "median": float(s.median()) if not s.empty else None,
                "min": float(s.min()) if not s.empty else None,
                "max": float(s.max()) if not s.empty else None,
                "std_dev": float(s.std()) if not s.empty and len(s) > 1 else None,
            }
            
            # Detect trends if we have time series data
            if isinstance(s.index, pd.DatetimeIndex) and len(s) > 2:
                # Simple linear regression for trend detection
                x = np.arange(len(s))
                y = s.values
                slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
                
                metric_analysis["trend"] = {
                    "slope": float(slope),
                    "r_squared": float(r_value ** 2),
                    "p_value": float(p_value),
                    "direction": "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable",
                    "significant": p_value < 0.05
                }
                
                # Detect anomalies (simple z-score method)
                z_scores = np.abs(stats.zscore(s.values))
                anomalies = np.where(z_scores > 3)[0]  # Points more than 3 standard deviations away
                
                if len(anomalies) > 0:
                    metric_analysis["anomalies"] = {
                        "count": int(len(anomalies)),
                        "indices": anomalies.tolist(),
                        "timestamps": [s.index[i].isoformat() for i in anomalies] if isinstance(s.index, pd.DatetimeIndex) else None,
                        "values": [float(s.iloc[i]) for i in anomalies]
                    }
                else:
                    metric_analysis["anomalies"] = {"count": 0}
            
            analysis[metric_name] = metric_analysis
        
        return analysis
    
    def identify_bottlenecks(self, threshold: float = 0.8) -> dict[str, Any]:
        """
        Identify potential bottlenecks in the memory system.
        
        Args:
            threshold: Threshold value for identifying bottlenecks (0.0-1.0).
                Higher values mean only more severe bottlenecks are reported.
                
        Returns:
            Dict containing identified bottlenecks and their severity.
            
        Raises:
            AnalysisError: If bottleneck identification fails.
            ValueError: If threshold is not between 0 and 1.
        """
        logger.debug(f"Identifying bottlenecks with threshold: {threshold}")
        
        if not 0 <= threshold <= 1:
            raise ValueError("Threshold must be between 0 and 1")
        
        try:
            # Get current memory snapshot
            snapshot = self.get_memory_snapshot()
            
            # Get recent performance metrics
            perf_data = self.metrics_collector.get_performance_metrics(
                time_window="1h"
            )
            
            # Identify bottlenecks based on various indicators
            bottlenecks = self._identify_bottleneck_indicators(snapshot, perf_data, threshold)
            
            # Add metadata to the results
            result = {
                "timestamp": datetime.datetime.now().isoformat(),
                "threshold": threshold,
                "bottlenecks": bottlenecks
            }
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to identify bottlenecks: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise AnalysisError(error_msg)
    
    def _identify_bottleneck_indicators(
        self, 
        snapshot: dict[str, Any], 
        perf_data: dict[str, Any], 
        threshold: float
    ) -> dict[str, Any]:
        """
        Identify bottleneck indicators from memory snapshot and performance data.
        
        Args:
            snapshot: Current memory snapshot.
            perf_data: Performance metrics data.
            threshold: Threshold for bottleneck identification.
            
        Returns:
            Dict containing identified bottlenecks.
        """
        bottlenecks = {}
        
        # Check memory usage bottlenecks
        if "metrics" in snapshot:
            for tier_name, tier_metrics in snapshot["metrics"].items():
                if "capacity" in tier_metrics and "used" in tier_metrics:
                    usage_ratio = tier_metrics["used"] / tier_metrics["capacity"]
                    
                    if usage_ratio > threshold:
                        bottlenecks[f"{tier_name}_capacity"] = {
                            "type": "capacity",
                            "tier": tier_name,
                            "severity": (usage_ratio - threshold) / (1 - threshold),  # Normalized severity
                            "current_usage": usage_ratio,
                            "threshold": threshold
                        }
        
        # Check latency bottlenecks
        if "access_latency" in perf_data:
            latency_data = perf_data["access_latency"]
            
            for tier_name, tier_latency in latency_data.items():
                if isinstance(tier_latency, dict) and "expected" in tier_latency and "actual" in tier_latency:
                    latency_ratio = tier_latency["actual"] / tier_latency["expected"]
                    
                    if latency_ratio > 1 + threshold:  # If actual is significantly higher than expected
                        bottlenecks[f"{tier_name}_latency"] = {
                            "type": "latency",
                            "tier": tier_name,
                            "severity": (latency_ratio - (1 + threshold)) / threshold,  # Normalized severity
                            "current_ratio": latency_ratio,
                            "threshold": 1 + threshold
                        }
        
        # Check throughput bottlenecks
        if "throughput" in perf_data:
            throughput_data = perf_data["throughput"]
            
            for tier_name, tier_throughput in throughput_data.items():
                if isinstance(tier_throughput, dict) and "expected" in tier_throughput and "actual" in tier_throughput:
                    throughput_ratio = tier_throughput["actual"] / tier_throughput["expected"]
                    
                    if throughput_ratio < threshold:  # If actual is significantly lower than expected
                        bottlenecks[f"{tier_name}_throughput"] = {
                            "type": "throughput",
                            "tier": tier_name,
                            "severity": (threshold - throughput_ratio) / threshold,  # Normalized severity
                            "current_ratio": throughput_ratio,
                            "threshold": threshold
                        }
        
        return bottlenecks
    
    def generate_recommendations(self) -> dict[str, Any]:
        """
        Generate optimization recommendations based on memory analysis.
        
        Returns:
            Dict containing optimization recommendations.
            
        Raises:
            AnalysisError: If recommendation generation fails.
        """
        logger.debug("Generating memory optimization recommendations")
        
        try:
            # Identify bottlenecks with a moderate threshold
            bottlenecks = self.identify_bottlenecks(threshold=0.7)
            
            # Get recent performance metrics
            perf_data = self.metrics_collector.get_performance_metrics(
                time_window="24h"
            )
            
            # Get access patterns
            access_patterns = self.analyze_access_patterns(time_window="24h")
            
            # Generate recommendations based on the analysis
            recommendations = self._generate_optimization_recommendations(
                bottlenecks, perf_data, access_patterns
            )
            
            # Add metadata to the results
            result = {
                "timestamp": datetime.datetime.now().isoformat(),
                "recommendations": recommendations
            }
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to generate recommendations: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise AnalysisError(error_msg)
    
    def _generate_optimization_recommendations(
        self,
        bottlenecks: dict[str, Any],
        perf_data: dict[str, Any],
        access_patterns: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Generate specific optimization recommendations based on analysis results.
        
        Args:
            bottlenecks: Identified bottlenecks.
            perf_data: Performance metrics data.
            access_patterns: Memory access patterns.
            
        Returns:
            List of recommendation dictionaries.
        """
        recommendations = []
        
        # Process capacity bottlenecks
        if "bottlenecks" in bottlenecks:
            for _bottleneck_id, bottleneck in bottlenecks["bottlenecks"].items():
                if bottleneck["type"] == "capacity":
                    recommendations.append({
                        "id": f"capacity_{bottleneck['tier']}",
                        "type": "capacity_optimization",
                        "tier": bottleneck["tier"],
                        "severity": bottleneck["severity"],
                        "description": f"Memory capacity in {bottleneck['tier']} tier is at {bottleneck['current_usage']*100:.1f}% of maximum",
                        "actions": [
                            "Increase memory allocation for this tier",
                            "Implement more aggressive cleanup of unused items",
                            "Review retention policies for this memory tier"
                        ]
                    })
                elif bottleneck["type"] == "latency":
                    recommendations.append({
                        "id": f"latency_{bottleneck['tier']}",
                        "type": "latency_optimization",
                        "tier": bottleneck["tier"],
                        "severity": bottleneck["severity"],
                        "description": f"Access latency in {bottleneck['tier']} tier is {bottleneck['current_ratio']:.1f}x higher than expected",
                        "actions": [
                            "Optimize memory access patterns",
                            "Review indexing strategies",
                            "Consider hardware upgrades if persistent"
                        ]
                    })
        
        # Check for access pattern optimizations
        if "patterns" in access_patterns:
            patterns = access_patterns["patterns"]
            
            # Check for highly skewed access patterns
            if "item_frequency" in patterns:
                item_freq = patterns["item_frequency"]
                if item_freq:
                    # Calculate Gini coefficient as a measure of access inequality
                    values = np.array(list(item_freq.values()))
                    values = values[values > 0]  # Remove zeros
                    if len(values) > 1:
                        values = np.sort(values)
                        index = np.arange(1, len(values) + 1)
                        n = len(values)
                        gini = (np.sum((2 * index - n - 1) * values)) / (n * np.sum(values))
                        
                        if gini > 0.8:  # High inequality in access patterns
                            recommendations.append({
                                "id": "skewed_access",
                                "type": "access_pattern_optimization",
                                "severity": (gini - 0.8) / 0.2,  # Normalized severity
                                "description": f"Highly skewed memory access patterns detected (Gini={gini:.2f})",
                                "actions": [
                                    "Consider caching frequently accessed items in faster memory tiers",
                                    "Review memory organization to better match access patterns",
                                    "Implement predictive prefetching for common access sequences"
                                ]
                            })
        
        # Check for temporal optimization opportunities
        if "patterns" in access_patterns and "hourly_distribution" in access_patterns["patterns"]:
            hourly = access_patterns["patterns"]["hourly_distribution"]
            if hourly:
                hours = list(hourly.keys())
                counts = list(hourly.values())
                
                # Check if there are clear peak usage times
                max_count = max(counts)
                avg_count = sum(counts) / len(counts)
                
                if max_count > 2 * avg_count:  # Significant peak detected
                    peak_hours = [hours[i] for i, count in enumerate(counts) if count > 1.5 * avg_count]
                    
                    recommendations.append({
                        "id": "temporal_optimization",
                        "type": "scheduling_optimization",
                        "severity": 0.6,  # Medium severity
                        "description": f"Significant usage peaks detected during hours: {peak_hours}",
                        "actions": [
                            "Schedule resource-intensive operations outside peak hours",
                            "Increase memory allocation during peak times",
                            "Implement dynamic scaling based on time patterns"
                        ]
                    })
        
        # Sort recommendations by severity
        recommendations.sort(key=lambda x: x.get("severity", 0), reverse=True)
        
        return recommendations
    
    def visualize_memory_usage(
        self,
        time_window: str = "24h",
        tier: Optional[MemoryTier] = None,
        output_path: Optional[str] = None,
        show_plot: bool = False
    ) -> str:
        """
        Visualize memory usage over time.
        
        Args:
            time_window: Time window for visualization.
            tier: Optional specific memory tier to visualize.
                If None, all tiers will be visualized.
            output_path: Path to save the visualization.
                If None, a default path will be generated.
            show_plot: Whether to display the plot interactively.
            
        Returns:
            Path to the saved visualization file.
            
        Raises:
            AnalysisError: If visualization fails.
        """
        logger.debug(f"Visualizing memory usage for window: {time_window}, tier: {tier or 'all'}")
        
        try:
            # Get memory usage data
            usage_data = self.metrics_collector.get_memory_metrics(
                metric=MemoryMetricType.USAGE.value,
                time_window=time_window,
                tier=tier
            )
            
            # Generate default output path if not provided
            if not output_path:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                tier_str = tier.name if tier else "all_tiers"
                filename = f"memory_usage_{tier_str}_{timestamp}.png"
                output_path = os.path.join(self.output_dir, filename)
            
            # Create visualization
            plt.figure(figsize=(12, 6))
            
            # Process and plot the data
            if isinstance(usage_data, dict):
                # Multiple tiers
                for tier_name, tier_data in usage_data.items():
                    if isinstance(tier_data, list) and tier_data:
                        # Extract timestamps and values
                        timestamps = [pd.to_datetime(item.get('timestamp')) for item in tier_data]
                        values = [item.get('value') for item in tier_data]
                        
                        # Sort by timestamp
                        sorted_data = sorted(zip(timestamps, values))
                        timestamps = [item[0] for item in sorted_data]
                        values = [item[1] for item in sorted_data]
                        
                        plt.plot(timestamps, values, label=tier_name)
            else:
                # Single tier or aggregated data
                if isinstance(usage_data, list) and usage_data:
                    # Extract timestamps and values
                    timestamps = [pd.to_datetime(item.get('timestamp')) for item in usage_data]
                    values = [item.get('value') for item in usage_data]
                    
                    # Sort by timestamp
                    sorted_data = sorted(zip(timestamps, values))
                    timestamps = [item[0] for item in sorted_data]
                    values = [item[1] for item in sorted_data]
                    
                    plt.plot(timestamps, values, label=tier.name if tier else "All Tiers")
            
            # Add labels and title
            plt.xlabel("Time")
            plt.ylabel("Memory Usage")
            plt.title(f"Memory Usage Over Time ({time_window})")
            plt.legend()
            plt.grid(True)
            
            # Save the figure
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            
            if show_plot:
                plt.show()
            else:
                plt.close()
            
            logger.info(f"Memory usage visualization saved to: {output_path}")
            return output_path
            
        except Exception as e:
            error_msg = f"Failed to visualize memory usage: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise AnalysisError(error_msg)
    
    def visualize_access_patterns(
        self,
        time_window: str = "24h",
        tier: Optional[MemoryTier] = None,
        output_path: Optional[str] = None,
        show_plot: bool = False
    ) -> str:
        """
        Visualize memory access patterns.
        
        Args:
            time_window: Time window for visualization.
            tier: Optional specific memory tier to visualize.
                If None, all tiers will be visualized.
            output_path: Path to save the visualization.
                If None, a default path will be generated.
            show_plot: Whether to display the plot interactively.
            
        Returns:
            Path to the saved visualization file.
            
        Raises:
            AnalysisError: If visualization fails.
        """
        logger.debug(f"Visualizing access patterns for window: {time_window}, tier: {tier or 'all'}")
        
        try:
            # Get access pattern data
            access_patterns = self.analyze_access_patterns(time_window=time_window, tier=tier)
            
            # Generate default output path if not provided
            if not output_path:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                tier_str = tier.name if tier else "all_tiers"
                filename = f"access_patterns_{tier_str}_{timestamp}.png"
                output_path = os.path.join(self.output_dir, filename)
            
            # Create visualization with subplots
            fig, axs = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle(f"Memory Access Patterns ({time_window})", fontsize=16)
            
            # Plot hourly distribution if available
            if "patterns" in access_patterns and "hourly_distribution" in access_patterns["patterns"]:
                hourly = access_patterns["patterns"]["hourly_distribution"]
                if hourly:
                    hours = sorted(hourly.keys())
                    counts = [hourly[hour] for hour in hours]
                    axs[0, 0].bar(hours, counts)
                    axs[0, 0].set_title("Hourly Access Distribution")
                    axs[0, 0].set_xlabel("Hour of Day")
                    axs[0, 0].set_ylabel("Access Count")
                    axs[0, 0].grid(True, alpha=0.3)
            
            # Plot daily distribution if available
            if "patterns" in access_patterns and "daily_distribution" in access_patterns["patterns"]:
                daily = access_patterns["patterns"]["daily_distribution"]
                if daily:
                    days = sorted(daily.keys())
                    counts = [daily[day] for day in days]
                    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                    day_labels = [day_names[int(day)] for day in days]
                    axs[0, 1].bar(day_labels, counts)
                    axs[0, 1].set_title("Daily Access Distribution")
                    axs[0, 1].set_xlabel("Day of Week")
                    axs[0, 1].set_ylabel("Access Count")
                    axs[0, 1].grid(True, alpha=0.3)
            
            # Plot top accessed items if available
            if "patterns" in access_patterns and "top_accessed_items" in access_patterns["patterns"]:
                top_items = access_patterns["patterns"]["top_accessed_items"]
                if top_items:
                    items = list(top_items.keys())[:10]  # Limit to top 10
                    counts = [top_items[item] for item in items]
                    
                    # Shorten item IDs for display
                    short_items = [str(item)[:10] + "..." if len(str(item)) > 10 else str(item) for item in items]
                    
                    axs[1, 0].barh(short_items, counts)
                    axs[1, 0].set_title("Top Accessed Items")
                    axs[1, 0].set_xlabel("Access Count")
                    axs[1, 0].set_ylabel("Item ID")
                    axs[1, 0].grid(True, alpha=0.3)
            
            # Plot operation distribution if available
            if "patterns" in access_patterns and "operation_distribution" in access_patterns["patterns"]:
                ops = access_patterns["patterns"]["operation_distribution"]
                if ops:
                    op_types = list(ops.keys())
                    counts = [ops[op] for op in op_types]
                    axs[1, 1].pie(counts, labels=op_types, autopct='%1.1f%%')
                    axs[1, 1].set_title("Operation Type Distribution")
            
            plt.tight_layout()
            
            # Save the figure
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            
            if show_plot:
                plt.show()
            else:
                plt.close()
            
            logger.info(f"Access pattern visualization saved to: {output_path}")
            return output_path
            
        except Exception as e:
            error_msg = f"Failed to visualize access patterns: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise AnalysisError(error_msg)
    
    def export_analysis_report(
        self,
        time_window: str = "24h",
        include_visualizations: bool = True,
        output_format: str = "json",
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate and export a comprehensive memory analysis report.
        
        Args:
            time_window: Time window for the report.
            include_visualizations: Whether to include visualizations.
            output_format: Format of the report ('json' or 'html').
            output_path: Path to save the report.
                If None, a default path will be generated.
                
        Returns:
            Path to the saved report file.
            
        Raises:
            AnalysisError: If report generation fails.
            ValueError: If an invalid output format is specified.
        """
        logger.debug(f"Generating memory analysis report for window: {time_window}")
        
        if output_format not in ["json", "html"]:
            raise ValueError(f"Unsupported output format: {output_format}")
        
        try:
            # Generate default output path if not provided
            if not output_path:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"memory_analysis_report_{timestamp}.{output_format}"
                output_path = os.path.join(self.output_dir, filename)
            
            # Collect all analysis data
            report_data = {
                "metadata": {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "time_window": time_window,
                    "version": "1.0"
                },
                "memory_snapshot": self.get_memory_snapshot(),
                "performance_analysis": self.analyze_performance(time_window=time_window),
                "access_patterns": self.analyze_access_patterns(time_window=time_window),
                "bottlenecks": self.identify_bottlenecks(),
                "recommendations": self.generate_recommendations()
            }
            
            # Generate visualizations if requested
            if include_visualizations:
                viz_dir = os.path.join(os.path.dirname(output_path), "visualizations")
                os.makedirs(viz_dir, exist_ok=True)
                
                usage_viz = self.visualize_memory_usage(
                    time_window=time_window,
                    output_path=os.path.join(viz_dir, f"memory_usage_{timestamp}.png")
                )
                
                access_viz = self.visualize_access_patterns(
                    time_window=time_window,
                    output_path=os.path.join(viz_dir, f"access_patterns_{timestamp}.png")
                )
                
                report_data["visualizations"] = {
                    "memory_usage": os.path.relpath(usage_viz, os.path.dirname(output_path)),
                    "access_patterns": os.path.relpath(access_viz, os.path.dirname(output_path))
                }
            
            # Export the report in the requested format
            if output_format == "json":
                with open(output_path, 'w') as f:
                    json.dump(report_data, f, indent=2, default=str)
            else:  # HTML format
                # Simple HTML report template
                html_content = self._generate_html_report(report_data)
                
                with open(output_path, 'w') as f:
                    f.write(html_content)
            
            logger.info(f"Memory analysis report saved to: {output_path}")
            return output_path
            
        except Exception as e:
            error_msg = f"Failed to generate analysis report: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise AnalysisError(error_msg)
    
    def _generate_html_report(self, report_data: dict[str, Any]) -> str:
        """
        Generate HTML content for the analysis report.
        
        Args:
            report_data: Report data dictionary.
            
        Returns:
            HTML content as a string.
        """
        # Simple HTML template for the report
        html = f"""<!DOCTYPE html>
        <html>
        <head>
            <title>Memory Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2, h3 {{ color: #2c3e50; }}
                .section {{ margin-bottom: 30px; border: 1px solid #ddd; padding: 15px; border-radius: 5px; }}
                .recommendation {{ background-color: #f8f9fa; padding: 10px; margin: 10px 0; border-left: 4px solid #28a745; }}
                .bottleneck {{ background-color: #f8f9fa; padding: 10px; margin: 10px 0; border-left: 4px solid #dc3545; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .visualization {{ margin: 20px 0; text-align: center; }}
                .visualization img {{ max-width: 100%; height: auto; }}
            </style>
        </head>
        <body>
            <h1>Memory Analysis Report</h1>
            <p>Generated: {report_data['metadata']['timestamp']}</p>
            <p>Time Window: {report_data['metadata']['time_window']}</p>
            
            <div class="section">
                <h2>Memory Snapshot</h2>
                <pre>{json.dumps(report_data['memory_snapshot'], indent=2, default=str)}</pre>
            </div>
            
            <div class="section">
                <h2>Performance Analysis</h2>
                <pre>{json.dumps(report_data['performance_analysis'], indent=2, default=str)}</pre>
            </div>
            
            <div class="section">
                <h2>Access Patterns</h2>
                <pre>{json.dumps(report_data['access_patterns'], indent=2, default=str)}</pre>
            </div>
            
            <div class="section">
                <h2>Bottlenecks</h2>
                """
        
        # Add bottlenecks
        if "bottlenecks" in report_data and "bottlenecks" in report_data["bottlenecks"]:
            for bottleneck_id, bottleneck in report_data["bottlenecks"]["bottlenecks"].items():
                html += f"""
                <div class="bottleneck">
                    <h3>{bottleneck_id}</h3>
                    <p><strong>Type:</strong> {bottleneck.get('type')}</p>
                    <p><strong>Tier:</strong> {bottleneck.get('tier')}</p>
                    <p><strong>Severity:</strong> {bottleneck.get('severity', 0):.2f}</p>
                    <p><strong>Description:</strong> {bottleneck.get('description', 'No description')}</p>
                </div>
                """
        else:
            html += "<p>No bottlenecks identified.</p>"
        
        html += """
            </div>
            
            <div class="section">
                <h2>Recommendations</h2>
            """
        
        # Add recommendations
        if "recommendations" in report_data and "recommendations" in report_data["recommendations"]:
            for rec in report_data["recommendations"]["recommendations"]:
                html += f"""
                <div class="recommendation">
                    <h3>{rec.get('id')}</h3>
                    <p><strong>Type:</strong> {rec.get('type')}</p>
                    <p><strong>Severity:</strong> {rec.get('severity', 0):.2f}</p>
                    <p><strong>Description:</strong> {rec.get('description', 'No description')}</p>
                    <p><strong>Recommended Actions:</strong></p>
                    <ul>
                    """
                
                for action in rec.get('actions', []):
                    html += f"<li>{action}</li>"
                
                html += """
                    </ul>
                </div>
                """
        else:
            html += "<p>No recommendations available.</p>"
        
        html += """
            </div>
            """
        
        # Add visualizations if available
        if "visualizations" in report_data:
            html += """
            <div class="section">
                <h2>Visualizations</h2>
            """
            
            for viz_name, viz_path in report_data["visualizations"].items():
                html += f"""
                <div class="visualization">
                    <h3>{viz_name.replace('_', ' ').title()}</h3>
                    <img src="{viz_path}" alt="{viz_name}" />
                </div>
                """
            
            html += """
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        return html


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    try:
        analyzer = MemoryAnalyzer()
        
        # Get current memory snapshot
        snapshot = analyzer.get_memory_snapshot()
        print(f"Memory snapshot: {snapshot}")
        
        # Generate a comprehensive report
        report_path = analyzer.export_analysis_report(
            time_window="24h",
            include_visualizations=True,
            output_format="html"
        )
        
        print(f"Memory analysis report generated: {report_path}")
        
    except Exception as e:
        logging.error(f"Error in memory analysis: {str(e)}", exc_info=True)