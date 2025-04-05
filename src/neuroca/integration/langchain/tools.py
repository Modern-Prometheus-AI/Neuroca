"""
LangChain Tools Integration for NeuroCognitive Architecture (NCA)

This module provides custom LangChain tools that enable LLMs to interact with the
NeuroCognitive Architecture system. These tools allow LLMs to:
1. Access and manipulate the three-tiered memory system
2. Monitor and respond to health dynamics
3. Utilize cognitive functions provided by the NCA

The tools follow LangChain's tool specification and can be used with various
LangChain components like agents and chains.

Usage:
    from neuroca.integration.langchain.tools import (
        MemoryStorageTool, 
        MemoryRetrievalTool,
        HealthMonitorTool
    )
    
    # Create a LangChain agent with NCA tools
    tools = [MemoryStorageTool(), MemoryRetrievalTool(), HealthMonitorTool()]
    agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION)
"""

import json
import logging
from typing import Any, Optional

from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun

# LangChain imports
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from neuroca.core.exceptions import (
    HealthMonitorError,
    InvalidInputError,
    MemoryAccessError,
    MemoryStorageError,
)
from neuroca.core.health import HealthMonitor
from neuroca.memory.episodic_memory import EpisodicMemory
from neuroca.memory.semantic_memory import SemanticMemory

# NCA imports
from neuroca.memory.working_memory import WorkingMemory

# Configure logging
logger = logging.getLogger(__name__)


class MemoryInput(BaseModel):
    """Input schema for memory-related tools."""
    content: str = Field(..., description="The content to store or query in memory")
    memory_type: str = Field(
        ..., 
        description="The type of memory to access: 'working', 'episodic', or 'semantic'"
    )
    tags: Optional[list[str]] = Field(
        default=None, 
        description="Optional tags to categorize the memory"
    )
    metadata: Optional[dict[str, Any]] = Field(
        default=None, 
        description="Optional metadata associated with the memory"
    )


class MemoryRetrievalInput(BaseModel):
    """Input schema for memory retrieval operations."""
    query: str = Field(..., description="The query to search for in memory")
    memory_type: str = Field(
        ..., 
        description="The type of memory to search: 'working', 'episodic', or 'semantic'"
    )
    limit: int = Field(
        default=5, 
        description="Maximum number of results to return"
    )
    threshold: Optional[float] = Field(
        default=0.7, 
        description="Similarity threshold for retrieval (0.0 to 1.0)"
    )
    tags: Optional[list[str]] = Field(
        default=None, 
        description="Filter results by these tags"
    )


class HealthInput(BaseModel):
    """Input schema for health-related tools."""
    action: str = Field(
        ..., 
        description="The health action to perform: 'status', 'update', or 'alert'"
    )
    parameters: Optional[dict[str, Any]] = Field(
        default=None, 
        description="Parameters for the health action"
    )


