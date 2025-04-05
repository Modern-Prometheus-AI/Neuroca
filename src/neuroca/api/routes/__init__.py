"""
API Routes Module for NeuroCognitive Architecture (NCA)

This module initializes and configures all API routes for the NCA system.
It provides a function to register routes with the FastAPI application
and organizes route modules in a structured way.

The module follows a modular approach where each domain has its own router
that is registered with the main application. This allows for better organization,
maintainability, and testability of the API endpoints.

Usage:
    from fastapi import FastAPI
    from neuroca.api.routes import register_routes
    
    app = FastAPI()
    register_routes(app)
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, FastAPI
from fastapi.routing import APIRoute

from neuroca.api.middleware.auth import get_current_user
from neuroca.api.routes.admin import router as admin_router
from neuroca.api.routes.auth import router as auth_router
from neuroca.api.routes.cognitive import router as cognitive_router

# Import all route modules
from neuroca.api.routes.health import router as health_router
from neuroca.api.routes.integration import router as integration_router
from neuroca.api.routes.memory import router as memory_router
from neuroca.api.routes.monitoring import router as monitoring_router
from neuroca.config import settings

# Configure logger
logger = logging.getLogger(__name__)

# Define all available routers with their prefixes and tags
ROUTERS = [
    {"router": health_router, "prefix": "/health", "tags": ["Health"]},
    {"router": memory_router, "prefix": "/memory", "tags": ["Memory"]},
    {"router": cognitive_router, "prefix": "/cognitive", "tags": ["Cognitive"]},
    {"router": integration_router, "prefix": "/integration", "tags": ["Integration"]},
    {"router": admin_router, "prefix": "/admin", "tags": ["Admin"]},
    {"router": monitoring_router, "prefix": "/monitoring", "tags": ["Monitoring"]},
    {"router": auth_router, "prefix": "/auth", "tags": ["Authentication"]},
]


def register_routes(app: FastAPI) -> None:
    """
    Register all API routes with the FastAPI application.
    
    This function iterates through all defined routers and includes them
    in the main FastAPI application with their respective prefixes and tags.
    It also handles authentication dependencies based on configuration.
    
    Args:
        app (FastAPI): The FastAPI application instance
        
    Returns:
        None
        
    Raises:
        ValueError: If there's an issue with router configuration
    """
    try:
        logger.info("Registering API routes")
        
        # Create main API router
        api_router = APIRouter(prefix=settings.API_PREFIX)
        
        # Include all routers
        for router_config in ROUTERS:
            router = router_config["router"]
            prefix = router_config["prefix"]
            tags = router_config.get("tags", [])
            
            # Apply authentication to protected routes if enabled
            if (settings.AUTH_ENABLED and 
                prefix not in ["/health", "/auth"] and 
                not prefix.startswith("/public")):
                
                # Apply authentication dependency to all routes in the router
                for route in router.routes:
                    if isinstance(route, APIRoute):
                        route.dependencies.append(Depends(get_current_user))
                
                logger.debug(f"Applied authentication to routes with prefix: {prefix}")
            
            # Include the router
            api_router.include_router(
                router,
                prefix=prefix,
                tags=tags
            )
            logger.debug(f"Registered router with prefix: {prefix}")
        
        # Include the main API router in the app
        app.include_router(api_router)
        
        logger.info(f"Successfully registered {len(ROUTERS)} route modules")
    
    except Exception as e:
        logger.error(f"Failed to register routes: {str(e)}")
        raise ValueError(f"Route registration failed: {str(e)}") from e


def get_all_routes() -> list[dict]:
    """
    Get information about all registered routes.
    
    This function is useful for documentation and debugging purposes.
    It returns a list of dictionaries containing information about each route.
    
    Returns:
        List[dict]: A list of dictionaries with route information
        
    Example:
        >>> routes = get_all_routes()
        >>> for route in routes:
        ...     print(f"{route['method']} {route['path']}")
    """
    routes = []
    
    for router_config in ROUTERS:
        router = router_config["router"]
        prefix = router_config["prefix"]
        
        for route in router.routes:
            if isinstance(route, APIRoute):
                routes.append({
                    "path": f"{settings.API_PREFIX}{prefix}{route.path}",
                    "name": route.name,
                    "method": ", ".join(route.methods),
                    "tags": router_config.get("tags", [])
                })
    
    return routes


def get_route_by_name(name: str) -> Optional[dict]:
    """
    Find a route by its name.
    
    Args:
        name (str): The name of the route to find
        
    Returns:
        Optional[dict]: Route information or None if not found
        
    Example:
        >>> route = get_route_by_name("get_memory_by_id")
        >>> if route:
        ...     print(f"Found route: {route['method']} {route['path']}")
        ... else:
        ...     print("Route not found")
    """
    all_routes = get_all_routes()
    
    for route in all_routes:
        if route["name"] == name:
            return route
    
    return None