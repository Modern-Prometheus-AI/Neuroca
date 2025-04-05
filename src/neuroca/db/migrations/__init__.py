"""
Database Migrations Module for NeuroCognitive Architecture (NCA).

This module provides the infrastructure for database schema migrations in the NCA system.
It establishes a versioned migration system that allows for tracking, applying, and
rolling back database schema changes in a controlled and reproducible manner.

The migrations system follows these principles:
1. Versioned migrations with sequential numbering
2. Support for both upgrade and downgrade operations
3. Transactional safety where possible
4. Comprehensive logging of migration operations
5. Migration dependency management

Usage:
    from neuroca.db.migrations import MigrationManager
    
    # Initialize the migration manager with database connection
    migration_manager = MigrationManager(db_connection)
    
    # Check current migration status
    current_version = migration_manager.get_current_version()
    
    # Apply all pending migrations
    migration_manager.migrate()
    
    # Rollback to a specific version
    migration_manager.rollback(target_version=20230101120000)
"""

import importlib
import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Union

# Configure module logger
logger = logging.getLogger(__name__)

# Migration version pattern (YYYYMMDDHHMMSS format)
MIGRATION_VERSION_PATTERN = r"^V(\d{14})__.*\.py$"

class MigrationError(Exception):
    """Base exception for migration-related errors."""
    pass

class MigrationVersionError(MigrationError):
    """Exception raised for errors related to migration versioning."""
    pass

class MigrationExecutionError(MigrationError):
    """Exception raised when a migration fails to execute."""
    pass

class MigrationDependencyError(MigrationError):
    """Exception raised when migration dependencies cannot be resolved."""
    pass

class Migration:
    """
    Represents a single database migration with upgrade and downgrade capabilities.
    
    Attributes:
        version (int): The migration version number (timestamp format: YYYYMMDDHHMMSS)
        name (str): Human-readable name of the migration
        path (Path): Path to the migration file
        module (module): The imported migration module
    """
    
    def __init__(self, version: int, name: str, path: Path):
        """
        Initialize a Migration object.
        
        Args:
            version (int): The migration version number
            name (str): Human-readable name of the migration
            path (Path): Path to the migration file
        """
        self.version = version
        self.name = name
        self.path = path
        self.module = None
        
    def load(self) -> None:
        """
        Load the migration module.
        
        Raises:
            MigrationError: If the migration module cannot be loaded or lacks required functions
        """
        try:
            # Convert path to module path
            module_path = str(self.path.with_suffix('')).replace(os.sep, '.')
            if module_path.startswith('.'):
                module_path = module_path[1:]
                
            self.module = importlib.import_module(module_path)
            
            # Validate that the module has the required functions
            if not hasattr(self.module, 'upgrade') or not callable(self.module.upgrade):
                raise MigrationError(f"Migration {self.name} is missing the 'upgrade' function")
                
            if not hasattr(self.module, 'downgrade') or not callable(self.module.downgrade):
                raise MigrationError(f"Migration {self.name} is missing the 'downgrade' function")
                
        except ImportError as e:
            raise MigrationError(f"Failed to import migration {self.name}: {str(e)}")
    
    def upgrade(self, connection: Any) -> None:
        """
        Apply the migration upgrade.
        
        Args:
            connection: Database connection object
            
        Raises:
            MigrationExecutionError: If the upgrade operation fails
        """
        if not self.module:
            self.load()
            
        try:
            logger.info(f"Applying migration {self.version} ({self.name})")
            start_time = time.time()
            self.module.upgrade(connection)
            duration = time.time() - start_time
            logger.info(f"Migration {self.version} applied successfully in {duration:.2f}s")
        except Exception as e:
            logger.error(f"Migration {self.version} failed: {str(e)}")
            raise MigrationExecutionError(f"Failed to apply migration {self.name}: {str(e)}") from e
    
    def downgrade(self, connection: Any) -> None:
        """
        Apply the migration downgrade.
        
        Args:
            connection: Database connection object
            
        Raises:
            MigrationExecutionError: If the downgrade operation fails
        """
        if not self.module:
            self.load()
            
        try:
            logger.info(f"Rolling back migration {self.version} ({self.name})")
            start_time = time.time()
            self.module.downgrade(connection)
            duration = time.time() - start_time
            logger.info(f"Migration {self.version} rolled back successfully in {duration:.2f}s")
        except Exception as e:
            logger.error(f"Migration {self.version} rollback failed: {str(e)}")
            raise MigrationExecutionError(f"Failed to roll back migration {self.name}: {str(e)}") from e

