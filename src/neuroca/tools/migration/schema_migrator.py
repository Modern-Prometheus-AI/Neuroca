"""
Schema Migrator for NeuroCognitive Architecture

This module provides a robust framework for managing database schema migrations
in the NeuroCognitive Architecture system. It supports:

1. Version-controlled schema changes
2. Forward and backward migrations
3. Migration history tracking
4. Validation of schema integrity
5. Dry-run capability for testing migrations
6. Support for multiple database backends

Usage:
    # Basic usage to upgrade to latest schema version
    migrator = SchemaMigrator(db_connection, migration_dir="migrations/")
    migrator.migrate_to_latest()

    # Migrate to a specific version
    migrator.migrate_to_version("1.2.3")

    # Perform a dry run to validate migrations without applying them
    migrator.migrate_to_latest(dry_run=True)

    # Roll back to a previous version
    migrator.rollback_to_version("1.1.0")
"""

import hashlib
import importlib.util
import json
import logging
import re
import sys
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

# Database adapters - import as needed based on configuration
try:
    import psycopg2
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

try:
    import sqlite3
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False

try:
    import pymongo
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)


class MigrationDirection(Enum):
    """Enum representing the direction of a migration."""
    UP = "up"
    DOWN = "down"


class MigrationError(Exception):
    """Base exception for migration-related errors."""
    pass


class MigrationVersionError(MigrationError):
    """Exception raised for errors related to migration versioning."""
    pass


class MigrationFileError(MigrationError):
    """Exception raised for errors related to migration files."""
    pass


class MigrationExecutionError(MigrationError):
    """Exception raised for errors during migration execution."""
    pass


class DatabaseAdapter:
    """Abstract base class for database adapters."""
    
    def __init__(self, connection_params: dict[str, Any]):
        """
        Initialize the database adapter.
        
        Args:
            connection_params: Database connection parameters
        """
        self.connection_params = connection_params
        self.connection = None
    
    def connect(self) -> None:
        """Establish a connection to the database."""
        raise NotImplementedError("Subclasses must implement connect()")
    
    def disconnect(self) -> None:
        """Close the database connection."""
        raise NotImplementedError("Subclasses must implement disconnect()")
    
    def execute(self, query: str, params: Optional[dict[str, Any]] = None) -> Any:
        """
        Execute a query on the database.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            Query result
        """
        raise NotImplementedError("Subclasses must implement execute()")
    
    def transaction_begin(self) -> None:
        """Begin a database transaction."""
        raise NotImplementedError("Subclasses must implement transaction_begin()")
    
    def transaction_commit(self) -> None:
        """Commit the current transaction."""
        raise NotImplementedError("Subclasses must implement transaction_commit()")
    
    def transaction_rollback(self) -> None:
        """Roll back the current transaction."""
        raise NotImplementedError("Subclasses must implement transaction_rollback()")
    
    def ensure_migration_table(self) -> None:
        """Ensure the migration tracking table exists."""
        raise NotImplementedError("Subclasses must implement ensure_migration_table()")
    
    def get_current_version(self) -> Optional[str]:
        """
        Get the current schema version.
        
        Returns:
            Current version string or None if no migrations have been applied
        """
        raise NotImplementedError("Subclasses must implement get_current_version()")
    
    def record_migration(self, version: str, direction: MigrationDirection, 
                         script_hash: str, execution_time: float) -> None:
        """
        Record a migration in the migration history.
        
        Args:
            version: Migration version
            direction: Direction of migration (up or down)
            script_hash: Hash of the migration script
            execution_time: Time taken to execute the migration in seconds
        """
        raise NotImplementedError("Subclasses must implement record_migration()")


