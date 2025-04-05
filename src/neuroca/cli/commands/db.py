"""
Database CLI Commands Module.

This module provides command-line interface commands for managing the NeuroCognitive Architecture
database. It includes functionality for initializing, migrating, upgrading, downgrading,
and inspecting the database schema.

Usage:
    neuroca db init
    neuroca db migrate -m "migration message"
    neuroca db upgrade [--revision=<rev>]
    neuroca db downgrade [--revision=<rev>]
    neuroca db current
    neuroca db history
    neuroca db check
    neuroca db purge [--confirm]

Examples:
    # Initialize the database
    $ neuroca db init
    
    # Create a new migration
    $ neuroca db migrate -m "Add user table"
    
    # Upgrade to the latest version
    $ neuroca db upgrade
    
    # Downgrade to a specific version
    $ neuroca db downgrade --revision=ae1027a6acf
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import click
from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from neuroca.core.exceptions import DatabaseError
from neuroca.db.connection import get_db_url

# Configure logger
logger = logging.getLogger(__name__)


def get_alembic_config() -> Config:
    """
    Create and configure an Alembic configuration object.
    
    Returns:
        Config: Configured Alembic Config object
    
    Raises:
        FileNotFoundError: If alembic.ini or migrations directory cannot be found
    """
    try:
        # Get the project root directory
        project_root = Path(__file__).parent.parent.parent.parent
        
        # Path to alembic.ini
        alembic_ini_path = project_root / "alembic.ini"
        
        if not alembic_ini_path.exists():
            raise FileNotFoundError(f"Alembic configuration file not found at {alembic_ini_path}")
        
        # Create Alembic config
        alembic_cfg = Config(str(alembic_ini_path))
        
        # Set the migrations directory path
        migrations_dir = project_root / "neuroca" / "db" / "migrations"
        
        if not migrations_dir.exists():
            raise FileNotFoundError(f"Migrations directory not found at {migrations_dir}")
        
        alembic_cfg.set_main_option("script_location", str(migrations_dir))
        
        # Set the database URL
        alembic_cfg.set_main_option("sqlalchemy.url", get_db_url())
        
        return alembic_cfg
    
    except Exception as e:
        logger.error(f"Failed to create Alembic configuration: {str(e)}")
        raise


def check_database_connection() -> bool:
    """
    Check if the database connection is working.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    engine = None
    try:
        db_url = get_db_url()
        engine = create_engine(db_url)
        
        # Try to connect and execute a simple query
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        logger.debug("Database connection successful")
        return True
    
    except OperationalError as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False
    
    except Exception as e:
        logger.error(f"Unexpected error checking database connection: {str(e)}")
        return False
    
    finally:
        if engine:
            engine.dispose()


def get_current_revision() -> Optional[str]:
    """
    Get the current database revision.
    
    Returns:
        Optional[str]: Current revision or None if not available
        
    Raises:
        DatabaseError: If there's an error accessing the database
    """
    engine = None
    try:
        db_url = get_db_url()
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            context = MigrationContext.configure(conn)
            current_rev = context.get_current_revision()
        
        return current_rev
    
    except SQLAlchemyError as e:
        logger.error(f"Database error getting current revision: {str(e)}")
        raise DatabaseError(f"Failed to get current revision: {str(e)}")
    
    except Exception as e:
        logger.error(f"Unexpected error getting current revision: {str(e)}")
        raise DatabaseError(f"Failed to get current revision: {str(e)}")
    
    finally:
        if engine:
            engine.dispose()


@click.group(name="db")
def db_commands():
    """Database management commands."""
    pass


@db_commands.command("init")
def init_db():
    """Initialize the database with Alembic."""
    try:
        if not check_database_connection():
            click.echo("Error: Could not connect to the database. Please check your configuration.")
            sys.exit(1)
        
        click.echo("Initializing the database...")
        alembic_cfg = get_alembic_config()
        command.init(alembic_cfg, "neuroca/db/migrations")
        click.echo("Database initialization complete.")
    
    except FileNotFoundError as e:
        click.echo(f"Error: {str(e)}")
        sys.exit(1)
    
    except Exception as e:
        click.echo(f"Error initializing database: {str(e)}")
        logger.exception("Database initialization failed")
        sys.exit(1)


@db_commands.command("migrate")
@click.option("-m", "--message", required=True, help="Migration message")
def create_migration(message: str):
    """Create a new migration."""
    try:
        if not message:
            click.echo("Error: Migration message is required.")
            sys.exit(1)
        
        click.echo(f"Creating migration with message: {message}")
        alembic_cfg = get_alembic_config()
        command.revision(alembic_cfg, message=message, autogenerate=True)
        click.echo("Migration created successfully.")
    
    except Exception as e:
        click.echo(f"Error creating migration: {str(e)}")
        logger.exception("Migration creation failed")
        sys.exit(1)


