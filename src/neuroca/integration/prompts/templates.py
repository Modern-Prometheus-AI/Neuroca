"""
Prompt Templates Module for NeuroCognitive Architecture (NCA)

This module provides a robust system for managing, validating, and rendering prompt templates
for Large Language Model interactions. It includes:

1. A TemplateManager for loading, validating and managing prompt templates
2. Template validation functionality to ensure templates meet requirements
3. Template rendering with variable substitution and context management
4. Support for different template formats and versioning
5. Error handling and logging for template operations

Usage:
    template_manager = TemplateManager()
    template_manager.load_templates_from_directory("path/to/templates")
    rendered_prompt = template_manager.render_template(
        "template_name", 
        variables={"var1": "value1"}
    )
"""

import json
import logging
import re
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Any, Optional

import yaml
from jinja2 import Environment, FileSystemLoader, Template, select_autoescape
from jinja2.exceptions import TemplateError, TemplateSyntaxError

# Configure module logger
logger = logging.getLogger(__name__)


class TemplateFormatError(Exception):
    """Exception raised for errors in template format or validation."""
    pass


class TemplateRenderError(Exception):
    """Exception raised for errors during template rendering."""
    pass


class TemplateNotFoundError(Exception):
    """Exception raised when a requested template cannot be found."""
    pass


class TemplateFormat(Enum):
    """Supported template file formats."""
    JSON = auto()
    YAML = auto()
    TXT = auto()
    JINJA = auto()


@dataclass
class TemplateMetadata:
    """Metadata for a prompt template."""
    name: str
    description: str
    version: str
    author: Optional[str] = None
    tags: list[str] = None
    required_variables: set[str] = None
    optional_variables: set[str] = None
    
    def __post_init__(self):
        """Initialize default values for optional fields."""
        if self.tags is None:
            self.tags = []
        if self.required_variables is None:
            self.required_variables = set()
        if self.optional_variables is None:
            self.optional_variables = set()


@dataclass
class PromptTemplate:
    """
    Represents a complete prompt template with content and metadata.
    
    Attributes:
        template_id: Unique identifier for the template
        content: The template content with variable placeholders
        metadata: Template metadata including version, author, etc.
        format: The format of the template (JSON, YAML, TXT, JINJA)
        compiled_template: The compiled Jinja template object (if applicable)
    """
    template_id: str
    content: str
    metadata: TemplateMetadata
    format: TemplateFormat
    compiled_template: Optional[Template] = None
    
    def extract_variables(self) -> set[str]:
        """
        Extract all variables from the template content.
        
        Returns:
            Set of variable names found in the template
        """
        # Match {{variable}} and {variable} patterns
        jinja_vars = set(re.findall(r'{{\s*(\w+)\s*}}', self.content))
        simple_vars = set(re.findall(r'{(\w+)}', self.content))
        return jinja_vars.union(simple_vars)