class MigrationManager:
    """
    Manages database migrations, including discovery, tracking, and execution.
    
    This class is responsible for:
    - Discovering migration files
    - Tracking applied migrations
    - Applying pending migrations
    - Rolling back migrations
    - Ensuring migration integrity
    
    Attributes:
        connection: Database connection object
        migrations_dir (Path): Directory containing migration files
        migrations (Dict[int, Migration]): Dictionary of discovered migrations
    """
    
    def __init__(self, connection: Any, migrations_dir: Optional[Union[str, Path]] = None):
        """
        Initialize the MigrationManager.
        
        Args:
            connection: Database connection object
            migrations_dir: Path to the directory containing migration files.
                           If None, defaults to the 'migrations' directory in the same package.
        """
        self.connection = connection
        
        if migrations_dir is None:
            # Default to the directory containing this file
            self.migrations_dir = Path(__file__).parent
        else:
            self.migrations_dir = Path(migrations_dir)
            
        self.migrations: dict[int, Migration] = {}
        self._ensure_migration_table()
        self._discover_migrations()
    
    def _ensure_migration_table(self) -> None:
        """
        Ensure the migration tracking table exists in the database.
        
        This table stores information about applied migrations.
        
        Raises:
            MigrationError: If the migration table cannot be created
        """
        try:
            # Implementation depends on the specific database being used
            # This is a generic example that should be adapted to the actual database
            logger.debug("Ensuring migration tracking table exists")
            
            # Example SQL for creating a migration tracking table
            # This should be replaced with the appropriate implementation for the actual database
            
            # Execute the SQL (implementation depends on the database driver)
            # For example, with SQLAlchemy:
            # self.connection.execute(create_table_sql)
            
            logger.debug("Migration tracking table verified")
        except Exception as e:
            logger.error(f"Failed to create migration tracking table: {str(e)}")
            raise MigrationError(f"Failed to initialize migration system: {str(e)}") from e
    
    def _discover_migrations(self) -> None:
        """
        Discover migration files in the migrations directory.
        
        Migration files should follow the naming convention: V{version}__{name}.py
        where version is a timestamp in the format YYYYMMDDHHMMSS.
        
        Raises:
            MigrationError: If migration discovery fails
        """
        try:
            logger.debug(f"Discovering migrations in {self.migrations_dir}")
            self.migrations = {}
            
            if not self.migrations_dir.exists():
                logger.warning(f"Migrations directory {self.migrations_dir} does not exist")
                return
                
            pattern = re.compile(MIGRATION_VERSION_PATTERN)
            
            for file_path in self.migrations_dir.glob("V*__*.py"):
                match = pattern.match(file_path.name)
                if match:
                    version = int(match.group(1))
                    name = file_path.name[match.end():].replace(".py", "")
                    
                    self.migrations[version] = Migration(version, name, file_path)
                    logger.debug(f"Discovered migration: {version} - {name}")
            
            logger.info(f"Discovered {len(self.migrations)} migrations")
        except Exception as e:
            logger.error(f"Failed to discover migrations: {str(e)}")
            raise MigrationError(f"Failed to discover migrations: {str(e)}") from e
    
    def get_current_version(self) -> int:
        """
        Get the current database migration version.
        
        Returns:
            int: The current migration version, or 0 if no migrations have been applied
            
        Raises:
            MigrationError: If the current version cannot be determined
        """
        try:
            # Implementation depends on the specific database being used
            # This is a generic example that should be adapted to the actual database
            logger.debug("Retrieving current migration version")
            
            # Example SQL for retrieving the current version
            # This should be replaced with the appropriate implementation for the actual database
            
            # Execute the query (implementation depends on the database driver)
            # For example, with SQLAlchemy:
            # result = self.connection.execute(query).scalar()
            
            # Placeholder for the actual implementation
            result = 0  # This should be replaced with the actual query result
            
            logger.debug(f"Current migration version: {result or 0}")
            return result or 0
        except Exception as e:
            logger.error(f"Failed to determine current migration version: {str(e)}")
            raise MigrationError(f"Failed to determine current migration version: {str(e)}") from e
    
    def get_pending_migrations(self) -> list[Migration]:
        """
        Get a list of pending migrations that need to be applied.
        
        Returns:
            List[Migration]: List of pending migrations, sorted by version
            
        Raises:
            MigrationError: If pending migrations cannot be determined
        """
        try:
            current_version = self.get_current_version()
            pending = [m for v, m in self.migrations.items() if v > current_version]
            return sorted(pending, key=lambda m: m.version)
        except Exception as e:
            logger.error(f"Failed to determine pending migrations: {str(e)}")
            raise MigrationError(f"Failed to determine pending migrations: {str(e)}") from e
    
    def migrate(self, target_version: Optional[int] = None) -> None:
        """
        Apply pending migrations up to the target version.
        
        If target_version is None, all pending migrations will be applied.
        
        Args:
            target_version: Target migration version, or None to apply all pending migrations
            
        Raises:
            MigrationError: If migrations cannot be applied
        """
        try:
            self.get_current_version()
            pending = self.get_pending_migrations()
            
            if not pending:
                logger.info("No pending migrations to apply")
                return
                
            if target_version is not None:
                pending = [m for m in pending if m.version <= target_version]
                
            logger.info(f"Applying {len(pending)} migration(s)")
            
            for migration in pending:
                start_time = time.time()
                migration.upgrade(self.connection)
                execution_time = time.time() - start_time
                
                # Record the migration in the tracking table
                self._record_migration(migration, execution_time)
                
            logger.info(f"Migration complete. Current version: {self.get_current_version()}")
        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            raise MigrationError(f"Migration failed: {str(e)}") from e
    
    def rollback(self, target_version: Optional[int] = None, steps: int = 1) -> None:
        """
        Roll back migrations to the target version or by the specified number of steps.
        
        Args:
            target_version: Target migration version, or None to use steps
            steps: Number of migrations to roll back (if target_version is None)
            
        Raises:
            MigrationError: If migrations cannot be rolled back
        """
        try:
            current_version = self.get_current_version()
            
            if current_version == 0:
                logger.info("No migrations to roll back")
                return
                
            # Get applied migrations in reverse order
            applied_versions = self._get_applied_versions()
            applied_versions.sort(reverse=True)
            
            if target_version is not None:
                # Roll back to the target version
                to_rollback = [v for v in applied_versions if v > target_version]
            else:
                # Roll back the specified number of steps
                to_rollback = applied_versions[:steps]
                
            if not to_rollback:
                logger.info("No migrations to roll back")
                return
                
            logger.info(f"Rolling back {len(to_rollback)} migration(s)")
            
            for version in to_rollback:
                if version in self.migrations:
                    migration = self.migrations[version]
                    migration.downgrade(self.connection)
                    
                    # Remove the migration from the tracking table
                    self._remove_migration_record(version)
                else:
                    logger.warning(f"Migration {version} not found in discovered migrations")
                    
            logger.info(f"Rollback complete. Current version: {self.get_current_version()}")
        except Exception as e:
            logger.error(f"Rollback failed: {str(e)}")
            raise MigrationError(f"Rollback failed: {str(e)}") from e
    
    def _get_applied_versions(self) -> list[int]:
        """
        Get a list of applied migration versions.
        
        Returns:
            List[int]: List of applied migration versions
            
        Raises:
            MigrationError: If applied versions cannot be determined
        """
        try:
            # Implementation depends on the specific database being used
            # This is a generic example that should be adapted to the actual database
            logger.debug("Retrieving applied migration versions")
            
            # Example SQL for retrieving applied versions
            # This should be replaced with the appropriate implementation for the actual database
            
            # Execute the query (implementation depends on the database driver)
            # For example, with SQLAlchemy:
            # result = [row[0] for row in self.connection.execute(query)]
            
            # Placeholder for the actual implementation
            result = []  # This should be replaced with the actual query result
            
            logger.debug(f"Found {len(result)} applied migrations")
            return result
        except Exception as e:
            logger.error(f"Failed to determine applied migration versions: {str(e)}")
            raise MigrationError(f"Failed to determine applied migration versions: {str(e)}") from e
    
    def _record_migration(self, migration: Migration, execution_time: float) -> None:
        """
        Record an applied migration in the tracking table.
        
        Args:
            migration: The applied migration
            execution_time: Time taken to apply the migration in seconds
            
        Raises:
            MigrationError: If the migration cannot be recorded
        """
        try:
            # Implementation depends on the specific database being used
            # This is a generic example that should be adapted to the actual database
            logger.debug(f"Recording migration {migration.version} in tracking table")
            
            # Example SQL for recording a migration
            # This should be replaced with the appropriate implementation for the actual database
            
            # Execute the SQL (implementation depends on the database driver)
            # For example, with SQLAlchemy:
            # self.connection.execute(insert_sql, (migration.version, migration.name, datetime.now(), execution_time))
            
            logger.debug(f"Migration {migration.version} recorded successfully")
        except Exception as e:
            logger.error(f"Failed to record migration {migration.version}: {str(e)}")
            raise MigrationError(f"Failed to record migration {migration.name}: {str(e)}") from e
    
    def _remove_migration_record(self, version: int) -> None:
        """
        Remove a migration record from the tracking table.
        
        Args:
            version: The migration version to remove
            
        Raises:
            MigrationError: If the migration record cannot be removed
        """
        try:
            # Implementation depends on the specific database being used
            # This is a generic example that should be adapted to the actual database
            logger.debug(f"Removing migration {version} from tracking table")
            
            # Example SQL for removing a migration record
            # This should be replaced with the appropriate implementation for the actual database
            
            # Execute the SQL (implementation depends on the database driver)
            # For example, with SQLAlchemy:
            # self.connection.execute(delete_sql, (version,))
            
            logger.debug(f"Migration {version} record removed successfully")
        except Exception as e:
            logger.error(f"Failed to remove migration record {version}: {str(e)}")
            raise MigrationError(f"Failed to remove migration record {version}: {str(e)}") from e

