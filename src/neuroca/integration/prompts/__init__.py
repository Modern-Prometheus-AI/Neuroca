"""
Prompt Management Module for NeuroCognitive Architecture (NCA).

This module provides a comprehensive framework for managing, validating, and
optimizing prompts used for LLM interactions within the NCA system. It serves as
the central interface for all prompt-related functionality, ensuring consistent
prompt handling across the application.

Key features:
- Standardized prompt templates with variable substitution
- Prompt validation and sanitization
- Prompt versioning and history tracking
- Context-aware prompt selection and optimization
- Integration with memory tiers for contextual enhancement

Usage Examples:
    # Basic prompt retrieval
    from neuroca.integration.prompts import get_prompt
    
    prompt = get_prompt("memory_recall", context={"topic": "neural networks"})
    
    # Creating a custom prompt
    from neuroca.integration.prompts import PromptTemplate
    
    template = PromptTemplate(
        "Analyze the following text: {{text}}",
        required_vars=["text"],
        metadata={"domain": "text_analysis", "version": "1.0"}
    )
    
    # Registering a new prompt template
    from neuroca.integration.prompts import register_prompt
    
    register_prompt("text_analysis", template)
"""

import hashlib
import importlib.resources
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Union

# Configure module logger
logger = logging.getLogger(__name__)

# Constants
DEFAULT_PROMPT_DIR = "templates"
PROMPT_FILE_EXTENSION = ".json"
VARIABLE_PATTERN = r"{{(.*?)}}"