class TemplateManager:
    """
    Manages prompt templates for the NeuroCognitive Architecture.
    
    This class handles loading, validating, and rendering prompt templates
    for LLM interactions. It supports multiple template formats and provides
    robust error handling and validation.
    """
    
    def __init__(self, template_dirs: Optional[list[str]] = None):
        """
        Initialize the TemplateManager.
        
        Args:
            template_dirs: Optional list of directories to load templates from
        """
        self.templates: dict[str, PromptTemplate] = {}
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dirs or []),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters to Jinja environment
        self.jinja_env.filters['trim'] = lambda x: x.strip() if x else x
        
        if template_dirs:
            for directory in template_dirs:
                self.load_templates_from_directory(directory)
        
        logger.info(f"TemplateManager initialized with {len(self.templates)} templates")
    
    def load_templates_from_directory(self, directory: str) -> int:
        """
        Load all templates from a directory.
        
        Args:
            directory: Path to directory containing template files
            
        Returns:
            Number of templates successfully loaded
            
        Raises:
            FileNotFoundError: If the directory does not exist
            TemplateFormatError: If a template file has invalid format
        """
        directory_path = Path(directory)
        if not directory_path.exists() or not directory_path.is_dir():
            error_msg = f"Template directory not found: {directory}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        # Update Jinja loader to include this directory
        self.jinja_env.loader.searchpath.append(str(directory_path))
        
        count = 0
        for file_path in directory_path.glob("**/*.*"):
            try:
                if self._is_template_file(file_path):
                    template = self._load_template_from_file(file_path)
                    self.add_template(template)
                    count += 1
            except (TemplateFormatError, json.JSONDecodeError, yaml.YAMLError) as e:
                logger.warning(f"Failed to load template {file_path}: {str(e)}")
                continue
        
        logger.info(f"Loaded {count} templates from {directory}")
        return count
    
    def _is_template_file(self, file_path: Path) -> bool:
        """
        Check if a file is a valid template file based on extension.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if the file is a valid template file, False otherwise
        """
        valid_extensions = {'.json', '.yaml', '.yml', '.txt', '.j2', '.jinja', '.template'}
        return file_path.is_file() and file_path.suffix.lower() in valid_extensions
    
    def _load_template_from_file(self, file_path: Path) -> PromptTemplate:
        """
        Load a template from a file.
        
        Args:
            file_path: Path to the template file
            
        Returns:
            PromptTemplate object
            
        Raises:
            TemplateFormatError: If the template file has invalid format
        """
        template_id = file_path.stem
        file_extension = file_path.suffix.lower()
        
        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()
            
            if file_extension in {'.json'}:
                return self._parse_json_template(template_id, content)
            elif file_extension in {'.yaml', '.yml'}:
                return self._parse_yaml_template(template_id, content)
            elif file_extension in {'.j2', '.jinja', '.template'}:
                return self._parse_jinja_template(template_id, content)
            else:  # .txt or other
                return self._parse_text_template(template_id, content)
                
        except Exception as e:
            error_msg = f"Error loading template from {file_path}: {str(e)}"
            logger.error(error_msg)
            raise TemplateFormatError(error_msg) from e
    
    def _parse_json_template(self, template_id: str, content: str) -> PromptTemplate:
        """Parse a JSON template file."""
        data = json.loads(content)
        
        # Extract template content and metadata
        template_content = data.get('content', '')
        if not template_content:
            raise TemplateFormatError(f"JSON template {template_id} missing 'content' field")
        
        metadata = self._extract_metadata(template_id, data)
        
        # Compile the template
        compiled_template = self.jinja_env.from_string(template_content)
        
        return PromptTemplate(
            template_id=template_id,
            content=template_content,
            metadata=metadata,
            format=TemplateFormat.JSON,
            compiled_template=compiled_template
        )
    
    def _parse_yaml_template(self, template_id: str, content: str) -> PromptTemplate:
        """Parse a YAML template file."""
        data = yaml.safe_load(content)
        
        # Extract template content and metadata
        template_content = data.get('content', '')
        if not template_content:
            raise TemplateFormatError(f"YAML template {template_id} missing 'content' field")
        
        metadata = self._extract_metadata(template_id, data)
        
        # Compile the template
        compiled_template = self.jinja_env.from_string(template_content)
        
        return PromptTemplate(
            template_id=template_id,
            content=template_content,
            metadata=metadata,
            format=TemplateFormat.YAML,
            compiled_template=compiled_template
        )
    
    def _parse_jinja_template(self, template_id: str, content: str) -> PromptTemplate:
        """Parse a Jinja template file."""
        # Extract metadata from comments if available
        metadata_match = re.search(r'{#\s*METADATA\s*(.*?)\s*#}', content, re.DOTALL)
        
        metadata = None
        if metadata_match:
            try:
                metadata_str = metadata_match.group(1)
                metadata_dict = yaml.safe_load(metadata_str)
                metadata = self._extract_metadata(template_id, metadata_dict)
            except Exception as e:
                logger.warning(f"Failed to parse metadata in template {template_id}: {str(e)}")
        
        if not metadata:
            # Create default metadata
            metadata = TemplateMetadata(
                name=template_id,
                description=f"Template {template_id}",
                version="1.0.0"
            )
        
        # Compile the template
        try:
            compiled_template = self.jinja_env.from_string(content)
            
            # Extract variables
            variables = set(re.findall(r'{{\s*(\w+)\s*}}', content))
            metadata.required_variables = variables
            
            return PromptTemplate(
                template_id=template_id,
                content=content,
                metadata=metadata,
                format=TemplateFormat.JINJA,
                compiled_template=compiled_template
            )
        except TemplateSyntaxError as e:
            raise TemplateFormatError(f"Syntax error in Jinja template {template_id}: {str(e)}")
    
    def _parse_text_template(self, template_id: str, content: str) -> PromptTemplate:
        """Parse a plain text template file."""
        # Create default metadata
        metadata = TemplateMetadata(
            name=template_id,
            description=f"Template {template_id}",
            version="1.0.0"
        )
        
        # Check for simple variable placeholders like {variable}
        simple_vars = set(re.findall(r'{(\w+)}', content))
        if simple_vars:
            metadata.required_variables = simple_vars
            
            # Convert simple {var} format to Jinja {{var}} format for consistency
            jinja_content = re.sub(r'{(\w+)}', r'{{\1}}', content)
            compiled_template = self.jinja_env.from_string(jinja_content)
            
            return PromptTemplate(
                template_id=template_id,
                content=content,  # Keep original content for reference
                metadata=metadata,
                format=TemplateFormat.TXT,
                compiled_template=compiled_template
            )
        else:
            # No variables, treat as static text
            compiled_template = self.jinja_env.from_string(content)
            
            return PromptTemplate(
                template_id=template_id,
                content=content,
                metadata=metadata,
                format=TemplateFormat.TXT,
                compiled_template=compiled_template
            )
    
    def _extract_metadata(self, template_id: str, data: dict[str, Any]) -> TemplateMetadata:
        """
        Extract metadata from template data.
        
        Args:
            template_id: Template identifier
            data: Dictionary containing template data
            
        Returns:
            TemplateMetadata object
        """
        metadata = data.get('metadata', {})
        
        # Extract required variables if specified
        required_vars = set(metadata.get('required_variables', []))
        
        # Extract optional variables if specified
        optional_vars = set(metadata.get('optional_variables', []))
        
        return TemplateMetadata(
            name=metadata.get('name', template_id),
            description=metadata.get('description', f"Template {template_id}"),
            version=metadata.get('version', '1.0.0'),
            author=metadata.get('author'),
            tags=metadata.get('tags', []),
            required_variables=required_vars,
            optional_variables=optional_vars
        )
    
    def add_template(self, template: PromptTemplate) -> None:
        """
        Add a template to the manager.
        
        Args:
            template: PromptTemplate object to add
            
        Raises:
            ValueError: If a template with the same ID already exists
        """
        if template.template_id in self.templates:
            error_msg = f"Template with ID '{template.template_id}' already exists"
            logger.warning(error_msg)
            raise ValueError(error_msg)
        
        self.templates[template.template_id] = template
        logger.debug(f"Added template '{template.template_id}'")
    
    def get_template(self, template_id: str) -> PromptTemplate:
        """
        Get a template by ID.
        
        Args:
            template_id: ID of the template to retrieve
            
        Returns:
            PromptTemplate object
            
        Raises:
            TemplateNotFoundError: If the template is not found
        """
        if template_id not in self.templates:
            error_msg = f"Template '{template_id}' not found"
            logger.error(error_msg)
            raise TemplateNotFoundError(error_msg)
        
        return self.templates[template_id]
    
    def render_template(self, template_id: str, variables: dict[str, Any] = None) -> str:
        """
        Render a template with the provided variables.
        
        Args:
            template_id: ID of the template to render
            variables: Dictionary of variables to use in rendering
            
        Returns:
            Rendered template string
            
        Raises:
            TemplateNotFoundError: If the template is not found
            TemplateRenderError: If there's an error during rendering
            ValueError: If required variables are missing
        """
        variables = variables or {}
        
        try:
            template = self.get_template(template_id)
            
            # Validate variables
            self._validate_template_variables(template, variables)
            
            # Render the template
            if template.compiled_template:
                rendered = template.compiled_template.render(**variables)
            else:
                # Fallback for templates without compiled version
                jinja_template = self.jinja_env.from_string(template.content)
                rendered = jinja_template.render(**variables)
            
            logger.debug(f"Successfully rendered template '{template_id}'")
            return rendered
            
        except TemplateNotFoundError:
            raise
        except TemplateError as e:
            error_msg = f"Error rendering template '{template_id}': {str(e)}"
            logger.error(error_msg)
            raise TemplateRenderError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error rendering template '{template_id}': {str(e)}"
            logger.error(error_msg)
            raise TemplateRenderError(error_msg) from e
    
    def _validate_template_variables(self, template: PromptTemplate, variables: dict[str, Any]) -> None:
        """
        Validate that all required variables are provided.
        
        Args:
            template: Template to validate variables for
            variables: Dictionary of provided variables
            
        Raises:
            ValueError: If required variables are missing
        """
        missing_vars = template.metadata.required_variables - set(variables.keys())
        if missing_vars:
            error_msg = f"Missing required variables for template '{template.template_id}': {', '.join(missing_vars)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def create_template_from_string(self, template_id: str, content: str, 
                                   metadata: Optional[dict[str, Any]] = None) -> PromptTemplate:
        """
        Create a new template from a string.
        
        Args:
            template_id: ID for the new template
            content: Template content
            metadata: Optional metadata dictionary
            
        Returns:
            Created PromptTemplate object
            
        Raises:
            TemplateFormatError: If there's an error creating the template
        """
        try:
            metadata_obj = self._extract_metadata(template_id, {'metadata': metadata or {}})
            
            # Compile the template
            compiled_template = self.jinja_env.from_string(content)
            
            # Extract variables
            variables = set(re.findall(r'{{\s*(\w+)\s*}}', content))
            metadata_obj.required_variables = variables
            
            template = PromptTemplate(
                template_id=template_id,
                content=content,
                metadata=metadata_obj,
                format=TemplateFormat.JINJA,
                compiled_template=compiled_template
            )
            
            # Add to manager
            self.add_template(template)
            
            return template
            
        except Exception as e:
            error_msg = f"Error creating template '{template_id}': {str(e)}"
            logger.error(error_msg)
            raise TemplateFormatError(error_msg) from e
    
    def list_templates(self) -> list[str]:
        """
        Get a list of all template IDs.
        
        Returns:
            List of template IDs
        """
        return list(self.templates.keys())
    
    def get_templates_by_tag(self, tag: str) -> list[PromptTemplate]:
        """
        Get all templates with a specific tag.
        
        Args:
            tag: Tag to filter by
            
        Returns:
            List of matching PromptTemplate objects
        """
        return [t for t in self.templates.values() if tag in t.metadata.tags]
    
    def remove_template(self, template_id: str) -> bool:
        """
        Remove a template from the manager.
        
        Args:
            template_id: ID of the template to remove
            
        Returns:
            True if the template was removed, False if it wasn't found
        """
        if template_id in self.templates:
            del self.templates[template_id]
            logger.debug(f"Removed template '{template_id}'")
            return True
        return False


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create a template manager
    manager = TemplateManager()
    
    # Create a template from string
    manager.create_template_from_string(
        "greeting",
        "Hello, {{name}}! Welcome to {{system_name}}.",
        {"description": "Basic greeting template", "version": "1.0.0"}
    )
    
    # Render the template
    result = manager.render_template("greeting", {"name": "User", "system_name": "NeuroCognitive Architecture"})
    print(result)