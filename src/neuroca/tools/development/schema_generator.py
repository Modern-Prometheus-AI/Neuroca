#!/usr/bin/env python3
"""
Schema Generator for NeuroCognitive Architecture (NCA)

This module provides utilities for automatically generating schema definitions
from Python classes, database models, or other structured data sources. It supports
generating schemas in multiple formats (JSON Schema, Pydantic models, Protocol Buffers, etc.)
and can be used both programmatically and via CLI.

The generator helps maintain consistency between data models across different
parts of the system, reducing manual schema maintenance and potential errors.

Usage examples:
    # Generate JSON schema from a Pydantic model
    python -m neuroca.tools.development.schema_generator --source-type pydantic 
        --source-path neuroca.core.models.memory --output-format json 
        --output-dir ./schemas/json

    # Generate Protocol Buffer definitions from SQLAlchemy models
    python -m neuroca.tools.development.schema_generator --source-type sqlalchemy 
        --source-path neuroca.db.models --output-format protobuf 
        --output-dir ./schemas/proto

    # Programmatic usage
    from neuroca.tools.development.schema_generator import SchemaGenerator
    generator = SchemaGenerator()
    schema = generator.generate_from_pydantic(MyModel, output_format="json")
"""

import argparse
import importlib
import inspect
import json
import logging
import os
import sys
from abc import ABC, abstractmethod
from dataclasses import is_dataclass
from enum import Enum
from typing import Any, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class SchemaFormat(str, Enum):
    """Supported schema output formats."""
    JSON = "json"
    YAML = "yaml"
    PROTOBUF = "protobuf"
    AVRO = "avro"
    GRAPHQL = "graphql"
    PYDANTIC = "pydantic"
    TYPESCRIPT = "typescript"


class SourceType(str, Enum):
    """Supported source types for schema generation."""
    PYDANTIC = "pydantic"
    DATACLASS = "dataclass"
    SQLALCHEMY = "sqlalchemy"
    DICT = "dict"
    CLASS = "class"
    JSON = "json"


class SchemaGenerationError(Exception):
    """Base exception for schema generation errors."""
    pass


class InvalidSourceError(SchemaGenerationError):
    """Exception raised when the source is invalid or cannot be processed."""
    pass


class UnsupportedFormatError(SchemaGenerationError):
    """Exception raised when the requested output format is not supported."""
    pass


class SchemaFormatter(ABC):
    """Base class for schema formatters."""
    
    @abstractmethod
    def format(self, schema_data: dict[str, Any]) -> str:
        """Format the schema data into the target format."""
        pass
    
    @abstractmethod
    def get_file_extension(self) -> str:
        """Get the file extension for this format."""
        pass


class JsonSchemaFormatter(SchemaFormatter):
    """Formatter for JSON Schema format."""
    
    def format(self, schema_data: dict[str, Any]) -> str:
        """Format the schema data as JSON."""
        try:
            return json.dumps(schema_data, indent=2)
        except Exception as e:
            logger.error(f"Failed to format JSON schema: {e}")
            raise SchemaGenerationError(f"JSON formatting error: {e}")
    
    def get_file_extension(self) -> str:
        """Get the file extension for JSON files."""
        return ".json"


class YamlSchemaFormatter(SchemaFormatter):
    """Formatter for YAML Schema format."""
    
    def format(self, schema_data: dict[str, Any]) -> str:
        """Format the schema data as YAML."""
        try:
            import yaml
            return yaml.dump(schema_data, default_flow_style=False)
        except ImportError:
            logger.error("PyYAML package is required for YAML formatting")
            raise SchemaGenerationError("PyYAML package is required for YAML formatting")
        except Exception as e:
            logger.error(f"Failed to format YAML schema: {e}")
            raise SchemaGenerationError(f"YAML formatting error: {e}")
    
    def get_file_extension(self) -> str:
        """Get the file extension for YAML files."""
        return ".yaml"