@db_commands.command("upgrade")
@click.option("--revision", default="head", help="Revision to upgrade to (default: head)")
def upgrade_db(revision: str):
    """Upgrade the database to a specified revision or latest."""
    try:
        if not check_database_connection():
            click.echo("Error: Could not connect to the database. Please check your configuration.")
            sys.exit(1)
        
        click.echo(f"Upgrading database to revision: {revision}")
        alembic_cfg = get_alembic_config()
        command.upgrade(alembic_cfg, revision)
        
        current_rev = get_current_revision()
        click.echo(f"Database upgraded successfully. Current revision: {current_rev}")
    
    except Exception as e:
        click.echo(f"Error upgrading database: {str(e)}")
        logger.exception("Database upgrade failed")
        sys.exit(1)


@db_commands.command("downgrade")
@click.option("--revision", required=True, help="Revision to downgrade to")
def downgrade_db(revision: str):
    """Downgrade the database to a specified revision."""
    try:
        if not check_database_connection():
            click.echo("Error: Could not connect to the database. Please check your configuration.")
            sys.exit(1)
        
        if not revision:
            click.echo("Error: Revision is required for downgrade.")
            sys.exit(1)
        
        current_rev = get_current_revision()
        click.echo(f"Current revision: {current_rev}")
        click.echo(f"Downgrading database to revision: {revision}")
        
        alembic_cfg = get_alembic_config()
        command.downgrade(alembic_cfg, revision)
        
        new_rev = get_current_revision()
        click.echo(f"Database downgraded successfully. Current revision: {new_rev}")
    
    except Exception as e:
        click.echo(f"Error downgrading database: {str(e)}")
        logger.exception("Database downgrade failed")
        sys.exit(1)


@db_commands.command("current")
def show_current_revision():
    """Show the current database revision."""
    try:
        if not check_database_connection():
            click.echo("Error: Could not connect to the database. Please check your configuration.")
            sys.exit(1)
        
        current_rev = get_current_revision()
        if current_rev:
            click.echo(f"Current database revision: {current_rev}")
        else:
            click.echo("Database has not been initialized with Alembic yet.")
    
    except Exception as e:
        click.echo(f"Error getting current revision: {str(e)}")
        logger.exception("Failed to get current revision")
        sys.exit(1)


@db_commands.command("history")
def show_migration_history():
    """Show the migration history."""
    try:
        alembic_cfg = get_alembic_config()
        command.history(alembic_cfg, verbose=True)
    
    except Exception as e:
        click.echo(f"Error showing migration history: {str(e)}")
        logger.exception("Failed to show migration history")
        sys.exit(1)


@db_commands.command("check")
def check_db():
    """Check database connection and schema."""
    engine = None
    try:
        if not check_database_connection():
            click.echo("Error: Could not connect to the database. Please check your configuration.")
            sys.exit(1)
        
        click.echo("Database connection successful.")
        
        # Get current revision
        current_rev = get_current_revision()
        if current_rev:
            click.echo(f"Current database revision: {current_rev}")
        else:
            click.echo("Warning: Database has not been initialized with Alembic yet.")
        
        # Check tables
        db_url = get_db_url()
        engine = create_engine(db_url)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if tables:
            click.echo(f"Found {len(tables)} tables in the database:")
            for table in tables:
                click.echo(f"  - {table}")
        else:
            click.echo("No tables found in the database.")
        
        click.echo("Database check completed successfully.")
    
    except Exception as e:
        click.echo(f"Error checking database: {str(e)}")
        logger.exception("Database check failed")
        sys.exit(1)
    
    finally:
        if engine:
            engine.dispose()


@db_commands.command("purge")
@click.option("--confirm", is_flag=True, help="Confirm purging the database")
def purge_db(confirm: bool):
    """Purge the database (drop all tables)."""
    engine = None
    try:
        if not confirm:
            click.echo("Warning: This will delete all data in the database.")
            click.echo("Run with --confirm to proceed.")
            sys.exit(0)
        
        if not check_database_connection():
            click.echo("Error: Could not connect to the database. Please check your configuration.")
            sys.exit(1)
        
        click.echo("Purging database...")
        
        db_url = get_db_url()
        engine = create_engine(db_url)
        
        # Get all table names
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if not tables:
            click.echo("No tables found in the database.")
            return
        
        # Drop all tables
        with engine.begin() as conn:
            # Disable foreign key constraints if using SQLite
            if 'sqlite' in db_url:
                conn.execute(text("PRAGMA foreign_keys = OFF"))
            
            # Drop alembic_version table last
            non_alembic_tables = [t for t in tables if t != 'alembic_version']
            all_tables = non_alembic_tables + (['alembic_version'] if 'alembic_version' in tables else [])
            
            for table in all_tables:
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
            
            # Re-enable foreign key constraints if using SQLite
            if 'sqlite' in db_url:
                conn.execute(text("PRAGMA foreign_keys = ON"))
        
        click.echo(f"Successfully dropped {len(tables)} tables.")
        click.echo("Database purged successfully.")
    
    except Exception as e:
        click.echo(f"Error purging database: {str(e)}")
        logger.exception("Database purge failed")
        sys.exit(1)
    
    finally:
        if engine:
            engine.dispose()


if __name__ == "__main__":
    db_commands()