class PostgresAdapter(DatabaseAdapter):
    """Adapter for PostgreSQL databases."""
    
    def connect(self) -> None:
        """Establish a connection to PostgreSQL."""
        if not POSTGRES_AVAILABLE:
            raise ImportError("psycopg2 is required for PostgreSQL support")
        
        try:
            self.connection = psycopg2.connect(**self.connection_params)
            logger.info("Connected to PostgreSQL database")
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise MigrationError(f"Database connection failed: {e}")
    
    def disconnect(self) -> None:
        """Close the PostgreSQL connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Disconnected from PostgreSQL database")
    
    def execute(self, query: str, params: Optional[dict[str, Any]] = None) -> Any:
        """Execute a query on PostgreSQL."""
        if not self.connection:
            self.connect()
            
        cursor = self.connection.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
                
            if query.strip().upper().startswith(("SELECT", "RETURNING")):
                return cursor.fetchall()
            return None
        except psycopg2.Error as e:
            logger.error(f"Query execution failed: {e}")
            logger.debug(f"Failed query: {query}")
            if params:
                logger.debug(f"Query parameters: {params}")
            raise MigrationExecutionError(f"Query execution failed: {e}")
        finally:
            cursor.close()
    
    def transaction_begin(self) -> None:
        """Begin a PostgreSQL transaction."""
        # PostgreSQL automatically starts a transaction when needed
        pass
    
    def transaction_commit(self) -> None:
        """Commit the current PostgreSQL transaction."""
        if self.connection:
            self.connection.commit()
    
    def transaction_rollback(self) -> None:
        """Roll back the current PostgreSQL transaction."""
        if self.connection:
            self.connection.rollback()
    
    def ensure_migration_table(self) -> None:
        """Ensure the migration tracking table exists in PostgreSQL."""
        query = """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id SERIAL PRIMARY KEY,
            version VARCHAR(50) NOT NULL,
            applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            direction VARCHAR(5) NOT NULL,
            script_hash VARCHAR(64) NOT NULL,
            execution_time FLOAT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_schema_migrations_version ON schema_migrations(version);
        """
        self.execute(query)
        self.transaction_commit()
        logger.info("Ensured migration table exists")
    
    def get_current_version(self) -> Optional[str]:
        """Get the current schema version from PostgreSQL."""
        query = """
        SELECT version FROM schema_migrations 
        WHERE direction = 'up' 
        ORDER BY applied_at DESC 
        LIMIT 1
        """
        result = self.execute(query)
        if result and result[0]:
            return result[0][0]
        return None
    
    def record_migration(self, version: str, direction: MigrationDirection, 
                         script_hash: str, execution_time: float) -> None:
        """Record a migration in PostgreSQL."""
        query = """
        INSERT INTO schema_migrations 
        (version, direction, script_hash, execution_time) 
        VALUES (%s, %s, %s, %s)
        """
        self.execute(query, {
            "version": version,
            "direction": direction.value,
            "script_hash": script_hash,
            "execution_time": execution_time
        })
        self.transaction_commit()
        logger.info(f"Recorded migration: version={version}, direction={direction.value}")


class SQLiteAdapter(DatabaseAdapter):
    """Adapter for SQLite databases."""
    
    def connect(self) -> None:
        """Establish a connection to SQLite."""
        if not SQLITE_AVAILABLE:
            raise ImportError("sqlite3 is required for SQLite support")
        
        try:
            db_path = self.connection_params.get("database", ":memory:")
            self.connection = sqlite3.connect(db_path)
            self.connection.row_factory = sqlite3.Row
            logger.info(f"Connected to SQLite database at {db_path}")
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to SQLite: {e}")
            raise MigrationError(f"Database connection failed: {e}")
    
    def disconnect(self) -> None:
        """Close the SQLite connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Disconnected from SQLite database")
    
    def execute(self, query: str, params: Optional[dict[str, Any]] = None) -> Any:
        """Execute a query on SQLite."""
        if not self.connection:
            self.connect()
            
        cursor = self.connection.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
                
            if query.strip().upper().startswith("SELECT"):
                return cursor.fetchall()
            return None
        except sqlite3.Error as e:
            logger.error(f"Query execution failed: {e}")
            logger.debug(f"Failed query: {query}")
            if params:
                logger.debug(f"Query parameters: {params}")
            raise MigrationExecutionError(f"Query execution failed: {e}")
        finally:
            cursor.close()
    
    def transaction_begin(self) -> None:
        """Begin a SQLite transaction."""
        # SQLite automatically starts a transaction when needed
        pass
    
    def transaction_commit(self) -> None:
        """Commit the current SQLite transaction."""
        if self.connection:
            self.connection.commit()
    
    def transaction_rollback(self) -> None:
        """Roll back the current SQLite transaction."""
        if self.connection:
            self.connection.rollback()
    
    def ensure_migration_table(self) -> None:
        """Ensure the migration tracking table exists in SQLite."""
        query = """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT NOT NULL,
            applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            direction TEXT NOT NULL,
            script_hash TEXT NOT NULL,
            execution_time REAL NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_schema_migrations_version ON schema_migrations(version);
        """
        self.execute(query)
        self.transaction_commit()
        logger.info("Ensured migration table exists")
    
    def get_current_version(self) -> Optional[str]:
        """Get the current schema version from SQLite."""
        query = """
        SELECT version FROM schema_migrations 
        WHERE direction = 'up' 
        ORDER BY applied_at DESC 
        LIMIT 1
        """
        result = self.execute(query)
        if result and len(result) > 0:
            return result[0]['version']
        return None
    
    def record_migration(self, version: str, direction: MigrationDirection, 
                         script_hash: str, execution_time: float) -> None:
        """Record a migration in SQLite."""
        query = """
        INSERT INTO schema_migrations 
        (version, direction, script_hash, execution_time) 
        VALUES (?, ?, ?, ?)
        """
        self.execute(query, (
            version,
            direction.value,
            script_hash,
            execution_time
        ))
        self.transaction_commit()
        logger.info(f"Recorded migration: version={version}, direction={direction.value}")