class ProtobufSchemaFormatter(SchemaFormatter):
    """Formatter for Protocol Buffer format."""
    
    def format(self, schema_data: dict[str, Any]) -> str:
        """Format the schema data as Protocol Buffer definition."""
        try:
            # This is a simplified implementation
            # A real implementation would need to properly convert the schema to protobuf syntax
            output = []
            output.append('syntax = "proto3";\n')
            output.append(f'package {schema_data.get("package", "neuroca")};\n\n')
            
            # Process messages
            for message_name, properties in schema_data.get("messages", {}).items():
                output.append(f"message {message_name} {{\n")
                
                for i, (prop_name, prop_details) in enumerate(properties.items()):
                    prop_type = prop_details.get("type", "string")
                    # Convert JSON schema types to protobuf types
                    type_mapping = {
                        "string": "string",
                        "integer": "int32",
                        "number": "float",
                        "boolean": "bool",
                        "object": "map<string, string>",  # Simplified
                        "array": "repeated string",  # Simplified
                    }
                    pb_type = type_mapping.get(prop_type, "string")
                    output.append(f"  {pb_type} {prop_name} = {i+1};\n")
                
                output.append("}\n\n")
            
            return "".join(output)
        except Exception as e:
            logger.error(f"Failed to format Protobuf schema: {e}")
            raise SchemaGenerationError(f"Protobuf formatting error: {e}")
    
    def get_file_extension(self) -> str:
        """Get the file extension for Protocol Buffer files."""
        return ".proto"


