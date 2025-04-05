"""
Alembic Environment Configuration

This module configures the Alembic migration environment for the NeuroCognitive Architecture (NCA) project.
It handles database connection, migration context setup, and provides both offline and online migration
capabilities. The configuration supports multiple environments (development, testing, production) through
environment variables and configuration files.

Usage:
    This file is used by Alembic CLI commands to run database migrations:
    - alembic revision --autogenerate -m "description"  # Generate migration
    - alembic upgrade head                             # Apply migrations
    - alembic downgrade -1                             # Rollback migration

Environment Variables:
    - NEUROCA_DB_URL: Database connection URL (overrides config settings)
    - NEUROCA_ENV: Environment name (development, testing, production)
    - NEUROCA_CONFIG_PATH: Custom path to configuration file
"""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Add the project root directory to the Python path to enable imports
sys.path.insert(0, str(Path(__file__).parents[3]))

# Import the SQLAlchemy metadata object that should contain all models
from neuroca.config.settings import get_settings  # noqa: E402
from neuroca.core.logging import get_logger  # noqa: E402
from neuroca.db.models.base import Base  # noqa: E402

# Initialize logger
logger = get_logger(__name__)

# This is the Alembic Config object, which provides access to the values within the .ini file
config = context.config

# Load the logging configuration if present
if config.config_file_name is not None:
    try:
        fileConfig(config.config_file_name)
        logger.debug("Loaded logging configuration from %s", config.config_file_name)
    except Exception as e:
        logger.warning("Failed to load logging configuration: %s", str(e))

# Get database URL from environment or settings
settings = get_settings()
db_url = os.environ.get("NEUROCA_DB_URL", settings.database.url)

if not db_url:
    raise ValueError(
        "Database URL not configured. Set NEUROCA_DB_URL environment variable or "
        "configure it in the settings file."
    )

# Override sqlalchemy.url in alembic.ini with our dynamic configuration
config.set_main_option("sqlalchemy.url", db_url)

# Set target metadata
target_metadata = Base.metadata


def include_object(object, name, type_, reflected, compare_to):
    """
    Filter function to determine which database objects should be included in migrations.
    
    Args:
        object: The database object being considered
        name: The name of the object
        type_: The type of object (table, column, etc.)
        reflected: Whether the object was reflected
        compare_to: The object being compared to
        
    Returns:
        bool: True if the object should be included, False otherwise
    """
    # Exclude specific tables if needed (e.g., third-party tables, audit tables)
    excluded_tables = {"alembic_version", "spatial_ref_sys"}
    
    if type_ == "table" and name in excluded_tables:
        return False
    
    return True


def run_migrations_offline():
    """
    Run migrations in 'offline' mode.
    
    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.
    
    Calls to context.execute() here emit the given string to the script output.
    """
    logger.info("Running offline migrations")
    
    try:
        url = config.get_main_option("sqlalchemy.url")
        context.configure(
            url=url,
            target_metadata=target_metadata,
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
            include_object=include_object,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()
            
        logger.info("Offline migrations completed successfully")
    except Exception as e:
        logger.error("Offline migrations failed: %s", str(e), exc_info=True)
        raise


def run_migrations_online():
    """
    Run migrations in 'online' mode.
    
    In this scenario we need to create an Engine and associate a connection with the context.
    This is the preferred way to run migrations as it allows for transactional DDL.
    """
    logger.info("Running online migrations")
    
    # Configure connection parameters based on the database type
    connectable_args = {
        "poolclass": pool.NullPool,  # Don't keep connections open during migrations
    }
    
    # Add specific connection parameters based on database type
    if "postgresql" in db_url:
        connectable_args["connect_args"] = {
            "connect_timeout": 60,  # Longer timeout for migrations
        }
    
    try:
        connectable = engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            **connectable_args
        )

        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                include_object=include_object,
                compare_type=True,
                # Enable transactional DDL for databases that support it
                transaction_per_migration=True,
                # Render SQL with proper indentation
                render_as_batch=True,
            )

            with context.begin_transaction():
                context.run_migrations()
                
        logger.info("Online migrations completed successfully")
    except Exception as e:
        logger.error("Online migrations failed: %s", str(e), exc_info=True)
        raise


# Determine migration mode and run appropriate function
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()