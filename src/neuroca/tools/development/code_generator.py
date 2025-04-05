"""
Code Generator for NeuroCognitive Architecture (NCA)

This module provides a flexible code generation system for the NeuroCognitive Architecture
project. It supports generating boilerplate code, templates, and scaffolding for various
components of the NCA system based on predefined templates and configurations.

The generator supports:
- Component generation (memory systems, cognitive modules, etc.)
- Test scaffolding
- API endpoint generation
- Database model generation
- Configuration file generation

Usage:
    from neuroca.tools.development.code_generator import CodeGenerator
    
    # Generate a new memory component
    generator = CodeGenerator()
    generator.generate_component(
        component_type="memory",
        component_name="episodic_buffer",
        output_dir="neuroca/memory/episodic"
    )

    # Generate from custom template
    generator.generate_from_template(
        template_path="templates/custom.py.jinja",
        output_path="neuroca/custom_module.py",
        context={"class_name": "CustomProcessor"}
    )
"""

import argparse
import datetime
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any, Optional, Union

import jinja2
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TemplateError(Exception):
    """Exception raised for errors in the template processing."""
    pass


class OutputError(Exception):
    """Exception raised for errors in writing output files."""
    pass


class ValidationError(Exception):
    """Exception raised for validation errors in input parameters."""
    pass


