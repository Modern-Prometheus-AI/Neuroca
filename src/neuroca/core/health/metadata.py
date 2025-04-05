"""
Health Metadata Management Module for NeuroCognitive Architecture.

This module provides functionality for managing, validating, and tracking health-related
metadata within the NeuroCognitive Architecture (NCA) system. It includes classes and
utilities for representing, validating, and manipulating health metrics metadata,
supporting the biological-inspired components of the architecture.

The module implements:
- Health metadata schema definition and validation
- Metadata versioning and history tracking
- Serialization/deserialization for persistence
- Metadata comparison and differential analysis

Usage:
    from neuroca.core.health.metadata import HealthMetadata, MetadataRegistry
    
    # Create health metadata for a component
    metadata = HealthMetadata(
        component_id="memory_consolidation_01",
        metrics={"stability": 0.85, "energy_consumption": 0.42},
        category="memory"
    )
    
    # Register metadata
    registry = MetadataRegistry()
    registry.register(metadata)
    
    # Retrieve and analyze metadata
    component_metadata = registry.get("memory_consolidation_01")
    if component_metadata.is_healthy():
        print("Component is healthy")
"""

import copy
import datetime
import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Optional, Union

# Configure logging
logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Enumeration of possible health statuses for system components."""
    OPTIMAL = auto()
    NORMAL = auto()
    DEGRADED = auto()
    CRITICAL = auto()
    UNKNOWN = auto()


class MetadataValidationError(Exception):
    """Exception raised when health metadata validation fails."""
    pass


class MetadataNotFoundError(Exception):
    """Exception raised when requested metadata cannot be found."""
    pass


class MetadataVersionError(Exception):
    """Exception raised for metadata version conflicts or issues."""
    pass


@dataclass
class HealthMetricDefinition:
    """Definition of a health metric including validation parameters."""
    
    name: str
    description: str
    unit: str
    min_value: float
    max_value: float
    default_value: float
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    
    def validate_value(self, value: float) -> bool:
        """
        Validate if a metric value is within the defined range.
        
        Args:
            value: The metric value to validate
            
        Returns:
            bool: True if the value is valid, False otherwise
            
        Raises:
            TypeError: If the value is not a number
        """
        if not isinstance(value, (int, float)):
            raise TypeError(f"Metric value must be a number, got {type(value).__name__}")
        
        return self.min_value <= value <= self.max_value
    
    def get_status(self, value: float) -> HealthStatus:
        """
        Determine the health status based on the metric value.
        
        Args:
            value: The metric value to evaluate
            
        Returns:
            HealthStatus: The corresponding health status
        """
        if not self.validate_value(value):
            return HealthStatus.UNKNOWN
        
        if self.critical_threshold is not None and value >= self.critical_threshold:
            return HealthStatus.CRITICAL
        
        if self.warning_threshold is not None and value >= self.warning_threshold:
            return HealthStatus.DEGRADED
        
        if value == self.default_value:
            return HealthStatus.OPTIMAL
        
        return HealthStatus.NORMAL


@dataclass
class HealthMetadata:
    """
    Container for health-related metadata of a system component.
    
    This class stores and manages health metrics and metadata for components
    in the NeuroCognitive Architecture, providing validation, serialization,
    and status assessment capabilities.
    """
    
    component_id: str
    metrics: dict[str, float]
    category: str
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)
    version: int = 1
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: Optional[str] = None
    tags: set[str] = field(default_factory=set)
    parent_id: Optional[str] = None
    metric_definitions: dict[str, HealthMetricDefinition] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate the metadata after initialization."""
        self.validate()
    
    def validate(self) -> bool:
        """
        Validate the metadata structure and values.
        
        Returns:
            bool: True if validation passes
            
        Raises:
            MetadataValidationError: If validation fails
        """
        # Validate component_id
        if not self.component_id or not isinstance(self.component_id, str):
            raise MetadataValidationError("Component ID must be a non-empty string")
        
        # Validate metrics
        if not isinstance(self.metrics, dict):
            raise MetadataValidationError("Metrics must be a dictionary")
        
        # Validate metric values against definitions if available
        for metric_name, metric_value in self.metrics.items():
            if not isinstance(metric_value, (int, float)):
                raise MetadataValidationError(
                    f"Metric '{metric_name}' value must be a number, got {type(metric_value).__name__}"
                )
            
            if metric_name in self.metric_definitions:
                try:
                    if not self.metric_definitions[metric_name].validate_value(metric_value):
                        raise MetadataValidationError(
                            f"Metric '{metric_name}' value {metric_value} is outside "
                            f"allowed range [{self.metric_definitions[metric_name].min_value}, "
                            f"{self.metric_definitions[metric_name].max_value}]"
                        )
                except TypeError as e:
                    raise MetadataValidationError(str(e))
        
        # Validate category
        if not self.category or not isinstance(self.category, str):
            raise MetadataValidationError("Category must be a non-empty string")
        
        # Validate tags
        if not isinstance(self.tags, set):
            raise MetadataValidationError("Tags must be a set")
        
        for tag in self.tags:
            if not isinstance(tag, str) or not tag:
                raise MetadataValidationError("Tags must be non-empty strings")
        
        return True
    
    def update_metrics(self, metrics: dict[str, float]) -> None:
        """
        Update the metrics with new values and increment version.
        
        Args:
            metrics: Dictionary of metric names and values to update
            
        Raises:
            MetadataValidationError: If any of the new metrics are invalid
        """
        # Create a copy of current metrics
        updated_metrics = copy.deepcopy(self.metrics)
        
        # Update with new values
        updated_metrics.update(metrics)
        
        # Create a temporary metadata object to validate
        temp_metadata = copy.deepcopy(self)
        temp_metadata.metrics = updated_metrics
        
        try:
            temp_metadata.validate()
            # If validation passes, update the actual object
            self.metrics = updated_metrics
            self.version += 1
            self.timestamp = datetime.datetime.now()
            logger.debug(f"Updated metrics for component {self.component_id}, new version: {self.version}")
        except MetadataValidationError as e:
            logger.error(f"Failed to update metrics for component {self.component_id}: {str(e)}")
            raise
    
    def is_healthy(self) -> bool:
        """
        Check if the component is in a healthy state based on its metrics.
        
        Returns:
            bool: True if all metrics indicate a healthy state, False otherwise
        """
        for metric_name, metric_value in self.metrics.items():
            if metric_name in self.metric_definitions:
                status = self.metric_definitions[metric_name].get_status(metric_value)
                if status in (HealthStatus.CRITICAL, HealthStatus.UNKNOWN):
                    return False
        
        return True
    
    def get_overall_status(self) -> HealthStatus:
        """
        Calculate the overall health status based on all metrics.
        
        Returns:
            HealthStatus: The overall health status of the component
        """
        statuses = []
        
        for metric_name, metric_value in self.metrics.items():
            if metric_name in self.metric_definitions:
                statuses.append(self.metric_definitions[metric_name].get_status(metric_value))
            else:
                statuses.append(HealthStatus.UNKNOWN)
        
        if not statuses:
            return HealthStatus.UNKNOWN
        
        if HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL
        elif HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        elif HealthStatus.UNKNOWN in statuses:
            return HealthStatus.UNKNOWN
        elif all(status == HealthStatus.OPTIMAL for status in statuses):
            return HealthStatus.OPTIMAL
        else:
            return HealthStatus.NORMAL
    
    def to_dict(self) -> dict[str, Any]:
        """
        Convert the metadata to a dictionary for serialization.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the metadata
        """
        result = asdict(self)
        
        # Convert datetime to ISO format string
        result['timestamp'] = self.timestamp.isoformat()
        
        # Convert tags set to list for JSON serialization
        result['tags'] = list(self.tags)
        
        # Convert metric definitions to dictionaries
        result['metric_definitions'] = {
            name: asdict(definition) 
            for name, definition in self.metric_definitions.items()
        }
        
        return result
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'HealthMetadata':
        """
        Create a HealthMetadata instance from a dictionary.
        
        Args:
            data: Dictionary containing metadata attributes
            
        Returns:
            HealthMetadata: New instance created from the dictionary
            
        Raises:
            MetadataValidationError: If the dictionary contains invalid data
        """
        # Make a copy to avoid modifying the input
        data_copy = copy.deepcopy(data)
        
        # Convert timestamp string to datetime
        if 'timestamp' in data_copy and isinstance(data_copy['timestamp'], str):
            try:
                data_copy['timestamp'] = datetime.datetime.fromisoformat(data_copy['timestamp'])
            except ValueError:
                raise MetadataValidationError(f"Invalid timestamp format: {data_copy['timestamp']}")
        
        # Convert tags list to set
        if 'tags' in data_copy and isinstance(data_copy['tags'], list):
            data_copy['tags'] = set(data_copy['tags'])
        
        # Convert metric definitions dictionaries to objects
        if 'metric_definitions' in data_copy and isinstance(data_copy['metric_definitions'], dict):
            metric_defs = {}
            for name, def_dict in data_copy['metric_definitions'].items():
                try:
                    metric_defs[name] = HealthMetricDefinition(**def_dict)
                except TypeError as e:
                    raise MetadataValidationError(f"Invalid metric definition for {name}: {str(e)}")
            data_copy['metric_definitions'] = metric_defs
        
        try:
            return cls(**data_copy)
        except TypeError as e:
            raise MetadataValidationError(f"Invalid metadata format: {str(e)}")
    
    def to_json(self) -> str:
        """
        Convert the metadata to a JSON string.
        
        Returns:
            str: JSON representation of the metadata
        """
        try:
            return json.dumps(self.to_dict(), indent=2)
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize metadata to JSON: {str(e)}")
            raise MetadataValidationError(f"Failed to serialize metadata to JSON: {str(e)}")
    
    @classmethod
    def from_json(cls, json_str: str) -> 'HealthMetadata':
        """
        Create a HealthMetadata instance from a JSON string.
        
        Args:
            json_str: JSON string containing metadata
            
        Returns:
            HealthMetadata: New instance created from the JSON
            
        Raises:
            MetadataValidationError: If the JSON is invalid or contains invalid data
        """
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse metadata JSON: {str(e)}")
            raise MetadataValidationError(f"Failed to parse metadata JSON: {str(e)}")