class SchemaGenerator:
    """
    Main schema generator class that orchestrates the schema generation process.
    
    This class provides methods to generate schemas from various source types
    and output them in different formats.
    """
    
    def __init__(self):
        """Initialize the schema generator with supported formatters."""
        self.formatters = {
            SchemaFormat.JSON: JsonSchemaFormatter(),
            SchemaFormat.YAML: YamlSchemaFormatter(),
            SchemaFormat.PROTOBUF: ProtobufSchemaFormatter(),
            # Other formatters would be initialized here
        }
        
        # Register source handlers
        self.source_handlers = {
            SourceType.PYDANTIC: self._handle_pydantic,
            SourceType.DATACLASS: self._handle_dataclass,
            SourceType.SQLALCHEMY: self._handle_sqlalchemy,
            SourceType.DICT: self._handle_dict,
            SourceType.CLASS: self._handle_class,
            SourceType.JSON: self._handle_json,
        }
    
    def generate(
        self,
        source: Any,
        source_type: SourceType,
        output_format: SchemaFormat,
        output_path: Optional[str] = None,
        namespace: Optional[str] = None,
    ) -> Union[str, dict[str, Any]]:
        """
        Generate a schema from the given source.
        
        Args:
            source: The source to generate the schema from
            source_type: The type of the source
            output_format: The desired output format
            output_path: Optional path to write the schema to
            namespace: Optional namespace for the schema
            
        Returns:
            The generated schema as a string or dict, depending on whether output_path is provided
            
        Raises:
            InvalidSourceError: If the source is invalid or cannot be processed
            UnsupportedFormatError: If the requested output format is not supported
            SchemaGenerationError: For other schema generation errors
        """
        logger.info(f"Generating {output_format} schema from {source_type} source")
        
        try:
            # Validate inputs
            if source_type not in SourceType:
                raise InvalidSourceError(f"Unsupported source type: {source_type}")
            
            if output_format not in SchemaFormat:
                raise UnsupportedFormatError(f"Unsupported output format: {output_format}")
            
            # Get the appropriate handler for the source type
            handler = self.source_handlers.get(source_type)
            if not handler:
                raise InvalidSourceError(f"No handler available for source type: {source_type}")
            
            # Generate the schema data
            schema_data = handler(source, namespace)
            
            # Format the schema
            formatter = self.formatters.get(output_format)
            if not formatter:
                raise UnsupportedFormatError(f"No formatter available for format: {output_format}")
            
            formatted_schema = formatter.format(schema_data)
            
            # Write to file if output path is provided
            if output_path:
                self._write_schema(formatted_schema, output_path, formatter.get_file_extension())
                return schema_data  # Return the data dict when writing to file
            
            return formatted_schema  # Return the formatted string otherwise
            
        except Exception as e:
            if not isinstance(e, SchemaGenerationError):
                logger.error(f"Unexpected error during schema generation: {e}", exc_info=True)
                raise SchemaGenerationError(f"Schema generation failed: {e}")
            raise
    
    def _write_schema(self, schema: str, output_path: str, extension: str) -> None:
        """
        Write the schema to a file.
        
        Args:
            schema: The formatted schema string
            output_path: The path to write to
            extension: The file extension to use
            
        Raises:
            SchemaGenerationError: If writing to the file fails
        """
        try:
            # Create directory if it doesn't exist
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            # If output_path is a directory, generate a filename
            if os.path.isdir(output_path):
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"schema_{timestamp}{extension}"
                output_path = os.path.join(output_path, filename)
            elif not output_path.endswith(extension):
                output_path += extension
            
            # Write the schema to the file
            with open(output_path, 'w') as f:
                f.write(schema)
            
            logger.info(f"Schema written to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to write schema to {output_path}: {e}")
            raise SchemaGenerationError(f"Failed to write schema: {e}")
    
    def _handle_pydantic(self, source: Any, namespace: Optional[str] = None) -> dict[str, Any]:
        """
        Generate schema data from a Pydantic model.
        
        Args:
            source: A Pydantic model class or module containing Pydantic models
            namespace: Optional namespace for the schema
            
        Returns:
            Dict containing the schema data
            
        Raises:
            InvalidSourceError: If the source is not a valid Pydantic model or module
        """
        try:
            # Try to import pydantic
            try:
                import pydantic
                from pydantic import BaseModel
            except ImportError:
                logger.error("Pydantic package is required for Pydantic schema generation")
                raise SchemaGenerationError("Pydantic package is required for Pydantic schema generation")
            
            # If source is a string, try to import it
            if isinstance(source, str):
                try:
                    module = importlib.import_module(source)
                    source = module
                except ImportError:
                    raise InvalidSourceError(f"Could not import module: {source}")
            
            # If source is a module, find all Pydantic models in it
            if inspect.ismodule(source):
                models = []
                for _name, obj in inspect.getmembers(source):
                    if inspect.isclass(obj) and issubclass(obj, BaseModel) and obj != BaseModel:
                        models.append(obj)
                
                if not models:
                    raise InvalidSourceError(f"No Pydantic models found in module: {source.__name__}")
                
                # Generate schema for each model
                schema_data = {
                    "$schema": "http://json-schema.org/draft-07/schema#",
                    "title": namespace or source.__name__,
                    "type": "object",
                    "definitions": {}
                }
                
                for model in models:
                    model_schema = model.schema()
                    schema_data["definitions"][model.__name__] = model_schema
                
                return schema_data
            
            # If source is a class, check if it's a Pydantic model
            elif inspect.isclass(source) and issubclass(source, BaseModel):
                schema_data = source.schema()
                if namespace:
                    schema_data["title"] = namespace
                return schema_data
            
            else:
                raise InvalidSourceError("Source must be a Pydantic model, a module containing Pydantic models, or a path to such a module")
                
        except Exception as e:
            if not isinstance(e, SchemaGenerationError):
                logger.error(f"Error generating schema from Pydantic model: {e}", exc_info=True)
                raise SchemaGenerationError(f"Pydantic schema generation failed: {e}")
            raise
    
    def _handle_dataclass(self, source: Any, namespace: Optional[str] = None) -> dict[str, Any]:
        """
        Generate schema data from a dataclass.
        
        Args:
            source: A dataclass or module containing dataclasses
            namespace: Optional namespace for the schema
            
        Returns:
            Dict containing the schema data
            
        Raises:
            InvalidSourceError: If the source is not a valid dataclass or module
        """
        try:
            # If source is a string, try to import it
            if isinstance(source, str):
                try:
                    module = importlib.import_module(source)
                    source = module
                except ImportError:
                    raise InvalidSourceError(f"Could not import module: {source}")
            
            # If source is a module, find all dataclasses in it
            if inspect.ismodule(source):
                dataclasses = []
                for _name, obj in inspect.getmembers(source):
                    if inspect.isclass(obj) and is_dataclass(obj):
                        dataclasses.append(obj)
                
                if not dataclasses:
                    raise InvalidSourceError(f"No dataclasses found in module: {source.__name__}")
                
                # Generate schema for each dataclass
                schema_data = {
                    "$schema": "http://json-schema.org/draft-07/schema#",
                    "title": namespace or source.__name__,
                    "type": "object",
                    "definitions": {}
                }
                
                for dc in dataclasses:
                    schema_data["definitions"][dc.__name__] = self._dataclass_to_schema(dc)
                
                return schema_data
            
            # If source is a class, check if it's a dataclass
            elif inspect.isclass(source) and is_dataclass(source):
                schema_data = self._dataclass_to_schema(source)
                if namespace:
                    schema_data["title"] = namespace
                return schema_data
            
            else:
                raise InvalidSourceError("Source must be a dataclass, a module containing dataclasses, or a path to such a module")
                
        except Exception as e:
            if not isinstance(e, SchemaGenerationError):
                logger.error(f"Error generating schema from dataclass: {e}", exc_info=True)
                raise SchemaGenerationError(f"Dataclass schema generation failed: {e}")
            raise
    
    def _dataclass_to_schema(self, dataclass_obj: type) -> dict[str, Any]:
        """Convert a dataclass to a JSON schema."""
        from dataclasses import fields
        
        schema = {
            "type": "object",
            "title": dataclass_obj.__name__,
            "properties": {},
            "required": []
        }
        
        for field in fields(dataclass_obj):
            # Map Python types to JSON schema types
            field_type = field.type
            type_info = self._python_type_to_json_schema(field_type)
            
            schema["properties"][field.name] = type_info
            
            # Check if field is required
            if field.default == field.default_factory == dataclasses._MISSING_TYPE:
                schema["required"].append(field.name)
        
        return schema
    
    def _python_type_to_json_schema(self, py_type: type) -> dict[str, Any]:
        """Convert a Python type to a JSON schema type definition."""
        # This is a simplified implementation
        if py_type == str:
            return {"type": "string"}
        elif py_type == int:
            return {"type": "integer"}
        elif py_type == float:
            return {"type": "number"}
        elif py_type == bool:
            return {"type": "boolean"}
        elif py_type in (list, list):
            return {"type": "array", "items": {}}
        elif py_type in (dict, dict):
            return {"type": "object"}
        elif hasattr(py_type, "__origin__") and py_type.__origin__ == list:
            # Handle List[X]
            item_type = py_type.__args__[0]
            return {
                "type": "array",
                "items": self._python_type_to_json_schema(item_type)
            }
        elif hasattr(py_type, "__origin__") and py_type.__origin__ == dict:
            # Handle Dict[X, Y]
            return {"type": "object"}
        elif hasattr(py_type, "__origin__") and py_type.__origin__ == Union:
            # Handle Optional[X] and Union[X, Y, ...]
            types = [self._python_type_to_json_schema(arg) for arg in py_type.__args__ if arg != type(None)]
            if len(types) == 1:
                return types[0]
            return {"anyOf": types}
        else:
            # Default to string for complex types
            return {"type": "string"}
    
    def _handle_sqlalchemy(self, source: Any, namespace: Optional[str] = None) -> dict[str, Any]:
        """
        Generate schema data from SQLAlchemy models.
        
        Args:
            source: A SQLAlchemy model class, a module containing models, or a path to such a module
            namespace: Optional namespace for the schema
            
        Returns:
            Dict containing the schema data
            
        Raises:
            InvalidSourceError: If the source is not a valid SQLAlchemy model or module
        """
        try:
            # Try to import SQLAlchemy
            try:
                import sqlalchemy
                from sqlalchemy.ext.declarative import DeclarativeMeta
            except ImportError:
                logger.error("SQLAlchemy package is required for SQLAlchemy schema generation")
                raise SchemaGenerationError("SQLAlchemy package is required for SQLAlchemy schema generation")
            
            # If source is a string, try to import it
            if isinstance(source, str):
                try:
                    module = importlib.import_module(source)
                    source = module
                except ImportError:
                    raise InvalidSourceError(f"Could not import module: {source}")
            
            # If source is a module, find all SQLAlchemy models in it
            if inspect.ismodule(source):
                models = []
                for _name, obj in inspect.getmembers(source):
                    if inspect.isclass(obj) and isinstance(obj, DeclarativeMeta):
                        models.append(obj)
                
                if not models:
                    raise InvalidSourceError(f"No SQLAlchemy models found in module: {source.__name__}")
                
                # Generate schema for each model
                schema_data = {
                    "$schema": "http://json-schema.org/draft-07/schema#",
                    "title": namespace or source.__name__,
                    "type": "object",
                    "definitions": {}
                }
                
                for model in models:
                    schema_data["definitions"][model.__name__] = self._sqlalchemy_to_schema(model)
                
                return schema_data
            
            # If source is a class, check if it's a SQLAlchemy model
            elif inspect.isclass(source) and isinstance(source, DeclarativeMeta):
                schema_data = self._sqlalchemy_to_schema(source)
                if namespace:
                    schema_data["title"] = namespace
                return schema_data
            
            else:
                raise InvalidSourceError("Source must be a SQLAlchemy model, a module containing SQLAlchemy models, or a path to such a module")
                
        except Exception as e:
            if not isinstance(e, SchemaGenerationError):
                logger.error(f"Error generating schema from SQLAlchemy model: {e}", exc_info=True)
                raise SchemaGenerationError(f"SQLAlchemy schema generation failed: {e}")
            raise
    
    def _sqlalchemy_to_schema(self, model: type) -> dict[str, Any]:
        """Convert a SQLAlchemy model to a JSON schema."""
        
        schema = {
            "type": "object",
            "title": model.__name__,
            "properties": {},
            "required": []
        }
        
        # Get model columns
        for column_name, column in model.__table__.columns.items():
            # Map SQLAlchemy types to JSON schema types
            type_info = self._sqlalchemy_type_to_json_schema(column.type)
            
            # Add constraints
            if column.nullable is False:
                schema["required"].append(column_name)
            
            if hasattr(column.type, "length") and column.type.length is not None:
                type_info["maxLength"] = column.type.length
            
            schema["properties"][column_name] = type_info
        
        return schema
    
    def _sqlalchemy_type_to_json_schema(self, sa_type: Any) -> dict[str, Any]:
        """Convert a SQLAlchemy type to a JSON schema type definition."""
        import sqlalchemy as sa
        
        # This is a simplified implementation
        if isinstance(sa_type, sa.String):
            return {"type": "string"}
        elif isinstance(sa_type, sa.Integer):
            return {"type": "integer"}
        elif isinstance(sa_type, sa.Float):
            return {"type": "number"}
        elif isinstance(sa_type, sa.Boolean):
            return {"type": "boolean"}
        elif isinstance(sa_type, sa.Date):
            return {"type": "string", "format": "date"}
        elif isinstance(sa_type, sa.DateTime):
            return {"type": "string", "format": "date-time"}
        elif isinstance(sa_type, sa.Enum):
            return {
                "type": "string",
                "enum": [e.name for e in sa_type.enum_class]
            }
        else:
            # Default to string for complex types
            return {"type": "string"}
    
    def _handle_dict(self, source: dict[str, Any], namespace: Optional[str] = None) -> dict[str, Any]:
        """
        Generate schema data from a dictionary.
        
        Args:
            source: A dictionary to generate schema from
            namespace: Optional namespace for the schema
            
        Returns:
            Dict containing the schema data
            
        Raises:
            InvalidSourceError: If the source is not a valid dictionary
        """
        if not isinstance(source, dict):
            raise InvalidSourceError("Source must be a dictionary")
        
        # For dictionaries, we'll infer the schema from the structure
        schema_data = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": namespace or "Dictionary Schema",
            "type": "object",
            "properties": {}
        }
        
        for key, value in source.items():
            schema_data["properties"][key] = self._infer_type(value)
        
        return schema_data
    
    def _infer_type(self, value: Any) -> dict[str, Any]:
        """Infer JSON schema type from a Python value."""
        if value is None:
            return {"type": "null"}
        elif isinstance(value, str):
            return {"type": "string"}
        elif isinstance(value, int):
            return {"type": "integer"}
        elif isinstance(value, float):
            return {"type": "number"}
        elif isinstance(value, bool):
            return {"type": "boolean"}
        elif isinstance(value, list):
            if value:
                # Infer type from the first item
                item_schema = self._infer_type(value[0])
                return {"type": "array", "items": item_schema}
            else:
                return {"type": "array", "items": {}}
        elif isinstance(value, dict):
            properties = {}
            for k, v in value.items():
                properties[k] = self._infer_type(v)
            return {"type": "object", "properties": properties}
        else:
            # Default to string for complex types
            return {"type": "string"}
    
    def _handle_class(self, source: Any, namespace: Optional[str] = None) -> dict[str, Any]:
        """
        Generate schema data from a Python class.
        
        Args:
            source: A Python class or module containing classes
            namespace: Optional namespace for the schema
            
        Returns:
            Dict containing the schema data
            
        Raises:
            InvalidSourceError: If the source is not a valid class or module
        """
        try:
            # If source is a string, try to import it
            if isinstance(source, str):
                try:
                    module = importlib.import_module(source)
                    source = module
                except ImportError:
                    raise InvalidSourceError(f"Could not import module: {source}")
            
            # If source is a module, find all classes in it
            if inspect.ismodule(source):
                classes = []
                for _name, obj in inspect.getmembers(source):
                    if inspect.isclass(obj) and obj.__module__ == source.__name__:
                        classes.append(obj)
                
                if not classes:
                    raise InvalidSourceError(f"No classes found in module: {source.__name__}")
                
                # Generate schema for each class
                schema_data = {
                    "$schema": "http://json-schema.org/draft-07/schema#",
                    "title": namespace or source.__name__,
                    "type": "object",
                    "definitions": {}
                }
                
                for cls in classes:
                    schema_data["definitions"][cls.__name__] = self._class_to_schema(cls)
                
                return schema_data
            
            # If source is a class
            elif inspect.isclass(source):
                schema_data = self._class_to_schema(source)
                if namespace:
                    schema_data["title"] = namespace
                return schema_data
            
            else:
                raise InvalidSourceError("Source must be a class, a module containing classes, or a path to such a module")
                
        except Exception as e:
            if not isinstance(e, SchemaGenerationError):
                logger.error(f"Error generating schema from class: {e}", exc_info=True)
                raise SchemaGenerationError(f"Class schema generation failed: {e}")
            raise
    
    def _class_to_schema(self, cls: type) -> dict[str, Any]:
        """Convert a Python class to a JSON schema."""
        schema = {
            "type": "object",
            "title": cls.__name__,
            "properties": {}
        }
        
        # Get class attributes with type annotations
        for name, annotation in getattr(cls, "__annotations__", {}).items():
            schema["properties"][name] = self._python_type_to_json_schema(annotation)
        
        # Get instance variables from __init__ parameters
        if hasattr(cls, "__init__"):
            sig = inspect.signature(cls.__init__)
            for param_name, param in sig.parameters.items():
                if param_name != "self" and param_name not in schema["properties"]:
                    if param.annotation != inspect.Parameter.empty:
                        schema["properties"][param_name] = self._python_type_to_json_schema(param.annotation)
                    else:
                        schema["properties"][param_name] = {"type": "string"}
        
        return schema
    
    def _handle_json(self, source: Any, namespace: Optional[str] = None) -> dict[str, Any]:
        """
        Generate schema data from JSON.
        
        Args:
            source: A JSON string, file path, or parsed JSON object
            namespace: Optional namespace for the schema
            
        Returns:
            Dict containing the schema data
            
        Raises:
            InvalidSourceError: If the source is not valid JSON
        """
        try:
            # If source is a string that looks like a file path
            if isinstance(source, str) and (os.path.exists(source) or source.startswith("./") or source.startswith("/")):
                try:
                    with open(source) as f:
                        data = json.load(f)
                except Exception as e:
                    raise InvalidSourceError(f"Failed to load JSON from file {source}: {e}")
            
            # If source is a JSON string
            elif isinstance(source, str):
                try:
                    data = json.loads(source)
                except json.JSONDecodeError:
                    raise InvalidSourceError("Invalid JSON string")
            
            # If source is already a parsed JSON object (dict or list)
            elif isinstance(source, (dict, list)):
                data = source
            
            else:
                raise InvalidSourceError("Source must be a JSON string, file path, or parsed JSON object")
            
            # Generate schema from the JSON data
            schema_data = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": namespace or "JSON Schema"
            }
            
            if isinstance(data, dict):
                schema_data["type"] = "object"
                schema_data["properties"] = {}
                
                for key, value in data.items():
                    schema_data["properties"][key] = self._infer_type(value)
            
            elif isinstance(data, list):
                schema_data["type"] = "array"
                if data:
                    # Infer type from the first item
                    schema_data["items"] = self._infer_type(data[0])
                else:
                    schema_data["items"] = {}
            
            return schema_data
                
        except Exception as e:
            if not isinstance(e, SchemaGenerationError):
                logger.error(f"Error generating schema from JSON: {e}", exc_info=True)
                raise SchemaGenerationError(f"JSON schema generation failed: {e}")
            raise


