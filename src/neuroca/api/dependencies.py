"""
API Dependencies Module for NeuroCognitive Architecture (NCA)

This module provides FastAPI dependency functions that can be injected into API endpoints.
Dependencies include database sessions, authentication, memory system access, configuration,
logging, and other core services required by the API layer.

Dependencies are organized into categories:
- Database: For database session management
- Authentication: For user authentication and authorization
- Memory: For accessing the three-tiered memory system
- Configuration: For accessing application configuration
- Logging: For structured logging
- Services: For accessing core application services

Usage:
    from fastapi import Depends, APIRouter
    from neuroca.api.dependencies import get_db, get_current_user

    router = APIRouter()

    @router.get("/items/")
    async def read_items(db=Depends(get_db), user=Depends(get_current_user)):
        return db.query(Item).filter(Item.owner_id == user.id).all()
"""

import logging
from collections.abc import AsyncGenerator, Generator
from datetime import datetime

from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import JWTError, jwt
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from neuroca.config.settings import Settings, get_settings
from neuroca.core.exceptions import ServiceUnavailableError
from neuroca.core.models.user import User
from neuroca.core.schemas.auth import TokenData
from neuroca.core.schemas.health import SystemHealth
from neuroca.core.services.health_monitor import HealthMonitor
from neuroca.core.services.llm_service import LLMService
from neuroca.db.session import get_async_db_session, get_db_session
from neuroca.memory.episodic_memory import EpisodicMemoryManager
from neuroca.memory.semantic_memory import SemanticMemoryManager
from neuroca.memory.working_memory import WorkingMemoryManager

# Configure module logger
logger = logging.getLogger(__name__)

# OAuth2 configuration
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/token",
    scopes={
        "admin": "Full system access",
        "user": "Regular user access",
        "read": "Read-only access",
    },
)

# ==================== Database Dependencies ====================

