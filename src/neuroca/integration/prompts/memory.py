"""
Memory-related prompt templates and utilities for NeuroCognitive Architecture.

This module provides a collection of prompt templates and utilities for interacting
with the three-tiered memory system of the NeuroCognitive Architecture. It includes
templates for memory retrieval, storage, consolidation, and forgetting operations.

The module is designed to be used by the integration layer to format prompts for
LLM interactions related to memory operations.

Usage:
    from neuroca.integration.prompts.memory import (
        get_working_memory_prompt,
        get_episodic_memory_prompt,
        get_semantic_memory_prompt,
        get_memory_consolidation_prompt,
    )

    # Generate a prompt for retrieving information from working memory
    prompt = get_working_memory_prompt(context="current task", query="recent information")
"""

import json
import logging
from datetime import datetime
from typing import Any, Optional, Union

from neuroca.core.exceptions import InvalidPromptParameterError, PromptGenerationError
from neuroca.core.utils.validation import validate_dict, validate_list, validate_string

# Configure logger
logger = logging.getLogger(__name__)

# Constants for prompt templates
MAX_PROMPT_LENGTH = 8192  # Maximum length of a prompt in tokens (adjust based on model)
MAX_MEMORY_ITEMS = 100    # Maximum number of memory items to include in a prompt
DEFAULT_TEMPERATURE = 0.7  # Default temperature for memory-related prompts

# Template sections
SYSTEM_HEADER = """You are a cognitive architecture with a three-tiered memory system:
1. Working Memory: Short-term, limited capacity, currently active information
2. Episodic Memory: Personal experiences and events with temporal context
3. Semantic Memory: General knowledge, concepts, and facts without specific context

Your task is to {task} based on the provided information."""

WORKING_MEMORY_TEMPLATE = """
## Working Memory Context
{context}

## Current Task
{task_description}

## Query
{query}

Respond with information from your working memory that is relevant to the query.
Be concise and focus on the most recent and relevant information.
"""

EPISODIC_MEMORY_TEMPLATE = """
## Episodic Memory Access
Time Period: {time_period}
Location: {location}
Associated Entities: {entities}
Emotional Valence: {emotional_valence}

## Memory Query
{query}

Retrieve episodic memories that match these parameters. Include temporal context,
sensory details, and emotional components. If multiple memories match, prioritize
by {priority_criteria}.
"""

SEMANTIC_MEMORY_TEMPLATE = """
## Semantic Memory Access
Domain: {domain}
Concepts: {concepts}
Relationships: {relationships}

## Knowledge Query
{query}

Retrieve semantic knowledge related to this query. Provide structured information
without specific episodic context. Include definitions, relationships, and general facts.
"""

MEMORY_CONSOLIDATION_TEMPLATE = """
## Memory Consolidation Process
Source Memory Type: {source_memory_type}
Target Memory Type: {target_memory_type}
Consolidation Criteria: {consolidation_criteria}

## Memory Items to Consider
{memory_items}

Analyze these memory items and determine which should be consolidated from {source_memory_type}
to {target_memory_type} based on the provided criteria. For each item, provide:
1. Decision (consolidate/retain/discard)
2. Justification
3. Transformed representation (if consolidated)
"""

MEMORY_FORGETTING_TEMPLATE = """
## Memory Forgetting Process
Memory Type: {memory_type}
Forgetting Criteria: {forgetting_criteria}
Retention Importance: {retention_importance}

## Memory Items to Evaluate
{memory_items}

Evaluate these memory items against the forgetting criteria. For each item, provide:
1. Decision (retain/forget)
2. Importance score (1-10)
3. Justification
"""