class MetadataRegistry:
    """
    Registry for managing and retrieving health metadata for system components.
    
    This class provides a centralized repository for storing, retrieving, and
    managing health metadata across the system, with support for versioning,
    filtering, and persistence.
    """
    
    def __init__(self, storage_path: Optional[Union[str, Path]] = None):
        """
        Initialize a new metadata registry.
        
        Args:
            storage_path: Optional path for persisting metadata to disk
        """
        self._metadata: dict[str, list[HealthMetadata]] = {}
        self._storage_path = Path(storage_path) if storage_path else None
        
        if self._storage_path and not self._storage_path.exists():
            try:
                self._storage_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created metadata storage directory: {self._storage_path}")
            except OSError as e:
                logger.error(f"Failed to create metadata storage directory: {str(e)}")
                self._storage_path = None
    
    def register(self, metadata: HealthMetadata) -> None:
        """
        Register new health metadata for a component.
        
        Args:
            metadata: The health metadata to register
            
        Raises:
            MetadataValidationError: If the metadata is invalid
        """
        # Validate metadata before registering
        try:
            metadata.validate()
        except MetadataValidationError as e:
            logger.error(f"Failed to register invalid metadata: {str(e)}")
            raise
        
        component_id = metadata.component_id
        
        # Initialize component history if needed
        if component_id not in self._metadata:
            self._metadata[component_id] = []
        
        # Add metadata to history
        self._metadata[component_id].append(metadata)
        logger.debug(f"Registered metadata for component {component_id}, version {metadata.version}")
        
        # Persist to storage if configured
        if self._storage_path:
            self._persist_metadata(metadata)
    
    def get(self, component_id: str, version: Optional[int] = None) -> HealthMetadata:
        """
        Retrieve health metadata for a component.
        
        Args:
            component_id: ID of the component
            version: Optional specific version to retrieve (latest if None)
            
        Returns:
            HealthMetadata: The requested metadata
            
        Raises:
            MetadataNotFoundError: If the requested metadata cannot be found
        """
        if component_id not in self._metadata or not self._metadata[component_id]:
            logger.warning(f"Metadata not found for component {component_id}")
            raise MetadataNotFoundError(f"No metadata found for component {component_id}")
        
        if version is None:
            # Return the latest version
            return self._metadata[component_id][-1]
        
        # Find the requested version
        for metadata in self._metadata[component_id]:
            if metadata.version == version:
                return metadata
        
        logger.warning(f"Version {version} not found for component {component_id}")
        raise MetadataNotFoundError(f"Version {version} not found for component {component_id}")
    
    def get_history(self, component_id: str) -> list[HealthMetadata]:
        """
        Retrieve the full history of metadata for a component.
        
        Args:
            component_id: ID of the component
            
        Returns:
            List[HealthMetadata]: List of all metadata versions for the component
            
        Raises:
            MetadataNotFoundError: If no metadata exists for the component
        """
        if component_id not in self._metadata or not self._metadata[component_id]:
            logger.warning(f"No metadata history found for component {component_id}")
            raise MetadataNotFoundError(f"No metadata found for component {component_id}")
        
        return self._metadata[component_id]
    
    def list_components(self, category: Optional[str] = None, tag: Optional[str] = None) -> list[str]:
        """
        List all component IDs in the registry, optionally filtered by category or tag.
        
        Args:
            category: Optional category to filter by
            tag: Optional tag to filter by
            
        Returns:
            List[str]: List of component IDs matching the filters
        """
        components = []
        
        for component_id, history in self._metadata.items():
            if not history:
                continue
                
            # Get the latest metadata for filtering
            latest = history[-1]
            
            # Apply category filter if specified
            if category is not None and latest.category != category:
                continue
                
            # Apply tag filter if specified
            if tag is not None and tag not in latest.tags:
                continue
                
            components.append(component_id)
            
        return components
    
    def update(self, component_id: str, metrics: dict[str, float]) -> HealthMetadata:
        """
        Update metrics for a component and create a new version.
        
        Args:
            component_id: ID of the component to update
            metrics: Dictionary of metric names and values to update
            
        Returns:
            HealthMetadata: The updated metadata
            
        Raises:
            MetadataNotFoundError: If the component doesn't exist
            MetadataValidationError: If the update would result in invalid metadata
        """
        try:
            current = self.get(component_id)
        except MetadataNotFoundError:
            logger.error(f"Cannot update non-existent component {component_id}")
            raise
        
        # Create a new metadata object based on the current one
        updated = copy.deepcopy(current)
        
        try:
            updated.update_metrics(metrics)
            self.register(updated)
            return updated
        except MetadataValidationError as e:
            logger.error(f"Failed to update component {component_id}: {str(e)}")
            raise
    
    def compare(self, component_id: str, version1: int, version2: int) -> dict[str, tuple[float, float]]:
        """
        Compare metrics between two versions of a component's metadata.
        
        Args:
            component_id: ID of the component
            version1: First version to compare
            version2: Second version to compare
            
        Returns:
            Dict[str, Tuple[float, float]]: Dictionary mapping metric names to (version1_value, version2_value) tuples
            
        Raises:
            MetadataNotFoundError: If either version cannot be found
        """
        try:
            metadata1 = self.get(component_id, version1)
            metadata2 = self.get(component_id, version2)
        except MetadataNotFoundError as e:
            logger.error(f"Cannot compare versions: {str(e)}")
            raise
        
        # Combine all metric keys from both versions
        all_metrics = set(metadata1.metrics.keys()) | set(metadata2.metrics.keys())
        
        # Create comparison dictionary
        comparison = {}
        for metric in all_metrics:
            value1 = metadata1.metrics.get(metric, None)
            value2 = metadata2.metrics.get(metric, None)
            comparison[metric] = (value1, value2)
        
        return comparison
    
    def _persist_metadata(self, metadata: HealthMetadata) -> None:
        """
        Persist metadata to storage.
        
        Args:
            metadata: The metadata to persist
        """
        if not self._storage_path:
            return
            
        component_dir = self._storage_path / metadata.component_id
        try:
            component_dir.mkdir(exist_ok=True)
            
            # Save as JSON file with version in filename
            file_path = component_dir / f"v{metadata.version}.json"
            with open(file_path, 'w') as f:
                f.write(metadata.to_json())
                
            # Also save as latest.json for quick access
            latest_path = component_dir / "latest.json"
            with open(latest_path, 'w') as f:
                f.write(metadata.to_json())
                
            logger.debug(f"Persisted metadata for {metadata.component_id} v{metadata.version} to {file_path}")
        except OSError as e:
            logger.error(f"Failed to persist metadata: {str(e)}")
    
    def load_from_storage(self) -> int:
        """
        Load all metadata from storage.
        
        Returns:
            int: Number of metadata items loaded
        """
        if not self._storage_path or not self._storage_path.exists():
            logger.warning("No storage path configured or directory doesn't exist")
            return 0
            
        count = 0
        
        try:
            # Iterate through component directories
            for component_dir in self._storage_path.iterdir():
                if not component_dir.is_dir():
                    continue
                    
                # Find all version files
                version_files = sorted(component_dir.glob("v*.json"), key=lambda f: int(f.stem[1:]))  # Sort by version number
                
                for file_path in version_files:
                    try:
                        with open(file_path) as f:
                            metadata = HealthMetadata.from_json(f.read())
                            
                        # Add to registry without persisting again
                        component_id = metadata.component_id
                        if component_id not in self._metadata:
                            self._metadata[component_id] = []
                        self._metadata[component_id].append(metadata)
                        count += 1
                    except (OSError, json.JSONDecodeError, MetadataValidationError) as e:
                        logger.error(f"Failed to load metadata from {file_path}: {str(e)}")
                        continue
            
            logger.info(f"Loaded {count} metadata items from storage")
            return count
        except Exception as e:
            logger.error(f"Error loading metadata from storage: {str(e)}")
            return count


