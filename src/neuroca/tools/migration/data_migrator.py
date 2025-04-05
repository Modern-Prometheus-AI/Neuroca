"""
Data Migrator for NeuroCognitive Architecture (NCA)

This module provides a robust framework for migrating data between different versions
of the NCA system. It supports:
- Schema migrations for all memory tiers (working, episodic, semantic)
- Data transformations during migrations
- Validation of data integrity before and after migrations
- Rollback capabilities in case of migration failures
- Detailed logging and reporting of migration processes

Usage:
    # Basic usage with default configuration
    migrator = DataMigrator()
    migrator.migrate()

    # Migration with specific version targets
    migrator = DataMigrator(source_version="1.0.0", target_version="2.0.0")
    migrator.migrate()

    # Migration with custom handlers
    migrator = DataMigrator()
    migrator.register_migration_handler("1.0.0", "1.1.0", custom_handler_function)
    migrator.migrate()
"""

import datetime
import importlib
import json
import logging
import os
import re
import tempfile
import time
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Optional

import yaml

# Configure logging
logger = logging.getLogger(__name__)


class MigrationError(Exception):
    """Base exception for all migration-related errors."""
    pass


class ValidationError(MigrationError):
    """Exception raised when data validation fails during migration."""
    pass


class MigrationNotFoundError(MigrationError):
    """Exception raised when a required migration path is not found."""
    pass


class RollbackError(MigrationError):
    """Exception raised when rollback operation fails."""
    pass


class MigrationType(Enum):
    """Types of migrations supported by the system."""
    SCHEMA = auto()  # Database schema changes
    DATA = auto()    # Data transformations
    CONFIG = auto()  # Configuration changes
    MIXED = auto()   # Combination of different types


class MemoryTier(Enum):
    """Memory tiers in the NCA system."""
    WORKING = auto()
    EPISODIC = auto()
    SEMANTIC = auto()
    ALL = auto()