def get_working_memory_prompt(
    context: str,
    query: str,
    task_description: str = "process current information",
    system_instruction: Optional[str] = None,
) -> dict[str, Union[str, float]]:
    """
    Generate a prompt for retrieving information from working memory.

    Args:
        context: The current context in working memory
        query: The specific query or question about working memory
        task_description: Description of the current task (default: "process current information")
        system_instruction: Optional custom system instruction to override default

    Returns:
        Dict containing the formatted prompt with 'system', 'user' messages and parameters

    Raises:
        InvalidPromptParameterError: If any input parameters are invalid
        PromptGenerationError: If prompt generation fails
    """
    try:
        # Validate inputs
        validate_string(context, "context", min_length=1, max_length=MAX_PROMPT_LENGTH // 2)
        validate_string(query, "query", min_length=1, max_length=1000)
        validate_string(task_description, "task_description", min_length=1, max_length=500)
        
        if system_instruction is not None:
            validate_string(system_instruction, "system_instruction", max_length=1000)
        
        # Format system message
        system_msg = system_instruction or SYSTEM_HEADER.format(task="access working memory")
        
        # Format user message
        user_msg = WORKING_MEMORY_TEMPLATE.format(
            context=context,
            task_description=task_description,
            query=query
        )
        
        # Check if prompt is too long
        if len(system_msg) + len(user_msg) > MAX_PROMPT_LENGTH:
            logger.warning(
                "Working memory prompt exceeds recommended length. Truncating context."
            )
            # Truncate context to fit within limits
            max_context_length = MAX_PROMPT_LENGTH - len(system_msg) - len(user_msg) + len(context)
            context = context[:max_context_length] + "... [truncated]"
            user_msg = WORKING_MEMORY_TEMPLATE.format(
                context=context,
                task_description=task_description,
                query=query
            )
        
        logger.debug(f"Generated working memory prompt for query: {query[:50]}...")
        
        return {
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            "temperature": DEFAULT_TEMPERATURE,
            "max_tokens": 1000
        }
    
    except (InvalidPromptParameterError) as e:
        logger.error(f"Invalid parameter in working memory prompt: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Failed to generate working memory prompt: {str(e)}")
        raise PromptGenerationError(f"Failed to generate working memory prompt: {str(e)}")


def get_episodic_memory_prompt(
    query: str,
    time_period: Optional[str] = None,
    location: Optional[str] = None,
    entities: Optional[list[str]] = None,
    emotional_valence: Optional[str] = None,
    priority_criteria: str = "recency and emotional significance",
    system_instruction: Optional[str] = None,
) -> dict[str, Union[str, float]]:
    """
    Generate a prompt for retrieving information from episodic memory.

    Args:
        query: The specific query about episodic memory
        time_period: Optional time period to search within (e.g., "yesterday", "last week")
        location: Optional location associated with the memory
        entities: Optional list of entities (people, objects) associated with the memory
        emotional_valence: Optional emotional tone of the memory (e.g., "positive", "negative")
        priority_criteria: Criteria for prioritizing memories (default: "recency and emotional significance")
        system_instruction: Optional custom system instruction to override default

    Returns:
        Dict containing the formatted prompt with 'system', 'user' messages and parameters

    Raises:
        InvalidPromptParameterError: If any input parameters are invalid
        PromptGenerationError: If prompt generation fails
    """
    try:
        # Validate inputs
        validate_string(query, "query", min_length=1, max_length=1000)
        validate_string(priority_criteria, "priority_criteria", min_length=1, max_length=200)
        
        if time_period is not None:
            validate_string(time_period, "time_period", max_length=200)
        
        if location is not None:
            validate_string(location, "location", max_length=200)
        
        if entities is not None:
            validate_list(entities, "entities", max_length=20)
            for i, entity in enumerate(entities):
                validate_string(entity, f"entities[{i}]", max_length=100)
        
        if emotional_valence is not None:
            validate_string(emotional_valence, "emotional_valence", max_length=100)
            
        if system_instruction is not None:
            validate_string(system_instruction, "system_instruction", max_length=1000)
        
        # Format system message
        system_msg = system_instruction or SYSTEM_HEADER.format(task="access episodic memory")
        
        # Format user message with defaults for optional parameters
        user_msg = EPISODIC_MEMORY_TEMPLATE.format(
            time_period=time_period or "any time period",
            location=location or "any location",
            entities=", ".join(entities) if entities else "any relevant entities",
            emotional_valence=emotional_valence or "any emotional tone",
            query=query,
            priority_criteria=priority_criteria
        )
        
        logger.debug(f"Generated episodic memory prompt for query: {query[:50]}...")
        
        return {
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            "temperature": DEFAULT_TEMPERATURE,
            "max_tokens": 1500
        }
    
    except (InvalidPromptParameterError) as e:
        logger.error(f"Invalid parameter in episodic memory prompt: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Failed to generate episodic memory prompt: {str(e)}")
        raise PromptGenerationError(f"Failed to generate episodic memory prompt: {str(e)}")


def get_semantic_memory_prompt(
    query: str,
    domain: Optional[str] = None,
    concepts: Optional[list[str]] = None,
    relationships: Optional[list[str]] = None,
    system_instruction: Optional[str] = None,
) -> dict[str, Union[str, float]]:
    """
    Generate a prompt for retrieving information from semantic memory.

    Args:
        query: The specific query about semantic knowledge
        domain: Optional knowledge domain to search within (e.g., "physics", "history")
        concepts: Optional list of concepts related to the query
        relationships: Optional list of relationships between concepts to explore
        system_instruction: Optional custom system instruction to override default

    Returns:
        Dict containing the formatted prompt with 'system', 'user' messages and parameters

    Raises:
        InvalidPromptParameterError: If any input parameters are invalid
        PromptGenerationError: If prompt generation fails
    """
    try:
        # Validate inputs
        validate_string(query, "query", min_length=1, max_length=1000)
        
        if domain is not None:
            validate_string(domain, "domain", max_length=200)
        
        if concepts is not None:
            validate_list(concepts, "concepts", max_length=20)
            for i, concept in enumerate(concepts):
                validate_string(concept, f"concepts[{i}]", max_length=100)
        
        if relationships is not None:
            validate_list(relationships, "relationships", max_length=20)
            for i, relationship in enumerate(relationships):
                validate_string(relationship, f"relationships[{i}]", max_length=100)
                
        if system_instruction is not None:
            validate_string(system_instruction, "system_instruction", max_length=1000)
        
        # Format system message
        system_msg = system_instruction or SYSTEM_HEADER.format(task="access semantic memory")
        
        # Format user message with defaults for optional parameters
        user_msg = SEMANTIC_MEMORY_TEMPLATE.format(
            domain=domain or "relevant domains",
            concepts=", ".join(concepts) if concepts else "relevant concepts",
            relationships=", ".join(relationships) if relationships else "relevant relationships",
            query=query
        )
        
        logger.debug(f"Generated semantic memory prompt for query: {query[:50]}...")
        
        return {
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            "temperature": DEFAULT_TEMPERATURE,
            "max_tokens": 2000
        }
    
    except (InvalidPromptParameterError) as e:
        logger.error(f"Invalid parameter in semantic memory prompt: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Failed to generate semantic memory prompt: {str(e)}")
        raise PromptGenerationError(f"Failed to generate semantic memory prompt: {str(e)}")


def get_memory_consolidation_prompt(
    memory_items: list[dict[str, Any]],
    source_memory_type: str,
    target_memory_type: str,
    consolidation_criteria: str,
    system_instruction: Optional[str] = None,
) -> dict[str, Union[str, float]]:
    """
    Generate a prompt for memory consolidation between different memory tiers.

    Args:
        memory_items: List of memory items to consider for consolidation
        source_memory_type: The source memory tier (e.g., "working", "episodic", "semantic")
        target_memory_type: The target memory tier (e.g., "working", "episodic", "semantic")
        consolidation_criteria: Criteria for determining what should be consolidated
        system_instruction: Optional custom system instruction to override default

    Returns:
        Dict containing the formatted prompt with 'system', 'user' messages and parameters

    Raises:
        InvalidPromptParameterError: If any input parameters are invalid
        PromptGenerationError: If prompt generation fails
    """
    try:
        # Validate inputs
        validate_list(memory_items, "memory_items", min_length=1, max_length=MAX_MEMORY_ITEMS)
        validate_string(source_memory_type, "source_memory_type", min_length=1, max_length=100)
        validate_string(target_memory_type, "target_memory_type", min_length=1, max_length=100)
        validate_string(consolidation_criteria, "consolidation_criteria", min_length=1, max_length=500)
        
        if system_instruction is not None:
            validate_string(system_instruction, "system_instruction", max_length=1000)
        
        # Validate memory items
        for i, item in enumerate(memory_items):
            validate_dict(item, f"memory_items[{i}]")
        
        # Format memory items as JSON string
        memory_items_str = json.dumps(memory_items, indent=2)
        
        # Check if memory items are too large and truncate if necessary
        if len(memory_items_str) > MAX_PROMPT_LENGTH // 2:
            logger.warning(
                f"Memory items exceed recommended length. Truncating to {MAX_MEMORY_ITEMS // 2} items."
            )
            memory_items = memory_items[:MAX_MEMORY_ITEMS // 2]
            memory_items_str = json.dumps(memory_items, indent=2)
            memory_items_str += "\n... [additional items truncated]"
        
        # Format system message
        system_msg = system_instruction or SYSTEM_HEADER.format(task="perform memory consolidation")
        
        # Format user message
        user_msg = MEMORY_CONSOLIDATION_TEMPLATE.format(
            source_memory_type=source_memory_type,
            target_memory_type=target_memory_type,
            consolidation_criteria=consolidation_criteria,
            memory_items=memory_items_str
        )
        
        logger.debug(
            f"Generated memory consolidation prompt from {source_memory_type} to {target_memory_type} "
            f"with {len(memory_items)} items"
        )
        
        return {
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            "temperature": DEFAULT_TEMPERATURE,
            "max_tokens": 2000
        }
    
    except (InvalidPromptParameterError) as e:
        logger.error(f"Invalid parameter in memory consolidation prompt: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Failed to generate memory consolidation prompt: {str(e)}")
        raise PromptGenerationError(f"Failed to generate memory consolidation prompt: {str(e)}")


def get_memory_forgetting_prompt(
    memory_items: list[dict[str, Any]],
    memory_type: str,
    forgetting_criteria: str,
    retention_importance: str = "relevance to current goals and emotional significance",
    system_instruction: Optional[str] = None,
) -> dict[str, Union[str, float]]:
    """
    Generate a prompt for memory forgetting/pruning operations.

    Args:
        memory_items: List of memory items to evaluate for forgetting
        memory_type: The memory tier to operate on (e.g., "working", "episodic", "semantic")
        forgetting_criteria: Criteria for determining what should be forgotten
        retention_importance: Criteria for determining what should be retained
        system_instruction: Optional custom system instruction to override default

    Returns:
        Dict containing the formatted prompt with 'system', 'user' messages and parameters

    Raises:
        InvalidPromptParameterError: If any input parameters are invalid
        PromptGenerationError: If prompt generation fails
    """
    try:
        # Validate inputs
        validate_list(memory_items, "memory_items", min_length=1, max_length=MAX_MEMORY_ITEMS)
        validate_string(memory_type, "memory_type", min_length=1, max_length=100)
        validate_string(forgetting_criteria, "forgetting_criteria", min_length=1, max_length=500)
        validate_string(retention_importance, "retention_importance", min_length=1, max_length=500)
        
        if system_instruction is not None:
            validate_string(system_instruction, "system_instruction", max_length=1000)
        
        # Validate memory items
        for i, item in enumerate(memory_items):
            validate_dict(item, f"memory_items[{i}]")
        
        # Format memory items as JSON string
        memory_items_str = json.dumps(memory_items, indent=2)
        
        # Check if memory items are too large and truncate if necessary
        if len(memory_items_str) > MAX_PROMPT_LENGTH // 2:
            logger.warning(
                f"Memory items exceed recommended length. Truncating to {MAX_MEMORY_ITEMS // 2} items."
            )
            memory_items = memory_items[:MAX_MEMORY_ITEMS // 2]
            memory_items_str = json.dumps(memory_items, indent=2)
            memory_items_str += "\n... [additional items truncated]"
        
        # Format system message
        system_msg = system_instruction or SYSTEM_HEADER.format(task="evaluate memory items for forgetting")
        
        # Format user message
        user_msg = MEMORY_FORGETTING_TEMPLATE.format(
            memory_type=memory_type,
            forgetting_criteria=forgetting_criteria,
            retention_importance=retention_importance,
            memory_items=memory_items_str
        )
        
        logger.debug(
            f"Generated memory forgetting prompt for {memory_type} memory with {len(memory_items)} items"
        )
        
        return {
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            "temperature": DEFAULT_TEMPERATURE,
            "max_tokens": 2000
        }
    
    except (InvalidPromptParameterError) as e:
        logger.error(f"Invalid parameter in memory forgetting prompt: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Failed to generate memory forgetting prompt: {str(e)}")
        raise PromptGenerationError(f"Failed to generate memory forgetting prompt: {str(e)}")


def format_memory_for_prompt(
    memories: list[dict[str, Any]], 
    max_items: int = 20,
    include_fields: Optional[list[str]] = None
) -> str:
    """
    Format a list of memory items for inclusion in a prompt.

    Args:
        memories: List of memory dictionaries to format
        max_items: Maximum number of memory items to include
        include_fields: Optional list of fields to include (defaults to all)

    Returns:
        Formatted string representation of memories

    Raises:
        InvalidPromptParameterError: If input parameters are invalid
    """
    try:
        validate_list(memories, "memories", max_length=MAX_MEMORY_ITEMS)
        
        if include_fields is not None:
            validate_list(include_fields, "include_fields", max_length=20)
            for i, field in enumerate(include_fields):
                validate_string(field, f"include_fields[{i}]", max_length=100)
        
        # Limit number of memories
        memories = memories[:max_items]
        
        formatted_memories = []
        for i, memory in enumerate(memories):
            validate_dict(memory, f"memories[{i}]")
            
            # Filter fields if specified
            if include_fields:
                memory = {k: v for k, v in memory.items() if k in include_fields}
            
            # Format timestamp if present
            if "timestamp" in memory and isinstance(memory["timestamp"], (int, float)):
                try:
                    memory["timestamp"] = datetime.fromtimestamp(memory["timestamp"]).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                except (ValueError, OverflowError, OSError) as e:
                    logger.warning(f"Failed to format timestamp: {str(e)}")
            
            # Format the memory item
            memory_str = f"Memory {i+1}:\n"
            for key, value in memory.items():
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, indent=2)
                memory_str += f"  {key}: {value}\n"
            
            formatted_memories.append(memory_str)
        
        return "\n".join(formatted_memories)
    
    except (InvalidPromptParameterError) as e:
        logger.error(f"Invalid parameter in memory formatting: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Failed to format memories for prompt: {str(e)}")
        raise PromptGenerationError(f"Failed to format memories for prompt: {str(e)}")


def get_memory_search_prompt(
    query: str,
    memory_types: list[str],
    search_parameters: Optional[dict[str, Any]] = None,
    system_instruction: Optional[str] = None,
) -> dict[str, Union[str, float]]:
    """
    Generate a prompt for searching across multiple memory types.

    Args:
        query: The search query
        memory_types: List of memory types to search (e.g., ["working", "episodic", "semantic"])
        search_parameters: Optional additional search parameters
        system_instruction: Optional custom system instruction to override default

    Returns:
        Dict containing the formatted prompt with 'system', 'user' messages and parameters

    Raises:
        InvalidPromptParameterError: If any input parameters are invalid
        PromptGenerationError: If prompt generation fails
    """
    try:
        # Validate inputs
        validate_string(query, "query", min_length=1, max_length=1000)
        validate_list(memory_types, "memory_types", min_length=1, max_length=10)
        
        for i, memory_type in enumerate(memory_types):
            validate_string(memory_type, f"memory_types[{i}]", min_length=1, max_length=100)
        
        if search_parameters is not None:
            validate_dict(search_parameters, "search_parameters")
        
        if system_instruction is not None:
            validate_string(system_instruction, "system_instruction", max_length=1000)
        
        # Format system message
        system_msg = system_instruction or SYSTEM_HEADER.format(task="search across memory systems")
        
        # Format user message
        user_msg = f"""
## Memory Search Request
Query: {query}
Memory Types to Search: {', '.join(memory_types)}

"""
        
        # Add search parameters if provided
        if search_parameters:
            user_msg += "## Search Parameters\n"
            for key, value in search_parameters.items():
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, indent=2)
                user_msg += f"{key}: {value}\n"
        
        user_msg += """
Search across the specified memory types for information relevant to the query.
For each memory type, provide:
1. Relevant information found
2. Confidence level (high/medium/low)
3. Source attribution

If information conflicts between memory types, note the discrepancies and provide reasoning
about which source is likely more reliable.
"""
        
        logger.debug(f"Generated memory search prompt for query: {query[:50]}...")
        
        return {
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            "temperature": DEFAULT_TEMPERATURE,
            "max_tokens": 2000
        }
    
    except (InvalidPromptParameterError) as e:
        logger.error(f"Invalid parameter in memory search prompt: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Failed to generate memory search prompt: {str(e)}")
        raise PromptGenerationError(f"Failed to generate memory search prompt: {str(e)}")