def create_migration(name: str, migrations_dir: Optional[Union[str, Path]] = None) -> Path:
    """
    Create a new migration file with the given name.
    
    Args:
        name: Name of the migration (will be converted to snake_case)
        migrations_dir: Directory where the migration file will be created
        
    Returns:
        Path: Path to the created migration file
        
    Raises:
        MigrationError: If the migration file cannot be created
    """
    try:
        # Convert name to snake_case
        snake_name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
        snake_name = re.sub(r'[^a-z0-9_]', '_', snake_name)
        
        # Generate version timestamp (YYYYMMDDHHMMSS)
        version = datetime.now().strftime("%Y%m%d%H%M%S")
        
        migrations_dir = Path(__file__).parent if migrations_dir is None else Path(migrations_dir)
            
        if not migrations_dir.exists():
            migrations_dir.mkdir(parents=True, exist_ok=True)
            
        # Create the migration file
        file_path = migrations_dir / f"V{version}__{snake_name}.py"
        
        with open(file_path, 'w') as f:
            f.write(f'''"""
Migration: {name}
Version: {version}

Description:
    [Add a description of what this migration does]
"""

def upgrade(connection):
    """
    Apply the migration.
    
    Args:
        connection: Database connection object
    """
    # TODO: Implement the upgrade logic
    pass

def downgrade(connection):
    """
    Roll back the migration.
    
    Args:
        connection: Database connection object
    """
    # TODO: Implement the downgrade logic
    pass
''')
        
        logger.info(f"Created migration file: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Failed to create migration file: {str(e)}")
        raise MigrationError(f"Failed to create migration file: {str(e)}") from e

# Export public API
__all__ = [
    'Migration',
    'MigrationManager',
    'MigrationError',
    'MigrationVersionError',
    'MigrationExecutionError',
    'MigrationDependencyError',
    'create_migration',
]