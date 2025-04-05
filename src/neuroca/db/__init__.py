"""
Database Module for NeuroCognitive Architecture (NCA)

This module initializes and manages database connections and provides core database
functionality for the NeuroCognitive Architecture system. It handles connection pooling,
configuration management, and exposes a clean API for database operations throughout
the application.

The module supports multiple database backends (PostgreSQL, SQLite) and implements
connection lifecycle management, transaction handling, and error recovery strategies.

Usage:
    from neuroca.db import get_db_session, init_db
    
    # Initialize the database (typically called once during application startup)
    init_db()
    
    # Get a database session for operations
    with get_db_session() as session:
        result = session.execute("SELECT * FROM cognitive_states")
        
Examples:
    # Basic query execution
    from neuroca.db import get_db_session
    
    with get_db_session() as session:
        try:
            result = session.execute("SELECT * FROM memory_items WHERE type = :type", 
                                    {"type": "episodic"})
            items = result.fetchall()
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            raise
"""

import logging
import os
import threading
import time
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any, Optional

from sqlalchemy import create_engine, event, exc
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, scoped_session, sessionmaker

# Configure module logger
logger = logging.getLogger(__name__)

# Thread-local storage for database connections
_thread_local = threading.local()

# SQLAlchemy base class for all models
Base = declarative_base()

# Global engine instances
_engines: dict[str, Engine] = {}
_session_factories: dict[str, scoped_session] = {}

# Default connection settings
DEFAULT_POOL_SIZE = 10
DEFAULT_MAX_OVERFLOW = 20
DEFAULT_POOL_TIMEOUT = 30
DEFAULT_POOL_RECYCLE = 1800  # 30 minutes
DEFAULT_CONNECT_RETRY_COUNT = 3
DEFAULT_CONNECT_RETRY_INTERVAL = 2  # seconds
DEFAULT_DB_URL_ENV_VAR = "NEUROCA_DATABASE_URL"
DEFAULT_DB_NAME = "default"

# Connection status tracking
_initialized = False


class DatabaseError(Exception):
    """Base exception for all database-related errors in the NeuroCognitive Architecture."""
    pass


class ConnectionError(DatabaseError):
    """Exception raised when database connection cannot be established."""
    pass


class ConfigurationError(DatabaseError):
    """Exception raised when database configuration is invalid."""
    pass


class TransactionError(DatabaseError):
    """Exception raised when a database transaction fails."""
    pass


def _get_database_url(db_name: str = DEFAULT_DB_NAME) -> str:
    """
    Get the database URL from environment variables or configuration.
    
    Args:
        db_name: The name of the database configuration to use
        
    Returns:
        The database URL as a string
        
    Raises:
        ConfigurationError: If the database URL is not configured
    """
    # Check for environment variable specific to this database
    env_var = f"NEUROCA_DATABASE_URL_{db_name.upper()}" if db_name != DEFAULT_DB_NAME else DEFAULT_DB_URL_ENV_VAR
    db_url = os.environ.get(env_var)
    
    if not db_url:
        # Fall back to default environment variable
        db_url = os.environ.get(DEFAULT_DB_URL_ENV_VAR)
    
    if not db_url:
        raise ConfigurationError(
            f"Database URL not configured. Set {env_var} environment variable."
        )
    
    logger.debug(f"Using database URL from {env_var}")
    return db_url