class CodeGenerator:
    """
    Main code generator class that handles template rendering and file generation
    for the NeuroCognitive Architecture project.
    """
    
    # Standard component types supported by the generator
    COMPONENT_TYPES = [
        "memory", "cognitive", "api", "model", "test", "config", 
        "integration", "monitoring", "infrastructure"
    ]
    
    # Template directory relative to this file
    DEFAULT_TEMPLATE_DIR = "../../../templates"
    
    def __init__(self, template_dir: Optional[str] = None, 
                 config_file: Optional[str] = None):
        """
        Initialize the code generator with template directory and optional config.
        
        Args:
            template_dir: Directory containing template files. If None, uses default.
            config_file: Path to configuration file for the generator. If None, uses default.
        
        Raises:
            FileNotFoundError: If template directory doesn't exist
            json.JSONDecodeError: If config file exists but is invalid JSON
        """
        # Resolve template directory path
        if template_dir is None:
            # Use the default template directory relative to this file
            current_dir = Path(__file__).parent.absolute()
            self.template_dir = (current_dir / self.DEFAULT_TEMPLATE_DIR).resolve()
        else:
            self.template_dir = Path(template_dir).resolve()
        
        # Ensure template directory exists
        if not self.template_dir.exists():
            logger.error(f"Template directory not found: {self.template_dir}")
            raise FileNotFoundError(f"Template directory not found: {self.template_dir}")
        
        logger.debug(f"Using template directory: {self.template_dir}")
        
        # Initialize Jinja environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True
        )
        
        # Add custom filters
        self.env.filters['camelcase'] = self._to_camel_case
        self.env.filters['snakecase'] = self._to_snake_case
        self.env.filters['pascalcase'] = self._to_pascal_case
        
        # Load configuration if provided
        self.config = {}
        if config_file:
            config_path = Path(config_file).resolve()
            if config_path.exists():
                try:
                    with open(config_path) as f:
                        self.config = json.load(f)
                    logger.debug(f"Loaded configuration from {config_path}")
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON in config file: {config_path}")
                    raise
            else:
                logger.warning(f"Config file not found: {config_path}")
    
    def generate_component(self, component_type: str, component_name: str, 
                          output_dir: str, options: Optional[dict[str, Any]] = None) -> list[str]:
        """
        Generate code for a specific component type.
        
        Args:
            component_type: Type of component to generate (memory, cognitive, etc.)
            component_name: Name of the component
            output_dir: Directory where generated files will be saved
            options: Additional options for generation
            
        Returns:
            List of paths to generated files
            
        Raises:
            ValidationError: If component type is invalid or required parameters are missing
            TemplateError: If template rendering fails
            OutputError: If writing output files fails
        """
        # Validate component type
        if component_type not in self.COMPONENT_TYPES:
            valid_types = ", ".join(self.COMPONENT_TYPES)
            logger.error(f"Invalid component type: {component_type}. Valid types: {valid_types}")
            raise ValidationError(f"Invalid component type: {component_type}. Valid types: {valid_types}")
        
        # Validate component name
        if not component_name or not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', component_name):
            logger.error(f"Invalid component name: {component_name}")
            raise ValidationError(f"Invalid component name: {component_name}. Must start with a letter and contain only letters, numbers, and underscores.")
        
        # Prepare context for templates
        context = {
            'component_name': component_name,
            'component_type': component_type,
            'date_created': datetime.datetime.now().strftime("%Y-%m-%d"),
            'year': datetime.datetime.now().year,
            'options': options or {},
        }
        
        # Get templates for this component type
        component_template_dir = self.template_dir / component_type
        if not component_template_dir.exists():
            logger.error(f"No templates found for component type: {component_type}")
            raise TemplateError(f"No templates found for component type: {component_type}")
        
        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        generated_files = []
        
        # Find all template files for this component type
        template_files = list(component_template_dir.glob('*.j2')) + list(component_template_dir.glob('*.jinja'))
        
        if not template_files:
            logger.warning(f"No template files found in {component_template_dir}")
            return generated_files
        
        # Process each template
        for template_file in template_files:
            try:
                # Get relative path from template dir to use as template name
                template_name = str(template_file.relative_to(self.template_dir))
                
                # Determine output filename (replace placeholders)
                output_filename = self._get_output_filename(template_file.name, component_name)
                output_file_path = output_path / output_filename
                
                # Render template
                rendered_content = self._render_template(template_name, context)
                
                # Write output file
                with open(output_file_path, 'w') as f:
                    f.write(rendered_content)
                
                logger.info(f"Generated file: {output_file_path}")
                generated_files.append(str(output_file_path))
                
            except (jinja2.exceptions.TemplateError, OSError) as e:
                logger.error(f"Error generating file from template {template_file}: {str(e)}")
                raise TemplateError(f"Error generating file from template {template_file}: {str(e)}")
        
        return generated_files
    
    def generate_from_template(self, template_path: str, output_path: str, 
                              context: dict[str, Any]) -> str:
        """
        Generate a file from a specific template with custom context.
        
        Args:
            template_path: Path to the template file (relative to template_dir)
            output_path: Path where the generated file will be saved
            context: Dictionary of variables to use in the template
            
        Returns:
            Path to the generated file
            
        Raises:
            TemplateError: If template rendering fails
            OutputError: If writing output file fails
        """
        try:
            # Ensure template exists
            full_template_path = self.template_dir / template_path
            if not full_template_path.exists():
                logger.error(f"Template not found: {full_template_path}")
                raise TemplateError(f"Template not found: {full_template_path}")
            
            # Get template name relative to template dir
            template_name = str(Path(template_path))
            
            # Add standard context variables if not provided
            if 'date_created' not in context:
                context['date_created'] = datetime.datetime.now().strftime("%Y-%m-%d")
            if 'year' not in context:
                context['year'] = datetime.datetime.now().year
            
            # Render template
            rendered_content = self._render_template(template_name, context)
            
            # Create output directory if it doesn't exist
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write output file
            with open(output_file, 'w') as f:
                f.write(rendered_content)
            
            logger.info(f"Generated file: {output_file}")
            return str(output_file)
            
        except jinja2.exceptions.TemplateError as e:
            logger.error(f"Template error: {str(e)}")
            raise TemplateError(f"Error rendering template {template_path}: {str(e)}")
        except OSError as e:
            logger.error(f"Output error: {str(e)}")
            raise OutputError(f"Error writing to {output_path}: {str(e)}")
    
    def generate_project_structure(self, base_dir: str, 
                                  structure_config: Optional[Union[dict, str]] = None) -> list[str]:
        """
        Generate a project structure based on a configuration.
        
        Args:
            base_dir: Base directory where the structure will be created
            structure_config: Dictionary or path to JSON file defining the structure
            
        Returns:
            List of created directories and files
            
        Raises:
            ValidationError: If structure_config is invalid
            OutputError: If creating directories or files fails
        """
        # Load structure configuration
        if structure_config is None:
            # Use default structure from config
            if 'default_structure' not in self.config:
                logger.error("No default structure found in configuration")
                raise ValidationError("No default structure provided and no default found in configuration")
            structure = self.config['default_structure']
        elif isinstance(structure_config, str):
            # Load from file
            try:
                with open(structure_config) as f:
                    structure = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.error(f"Error loading structure config from {structure_config}: {str(e)}")
                raise ValidationError(f"Error loading structure config: {str(e)}")
        else:
            # Use provided dictionary
            structure = structure_config
        
        # Validate structure
        if not isinstance(structure, dict):
            logger.error(f"Invalid structure configuration: {structure}")
            raise ValidationError("Structure configuration must be a dictionary")
        
        # Create base directory
        base_path = Path(base_dir)
        base_path.mkdir(parents=True, exist_ok=True)
        
        created_items = [str(base_path)]
        
        # Process structure recursively
        try:
            self._create_structure(base_path, structure, created_items)
            logger.info(f"Project structure created in {base_path}")
            return created_items
        except OSError as e:
            logger.error(f"Error creating project structure: {str(e)}")
            raise OutputError(f"Error creating project structure: {str(e)}")
    
    def _create_structure(self, parent_dir: Path, structure: dict, created_items: list[str]) -> None:
        """
        Recursively create directories and files based on structure definition.
        
        Args:
            parent_dir: Parent directory where items will be created
            structure: Dictionary defining the structure
            created_items: List to track created items
            
        Raises:
            OSError: If creating directories or files fails
        """
        for name, content in structure.items():
            path = parent_dir / name
            
            if isinstance(content, dict):
                # It's a directory with contents
                path.mkdir(exist_ok=True)
                created_items.append(str(path))
                self._create_structure(path, content, created_items)
            elif isinstance(content, str):
                # It's a file with content or template reference
                if content.startswith('template:'):
                    # It's a template reference
                    template_path = content[9:].strip()
                    try:
                        context = {
                            'filename': name,
                            'path': str(path),
                            'date_created': datetime.datetime.now().strftime("%Y-%m-%d"),
                            'year': datetime.datetime.now().year,
                        }
                        self.generate_from_template(template_path, str(path), context)
                    except (TemplateError, OutputError) as e:
                        logger.warning(f"Error generating {path} from template: {str(e)}")
                        # Create empty file instead
                        path.touch()
                else:
                    # It's a file with content
                    with open(path, 'w') as f:
                        f.write(content)
                created_items.append(str(path))
            elif content is None:
                # It's an empty directory
                path.mkdir(exist_ok=True)
                created_items.append(str(path))
            else:
                logger.warning(f"Unsupported structure item: {name}: {content}")
    
    def _render_template(self, template_name: str, context: dict[str, Any]) -> str:
        """
        Render a template with the given context.
        
        Args:
            template_name: Name of the template to render
            context: Dictionary of variables to use in the template
            
        Returns:
            Rendered template content
            
        Raises:
            jinja2.exceptions.TemplateError: If template rendering fails
        """
        template = self.env.get_template(template_name)
        return template.render(**context)
    
    def _get_output_filename(self, template_filename: str, component_name: str) -> str:
        """
        Determine the output filename based on template filename and component name.
        
        Args:
            template_filename: Name of the template file
            component_name: Name of the component
            
        Returns:
            Output filename with placeholders replaced
        """
        # Remove template extension (.j2 or .jinja)
        output_name = re.sub(r'\.(j2|jinja)$', '', template_filename)
        
        # Replace placeholders
        output_name = output_name.replace('COMPONENT', component_name)
        output_name = output_name.replace('Component', self._to_pascal_case(component_name))
        output_name = output_name.replace('component', self._to_snake_case(component_name))
        
        return output_name
    
    @staticmethod
    def _to_snake_case(text: str) -> str:
        """Convert text to snake_case."""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    @staticmethod
    def _to_camel_case(text: str) -> str:
        """Convert text to camelCase."""
        s = re.sub(r'(_|-)+', ' ', text).title().replace(' ', '')
        return s[0].lower() + s[1:] if s else ''
    
    @staticmethod
    def _to_pascal_case(text: str) -> str:
        """Convert text to PascalCase."""
        return ''.join(word.capitalize() for word in re.sub(r'(_|-)+', ' ', text).split())