@dataclass
class MigrationContext:
    """Context information for a migration operation."""
    source_version: str
    target_version: str
    migration_type: MigrationType
    affected_tiers: list[MemoryTier]
    timestamp: datetime.datetime = datetime.datetime.now()
    metadata: dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class MigrationResult:
    """Result of a migration operation."""
    success: bool
    context: MigrationContext
    duration_seconds: float
    error: Optional[Exception] = None
    details: dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}
    
    @property
    def has_error(self) -> bool:
        """Check if the migration resulted in an error."""
        return self.error is not None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert the result to a dictionary for serialization."""
        result = {
            "success": self.success,
            "source_version": self.context.source_version,
            "target_version": self.context.target_version,
            "migration_type": self.context.migration_type.name,
            "affected_tiers": [tier.name for tier in self.context.affected_tiers],
            "timestamp": self.context.timestamp.isoformat(),
            "duration_seconds": self.duration_seconds,
            "details": self.details
        }
        
        if self.error:
            result["error"] = {
                "type": type(self.error).__name__,
                "message": str(self.error),
                "traceback": traceback.format_exception(
                    type(self.error), self.error, self.error.__traceback__
                )
            }
            
        return result


class MigrationHandler(ABC):
    """Abstract base class for migration handlers."""
    
    @abstractmethod
    def can_handle(self, source_version: str, target_version: str) -> bool:
        """
        Check if this handler can migrate from source_version to target_version.
        
        Args:
            source_version: The current version of the data
            target_version: The target version to migrate to
            
        Returns:
            bool: True if this handler can perform the migration
        """
        pass
    
    @abstractmethod
    def migrate(self, context: MigrationContext, data: Any) -> Any:
        """
        Perform the migration from source to target version.
        
        Args:
            context: Migration context with metadata
            data: The data to migrate
            
        Returns:
            The migrated data
            
        Raises:
            MigrationError: If migration fails
        """
        pass
    
    @abstractmethod
    def validate(self, context: MigrationContext, data: Any) -> bool:
        """
        Validate that the data conforms to the expected schema for the target version.
        
        Args:
            context: Migration context with metadata
            data: The data to validate
            
        Returns:
            bool: True if validation passes
            
        Raises:
            ValidationError: If validation fails
        """
        pass
    
    @abstractmethod
    def rollback(self, context: MigrationContext, data: Any, backup: Any) -> Any:
        """
        Roll back a failed migration.
        
        Args:
            context: Migration context with metadata
            data: The current (potentially corrupted) data
            backup: The backup data from before migration
            
        Returns:
            The restored data
            
        Raises:
            RollbackError: If rollback fails
        """
        pass


class VersionPathFinder:
    """Utility class to find migration paths between versions."""
    
    def __init__(self, available_migrations: dict[tuple[str, str], MigrationHandler]):
        """
        Initialize with available migrations.
        
        Args:
            available_migrations: Dictionary mapping version pairs to handlers
        """
        self.available_migrations = available_migrations
        self._build_version_graph()
    
    def _build_version_graph(self):
        """Build a graph representation of available migrations."""
        self.graph = {}
        for (source, target) in self.available_migrations:
            if source not in self.graph:
                self.graph[source] = set()
            self.graph[source].add(target)
    
    def find_path(self, source_version: str, target_version: str) -> list[tuple[str, str]]:
        """
        Find a path from source_version to target_version using available migrations.
        
        Args:
            source_version: Starting version
            target_version: Target version
            
        Returns:
            List of (source, target) version pairs representing the migration path
            
        Raises:
            MigrationNotFoundError: If no path exists
        """
        if source_version == target_version:
            return []
        
        # Direct path check
        if (source_version, target_version) in self.available_migrations:
            return [(source_version, target_version)]
        
        # BFS to find shortest path
        queue = [(source_version, [])]
        visited = {source_version}
        
        while queue:
            current, path = queue.pop(0)
            
            if current not in self.graph:
                continue
                
            for neighbor in self.graph[current]:
                if neighbor == target_version:
                    return path + [(current, neighbor)]
                
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [(current, neighbor)]))
        
        raise MigrationNotFoundError(
            f"No migration path found from {source_version} to {target_version}"
        )


class DataMigrator:
    """
    Main class for handling data migrations between different versions of the NCA system.
    
    This class orchestrates the migration process, including:
    - Finding the appropriate migration path
    - Creating backups before migration
    - Executing migrations in sequence
    - Validating results
    - Rolling back in case of failures
    - Logging and reporting
    """
    
    def __init__(
        self,
        source_version: Optional[str] = None,
        target_version: Optional[str] = None,
        config_path: Optional[str] = None,
        backup_dir: Optional[str] = None,
        auto_backup: bool = True,
        dry_run: bool = False
    ):
        """
        Initialize the data migrator.
        
        Args:
            source_version: Current version of the data (if None, will be detected)
            target_version: Target version to migrate to (if None, will use latest)
            config_path: Path to migration configuration file
            backup_dir: Directory to store backups (if None, uses system temp dir)
            auto_backup: Whether to automatically create backups before migration
            dry_run: If True, simulates migration without making changes
        """
        self.source_version = source_version
        self.target_version = target_version
        self.config_path = config_path or self._get_default_config_path()
        self.backup_dir = backup_dir or tempfile.gettempdir()
        self.auto_backup = auto_backup
        self.dry_run = dry_run
        
        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Initialize handlers registry
        self.migration_handlers: dict[tuple[str, str], MigrationHandler] = {}
        
        # Load configuration
        self._load_config()
        
        # Initialize version path finder
        self.path_finder = VersionPathFinder(self.migration_handlers)
        
        logger.info(f"Initialized DataMigrator (dry_run={dry_run})")
    
    def _get_default_config_path(self) -> str:
        """Get the default path for migration configuration."""
        return os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "config",
            "migration.yaml"
        )
    
    def _load_config(self):
        """Load migration configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path) as f:
                    config = yaml.safe_load(f)
                
                # Load migration handlers from configuration
                if 'migrations' in config:
                    for migration in config['migrations']:
                        source = migration.get('source_version')
                        target = migration.get('target_version')
                        handler_path = migration.get('handler')
                        
                        if source and target and handler_path:
                            self._load_handler(source, target, handler_path)
                
                # Set default versions if not provided
                if not self.source_version and 'current_version' in config:
                    self.source_version = config['current_version']
                
                if not self.target_version and 'latest_version' in config:
                    self.target_version = config['latest_version']
                
                logger.debug(f"Loaded configuration from {self.config_path}")
            else:
                logger.warning(f"Configuration file not found: {self.config_path}")
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            raise
    
    def _load_handler(self, source_version: str, target_version: str, handler_path: str):
        """
        Dynamically load a migration handler from a module path.
        
        Args:
            source_version: Source version for the migration
            target_version: Target version for the migration
            handler_path: Module path to the handler class (module.submodule:ClassName)
        """
        try:
            module_path, class_name = handler_path.split(':')
            module = importlib.import_module(module_path)
            handler_class = getattr(module, class_name)
            handler = handler_class()
            
            self.register_migration_handler(source_version, target_version, handler)
            logger.debug(f"Loaded handler {handler_path} for {source_version} -> {target_version}")
        except (ImportError, AttributeError, ValueError) as e:
            logger.error(f"Failed to load handler {handler_path}: {str(e)}")
            raise
    
    def register_migration_handler(
        self, 
        source_version: str, 
        target_version: str, 
        handler: MigrationHandler
    ):
        """
        Register a migration handler for a specific version transition.
        
        Args:
            source_version: Source version for the migration
            target_version: Target version for the migration
            handler: Migration handler instance
        """
        self.migration_handlers[(source_version, target_version)] = handler
        # Rebuild the path finder with updated handlers
        self.path_finder = VersionPathFinder(self.migration_handlers)
        logger.debug(f"Registered handler for {source_version} -> {target_version}")
    
    def detect_version(self, data: Any) -> str:
        """
        Detect the version of the provided data.
        
        Args:
            data: The data to analyze
            
        Returns:
            Detected version string
            
        Raises:
            MigrationError: If version cannot be detected
        """
        # Implementation depends on how version information is stored in the data
        # This is a simplified example
        if isinstance(data, dict) and 'version' in data:
            return data['version']
        
        # Try to infer from structure
        for handler in set(self.migration_handlers.values()):
            if hasattr(handler, 'detect_version') and callable(handler.detect_version):
                try:
                    detected = handler.detect_version(data)
                    if detected:
                        return detected
                except:
                    continue
        
        raise MigrationError("Could not detect data version")
    
    def create_backup(self, data: Any, context: MigrationContext) -> str:
        """
        Create a backup of the data before migration.
        
        Args:
            data: The data to back up
            context: Migration context
            
        Returns:
            Path to the backup file
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{context.source_version}_to_{context.target_version}_{timestamp}.json"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        try:
            with open(backup_path, 'w') as f:
                json.dump({
                    'data': data,
                    'context': {
                        'source_version': context.source_version,
                        'target_version': context.target_version,
                        'migration_type': context.migration_type.name,
                        'affected_tiers': [tier.name for tier in context.affected_tiers],
                        'timestamp': context.timestamp.isoformat(),
                        'metadata': context.metadata
                    }
                }, f, indent=2)
            
            logger.info(f"Created backup at {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to create backup: {str(e)}")
            raise MigrationError(f"Backup creation failed: {str(e)}")
    
    def load_backup(self, backup_path: str) -> tuple[Any, MigrationContext]:
        """
        Load data from a backup file.
        
        Args:
            backup_path: Path to the backup file
            
        Returns:
            Tuple of (data, context)
            
        Raises:
            MigrationError: If backup cannot be loaded
        """
        try:
            with open(backup_path) as f:
                backup = json.load(f)
            
            data = backup['data']
            context_dict = backup['context']
            
            context = MigrationContext(
                source_version=context_dict['source_version'],
                target_version=context_dict['target_version'],
                migration_type=MigrationType[context_dict['migration_type']],
                affected_tiers=[MemoryTier[tier] for tier in context_dict['affected_tiers']],
                timestamp=datetime.datetime.fromisoformat(context_dict['timestamp']),
                metadata=context_dict.get('metadata', {})
            )
            
            return data, context
        except Exception as e:
            logger.error(f"Failed to load backup: {str(e)}")
            raise MigrationError(f"Backup loading failed: {str(e)}")
    
    def migrate(self, data: Any = None) -> MigrationResult:
        """
        Perform migration from source version to target version.
        
        Args:
            data: The data to migrate (if None, will be loaded from the system)
            
        Returns:
            MigrationResult object with migration results
            
        Raises:
            MigrationError: If migration fails
        """
        start_time = time.time()
        
        try:
            # Detect versions if not provided
            if data is not None and not self.source_version:
                self.source_version = self.detect_version(data)
            
            if not self.source_version or not self.target_version:
                raise MigrationError(
                    "Source and target versions must be specified or detectable"
                )
            
            # Check if migration is needed
            if self.source_version == self.target_version:
                logger.info(f"No migration needed (already at version {self.target_version})")
                context = MigrationContext(
                    source_version=self.source_version,
                    target_version=self.target_version,
                    migration_type=MigrationType.MIXED,
                    affected_tiers=[MemoryTier.ALL]
                )
                return MigrationResult(
                    success=True,
                    context=context,
                    duration_seconds=time.time() - start_time,
                    details={"message": "No migration needed"}
                )
            
            # Find migration path
            migration_path = self.path_finder.find_path(
                self.source_version, self.target_version
            )
            
            logger.info(
                f"Migration path: {' -> '.join([v[0] for v in migration_path] + [self.target_version])}"
            )
            
            # Perform migrations step by step
            current_data = data
            
            for source, target in migration_path:
                handler = self.migration_handlers[(source, target)]
                
                # Create context for this step
                context = MigrationContext(
                    source_version=source,
                    target_version=target,
                    migration_type=MigrationType.MIXED,  # Could be more specific based on handler
                    affected_tiers=[MemoryTier.ALL]  # Could be more specific based on handler
                )
                
                # Create backup if enabled
                if self.auto_backup and not self.dry_run:
                    self.create_backup(current_data, context)
                
                # Perform migration step
                logger.info(f"Migrating from {source} to {target}...")
                
                if not self.dry_run:
                    # Actual migration
                    migrated_data = handler.migrate(context, current_data)
                    
                    # Validate result
                    if not handler.validate(context, migrated_data):
                        raise ValidationError(f"Validation failed for {source} -> {target}")
                    
                    current_data = migrated_data
                else:
                    # Dry run - just validate that the handler can process the data
                    if not handler.can_handle(source, target):
                        raise MigrationError(
                            f"Handler cannot migrate from {source} to {target}"
                        )
                    logger.info(f"Dry run: skipping actual migration from {source} to {target}")
                
            
            # Create final result
            final_context = MigrationContext(
                source_version=self.source_version,
                target_version=self.target_version,
                migration_type=MigrationType.MIXED,
                affected_tiers=[MemoryTier.ALL]
            )
            
            result = MigrationResult(
                success=True,
                context=final_context,
                duration_seconds=time.time() - start_time,
                details={
                    "migration_path": [f"{s} -> {t}" for s, t in migration_path],
                    "dry_run": self.dry_run
                }
            )
            
            logger.info(
                f"Migration {'simulation ' if self.dry_run else ''}completed successfully "
                f"({result.duration_seconds:.2f}s)"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            logger.debug(traceback.format_exc())
            
            # Create error result
            error_context = MigrationContext(
                source_version=self.source_version or "unknown",
                target_version=self.target_version or "unknown",
                migration_type=MigrationType.MIXED,
                affected_tiers=[MemoryTier.ALL]
            )
            
            return MigrationResult(
                success=False,
                context=error_context,
                duration_seconds=time.time() - start_time,
                error=e
            )
    
    def rollback(self, backup_path: str) -> MigrationResult:
        """
        Roll back to a previous state using a backup.
        
        Args:
            backup_path: Path to the backup file
            
        Returns:
            MigrationResult for the rollback operation
            
        Raises:
            RollbackError: If rollback fails
        """
        start_time = time.time()
        
        try:
            # Load backup
            data, context = self.load_backup(backup_path)
            
            # Swap source and target for rollback context
            rollback_context = MigrationContext(
                source_version=context.target_version,
                target_version=context.source_version,
                migration_type=context.migration_type,
                affected_tiers=context.affected_tiers,
                metadata={**context.metadata, "rollback": True}
            )
            
            logger.info(
                f"Rolling back from {rollback_context.source_version} "
                f"to {rollback_context.target_version}"
            )
            
            if self.dry_run:
                logger.info("Dry run: skipping actual rollback")
                return MigrationResult(
                    success=True,
                    context=rollback_context,
                    duration_seconds=time.time() - start_time,
                    details={"dry_run": True, "backup_path": backup_path}
                )
            
            # NOTE: Actual rollback logic needs implementation.
            # This typically involves restoring data from the backup
            # and updating version metadata. Current implementation assumes
            # the caller handles the restoration based on the returned backup data.
            
            logger.info(f"Rollback process initiated for backup: {backup_path}")
            
            return MigrationResult(
                success=True,
                context=rollback_context,
                duration_seconds=time.time() - start_time,
                details={"backup_path": backup_path}
            )
            
        except Exception as e:
            logger.error(f"Rollback failed: {str(e)}")
            logger.debug(traceback.format_exc())
            
            # Create error result
            error_context = MigrationContext(
                source_version="unknown",
                target_version="unknown",
                migration_type=MigrationType.MIXED,
                affected_tiers=[MemoryTier.ALL],
                metadata={"rollback": True}
            )
            
            return MigrationResult(
                success=False,
                context=error_context,
                duration_seconds=time.time() - start_time,
                error=e
            )
    
    def list_available_migrations(self) -> list[dict[str, str]]:
        """
        List all available migrations.
        
        Returns:
            List of dictionaries with source and target version information
        """
        return [
            {"source": source, "target": target}
            for source, target in self.migration_handlers
        ]
    
    def list_backups(self) -> list[dict[str, Any]]:
        """
        List all available backups.
        
        Returns:
            List of dictionaries with backup information
        """
        backups = []
        
        backup_pattern = re.compile(r"backup_(.+)_to_(.+)_(\d{8}_\d{6})\.json")
        
        for filename in os.listdir(self.backup_dir):
            match = backup_pattern.match(filename)
            if match:
                source, target, timestamp = match.groups()
                backup_path = os.path.join(self.backup_dir, filename)
                
                try:
                    # Get file stats
                    stats = os.stat(backup_path)
                    
                    backups.append({
                        "filename": filename,
                        "path": backup_path,
                        "source_version": source,
                        "target_version": target,
                        "timestamp": datetime.datetime.strptime(
                            timestamp, "%Y%m%d_%H%M%S"
                        ).isoformat(),
                        "size_bytes": stats.st_size,
                        "created": datetime.datetime.fromtimestamp(
                            stats.st_ctime
                        ).isoformat()
                    })
                except Exception as e:
                    logger.warning(f"Error processing backup {filename}: {str(e)}")
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x["created"], reverse=True)
        return backups


# Example of a simple migration handler implementation
class SchemaMigrationHandler(MigrationHandler):
    """Example handler for schema migrations."""
    
    def __init__(self, source_version: str, target_version: str):
        self.source_version = source_version
        self.target_version = target_version
    
    def can_handle(self, source_version: str, target_version: str) -> bool:
        return (
            source_version == self.source_version and 
            target_version == self.target_version
        )
    
    def migrate(self, context: MigrationContext, data: Any) -> Any:
        # Implementation would depend on the specific migration
        logger.info(f"Migrating schema from {context.source_version} to {context.target_version}")
        
        # Example transformation
        if isinstance(data, dict):
            # Make a copy to avoid modifying the original
            result = data.copy()
            
            # Update version
            result['version'] = context.target_version
            
            # Perform schema transformations here
            # ...
            
            return result
        
        raise MigrationError("Data format not supported")
    
    def validate(self, context: MigrationContext, data: Any) -> bool:
        # Validate that the data conforms to the target schema
        if not isinstance(data, dict):
            return False
        
        if data.get('version') != context.target_version:
            return False
        
        # Additional validation logic here
        # ...
        
        return True
    
    def rollback(self, context: MigrationContext, data: Any, backup: Any) -> Any:
        # Simple rollback by returning the backup
        logger.info(f"Rolling back from {context.source_version} to {context.target_version}")
        return backup


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Create migrator
    migrator = DataMigrator(
        source_version="1.0.0",
        target_version="2.0.0",
        dry_run=True
    )
    
    # Register a sample handler
    migrator.register_migration_handler(
        "1.0.0", "2.0.0", 
        SchemaMigrationHandler("1.0.0", "2.0.0")
    )
    
    # Sample data
    sample_data = {
        "version": "1.0.0",
        "content": "Sample data"
    }
    
    # Perform migration
    result = migrator.migrate(sample_data)
    
    # Print result
    print(f"Migration success: {result.success}")
    if not result.success:
        print(f"Error: {result.error}")