def create_default_metric_definitions() -> dict[str, HealthMetricDefinition]:
    """
    Create a set of default metric definitions for common health metrics.
    
    Returns:
        Dict[str, HealthMetricDefinition]: Dictionary of default metric definitions
    """
    return {
        "stability": HealthMetricDefinition(
            name="stability",
            description="Measure of system stability and resistance to perturbations",
            unit="ratio",
            min_value=0.0,
            max_value=1.0,
            default_value=0.9,
            warning_threshold=0.5,
            critical_threshold=0.3
        ),
        "energy_consumption": HealthMetricDefinition(
            name="energy_consumption",
            description="Normalized energy consumption of the component",
            unit="ratio",
            min_value=0.0,
            max_value=1.0,
            default_value=0.4,
            warning_threshold=0.8,
            critical_threshold=0.95
        ),
        "response_time": HealthMetricDefinition(
            name="response_time",
            description="Normalized response time of the component",
            unit="ratio",
            min_value=0.0,
            max_value=1.0,
            default_value=0.3,
            warning_threshold=0.7,
            critical_threshold=0.9
        ),
        "error_rate": HealthMetricDefinition(
            name="error_rate",
            description="Rate of errors in component operations",
            unit="ratio",
            min_value=0.0,
            max_value=1.0,
            default_value=0.05,
            warning_threshold=0.2,
            critical_threshold=0.5
        ),
        "utilization": HealthMetricDefinition(
            name="utilization",
            description="Resource utilization level",
            unit="ratio",
            min_value=0.0,
            max_value=1.0,
            default_value=0.6,
            warning_threshold=0.85,
            critical_threshold=0.95
        )
    }