def _create_engine_with_retry(db_url: str, **kwargs) -> Engine:
    """
    Create a SQLAlchemy engine with connection retry logic.
    
    Args:
        db_url: The database URL
        **kwargs: Additional arguments to pass to create_engine
        
    Returns:
        A configured SQLAlchemy engine
        
    Raises:
        ConnectionError: If connection cannot be established after retries
    """
    retry_count = kwargs.pop('retry_count', DEFAULT_CONNECT_RETRY_COUNT)
    retry_interval = kwargs.pop('retry_interval', DEFAULT_CONNECT_RETRY_INTERVAL)
    
    for attempt in range(retry_count):
        try:
            engine = create_engine(
                db_url,
                pool_size=kwargs.pop('pool_size', DEFAULT_POOL_SIZE),
                max_overflow=kwargs.pop('max_overflow', DEFAULT_MAX_OVERFLOW),
                pool_timeout=kwargs.pop('pool_timeout', DEFAULT_POOL_TIMEOUT),
                pool_recycle=kwargs.pop('pool_recycle', DEFAULT_POOL_RECYCLE),
                **kwargs
            )
            
            # Test the connection
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            
            logger.info(f"Database engine created successfully on attempt {attempt + 1}")
            return engine
            
        except (exc.SQLAlchemyError, exc.DBAPIError) as e:
            if attempt < retry_count - 1:
                logger.warning(
                    f"Database connection attempt {attempt + 1} failed: {e}. "
                    f"Retrying in {retry_interval} seconds..."
                )
                time.sleep(retry_interval)
            else:
                logger.error(f"Failed to connect to database after {retry_count} attempts: {e}")
                raise ConnectionError(f"Could not connect to database: {e}") from e
    return None