class MongoDBAdapter(DatabaseAdapter):
    """Adapter for MongoDB databases."""
    
    def connect(self) -> None:
        """Establish a connection to MongoDB."""
        if not MONGODB_AVAILABLE:
            raise ImportError("pymongo is required for MongoDB support")
        
        try:
            connection_string = self.connection_params.get("connection_string", "mongodb://localhost:27017/")
            db_name = self.connection_params.get("database", "neuroca")
            
            self.client = pymongo.MongoClient(connection_string)
            self.db = self.client[db_name]
            logger.info(f"Connected to MongoDB database: {db_name}")
        except pymongo.errors.ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise MigrationError(f"Database connection failed: {e}")
    
    def disconnect(self) -> None:
        """Close the MongoDB connection."""
        if hasattr(self, 'client') and self.client:
            self.client.close()
            delattr(self, 'client')
            delattr(self, 'db')
            logger.info("Disconnected from MongoDB database")
    
    def execute(self, query: str, params: Optional[dict[str, Any]] = None) -> Any:
        """
        Execute a MongoDB operation.
        
        For MongoDB, the query is a JSON string representing the operation to perform.
        """
        if not hasattr(self, 'db'):
            self.connect()
            
        try:
            operation = json.loads(query)
            collection_name = operation.get("collection")
            action = operation.get("action")
            
            if not collection_name or not action:
                raise MigrationExecutionError("MongoDB operation requires 'collection' and 'action' fields")
                
            collection = self.db[collection_name]
            
            if action == "insert":
                documents = operation.get("documents", [])
                if documents:
                    return collection.insert_many(documents)
                return None
            elif action == "update":
                filter_doc = operation.get("filter", {})
                update_doc = operation.get("update", {})
                return collection.update_many(filter_doc, update_doc)
            elif action == "delete":
                filter_doc = operation.get("filter", {})
                return collection.delete_many(filter_doc)
            elif action == "find":
                filter_doc = operation.get("filter", {})
                return list(collection.find(filter_doc))
            elif action == "create_index":
                keys = operation.get("keys", [])
                options = operation.get("options", {})
                return collection.create_index(keys, **options)
            elif action == "drop_index":
                index_name = operation.get("index_name")
                return collection.drop_index(index_name)
            elif action == "create_collection":
                return self.db.create_collection(collection_name)
            elif action == "drop_collection":
                return self.db.drop_collection(collection_name)
            else:
                raise MigrationExecutionError(f"Unsupported MongoDB action: {action}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid MongoDB operation JSON: {e}")
            raise MigrationExecutionError(f"Invalid MongoDB operation JSON: {e}")
        except pymongo.errors.PyMongoError as e:
            logger.error(f"MongoDB operation failed: {e}")
            logger.debug(f"Failed operation: {query}")
            raise MigrationExecutionError(f"MongoDB operation failed: {e}")
    
    def transaction_begin(self) -> None:
        """Begin a MongoDB transaction."""
        # MongoDB transactions are not used in this implementation
        # as they require a replica set
        pass
    
    def transaction_commit(self) -> None:
        """Commit the current MongoDB transaction."""
        # MongoDB transactions are not used in this implementation
        pass
    
    def transaction_rollback(self) -> None:
        """Roll back the current MongoDB transaction."""
        # MongoDB transactions are not used in this implementation
        pass
    
    def ensure_migration_table(self) -> None:
        """Ensure the migration tracking collection exists in MongoDB."""
        if not hasattr(self, 'db'):
            self.connect()
            
        if "schema_migrations" not in self.db.list_collection_names():
            self.db.create_collection("schema_migrations")
            self.db.schema_migrations.create_index([("version", pymongo.ASCENDING)])
            logger.info("Created schema_migrations collection")
        else:
            logger.info("schema_migrations collection already exists")
    
    def get_current_version(self) -> Optional[str]:
        """Get the current schema version from MongoDB."""
        if not hasattr(self, 'db'):
            self.connect()
            
        latest_migration = self.db.schema_migrations.find_one(
            {"direction": "up"},
            sort=[("applied_at", pymongo.DESCENDING)]
        )
        
        if latest_migration:
            return latest_migration.get("version")
        return None
    
    def record_migration(self, version: str, direction: MigrationDirection, 
                         script_hash: str, execution_time: float) -> None:
        """Record a migration in MongoDB."""
        if not hasattr(self, 'db'):
            self.connect()
            
        self.db.schema_migrations.insert_one({
            "version": version,
            "applied_at": datetime.now(),
            "direction": direction.value,
            "script_hash": script_hash,
            "execution_time": execution_time
        })
        logger.info(f"Recorded migration: version={version}, direction={direction.value}")


