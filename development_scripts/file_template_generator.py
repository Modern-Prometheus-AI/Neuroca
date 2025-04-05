#!/usr/bin/env python3
"""
File Template Generator

This script generates template files for new modules with proper imports and structure.
It helps ensure that new files follow the project's conventions and dependency patterns.
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any


# Template definitions for different file types
TEMPLATES = {
    "module": """\"\"\"
{module_name} Module

{description}
\"\"\"

from typing import Dict, List, Optional, Any, Union
{imports}

{content}
""",

    "cli_command": """\"\"\"
CLI Command: {command_name}

{description}
\"\"\"

import click
import typer
from typing import Dict, List, Optional, Any
from neuroca.utils.logging import get_logger
{imports}

logger = get_logger(__name__)

{content}
""",

    "api_route": """\"\"\"
API Route: {route_name}

{description}
\"\"\"

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, List, Optional, Any
from neuroca.utils.logging import get_logger
{imports}

router = APIRouter(prefix="/{route_prefix}", tags=["{tag}"])
logger = get_logger(__name__)

{content}
""",

    "model": """\"\"\"
Model: {model_name}

{description}
\"\"\"

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator
{imports}

{content}
""",

    "test": """\"\"\"
Test: {test_name}

{description}
\"\"\"

import unittest
import pytest
from typing import Dict, List, Optional, Any
{imports}

{content}
"""
}


def ensure_directory_exists(directory: str) -> None:
    """Ensure the directory exists, creating it if necessary."""
    os.makedirs(directory, exist_ok=True)


def ensure_init_files(directory: str) -> None:
    """Ensure all directories in the path have __init__.py files."""
    parts = Path(directory).parts
    current = parts[0]
    
    for part in parts[1:]:
        current = os.path.join(current, part)
        init_file = os.path.join(current, "__init__.py")
        
        if os.path.isdir(current) and not os.path.exists(init_file):
            with open(init_file, "w", encoding="utf-8") as f:
                package_name = os.path.basename(current).replace("_", " ").title()
                f.write(f'"""{package_name} package."""\n')
                
            print(f"Created {init_file}")


def get_default_content(template_type: str) -> str:
    """Get default content for the template type."""
    if template_type == "module":
        return """# Add your module code here

def main():
    \"\"\"Main function.\"\"\"
    pass


if __name__ == "__main__":
    main()
"""
    elif template_type == "cli_command":
        return """# Define your CLI command here

@click.command()
@click.option("--option", "-o", help="An example option")
def command(option: str):
    \"\"\"Command description.\"\"\"
    logger.info(f"Running command with option: {option}")
    # Implement command logic here
    

# For use with Typer
app = typer.Typer(help="Command description")

@app.command()
def run(option: str = typer.Option(None, "--option", "-o", help="An example option")):
    \"\"\"Run the command.\"\"\"
    logger.info(f"Running command with option: {option}")
    # Implement command logic here
"""
    elif template_type == "api_route":
        return """# Define your API routes here

@router.get("/")
async def get_items():
    \"\"\"
    Get all items.
    
    Returns:
        List of items
    \"\"\"
    logger.info("Getting all items")
    return {"items": []}


@router.get("/{item_id}")
async def get_item(item_id: str):
    \"\"\"
    Get a specific item by ID.
    
    Args:
        item_id: The ID of the item to retrieve
        
    Returns:
        The item if found
        
    Raises:
        HTTPException: If the item is not found
    \"\"\"
    logger.info(f"Getting item: {item_id}")
    # Implement logic to get item
    return {"id": item_id, "name": "Example Item"}
"""
    elif template_type == "model":
        return """# Define your models here

class SampleModel(BaseModel):
    \"\"\"Sample model class.\"\"\"
    id: str
    name: str
    description: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    
    @validator("id")
    def validate_id(cls, value):
        \"\"\"Validate the ID field.\"\"\"
        if not value:
            raise ValueError("ID cannot be empty")
        return value
"""
    elif template_type == "test":
        return """# Define your tests here

