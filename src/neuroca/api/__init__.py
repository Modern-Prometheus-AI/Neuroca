"""
NeuroCognitive Architecture (NCA) API Module.

This module initializes the API layer for the NeuroCognitive Architecture system,
providing endpoints for interacting with the cognitive architecture components,
memory systems, and LLM integration features.

The API is designed with the following principles:
- RESTful design for resource-oriented operations
- Authentication and authorization for secure access
- Comprehensive error handling and validation
- Proper logging and monitoring integration
- Versioned endpoints to support backward compatibility

Usage:
    This module is typically imported and used by the application server:
    
    ```python
    from neuroca.api import create_app
    
    app = create_app()
    app.run()
    ```

Security:
    - All endpoints require proper authentication unless explicitly marked as public
    - Input validation is performed on all request parameters
    - Rate limiting is applied to prevent abuse
    - Sensitive data is never exposed in responses or logs
"""

import logging
from typing import Optional

# Third-party imports
try:
    from flask import Flask, jsonify, request  # Removed unused Blueprint
    from flask_cors import CORS
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
except ImportError as e:
    raise ImportError(
        f"Required package not found: {e}. "
        "Please install required packages with: pip install flask flask-cors flask-limiter"
    ) from e

# Internal imports
from neuroca.config import ConfigurationError, load_config
from neuroca.core.exceptions import NeuroCaException, ResourceNotFoundError
from neuroca.monitoring.logging import setup_logger

# Initialize logger
logger = logging.getLogger(__name__)

# API version
__version__ = "0.1.0"

def create_app(config_path: Optional[str] = None) -> Flask:
    """
    Create and configure the Flask application for the NeuroCa API.
    
    This factory function initializes the Flask application with the appropriate
    configuration, registers all API blueprints, sets up error handlers, and
    configures middleware like CORS and rate limiting.
    
    Args:
        config_path: Optional path to a configuration file. If not provided,
                     the default configuration will be used.
    
    Returns:
        A configured Flask application instance ready to be run.
        
    Raises:
        ConfigurationError: If there's an issue with the configuration.
    """
    # Initialize Flask app
    app = Flask("neuroca-api")
    
    # Load configuration
    try:
        config = load_config(config_path)
        app.config.update(config)
    except ConfigurationError as e:
        logger.critical(f"Failed to load configuration: {e}")
        raise
    
    # Configure logging
    setup_logger(app)
    
    # Setup CORS
    CORS(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}})
    
    # Setup rate limiting
    Limiter(
        get_remote_address,
        app=app,
        default_limits=app.config.get("RATE_LIMITS", ["100 per day", "10 per minute"]),
        storage_uri=app.config.get("RATE_LIMIT_STORAGE", "memory://"),
    )
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register middleware
    register_middleware(app)
    
    logger.info(f"NeuroCa API initialized (version {__version__})")
    return app

def register_blueprints(app: Flask) -> None:
    """
    Register all API blueprints with the Flask application.
    
    This function imports and registers all blueprint modules from the API package,
    organizing them by version and feature area.
    
    Args:
        app: The Flask application instance.
    """
    # Import blueprints here to avoid circular imports
    try:
        # v1 API endpoints
        from neuroca.api.v1 import api_v1
        from neuroca.api.v1.cognitive import cognitive_bp
        from neuroca.api.v1.health import health_bp
        from neuroca.api.v1.integration import integration_bp
        from neuroca.api.v1.memory import memory_bp
        
        # Register main v1 blueprint
        app.register_blueprint(api_v1, url_prefix='/api/v1')
        
        # Register feature-specific blueprints under v1
        api_v1.register_blueprint(memory_bp, url_prefix='/memory')
        api_v1.register_blueprint(cognitive_bp, url_prefix='/cognitive')
        api_v1.register_blueprint(integration_bp, url_prefix='/integration')
        api_v1.register_blueprint(health_bp, url_prefix='/health')
        
        logger.debug("API blueprints registered successfully")
    except ImportError as e:
        logger.error(f"Failed to import API blueprints: {e}")
        # Don't raise here to allow the app to start with limited functionality
        # This helps with incremental development and testing

def register_error_handlers(app: Flask) -> None:
    """
    Register custom error handlers for the API.
    
    This function sets up handlers for various error types, ensuring consistent
    error responses across the API.
    
    Args:
        app: The Flask application instance.
    """
    @app.errorhandler(404)
    def handle_not_found(e):
        """Handle 404 Not Found errors."""
        logger.info(f"Not found: {request.path}")
        return jsonify({
            "error": "not_found",
            "message": "The requested resource was not found",
            "status_code": 404
        }), 404
    
    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        """Handle 405 Method Not Allowed errors."""
        logger.info(f"Method not allowed: {request.method} {request.path}")
        return jsonify({
            "error": "method_not_allowed",
            "message": f"The method {request.method} is not allowed for this resource",
            "status_code": 405
        }), 405
    
    @app.errorhandler(500)
    def handle_server_error(e):
        """Handle 500 Internal Server Error."""
        logger.error(f"Internal server error: {str(e)}", exc_info=True)
        return jsonify({
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
            "status_code": 500
        }), 500
    
    @app.errorhandler(NeuroCaException)
    def handle_neuroca_exception(e):
        """Handle custom NeuroCa exceptions."""
        status_code = getattr(e, "status_code", 500)
        error_code = getattr(e, "error_code", "internal_error")
        
        logger.warning(f"NeuroCa exception: {error_code} - {str(e)}")
        
        return jsonify({
            "error": error_code,
            "message": str(e),
            "status_code": status_code
        }), status_code
    
    @app.errorhandler(ResourceNotFoundError)
    def handle_resource_not_found(e):
        """Handle resource not found exceptions."""
        logger.info(f"Resource not found: {str(e)}")
        
        return jsonify({
            "error": "resource_not_found",
            "message": str(e),
            "status_code": 404
        }), 404

def register_middleware(app: Flask) -> None:
    """
    Register middleware for the Flask application.
    
    This function sets up request/response middleware for logging, metrics,
    and other cross-cutting concerns.
    
    Args:
        app: The Flask application instance.
    """
    @app.before_request
    def log_request_info():
        """Log information about each incoming request."""
        logger.debug(f"Request: {request.method} {request.path} - {request.remote_addr}")
    
    @app.after_request
    def add_header(response):
        """Add standard headers to all responses."""
        response.headers['X-API-Version'] = __version__
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Content-Security-Policy'] = "default-src 'self'"
        return response

# Export public API
__all__ = ['create_app', '__version__']

"""API module for NeuroCognitive Architecture."""