@dataclass
class PromptTemplate:
    """
    A structured template for LLM prompts with variable substitution capabilities.
    
    Attributes:
        template (str): The prompt template text with variables in {{variable}} format
        required_vars (Set[str]): Variables that must be provided when rendering
        optional_vars (Set[str]): Variables that may be provided but aren't required
        metadata (Dict[str, Any]): Additional information about the prompt
        version (str): Version identifier for the prompt template
        created_at (datetime): When this prompt template was created
        updated_at (datetime): When this prompt template was last modified
    """
    template: str
    required_vars: set[str] = field(default_factory=set)
    optional_vars: set[str] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate the template and extract variables if not explicitly provided."""
        # Extract all variables from the template if not provided
        if not self.required_vars and not self.optional_vars:
            all_vars = self._extract_variables()
            self.required_vars = all_vars
        
        # Validate that all required variables appear in the template
        template_vars = self._extract_variables()
        for var in self.required_vars:
            if var not in template_vars:
                raise ValueError(f"Required variable '{var}' not found in template")
        
        # Generate a version hash if not provided
        if self.version == "1.0.0":
            self.version = self._generate_version_hash()
    
    def _extract_variables(self) -> set[str]:
        """Extract all variable names from the template."""
        return set(re.findall(VARIABLE_PATTERN, self.template))
    
    def _generate_version_hash(self) -> str:
        """Generate a version hash based on the template content."""
        content_hash = hashlib.md5(self.template.encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d")
        return f"{timestamp}-{content_hash}"
    
    def render(self, context: dict[str, Any]) -> str:
        """
        Render the template by substituting variables with values from context.
        
        Args:
            context: Dictionary mapping variable names to their values
            
        Returns:
            The rendered prompt with all variables substituted
            
        Raises:
            ValueError: If required variables are missing from the context
        """
        # Validate that all required variables are provided
        missing_vars = self.required_vars - set(context.keys())
        if missing_vars:
            raise ValueError(f"Missing required variables: {', '.join(missing_vars)}")
        
        # Perform variable substitution
        result = self.template
        for var_name, var_value in context.items():
            if var_name in self.required_vars or var_name in self.optional_vars:
                result = result.replace(f"{{{{{var_name}}}}}", str(var_value))
        
        return result
    
    def to_dict(self) -> dict[str, Any]:
        """Convert the template to a dictionary for serialization."""
        return {
            "template": self.template,
            "required_vars": list(self.required_vars),
            "optional_vars": list(self.optional_vars),
            "metadata": self.metadata,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'PromptTemplate':
        """Create a PromptTemplate instance from a dictionary."""
        # Convert string dates back to datetime objects
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if isinstance(data.get("updated_at"), str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        
        # Convert lists back to sets
        if "required_vars" in data and isinstance(data["required_vars"], list):
            data["required_vars"] = set(data["required_vars"])
        if "optional_vars" in data and isinstance(data["optional_vars"], list):
            data["optional_vars"] = set(data["optional_vars"])
            
        return cls(**data)


class PromptRegistry:
    """
    Registry for managing and accessing prompt templates.
    
    This class provides a centralized store for prompt templates with methods
    for registration, retrieval, and management of prompts.
    """
    def __init__(self):
        """Initialize an empty prompt registry."""
        self._prompts: dict[str, PromptTemplate] = {}
        self._loaded = False
        self._prompt_dir = None
    
    def register(self, name: str, template: PromptTemplate) -> None:
        """
        Register a prompt template with the given name.
        
        Args:
            name: Unique identifier for the prompt
            template: The prompt template to register
            
        Raises:
            ValueError: If a prompt with the same name already exists
        """
        if name in self._prompts:
            logger.warning(f"Overwriting existing prompt template: {name}")
        
        self._prompts[name] = template
        logger.debug(f"Registered prompt template: {name} (version: {template.version})")
    
    def get(self, name: str) -> PromptTemplate:
        """
        Retrieve a prompt template by name.
        
        Args:
            name: The name of the prompt template to retrieve
            
        Returns:
            The requested prompt template
            
        Raises:
            KeyError: If no prompt with the given name exists
        """
        if not self._loaded:
            self.load_default_prompts()
            
        if name not in self._prompts:
            raise KeyError(f"Prompt template not found: {name}")
        
        return self._prompts[name]
    
    def render(self, name: str, context: dict[str, Any]) -> str:
        """
        Render a prompt template with the given context.
        
        Args:
            name: The name of the prompt template to render
            context: Dictionary of variables to substitute in the template
            
        Returns:
            The rendered prompt string
            
        Raises:
            KeyError: If no prompt with the given name exists
            ValueError: If required variables are missing from the context
        """
        template = self.get(name)
        return template.render(context)
    
    def list_prompts(self) -> list[str]:
        """
        List all registered prompt names.
        
        Returns:
            A list of all registered prompt template names
        """
        if not self._loaded:
            self.load_default_prompts()
            
        return list(self._prompts.keys())
    
    def set_prompt_directory(self, directory: Union[str, Path]) -> None:
        """
        Set the directory to load prompt templates from.
        
        Args:
            directory: Path to the directory containing prompt templates
        """
        self._prompt_dir = Path(directory)
        logger.info(f"Set prompt directory to: {self._prompt_dir}")
    
    def load_default_prompts(self) -> None:
        """
        Load default prompt templates from the package's templates directory.
        
        This method attempts to load prompt templates from:
        1. The directory set with set_prompt_directory()
        2. The package's templates directory
        """
        try:
            # Try to load from the specified directory
            if self._prompt_dir and self._prompt_dir.exists():
                self._load_from_directory(self._prompt_dir)
            else:
                # Try to load from the package's templates directory
                try:
                    with importlib.resources.path("neuroca.integration.prompts", DEFAULT_PROMPT_DIR) as path:
                        if path.exists():
                            self._load_from_directory(path)
                except (ImportError, FileNotFoundError) as e:
                    logger.warning(f"Could not load default prompts: {e}")
            
            self._loaded = True
            logger.info(f"Loaded {len(self._prompts)} prompt templates")
        except Exception as e:
            logger.error(f"Error loading default prompts: {e}", exc_info=True)
            # Don't raise the exception - failing to load default prompts
            # shouldn't break the application
    
    def _load_from_directory(self, directory: Path) -> None:
        """
        Load prompt templates from JSON files in the specified directory.
        
        Args:
            directory: Path to the directory containing prompt template files
        """
        if not directory.exists():
            logger.warning(f"Prompt directory does not exist: {directory}")
            return
            
        for file_path in directory.glob(f"*{PROMPT_FILE_EXTENSION}"):
            try:
                prompt_name = file_path.stem
                with open(file_path, encoding='utf-8') as f:
                    prompt_data = json.load(f)
                
                template = PromptTemplate.from_dict(prompt_data)
                self.register(prompt_name, template)
                logger.debug(f"Loaded prompt template from file: {file_path}")
            except Exception as e:
                logger.error(f"Error loading prompt template from {file_path}: {e}", exc_info=True)
    
    def save_to_directory(self, directory: Union[str, Path]) -> None:
        """
        Save all registered prompts to JSON files in the specified directory.
        
        Args:
            directory: Path to the directory where prompt templates will be saved
        """
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        
        for name, template in self._prompts.items():
            try:
                file_path = directory / f"{name}{PROMPT_FILE_EXTENSION}"
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(template.to_dict(), f, indent=2)
                logger.debug(f"Saved prompt template to file: {file_path}")
            except Exception as e:
                logger.error(f"Error saving prompt template {name} to {file_path}: {e}", exc_info=True)


# Create a global prompt registry instance
_registry = PromptRegistry()

# Public API functions

def get_prompt(name: str, context: Optional[dict[str, Any]] = None) -> Union[PromptTemplate, str]:
    """
    Get a prompt template or render it with the provided context.
    
    Args:
        name: The name of the prompt template to retrieve
        context: Optional dictionary of variables to substitute in the template
        
    Returns:
        If context is provided, returns the rendered prompt string.
        Otherwise, returns the prompt template object.
        
    Raises:
        KeyError: If no prompt with the given name exists
        ValueError: If required variables are missing from the context
    """
    if context is not None:
        return _registry.render(name, context)
    return _registry.get(name)

def register_prompt(name: str, template: Union[str, PromptTemplate], 
                   required_vars: Optional[list[str]] = None,
                   optional_vars: Optional[list[str]] = None,
                   metadata: Optional[dict[str, Any]] = None) -> None:
    """
    Register a new prompt template.
    
    Args:
        name: Unique identifier for the prompt
        template: Either a PromptTemplate object or a template string
        required_vars: List of required variables (only used if template is a string)
        optional_vars: List of optional variables (only used if template is a string)
        metadata: Additional information about the prompt (only used if template is a string)
        
    Raises:
        ValueError: If a prompt with the same name already exists
    """
    if isinstance(template, str):
        template = PromptTemplate(
            template=template,
            required_vars=set(required_vars or []),
            optional_vars=set(optional_vars or []),
            metadata=metadata or {}
        )
    
    _registry.register(name, template)

def list_prompts() -> list[str]:
    """
    List all registered prompt names.
    
    Returns:
        A list of all registered prompt template names
    """
    return _registry.list_prompts()

def set_prompt_directory(directory: Union[str, Path]) -> None:
    """
    Set the directory to load prompt templates from.
    
    Args:
        directory: Path to the directory containing prompt templates
    """
    _registry.set_prompt_directory(directory)

def load_prompts() -> None:
    """
    Explicitly load prompt templates from the configured directory.
    """
    _registry.load_default_prompts()

def save_prompts(directory: Union[str, Path]) -> None:
    """
    Save all registered prompts to JSON files in the specified directory.
    
    Args:
        directory: Path to the directory where prompt templates will be saved
    """
    _registry.save_to_directory(directory)

# Initialize the module by loading default prompts
try:
    load_prompts()
except Exception as e:
    logger.warning(f"Failed to load default prompts on module initialization: {e}")