class TestSample(unittest.TestCase):
    \"\"\"Sample test case.\"\"\"
    
    def setUp(self):
        \"\"\"Set up test fixtures.\"\"\"
        pass
        
    def test_something(self):
        \"\"\"Test something.\"\"\"
        self.assertTrue(True)
        
    def tearDown(self):
        \"\"\"Tear down test fixtures.\"\"\"
        pass


@pytest.fixture
def sample_fixture():
    \"\"\"Sample pytest fixture.\"\"\"
    # Set up code
    yield "sample_value"
    # Tear down code


def test_with_fixture(sample_fixture):
    \"\"\"Test using a fixture.\"\"\"
    assert sample_fixture == "sample_value"
"""


def generate_file(
    file_path: str,
    template_type: str = "module",
    module_name: str = None,
    description: str = None,
    command_name: str = None,
    route_name: str = None,
    route_prefix: str = None,
    tag: str = None,
    model_name: str = None,
    test_name: str = None,
    imports: List[str] = None,
    content: str = None,
) -> bool:
    """Generate a file from a template."""
    # Set default values
    if module_name is None:
        module_name = os.path.basename(file_path).replace(".py", "").replace("_", " ").title()
    
    if description is None:
        description = f"This module provides {module_name} functionality."
    
    if command_name is None:
        command_name = module_name
    
    if route_name is None:
        route_name = module_name
    
    if route_prefix is None:
        route_prefix = os.path.basename(file_path).replace(".py", "").lower()
    
    if tag is None:
        tag = route_prefix
    
    if model_name is None:
        model_name = module_name
    
    if test_name is None:
        test_name = module_name
    
    if imports is None:
        imports = []
    
    imports_str = "\n".join(imports)
    if imports_str and not imports_str.endswith("\n"):
        imports_str += "\n"
    
    if content is None:
        content = get_default_content(template_type)
    
    # Create directory structure if needed
    directory = os.path.dirname(file_path)
    if directory:
        ensure_directory_exists(directory)
        ensure_init_files(directory)
    
    # Check if file already exists
    if os.path.exists(file_path):
        print(f"Warning: {file_path} already exists.")
        overwrite = input("Overwrite? (y/N): ")
        if overwrite.lower() != "y":
            print("Aborted.")
            return False
    
    # Generate file content based on template
    template = TEMPLATES.get(template_type)
    if not template:
        print(f"Error: Unknown template type '{template_type}'")
        return False
    
    file_content = template.format(
        module_name=module_name,
        description=description,
        command_name=command_name,
        route_name=route_name,
        route_prefix=route_prefix,
        tag=tag,
        model_name=model_name,
        test_name=test_name,
        imports=imports_str,
        content=content,
    )
    
    # Write the file
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(file_content)
        print(f"Created {file_path}")
        return True
    except Exception as e:
        print(f"Error creating file: {str(e)}")
        return False


def main():
    """Main function to run the template generator."""
    parser = argparse.ArgumentParser(description="Generate file templates with proper imports and structure")
    parser.add_argument("file_path", help="Path to the new file")
    parser.add_argument("--type", "-t", choices=list(TEMPLATES.keys()), default="module",
                      help="Type of template to use")
    parser.add_argument("--name", "-n", help="Name for the module/command/route/model/test")
    parser.add_argument("--description", "-d", help="Description of the file")
    parser.add_argument("--imports", "-i", nargs="+", help="Additional import statements")
    
    args = parser.parse_args()
    
    success = generate_file(
        file_path=args.file_path,
        template_type=args.type,
        module_name=args.name,
        description=args.description,
        imports=args.imports,
    )
    
    if success:
        print("\nTemplate generation complete!")
        print("\nTo validate dependencies in this file, run:")
        print(f"    python development_scripts/dependency_validator.py --file {args.file_path}")
        print("\nTo automatically fix dependency issues, run:")
        print(f"    python development_scripts/dependency_validator.py --file {args.file_path} --fix")
    else:
        print("\nFailed to generate template.")
        sys.exit(1)


if __name__ == "__main__":
    main() 