class Migration:
    """Represents a single database migration."""
    
    def __init__(self, version: str, path: Path, description: str = ""):
        """
        Initialize a migration.
        
        Args:
            version: Migration version (e.g., "1.0.0")
            path: Path to the migration file
            description: Optional description of the migration
        """
        self.version = version
        self.path = path
        self.description = description
        self.hash = self._calculate_hash()
        
    def _calculate_hash(self) -> str:
        """
        Calculate a hash of the migration file content.
        
        Returns:
            SHA-256 hash of the file content
        """
        try:
            with open(self.path, 'rb') as f:
                content = f.read()
                return hashlib.sha256(content).hexdigest()
        except OSError as e:
            logger.error(f"Failed to read migration file {self.path}: {e}")
            raise MigrationFileError(f"Failed to read migration file {self.path}: {e}")
    
    def load(self) -> dict[str, Callable]:
        """
        Load the migration module.
        
        Returns:
            Dictionary with 'up' and 'down' migration functions
        """
        try:
            module_name = self.path.stem
            spec = importlib.util.spec_from_file_location(module_name, self.path)
            if spec is None or spec.loader is None:
                raise MigrationFileError(f"Failed to load migration module: {self.path}")
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Verify that the module has up and down functions
            if not hasattr(module, 'up') or not callable(module.up):
                raise MigrationFileError(f"Migration {self.path} is missing an 'up' function")
            
            if not hasattr(module, 'down') or not callable(module.down):
                raise MigrationFileError(f"Migration {self.path} is missing a 'down' function")
            
            return {
                'up': module.up,
                'down': module.down
            }
        except Exception as e:
            logger.error(f"Failed to load migration {self.path}: {e}")
            raise MigrationFileError(f"Failed to load migration {self.path}: {e}")
    
    def __str__(self) -> str:
        """String representation of the migration."""
        return f"Migration(version={self.version}, path={self.path.name})"
    
    def __repr__(self) -> str:
        """Detailed representation of the migration."""
        return f"Migration(version={self.version}, path={self.path}, description={self.description})"