def parse_args() -> argparse.Namespace:
    """Parse command line arguments for the code generator CLI."""
    parser = argparse.ArgumentParser(
        description='NeuroCognitive Architecture Code Generator',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Component generator
    component_parser = subparsers.add_parser('component', help='Generate a component')
    component_parser.add_argument('--type', '-t', required=True, 
                                 choices=CodeGenerator.COMPONENT_TYPES,
                                 help='Type of component to generate')
    component_parser.add_argument('--name', '-n', required=True,
                                 help='Name of the component')
    component_parser.add_argument('--output', '-o', required=True,
                                 help='Output directory')
    component_parser.add_argument('--options', type=json.loads, default={},
                                 help='Additional options as JSON string')
    
    # Template generator
    template_parser = subparsers.add_parser('template', help='Generate from a specific template')
    template_parser.add_argument('--template', '-t', required=True,
                               help='Path to template file (relative to template directory)')
    template_parser.add_argument('--output', '-o', required=True,
                               help='Output file path')
    template_parser.add_argument('--context', '-c', type=json.loads, required=True,
                               help='Context variables as JSON string')
    
    # Structure generator
    structure_parser = subparsers.add_parser('structure', help='Generate project structure')
    structure_parser.add_argument('--base-dir', '-b', required=True,
                                help='Base directory for the structure')
    structure_parser.add_argument('--config', '-c',
                                help='Path to structure configuration file')
    
    # Common options
    for subparser in [component_parser, template_parser, structure_parser]:
        subparser.add_argument('--template-dir', 
                             help='Directory containing templates')
        subparser.add_argument('--config-file',
                             help='Path to generator configuration file')
        subparser.add_argument('--verbose', '-v', action='store_true',
                             help='Enable verbose logging')
    
    return parser.parse_args()


def main() -> int:
    """
    Main entry point for the code generator CLI.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    args = parse_args()
    
    # Set up logging based on verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize generator
        generator = CodeGenerator(
            template_dir=args.template_dir,
            config_file=args.config_file
        )
        
        # Execute requested command
        if args.command == 'component':
            generated_files = generator.generate_component(
                component_type=args.type,
                component_name=args.name,
                output_dir=args.output,
                options=args.options
            )
            print(f"Generated {len(generated_files)} files:")
            for file in generated_files:
                print(f"  - {file}")
                
        elif args.command == 'template':
            output_file = generator.generate_from_template(
                template_path=args.template,
                output_path=args.output,
                context=args.context
            )
            print(f"Generated file: {output_file}")
            
        elif args.command == 'structure':
            created_items = generator.generate_project_structure(
                base_dir=args.base_dir,
                structure_config=args.config
            )
            print(f"Created {len(created_items)} directories and files")
            
        else:
            print("No command specified. Use --help for usage information.")
            return 1
            
        return 0
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        if args.verbose:
            logger.exception("Detailed error information:")
        return 1


if __name__ == "__main__":
    sys.exit(main())