def main():
    """Command-line interface for the schema generator."""
    parser = argparse.ArgumentParser(description="Generate schemas from various sources")
    
    parser.add_argument(
        "--source-type",
        type=str,
        choices=[t.value for t in SourceType],
        required=True,
        help="Type of the source to generate schema from"
    )
    
    parser.add_argument(
        "--source-path",
        type=str,
        required=True,
        help="Path to the source (module path, file path, etc.)"
    )
    
    parser.add_argument(
        "--output-format",
        type=str,
        choices=[f.value for f in SchemaFormat],
        required=True,
        help="Output format for the generated schema"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./schemas",
        help="Directory to write the generated schema to"
    )
    
    parser.add_argument(
        "--namespace",
        type=str,
        help="Namespace for the generated schema"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    try:
        # Create the schema generator
        generator = SchemaGenerator()
        
        # Generate the schema
        source_type = SourceType(args.source_type)
        output_format = SchemaFormat(args.output_format)
        
        # Make sure output directory exists
        os.makedirs(args.output_dir, exist_ok=True)
        
        # Generate output filename
        source_name = args.source_path.split(".")[-1]
        output_filename = f"{source_name}_schema"
        output_path = os.path.join(args.output_dir, output_filename)
        
        # Generate the schema
        generator.generate(
            source=args.source_path,
            source_type=source_type,
            output_format=output_format,
            output_path=output_path,
            namespace=args.namespace
        )
        
        logger.info(f"Schema generation completed successfully. Output: {output_path}")
        
    except Exception as e:
        logger.error(f"Schema generation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # Import datetime here to avoid circular imports
    import datetime
    main()