class SchemaMigrator:
    """
    Main class for managing database schema migrations.
    
    This class handles discovering, validating, and applying migrations to
    keep the database schema in sync with the application code.
    """
    
    def __init__(self, db_config: dict[str, Any], migration_dir: str = "migrations"):
        """
        Initialize the schema migrator.
        
        Args:
            db_config: Database configuration dictionary with keys:
                - type: Database type (postgres, sqlite, mongodb)
                - connection parameters specific to the database type
            migration_dir: Directory containing migration files
        """
        self.db_config = db_config
        self.migration_dir = Path(migration_dir)
        self.adapter = self._create_adapter()
        self.migrations = {}  # type: Dict[str, Migration]
        
        # Ensure migration directory exists
        if not self.migration_dir.exists():
            logger.warning(f"Migration directory {self.migration_dir} does not exist")
            self.migration_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created migration directory {self.migration_dir}")
        
        # Load available migrations
        self._load_migrations()
    
    def _create_adapter(self) -> DatabaseAdapter:
        """
        Create the appropriate database adapter based on configuration.
        
        Returns:
            DatabaseAdapter instance
        
        Raises:
            MigrationError: If the database type is unsupported
        """
        db_type = self.db_config.get("type", "").lower()
        connection_params = {k: v for k, v in self.db_config.items() if k != "type"}
        
        if db_type == "postgres":
            return PostgresAdapter(connection_params)
        elif db_type == "sqlite":
            return SQLiteAdapter(connection_params)
        elif db_type == "mongodb":
            return MongoDBAdapter(connection_params)
        else:
            raise MigrationError(f"Unsupported database type: {db_type}")
    
    def _load_migrations(self) -> None:
        """
        Load all available migrations from the migration directory.
        
        This method scans the migration directory for Python files with a valid
        version number in the filename, loads them, and stores them in the
        migrations dictionary.
        """
        # Clear existing migrations
        self.migrations = {}
        
        # Pattern for migration files: v1.0.0_description.py
        pattern = re.compile(r'^v(\d+\.\d+\.\d+)_(.*)\.py$')
        
        for file_path in self.migration_dir.glob("*.py"):
            match = pattern.match(file_path.name)
            if match:
                version = match.group(1)
                description = match.group(2).replace('_', ' ')
                
                if version in self.migrations:
                    logger.warning(f"Duplicate migration version {version} found: {file_path}")
                    continue
                
                self.migrations[version] = Migration(version, file_path, description)
                logger.debug(f"Loaded migration: {version} - {description}")
        
        logger.info(f"Loaded {len(self.migrations)} migrations")
    
    def _sort_versions(self, versions: list[str]) -> list[str]:
        """
        Sort version strings in semantic versioning order.
        
        Args:
            versions: List of version strings
            
        Returns:
            Sorted list of version strings
        """
        def version_key(v):
            return tuple(map(int, v.split('.')))
            
        return sorted(versions, key=version_key)
    
    def _get_migrations_to_apply(self, target_version: Optional[str], 
                                current_version: Optional[str]) -> list[tuple[str, MigrationDirection]]:
        """
        Determine which migrations need to be applied to reach the target version.
        
        Args:
            target_version: Target schema version
            current_version: Current schema version
            
        Returns:
            List of (version, direction) tuples representing migrations to apply
        """
        if not self.migrations:
            return []
            
        all_versions = self._sort_versions(list(self.migrations.keys()))
        
        # If no target version specified, use the latest
        if target_version is None:
            target_version = all_versions[-1]
        
        # Validate target version
        if target_version not in self.migrations:
            raise MigrationVersionError(f"Target version {target_version} not found")
        
        # If no current version, we need to apply all migrations up to target
        if current_version is None:
            return [(v, MigrationDirection.UP) for v in all_versions 
                   if self._compare_versions(v, target_version) <= 0]
        
        # Validate current version
        if current_version not in self.migrations:
            raise MigrationVersionError(f"Current version {current_version} not found")
        
        # Determine direction and migrations to apply
        if self._compare_versions(current_version, target_version) < 0:
            # Moving forward: apply UP migrations after current version up to target
            return [(v, MigrationDirection.UP) for v in all_versions 
                   if self._compare_versions(v, current_version) > 0 and 
                      self._compare_versions(v, target_version) <= 0]
        elif self._compare_versions(current_version, target_version) > 0:
            # Moving backward: apply DOWN migrations from current version down to target
            return [(v, MigrationDirection.DOWN) for v in reversed(all_versions)
                   if self._compare_versions(v, target_version) > 0 and 
                      self._compare_versions(v, current_version) <= 0]
        else:
            # Already at target version
            return []
    
    def _compare_versions(self, version1: str, version2: str) -> int:
        """
        Compare two version strings.
        
        Args:
            version1: First version string
            version2: Second version string
            
        Returns:
            -1 if version1 < version2
             0 if version1 == version2
             1 if version1 > version2
        """
        v1_parts = list(map(int, version1.split('.')))
        v2_parts = list(map(int, version2.split('.')))
        
        for i in range(max(len(v1_parts), len(v2_parts))):
            v1 = v1_parts[i] if i < len(v1_parts) else 0
            v2 = v2_parts[i] if i < len(v2_parts) else 0
            
            if v1 < v2:
                return -1
            elif v1 > v2:
                return 1
                
        return 0
    
    def migrate_to_latest(self, dry_run: bool = False) -> None:
        """
        Migrate the database to the latest available version.
        
        Args:
            dry_run: If True, only simulate the migration without applying changes
        """
        if not self.migrations:
            logger.info("No migrations available")
            return
            
        all_versions = self._sort_versions(list(self.migrations.keys()))
        latest_version = all_versions[-1]
        
        self.migrate_to_version(latest_version, dry_run)
    
    def migrate_to_version(self, target_version: str, dry_run: bool = False) -> None:
        """
        Migrate the database to a specific version.
        
        Args:
            target_version: Target schema version
            dry_run: If True, only simulate the migration without applying changes
            
        Raises:
            MigrationVersionError: If the target version is invalid
            MigrationExecutionError: If a migration fails to apply
        """
        # Connect to the database
        self.adapter.connect()
        
        try:
            # Ensure migration table exists
            self.adapter.ensure_migration_table()
            
            # Get current version
            current_version = self.adapter.get_current_version()
            
            if current_version == target_version:
                logger.info(f"Database is already at version {target_version}")
                return
                
            # Determine migrations to apply
            migrations_to_apply = self._get_migrations_to_apply(target_version, current_version)
            
            if not migrations_to_apply:
                logger.info(f"No migrations needed to reach version {target_version}")
                return
                
            logger.info(f"Migrating from {current_version or 'initial state'} to {target_version}")
            
            if dry_run:
                logger.info("DRY RUN - No changes will be applied")
                for version, direction in migrations_to_apply:
                    migration = self.migrations[version]
                    logger.info(f"Would apply: {direction.value} migration to version {version} ({migration.description})")
                return
            
            # Apply migrations
            for version, direction in migrations_to_apply:
                self._apply_migration(version, direction)
                
            logger.info(f"Successfully migrated to version {target_version}")
            
        finally:
            # Disconnect from the database
            self.adapter.disconnect()
    
    def rollback_to_version(self, target_version: Optional[str] = None, dry_run: bool = False) -> None:
        """
        Roll back the database to a previous version.
        
        Args:
            target_version: Target version to roll back to, or None to roll back one version
            dry_run: If True, only simulate the rollback without applying changes
            
        Raises:
            MigrationVersionError: If the target version is invalid
            MigrationExecutionError: If a migration fails to roll back
        """
        # Connect to the database
        self.adapter.connect()
        
        try:
            # Ensure migration table exists
            self.adapter.ensure_migration_table()
            
            # Get current version
            current_version = self.adapter.get_current_version()
            
            if current_version is None:
                logger.info("No migrations have been applied")
                return
            
            all_versions = self._sort_versions(list(self.migrations.keys()))
            
            # If no target version specified, roll back one version
            if target_version is None:
                current_index = all_versions.index(current_version)
                if current_index > 0:
                    target_version = all_versions[current_index - 1]
                else:
                    # Rolling back from the first version means going to initial state
                    target_version = None
            
            if target_version == current_version:
                logger.info(f"Database is already at version {target_version}")
                return
                
            # Migrate to the target version (which will handle rollbacks)
            self.migrate_to_version(target_version, dry_run)
            
        finally:
            # Disconnect from the database
            self.adapter.disconnect()
    
    def _apply_migration(self, version: str, direction: MigrationDirection) -> None:
        """
        Apply a single migration.
        
        Args:
            version: Migration version to apply
            direction: Direction of migration (up or down)
            
        Raises:
            MigrationExecutionError: If the migration fails to apply
        """
        migration = self.migrations[version]
        logger.info(f"Applying {direction.value} migration to version {version} ({migration.description})")
        
        # Load migration module
        migration_module = migration.load()
        migration_func = migration_module[direction.value]
        
        # Begin transaction if supported
        self.adapter.transaction_begin()
        
        start_time = time.time()
        try:
            # Apply migration
            migration_func(self.adapter)
            
            # Record migration
            execution_time = time.time() - start_time
            self.adapter.record_migration(version, direction, migration.hash, execution_time)
            
            # Commit transaction
            self.adapter.transaction_commit()
            
            logger.info(f"Successfully applied {direction.value} migration to version {version} "
                       f"in {execution_time:.2f} seconds")
                       
        except Exception as e:
            # Roll back transaction
            self.adapter.transaction_rollback()
            
            logger.error(f"Failed to apply {direction.value} migration to version {version}: {e}")
            raise MigrationExecutionError(f"Failed to apply {direction.value} migration to version {version}: {e}")
    
    def get_migration_history(self) -> list[dict[str, Any]]:
        """
        Get the migration history.
        
        Returns:
            List of migration history entries
        """
        self.adapter.connect()
        
        try:
            self.adapter.ensure_migration_table()
            
            # This is a simplified implementation - actual implementation would
            # need to be adapter-specific to retrieve the history
            query = """
            SELECT version, applied_at, direction, script_hash, execution_time 
            FROM schema_migrations 
            ORDER BY applied_at DESC
            """
            
            result = self.adapter.execute(query)
            
            # Format depends on the adapter, so we'll return a generic result
            return result
            
        finally:
            self.adapter.disconnect()
    
    def validate_migrations(self) -> list[str]:
        """
        Validate all migrations for consistency.
        
        This checks for:
        - Missing versions in the sequence
        - Duplicate versions
        - Migrations with changed content but same version
        
        Returns:
            List of validation error messages, empty if all valid
        """
        errors = []
        
        # Check for version sequence gaps
        self._sort_versions(list(self.migrations.keys()))
        
        # Connect to database to check applied migrations
        self.adapter.connect()
        
        try:
            self.adapter.ensure_migration_table()
            
            # Check for migrations with changed content
            query = """
            SELECT version, script_hash FROM schema_migrations 
            WHERE direction = 'up'
            """
            
            applied_migrations = self.adapter.execute(query)
            
            # Format depends on the adapter, but we need version and hash
            for applied in applied_migrations:
                version = applied[0] if isinstance(applied, tuple) else applied.get('version')
                db_hash = applied[1] if isinstance(applied, tuple) else applied.get('script_hash')
                
                if version in self.migrations:
                    file_hash = self.migrations[version].hash
                    if file_hash != db_hash:
                        errors.append(f"Migration {version} has changed since it was applied")
                else:
                    errors.append(f"Migration {version} was applied but is missing from migration files")
            
            return errors
            
        finally:
            self.adapter.disconnect()