class MemoryStorageTool(BaseTool):
    """
    Tool for storing information in the NCA memory system.
    
    This tool allows LLMs to store information in working, episodic, or semantic memory.
    Each memory type has different persistence and retrieval characteristics.
    """
    name = "memory_storage"
    description = """
    Store information in the NeuroCognitive Architecture memory system.
    Use this tool when you need to remember information for later use.
    You can specify the memory type:
    - 'working': Short-term, volatile memory for current task
    - 'episodic': Long-term memory for experiences and events
    - 'semantic': Long-term memory for facts and knowledge
    """
    args_schema: type[BaseModel] = MemoryInput
    
    def __init__(self):
        """Initialize memory storage tool with connections to memory systems."""
        super().__init__()
        self.working_memory = WorkingMemory()
        self.episodic_memory = EpisodicMemory()
        self.semantic_memory = SemanticMemory()
        logger.debug("MemoryStorageTool initialized")
    
    def _run(
        self, 
        content: str, 
        memory_type: str, 
        tags: Optional[list[str]] = None, 
        metadata: Optional[dict[str, Any]] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """
        Store content in the specified memory system.
        
        Args:
            content: The information to store
            memory_type: Type of memory ('working', 'episodic', or 'semantic')
            tags: Optional list of tags to categorize the memory
            metadata: Optional metadata to associate with the memory
            run_manager: LangChain callback manager
            
        Returns:
            Confirmation message with memory ID
            
        Raises:
            InvalidInputError: If memory_type is invalid
            MemoryStorageError: If storage operation fails
        """
        logger.debug(f"Storing in {memory_type} memory: {content[:50]}...")
        
        try:
            # Validate memory type
            memory_type = memory_type.lower()
            if memory_type not in ["working", "episodic", "semantic"]:
                raise InvalidInputError(f"Invalid memory type: {memory_type}. Must be 'working', 'episodic', or 'semantic'")
            
            # Prepare metadata
            safe_metadata = metadata or {}
            safe_tags = tags or []
            
            # Store in appropriate memory system
            if memory_type == "working":
                memory_id = self.working_memory.store(content, tags=safe_tags, metadata=safe_metadata)
            elif memory_type == "episodic":
                memory_id = self.episodic_memory.store(content, tags=safe_tags, metadata=safe_metadata)
            elif memory_type == "semantic":
                memory_id = self.semantic_memory.store(content, tags=safe_tags, metadata=safe_metadata)
            
            return f"Successfully stored in {memory_type} memory with ID: {memory_id}"
            
        except InvalidInputError as e:
            logger.error(f"Invalid input for memory storage: {str(e)}")
            return f"Error: {str(e)}"
        except MemoryStorageError as e:
            logger.error(f"Memory storage error: {str(e)}")
            return f"Failed to store in memory: {str(e)}"
        except Exception as e:
            logger.exception(f"Unexpected error in memory storage: {str(e)}")
            return f"Unexpected error storing memory: {str(e)}"
    
    async def _arun(
        self, 
        content: str, 
        memory_type: str, 
        tags: Optional[list[str]] = None, 
        metadata: Optional[dict[str, Any]] = None,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Async version of _run method."""
        # For simplicity, we're using the sync version
        # In a production environment, implement true async operations
        return self._run(content, memory_type, tags, metadata)


class MemoryRetrievalTool(BaseTool):
    """
    Tool for retrieving information from the NCA memory system.
    
    This tool allows LLMs to search and retrieve information from working,
    episodic, or semantic memory using similarity search.
    """
    name = "memory_retrieval"
    description = """
    Retrieve information from the NeuroCognitive Architecture memory system.
    Use this tool when you need to recall previously stored information.
    You can specify the memory type:
    - 'working': Short-term, volatile memory for current task
    - 'episodic': Long-term memory for experiences and events
    - 'semantic': Long-term memory for facts and knowledge
    """
    args_schema: type[BaseModel] = MemoryRetrievalInput
    
    def __init__(self):
        """Initialize memory retrieval tool with connections to memory systems."""
        super().__init__()
        self.working_memory = WorkingMemory()
        self.episodic_memory = EpisodicMemory()
        self.semantic_memory = SemanticMemory()
        logger.debug("MemoryRetrievalTool initialized")
    
    def _run(
        self, 
        query: str, 
        memory_type: str, 
        limit: int = 5, 
        threshold: float = 0.7,
        tags: Optional[list[str]] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """
        Retrieve content from the specified memory system.
        
        Args:
            query: The search query
            memory_type: Type of memory ('working', 'episodic', or 'semantic')
            limit: Maximum number of results to return
            threshold: Similarity threshold (0.0 to 1.0)
            tags: Optional list of tags to filter results
            run_manager: LangChain callback manager
            
        Returns:
            JSON string containing retrieved memories
            
        Raises:
            InvalidInputError: If memory_type is invalid or parameters are out of range
            MemoryAccessError: If retrieval operation fails
        """
        logger.debug(f"Retrieving from {memory_type} memory with query: {query[:50]}...")
        
        try:
            # Validate memory type
            memory_type = memory_type.lower()
            if memory_type not in ["working", "episodic", "semantic"]:
                raise InvalidInputError(f"Invalid memory type: {memory_type}. Must be 'working', 'episodic', or 'semantic'")
            
            # Validate parameters
            if limit < 1:
                limit = 1
            elif limit > 50:
                limit = 50
                
            if threshold < 0.0:
                threshold = 0.0
            elif threshold > 1.0:
                threshold = 1.0
            
            # Prepare filter parameters
            safe_tags = tags or []
            
            # Retrieve from appropriate memory system
            if memory_type == "working":
                results = self.working_memory.retrieve(
                    query, limit=limit, threshold=threshold, tags=safe_tags
                )
            elif memory_type == "episodic":
                results = self.episodic_memory.retrieve(
                    query, limit=limit, threshold=threshold, tags=safe_tags
                )
            elif memory_type == "semantic":
                results = self.semantic_memory.retrieve(
                    query, limit=limit, threshold=threshold, tags=safe_tags
                )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "id": result.id,
                    "content": result.content,
                    "similarity": result.similarity,
                    "created_at": str(result.created_at),
                    "tags": result.tags,
                    "metadata": result.metadata
                })
            
            if not formatted_results:
                return "No memories found matching the query."
                
            return json.dumps(formatted_results, indent=2)
            
        except InvalidInputError as e:
            logger.error(f"Invalid input for memory retrieval: {str(e)}")
            return f"Error: {str(e)}"
        except MemoryAccessError as e:
            logger.error(f"Memory access error: {str(e)}")
            return f"Failed to retrieve from memory: {str(e)}"
        except Exception as e:
            logger.exception(f"Unexpected error in memory retrieval: {str(e)}")
            return f"Unexpected error retrieving memory: {str(e)}"
    
    async def _arun(
        self, 
        query: str, 
        memory_type: str, 
        limit: int = 5, 
        threshold: float = 0.7,
        tags: Optional[list[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Async version of _run method."""
        # For simplicity, we're using the sync version
        # In a production environment, implement true async operations
        return self._run(query, memory_type, limit, threshold, tags)


class HealthMonitorTool(BaseTool):
    """
    Tool for interacting with the NCA health monitoring system.
    
    This tool allows LLMs to check the current health status of the NCA system,
    update health parameters, and respond to health alerts.
    """
    name = "health_monitor"
    description = """
    Monitor and interact with the NeuroCognitive Architecture health system.
    Use this tool to:
    - Check current health status ('status')
    - Update health parameters ('update')
    - Respond to health alerts ('alert')
    """
    args_schema: type[BaseModel] = HealthInput
    
    def __init__(self):
        """Initialize health monitor tool with connection to health system."""
        super().__init__()
        self.health_monitor = HealthMonitor()
        logger.debug("HealthMonitorTool initialized")
    
    def _run(
        self, 
        action: str, 
        parameters: Optional[dict[str, Any]] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """
        Perform health-related actions in the NCA system.
        
        Args:
            action: The health action to perform ('status', 'update', or 'alert')
            parameters: Parameters for the health action
            run_manager: LangChain callback manager
            
        Returns:
            Result of the health action
            
        Raises:
            InvalidInputError: If action is invalid
            HealthMonitorError: If health operation fails
        """
        logger.debug(f"Performing health action: {action}")
        
        try:
            # Validate action
            action = action.lower()
            if action not in ["status", "update", "alert"]:
                raise InvalidInputError(f"Invalid health action: {action}. Must be 'status', 'update', or 'alert'")
            
            # Prepare parameters
            safe_parameters = parameters or {}
            
            # Perform appropriate health action
            if action == "status":
                status = self.health_monitor.get_status()
                return json.dumps(status, indent=2)
                
            elif action == "update":
                if not safe_parameters:
                    raise InvalidInputError("Parameters required for 'update' action")
                
                result = self.health_monitor.update_parameters(safe_parameters)
                return f"Health parameters updated successfully: {json.dumps(result, indent=2)}"
                
            elif action == "alert":
                alert_id = safe_parameters.get("alert_id")
                if not alert_id:
                    # Get all active alerts
                    alerts = self.health_monitor.get_alerts()
                    if not alerts:
                        return "No active health alerts."
                    return f"Active health alerts: {json.dumps(alerts, indent=2)}"
                else:
                    # Respond to specific alert
                    response = safe_parameters.get("response", "acknowledged")
                    result = self.health_monitor.respond_to_alert(alert_id, response)
                    return f"Alert {alert_id} response processed: {result}"
            
        except InvalidInputError as e:
            logger.error(f"Invalid input for health action: {str(e)}")
            return f"Error: {str(e)}"
        except HealthMonitorError as e:
            logger.error(f"Health monitor error: {str(e)}")
            return f"Failed to perform health action: {str(e)}"
        except Exception as e:
            logger.exception(f"Unexpected error in health action: {str(e)}")
            return f"Unexpected error in health system: {str(e)}"
    
    async def _arun(
        self, 
        action: str, 
        parameters: Optional[dict[str, Any]] = None,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Async version of _run method."""
        # For simplicity, we're using the sync version
        # In a production environment, implement true async operations
        return self._run(action, parameters)


class CognitiveProcessTool(BaseTool):
    """
    Tool for triggering cognitive processes in the NCA system.
    
    This tool allows LLMs to initiate various cognitive processes like
    reasoning, planning, and decision-making within the NCA framework.
    """
    name = "cognitive_process"
    description = """
    Trigger cognitive processes in the NeuroCognitive Architecture.
    This tool allows access to higher-order cognitive functions like
    reasoning, planning, and decision-making.
    """
    
    def __init__(self):
        """Initialize cognitive process tool."""
        super().__init__()
        # Import here to avoid circular imports
        from neuroca.core.cognition import CognitiveProcessor
        self.cognitive_processor = CognitiveProcessor()
        logger.debug("CognitiveProcessTool initialized")
    
    def _run(
        self, 
        process_type: str, 
        input_data: str,
        parameters: Optional[dict[str, Any]] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """
        Trigger a cognitive process in the NCA system.
        
        Args:
            process_type: Type of cognitive process to trigger
            input_data: Input data for the cognitive process
            parameters: Additional parameters for the process
            run_manager: LangChain callback manager
            
        Returns:
            Result of the cognitive process
            
        Raises:
            InvalidInputError: If process_type is invalid
            Exception: If cognitive process fails
        """
        logger.debug(f"Triggering cognitive process: {process_type}")
        
        try:
            # Validate process type
            process_type = process_type.lower()
            valid_processes = ["reason", "plan", "decide", "reflect", "associate"]
            if process_type not in valid_processes:
                raise InvalidInputError(f"Invalid process type: {process_type}. Must be one of {valid_processes}")
            
            # Prepare parameters
            safe_parameters = parameters or {}
            
            # Trigger appropriate cognitive process
            result = self.cognitive_processor.process(
                process_type=process_type,
                input_data=input_data,
                parameters=safe_parameters
            )
            
            return json.dumps(result, indent=2)
            
        except InvalidInputError as e:
            logger.error(f"Invalid input for cognitive process: {str(e)}")
            return f"Error: {str(e)}"
        except Exception as e:
            logger.exception(f"Error in cognitive process: {str(e)}")
            return f"Failed to complete cognitive process: {str(e)}"
    
    async def _arun(
        self, 
        process_type: str, 
        input_data: str,
        parameters: Optional[dict[str, Any]] = None,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Async version of _run method."""
        # For simplicity, we're using the sync version
        # In a production environment, implement true async operations
        return self._run(process_type, input_data, parameters)


def get_all_tools() -> list[BaseTool]:
    """
    Get all available NCA tools for LangChain integration.
    
    Returns:
        List of all NCA tools ready for use with LangChain
    """
    return [
        MemoryStorageTool(),
        MemoryRetrievalTool(),
        HealthMonitorTool(),
        CognitiveProcessTool()
    ]


def get_memory_tools() -> list[BaseTool]:
    """
    Get only memory-related NCA tools.
    
    Returns:
        List of memory-related tools
    """
    return [MemoryStorageTool(), MemoryRetrievalTool()]


def get_health_tools() -> list[BaseTool]:
    """
    Get only health-related NCA tools.
    
    Returns:
        List of health-related tools
    """
    return [HealthMonitorTool()]


def get_cognitive_tools() -> list[BaseTool]:
    """
    Get only cognitive process NCA tools.
    
    Returns:
        List of cognitive process tools
    """
    return [CognitiveProcessTool()]