def get_db() -> Generator[Session, None, None]:
    """
    Provides a SQLAlchemy database session dependency.
    
    Yields:
        Session: A SQLAlchemy database session
        
    Example:
        @router.get("/items/")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = get_db_session()
    try:
        yield db
        db.commit()  # Auto-commit if no exceptions
    except Exception as e:
        db.rollback()
        logger.error(f"Database session error: {str(e)}")
        raise
    finally:
        db.close()
        logger.debug("Database session closed")

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides an async SQLAlchemy database session dependency.
    
    Yields:
        AsyncSession: An async SQLAlchemy database session
        
    Example:
        @router.get("/items/")
        async def get_items(db: AsyncSession = Depends(get_async_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    async_session = get_async_db_session()
    try:
        yield async_session
        await async_session.commit()  # Auto-commit if no exceptions
    except Exception as e:
        await async_session.rollback()
        logger.error(f"Async database session error: {str(e)}")
        raise
    finally:
        await async_session.close()
        logger.debug("Async database session closed")

# ==================== Authentication Dependencies ====================

async def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),  # noqa: B008
    settings: Settings = Depends(get_settings),  # noqa: B008
    db: Session = Depends(get_db)  # noqa: B008
) -> User:
    """
    Validates the access token and returns the current user.
    
    Args:
        security_scopes: Security scopes required for the endpoint
        token: JWT token from the request
        settings: Application settings
        db: Database session
        
    Returns:
        User: The authenticated user
        
    Raises:
        HTTPException: If authentication fails or user lacks required permissions
        
    Example:
        @router.get("/me/", response_model=UserRead)
        async def read_users_me(current_user: User = Depends(get_current_user)):
            return current_user
    """
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
        
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            logger.warning("Token missing 'sub' claim")
            raise credentials_exception
            
        token_scopes = payload.get("scopes", [])
        token_data = TokenData(scopes=token_scopes, username=username)
        
    except (JWTError, ValidationError) as e:
        logger.warning(f"Token validation error: {str(e)}")
        raise credentials_exception
        
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        logger.warning(f"User not found: {token_data.username}")
        raise credentials_exception
        
    # Check if token is expired
    if "exp" in payload and datetime.utcnow() > datetime.fromtimestamp(payload["exp"]):
        logger.warning(f"Expired token for user: {user.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": authenticate_value},
        )
        
    # Check for required scopes
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            logger.warning(f"User {user.username} missing required scope: {scope}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Required: {scope}",
                headers={"WWW-Authenticate": authenticate_value},
            )
            
    logger.debug(f"Authenticated user: {user.username}")
    return user

async def get_current_active_user(
    current_user: User = Security(get_current_user, scopes=["user"])  # noqa: B008
) -> User:
    """
    Verifies that the current user is active.
    
    Args:
        current_user: The authenticated user
        
    Returns:
        User: The active authenticated user
        
    Raises:
        HTTPException: If the user is inactive
        
    Example:
        @router.get("/items/")
        async def read_items(user: User = Depends(get_current_active_user)):
            return user.items
    """
    if not current_user.is_active:
        logger.warning(f"Inactive user attempted access: {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user

async def get_current_admin_user(
    current_user: User = Security(get_current_user, scopes=["admin"])  # noqa: B008
) -> User:
    """
    Verifies that the current user is an admin.
    
    Args:
        current_user: The authenticated user with admin scope
        
    Returns:
        User: The admin user
        
    Example:
        @router.get("/admin/users/")
        async def read_all_users(admin: User = Depends(get_current_admin_user)):
            # Admin-only endpoint
            return db.query(User).all()
    """
    logger.debug(f"Admin access by user: {current_user.username}")
    return current_user

# ==================== Memory System Dependencies ====================

def get_working_memory(
    db: Session = Depends(get_db),  # noqa: B008
    settings: Settings = Depends(get_settings)  # noqa: B008
) -> WorkingMemoryManager:
    """
    Provides access to the working memory system.
    
    Args:
        db: Database session
        settings: Application settings
        
    Returns:
        WorkingMemoryManager: Manager for working memory operations
        
    Example:
        @router.post("/thoughts/")
        async def create_thought(
            thought: ThoughtCreate,
            wm: WorkingMemoryManager = Depends(get_working_memory)
        ):
            return wm.add_thought(thought)
    """
    try:
        return WorkingMemoryManager(db=db, config=settings.memory.working_memory)
    except Exception as e:  # noqa: BLE001
        logger.error(f"Failed to initialize working memory: {str(e)}")
        raise ServiceUnavailableError("Working memory system unavailable") from e

def get_episodic_memory(
    db: Session = Depends(get_db),  # noqa: B008
    settings: Settings = Depends(get_settings)  # noqa: B008
) -> EpisodicMemoryManager:
    """
    Provides access to the episodic memory system.
    
    Args:
        db: Database session
        settings: Application settings
        
    Returns:
        EpisodicMemoryManager: Manager for episodic memory operations
        
    Example:
        @router.get("/memories/")
        async def get_memories(
            em: EpisodicMemoryManager = Depends(get_episodic_memory)
        ):
            return em.retrieve_recent_memories(limit=10)
    """
    try:
        return EpisodicMemoryManager(db=db, config=settings.memory.episodic_memory)
    except Exception as e:  # noqa: BLE001
        logger.error(f"Failed to initialize episodic memory: {str(e)}")
        raise ServiceUnavailableError("Episodic memory system unavailable") from e

def get_semantic_memory(
    db: Session = Depends(get_db),  # noqa: B008
    settings: Settings = Depends(get_settings)  # noqa: B008
) -> SemanticMemoryManager:
    """
    Provides access to the semantic memory system.
    
    Args:
        db: Database session
        settings: Application settings
        
    Returns:
        SemanticMemoryManager: Manager for semantic memory operations
        
    Example:
        @router.get("/knowledge/")
        async def get_knowledge(
            query: str,
            sm: SemanticMemoryManager = Depends(get_semantic_memory)
        ):
            return sm.query_knowledge(query)
    """
    try:
        return SemanticMemoryManager(db=db, config=settings.memory.semantic_memory)
    except Exception as e:  # noqa: BLE001
        logger.error(f"Failed to initialize semantic memory: {str(e)}")
        raise ServiceUnavailableError("Semantic memory system unavailable") from e

# ==================== Service Dependencies ====================

def get_llm_service(
    settings: Settings = Depends(get_settings)  # noqa: B008
) -> LLMService:
    """
    Provides access to the LLM service for generating responses.
    
    Args:
        settings: Application settings
        
    Returns:
        LLMService: Service for LLM interactions
        
    Example:
        @router.post("/generate/")
        async def generate_response(
            prompt: str,
            llm: LLMService = Depends(get_llm_service)
        ):
            return await llm.generate(prompt)
    """
    try:
        return LLMService(config=settings.llm)
    except Exception as e:  # noqa: BLE001
        logger.error(f"Failed to initialize LLM service: {str(e)}")
        raise ServiceUnavailableError("LLM service unavailable") from e

def get_health_monitor(
    db: Session = Depends(get_db),  # noqa: B008
    settings: Settings = Depends(get_settings)  # noqa: B008
) -> HealthMonitor:
    """
    Provides access to the system health monitoring service.
    
    Args:
        db: Database session
        settings: Application settings
        
    Returns:
        HealthMonitor: Service for monitoring system health
        
    Example:
        @router.get("/health/")
        async def get_system_health(
            health: HealthMonitor = Depends(get_health_monitor)
        ):
            return health.get_current_status()
    """
    try:
        return HealthMonitor(db=db, config=settings.health)
    except Exception as e:  # noqa: BLE001
        logger.error(f"Failed to initialize health monitor: {str(e)}")
        raise ServiceUnavailableError("Health monitoring system unavailable") from e

# ==================== Request Context Dependencies ====================

async def get_request_id(request: Request) -> str:
    """
    Extracts or generates a unique request ID for tracing.
    
    Args:
        request: FastAPI request object
        
    Returns:
        str: Unique request ID
        
    Example:
        @router.get("/items/")
        async def get_items(request_id: str = Depends(get_request_id)):
            logger.info(f"Processing request {request_id}")
            return {"request_id": request_id}
    """
    if "X-Request-ID" in request.headers:
        return request.headers["X-Request-ID"]
    
    # Generate a request ID if none provided
    import uuid
    return str(uuid.uuid4())

async def get_client_info(request: Request) -> dict[str, str]:
    """
    Extracts client information from the request.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Dict[str, str]: Client information including IP and user agent
        
    Example:
        @router.get("/status/")
        async def get_status(client: Dict[str, str] = Depends(get_client_info)):
            logger.info(f"Request from {client['ip']} using {client['user_agent']}")
            return {"status": "ok"}
    """
    return {
        "ip": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("User-Agent", "unknown"),
        "referer": request.headers.get("Referer", "unknown")
    }

# ==================== System Status Dependencies ====================

async def get_system_health(
    health_monitor: HealthMonitor = Depends(get_health_monitor)  # noqa: B008
) -> SystemHealth:
    """
    Provides the current system health status.
    
    Args:
        health_monitor: Health monitoring service
        
    Returns:
        SystemHealth: Current system health status
        
    Example:
        @router.get("/dashboard/")
        async def get_dashboard(health: SystemHealth = Depends(get_system_health)):
            return {"system_status": health.status, "metrics": health.metrics}
    """
    try:
        return health_monitor.get_current_status()
    except Exception as e:  # noqa: BLE001
        logger.error(f"Failed to get system health: {str(e)}")
        # Cannot raise here as it needs to return a SystemHealth object on failure
        return SystemHealth(
            status="degraded",
            message="Health monitoring system error",
            timestamp=datetime.utcnow(),
            metrics={}
        )

# ==================== Configuration Dependencies ====================

def get_api_version() -> str:
    """
    Returns the current API version.
    
    Returns:
        str: API version string
        
    Example:
        @router.get("/version/")
        async def get_version(version: str = Depends(get_api_version)):
            return {"version": version}
    """
    from neuroca import __version__
    return __version__