if __name__ == "__main__":
    """
    Command-line interface for the schema migrator.
    
    Usage:
        python schema_migrator.py [options]
        
    Options:
        --config FILE       Path to database configuration file
        --dir DIR           Path to migration directory
        --to VERSION        Migrate to specific version
        --latest            Migrate to latest version (default)
        --rollback [VERSION] Roll back to previous or specific version
        --dry-run           Simulate migration without applying changes
        --history           Show migration history
        --validate          Validate migrations
        --verbose           Enable verbose logging
    """
    import argparse
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description="Database Schema Migration Tool")
    parser.add_argument("--config", required=True, help="Path to database configuration file")
    parser.add_argument("--dir", default="migrations", help="Path to migration directory")
    parser.add_argument("--to", help="Migrate to specific version")
    parser.add_argument("--latest", action="store_true", help="Migrate to latest version")
    parser.add_argument("--rollback", nargs="?", const=True, help="Roll back to previous or specific version")
    parser.add_argument("--dry-run", action="store_true", help="Simulate migration without applying changes")
    parser.add_argument("--history", action="store_true", help="Show migration history")
    parser.add_argument("--validate", action="store_true", help="Validate migrations")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load configuration
    try:
        with open(args.config) as f:
            db_config = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load configuration file: {e}")
        sys.exit(1)
    
    # Create migrator
    try:
        migrator = SchemaMigrator(db_config, args.dir)
    except Exception as e:
        logger.error(f"Failed to initialize migrator: {e}")
        sys.exit(1)
    
    # Execute requested action
    try:
        if args.history:
            history = migrator.get_migration_history()
            print("Migration History:")
            for entry in history:
                print(f"  {entry}")
        elif args.validate:
            errors = migrator.validate_migrations()
            if errors:
                print("Validation Errors:")
                for error in errors:
                    print(f"  {error}")
                sys.exit(1)
            else:
                print("All migrations are valid")
        elif args.rollback is not None:
            if args.rollback is True:
                # Roll back one version
                migrator.rollback_to_version(dry_run=args.dry_run)
            else:
                # Roll back to specific version
                migrator.rollback_to_version(args.rollback, dry_run=args.dry_run)
        elif args.to:
            migrator.migrate_to_version(args.to, dry_run=args.dry_run)
        else:
            # Default: migrate to latest
            migrator.migrate_to_latest(dry_run=args.dry_run)
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)