def init_db(db_name: str = DEFAULT_DB_NAME, **kwargs) -> None:
    """
    Initialize the database connection and session factory.
    
    This function should be called during application startup to establish
    database connections and prepare the ORM session factory.
    
    Args:
        db_name: The name of the database configuration to use
        **kwargs: Additional configuration options for the database engine
        
    Raises:
        ConfigurationError: If database configuration is invalid
        ConnectionError: If database connection cannot be established
    """
    global _initialized
    
    try:
        db_url = _get_database_url(db_name)
        
        # Create the engine with retry logic
        engine = _create_engine_with_retry(db_url, **kwargs)
        _engines[db_name] = engine
        
        # Configure SQLite to enable foreign key constraints if using SQLite
        if db_url.startswith('sqlite'):
            @event.listens_for(engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
        
        # Create session factory
        session_factory = sessionmaker(bind=engine)
        _session_factories[db_name] = scoped_session(session_factory)
        
        logger.info(f"Database '{db_name}' initialized successfully")
        
        if db_name == DEFAULT_DB_NAME:
            _initialized = True
            
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


def create_all_tables(db_name: str = DEFAULT_DB_NAME) -> None:
    """
    Create all tables defined in SQLAlchemy models.
    
    Args:
        db_name: The name of the database configuration to use
        
    Raises:
        DatabaseError: If table creation fails
    """
    if db_name not in _engines:
        raise ConfigurationError(f"Database '{db_name}' not initialized. Call init_db() first.")
    
    try:
        Base.metadata.create_all(_engines[db_name])
        logger.info(f"All tables created successfully in database '{db_name}'")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise DatabaseError(f"Failed to create database tables: {e}") from e


def drop_all_tables(db_name: str = DEFAULT_DB_NAME) -> None:
    """
    Drop all tables defined in SQLAlchemy models.
    
    WARNING: This will delete all data in the database.
    
    Args:
        db_name: The name of the database configuration to use
        
    Raises:
        DatabaseError: If table dropping fails
    """
    if db_name not in _engines:
        raise ConfigurationError(f"Database '{db_name}' not initialized. Call init_db() first.")
    
    try:
        Base.metadata.drop_all(_engines[db_name])
        logger.info(f"All tables dropped successfully in database '{db_name}'")
    except Exception as e:
        logger.error(f"Failed to drop tables: {e}")
        raise DatabaseError(f"Failed to drop database tables: {e}") from e


@contextmanager
def get_db_session(db_name: str = DEFAULT_DB_NAME) -> Generator[Session, None, None]:
    """
    Get a database session for the specified database.
    
    This context manager provides a session that will be automatically closed
    when the context exits. It also handles transaction management.
    
    Args:
        db_name: The name of the database configuration to use
        
    Yields:
        An active SQLAlchemy session
        
    Raises:
        ConfigurationError: If the database is not initialized
        TransactionError: If a transaction error occurs
        
    Example:
        with get_db_session() as session:
            result = session.query(User).filter_by(username='admin').first()
    """
    if not _initialized and db_name == DEFAULT_DB_NAME:
        logger.warning("Database not initialized. Attempting to initialize with default settings.")
        init_db(db_name)
    
    if db_name not in _session_factories:
        raise ConfigurationError(
            f"Database '{db_name}' not initialized. Call init_db('{db_name}') first."
        )
    
    session = _session_factories[db_name]()
    
    try:
        logger.debug(f"Database session opened for '{db_name}'")
        yield session
        session.commit()
        logger.debug(f"Database session committed for '{db_name}'")
    except Exception as e:
        logger.error(f"Transaction error in database '{db_name}': {e}")
        session.rollback()
        logger.debug(f"Database session rolled back for '{db_name}'")
        raise TransactionError(f"Database transaction failed: {e}") from e
    finally:
        session.close()
        logger.debug(f"Database session closed for '{db_name}'")


def get_engine(db_name: str = DEFAULT_DB_NAME) -> Engine:
    """
    Get the SQLAlchemy engine for the specified database.
    
    Args:
        db_name: The name of the database configuration to use
        
    Returns:
        The SQLAlchemy engine instance
        
    Raises:
        ConfigurationError: If the database is not initialized
    """
    if db_name not in _engines:
        raise ConfigurationError(
            f"Database '{db_name}' not initialized. Call init_db('{db_name}') first."
        )
    
    return _engines[db_name]


def close_connections(db_name: Optional[str] = None) -> None:
    """
    Close all database connections.
    
    Args:
        db_name: The specific database to close, or None to close all
        
    Raises:
        DatabaseError: If closing connections fails
    """
    try:
        if db_name:
            if db_name in _engines:
                _engines[db_name].dispose()
                logger.info(f"Closed all connections for database '{db_name}'")
            else:
                logger.warning(f"No engine found for database '{db_name}'")
        else:
            for name, engine in _engines.items():
                engine.dispose()
                logger.info(f"Closed all connections for database '{name}'")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")
        raise DatabaseError(f"Failed to close database connections: {e}") from e


def health_check(db_name: str = DEFAULT_DB_NAME) -> dict[str, Any]:
    """
    Perform a health check on the database.
    
    Args:
        db_name: The name of the database configuration to use
        
    Returns:
        A dictionary with health check results
        
    Raises:
        DatabaseError: If the health check fails
    """
    if db_name not in _engines:
        raise ConfigurationError(
            f"Database '{db_name}' not initialized. Call init_db('{db_name}') first."
        )
    
    start_time = time.time()
    status = "healthy"
    error_message = None
    
    try:
        # Test query execution
        with get_db_session(db_name) as session:
            session.execute("SELECT 1").fetchone()
        
        # Get connection pool stats
        engine = _engines[db_name]
        pool_status = {
            "checkedin": engine.pool.checkedin(),
            "checkedout": engine.pool.checkedout(),
            "overflow": engine.pool.overflow(),
            "size": engine.pool.size()
        }
        
    except Exception as e:
        status = "unhealthy"
        error_message = str(e)
        pool_status = None
        logger.error(f"Database health check failed: {e}")
    
    response_time = time.time() - start_time
    
    return {
        "status": status,
        "database": db_name,
        "response_time_seconds": response_time,
        "error": error_message,
        "pool": pool_status
    }


# Export public API
__all__ = [
    'Base',
    'init_db',
    'get_db_session',
    'create_all_tables',
    'drop_all_tables',
    'close_connections',
    'get_engine',
    'health_check',
    'DatabaseError',
    'ConnectionError',
    'ConfigurationError',
    'TransactionError'
]