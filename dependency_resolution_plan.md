# NeuroCognitive Architecture (NCA) Dependency Resolution Plan

## EXECUTIVE SUMMARY

This document outlines a comprehensive plan to resolve the critical dependency issues identified in the NCA codebase. The current architecture suffers from severe structural problems that prevent proper package functionality, including missing namespace packages, invalid package initialization, inconsistent import patterns, and circular dependencies.

The implementation plan is structured into four phases over a four-week period:
1. **Package Restructuring** - Creating proper namespace package structure
2. **Import & Dependency Fixes** - Resolving import issues and circular dependencies
3. **Entry Point & Script Fixes** - Fixing CLI, API, and worker entry points
4. **Testing & Validation** - Verifying package installation and functionality

## CURRENT ISSUES

### Package Structure Issues
- Missing top-level `neuroca` package despite 241 import statements referencing it
- 50+ directories lacking proper `__init__.py` files
- 3 critical `__init__.py` files with invalid UTF-8 BOM characters
- Inconsistent import patterns mixing top-level, nested, and relative imports

### Missing Dependencies
- 41 missing dependencies including core modules and external libraries
- Multiple circular import patterns, especially in memory systems
- Version mismatches in 15 dependencies

### Code Organization Issues
- Duplicated functionality across multiple implementation files
- Inconsistent module organization creating confusion
- Entry point failures due to import errors

## IMPLEMENTATION PLAN

### Phase 1: Project Restructuring (Week 1)

#### 1.1 Create Proper Package Structure

```
# Create top-level neuroca directory
mkdir -p neuroca/core/memory
mkdir -p neuroca/core/health
mkdir -p neuroca/api
mkdir -p neuroca/cli
mkdir -p neuroca/db
mkdir -p neuroca/config
mkdir -p neuroca/utils
mkdir -p neuroca/models
mkdir -p neuroca/integration
mkdir -p neuroca/infrastructure
mkdir -p neuroca/monitoring
mkdir -p neuroca/tools
mkdir -p neuroca/scripts
mkdir -p neuroca/tests
```

#### 1.2 Create Base `__init__.py` Files

```python
# neuroca/__init__.py
"""
NeuroCognitive Architecture (NCA) - A biologically-inspired cognitive framework.

This package enhances Large Language Models with cognitive capabilities through
a three-tiered memory system, health dynamics, and adaptive neurological processes.
"""

__version__ = "0.1.0"
```

#### 1.3 Fix BOM Characters in Problematic Files

```
# Remove BOM characters from problematic files
for file in infrastructure/__init__.py scripts/__init__.py tools/__init__.py; do
    # Create backup
    cp "$file" "${file}.bak"
    # Remove BOM and write back
    tail -c +4 "${file}.bak" > "$file"
done
```

#### 1.4 Update Package Configuration in `pyproject.toml`

```toml
[tool.poetry]
name = "neuroca"
version = "0.1.0"
description = "NeuroCognitive Architecture for enhancing LLMs with biologically-inspired cognitive capabilities"
authors = ["NCA Team <team@neuroca.ai>"]
readme = "README.md"
packages = [{include = "neuroca"}]

[tool.poetry.scripts]
neuroca = "neuroca.cli.main:main"
neuroca-api = "neuroca.api.main:main"
neuroca-worker = "neuroca.infrastructure.worker:main"

# ... rest of the configuration
```

### Phase 2: Import & Dependency Fixes (Week 2)

#### 2.1 Move Existing Code to New Structure

```
# Move core modules to neuroca package
cp -r core/* neuroca/core/
cp -r memory/* neuroca/core/memory/
cp -r api/* neuroca/api/
cp -r cli/* neuroca/cli/
cp -r db/* neuroca/db/
cp -r config/* neuroca/config/
cp -r utils/* neuroca/utils/
cp -r models/* neuroca/models/
cp -r integration/* neuroca/integration/
cp -r infrastructure/* neuroca/infrastructure/
cp -r monitoring/* neuroca/monitoring/
cp -r tools/* neuroca/tools/
cp -r scripts/* neuroca/scripts/
cp -r tests/* neuroca/tests/
```

#### 2.2 Fix Import Statements

Create a script to update import statements:

```python
# scripts/fix_imports.py
import os
import re
import sys

def fix_imports(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix direct imports from top-level modules to use neuroca namespace
    patterns = [
        (r'from (memory|core|api|cli|db|config|utils|models|integration|infrastructure|monitoring|tools|scripts) import', r'from neuroca.\1 import'),
        (r'import (memory|core|api|cli|db|config|utils|models|integration|infrastructure|monitoring|tools|scripts)\.', r'import neuroca.\1.'),
        # Fix relative imports if needed
        (r'from \.\.(memory|core|api|cli|db|config|utils|models) import', r'from neuroca.\1 import'),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def process_directory(directory):
    count = 0
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if fix_imports(file_path):
                    count += 1
    return count

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_imports.py <directory>")
        sys.exit(1)
    
    directory = sys.argv[1]
    count = process_directory(directory)
    print(f"Updated imports in {count} files")
```

#### 2.3 Resolve Circular Imports

Identify and fix circular dependencies by refactoring shared functionality:

1. Create interface modules that define abstract base classes
2. Move shared functionality to utility modules
3. Use dependency injection where appropriate
4. Implement lazy imports for non-critical dependencies

Example fix for circular imports between memory modules:

```python
# neuroca/core/memory/interfaces.py
"""Interface definitions for memory systems to prevent circular imports."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

class MemoryChunk(ABC):
    """Abstract base class for memory chunks stored in any memory system."""
    
    @abstractmethod
    def get_content(self) -> Any:
        """Get the content of this memory chunk."""
        pass
    
    @abstractmethod
    def get_activation(self) -> float:
        """Get the current activation level of this memory chunk."""
        pass

class MemorySystem(ABC):
    """Abstract base class for all memory systems."""
    
    @abstractmethod
    def store(self, content: Any, **metadata) -> str:
        """Store content in this memory system."""
        pass
    
    @abstractmethod
    def retrieve(self, query: Any, **parameters) -> List[MemoryChunk]:
        """Retrieve content from this memory system."""
        pass
    
    @abstractmethod
    def forget(self, chunk_id: str) -> bool:
        """Remove content from this memory system."""
        pass
```

#### 2.4 Add Missing Dependencies to `pyproject.toml`

Update the dependencies section in `pyproject.toml`:

```toml
[tool.poetry.dependencies]
python = "^3.9"
numpy = "^1.24.0"
pandas = "^2.0.0"
torch = "^2.0.0"
fastapi = "^0.100.0"
uvicorn = "^0.23.0"
sqlalchemy = "^2.0.0"
alembic = "^1.11.0"
redis = "^4.6.0"
httpx = "^0.24.0"
transformers = "^4.30.0"
langchain = "^0.0.267"
faiss-cpu = "^1.7.4"
tiktoken = "^0.4.0"
loguru = "^0.7.0"
prometheus-client = "^0.17.0"
opentelemetry-api = "^1.18.0"
opentelemetry-sdk = "^1.18.0"
pydantic = "^2.0.0"
pyvis = "^0.3.2"
neo4j = "^5.9.0"
motor = "^3.2.0"
```

### Phase 3: Entry Point & Script Fixes (Week 3)

#### 3.1 Update CLI Entry Point

```python
# neuroca/cli/main.py
"""Command-line interface for the NeuroCognitive Architecture."""
import argparse
import sys
from typing import List, Optional

from neuroca.config.settings import get_settings
from neuroca.core.health import HealthMonitor

def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the CLI."""
    if args is None:
        args = sys.argv[1:]
    
    parser = argparse.ArgumentParser(description="NeuroCognitive Architecture CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Add health check command
    health_parser = subparsers.add_parser("health", help="Check system health")
    health_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed health information")
    
    # Add memory command
    memory_parser = subparsers.add_parser("memory", help="Memory system operations")
    memory_parser.add_argument("--type", "-t", choices=["working", "episodic", "semantic"], 
                              required=True, help="Memory type to operate on")
    memory_parser.add_argument("--operation", "-o", choices=["stats", "clear", "dump"], 
                              required=True, help="Operation to perform")
    
    # Parse arguments
    parsed_args = parser.parse_args(args)
    
    if not parsed_args.command:
        parser.print_help()
        return 1
    
    # Execute command
    if parsed_args.command == "health":
        return handle_health_command(parsed_args)
    elif parsed_args.command == "memory":
        return handle_memory_command(parsed_args)
    
    return 0

def handle_health_command(args):
    """Handle the health check command."""
    monitor = HealthMonitor()
    health_report = monitor.get_health_report()
    
    if args.verbose:
        print(health_report.json(indent=2))
    else:
        print(f"System health: {health_report.status}")
        if health_report.status != "healthy":
            print(f"Issues: {len(health_report.issues)}")
    
    return 0 if health_report.status == "healthy" else 1

def handle_memory_command(args):
    """Handle memory system operations."""
    from neuroca.core.memory.factory import create_memory_system
    
    memory_system = create_memory_system(args.type)
    
    if args.operation == "stats":
        stats = memory_system.get_statistics()
        print(f"{args.type.capitalize()} Memory Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    elif args.operation == "clear":
        memory_system.clear()
        print(f"{args.type.capitalize()} memory cleared.")
    elif args.operation == "dump":
        dump = memory_system.dump()
        print(f"{args.type.capitalize()} Memory Contents:")
        for item in dump:
            print(f"  - {item}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

#### 3.2 Update API Entry Point

```python
# neuroca/api/main.py
"""FastAPI application for the NeuroCognitive Architecture."""
import logging
from typing import Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from neuroca.config.settings import get_settings
from neuroca.core.health import HealthMonitor, HealthCheckResult
from neuroca.core.memory.factory import create_memory_system

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="NeuroCognitive Architecture API",
    description="API for interacting with the NeuroCognitive Architecture",
    version="0.1.0",
)

# Models
class MemoryRequest(BaseModel):
    """Request model for memory operations."""
    content: Dict
    metadata: Dict = {}

class MemoryResponse(BaseModel):
    """Response model for memory operations."""
    id: str
    success: bool
    message: str = ""

# Routes
@app.get("/health")
async def health_check() -> HealthCheckResult:
    """Check the health of the system."""
    monitor = HealthMonitor()
    health_report = monitor.get_health_report()
    return health_report

@app.post("/memory/{memory_type}/store", response_model=MemoryResponse)
async def store_memory(memory_type: str, request: MemoryRequest) -> MemoryResponse:
    """Store content in the specified memory system."""
    if memory_type not in ["working", "episodic", "semantic"]:
        raise HTTPException(status_code=400, detail=f"Invalid memory type: {memory_type}")
    
    try:
        memory_system = create_memory_system(memory_type)
        memory_id = memory_system.store(request.content, **request.metadata)
        return MemoryResponse(id=memory_id, success=True)
    except Exception as e:
        logger.exception(f"Error storing in {memory_type} memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory/{memory_type}/retrieve/{memory_id}")
async def retrieve_memory(memory_type: str, memory_id: str):
    """Retrieve content from the specified memory system."""
    if memory_type not in ["working", "episodic", "semantic"]:
        raise HTTPException(status_code=400, detail=f"Invalid memory type: {memory_type}")
    
    try:
        memory_system = create_memory_system(memory_type)
        result = memory_system.retrieve_by_id(memory_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Memory with ID {memory_id} not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error retrieving from {memory_type} memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def main():
    """Run the API server."""
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "neuroca.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )

if __name__ == "__main__":
    main()
```

#### 3.3 Update Worker Entry Point

```python
# neuroca/infrastructure/worker.py
"""Background worker for the NeuroCognitive Architecture."""
import logging
import signal
import sys
import time
from typing import Dict, List, Optional

from neuroca.config.settings import get_settings
from neuroca.core.health import HealthMonitor
from neuroca.core.memory.consolidation import MemoryConsolidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class Worker:
    """Background worker for processing tasks."""
    
    def __init__(self):
        """Initialize the worker."""
        self.settings = get_settings()
        self.health_monitor = HealthMonitor()
        self.memory_consolidator = MemoryConsolidator()
        self.running = False
    
    def start(self):
        """Start the worker."""
        logger.info("Starting worker...")
        self.running = True
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)
        
        try:
            self.run_loop()
        except Exception as e:
            logger.exception(f"Worker failed: {e}")
            return 1
        return 0
    
    def handle_signal(self, signum, frame):
        """Handle termination signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def run_loop(self):
        """Main processing loop."""
        while self.running:
            # Check system health
            health_report = self.health_monitor.get_health_report()
            if health_report.status != "healthy":
                logger.warning(f"System health issues detected: {health_report.issues}")
            
            # Run memory consolidation
            try:
                consolidated = self.memory_consolidator.consolidate()
                if consolidated:
                    logger.info(f"Consolidated {len(consolidated)} memories")
            except Exception as e:
                logger.error(f"Memory consolidation failed: {e}")
            
            # Sleep before next cycle
            time.sleep(self.settings.worker_interval)
        
        logger.info("Worker shutting down...")

def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the worker."""
    worker = Worker()
    return worker.start()

if __name__ == "__main__":
    sys.exit(main())
```

#### 3.4 Move Development Scripts into Package Structure

```
# Move development scripts into the package
mkdir -p neuroca/development
cp development_scripts/find_dependencies.py neuroca/development/
cp development_scripts/project_builder.py neuroca/development/
```

### Phase 4: Testing & Validation (Week 4)

#### 4.1 Install Package in Development Mode

```
# Install package in development mode
poetry install
```

#### 4.2 Test Entry Points

```
# Test CLI entry point
poetry run neuroca health

# Test API entry point
poetry run neuroca-api

# Test worker entry point
poetry run neuroca-worker
```

#### 4.3 Run Integration Tests

```
# Run tests
poetry run pytest neuroca/tests/
```

#### 4.4 Update Documentation

Update README.md and other documentation to reflect the new package structure and installation instructions.

#### 4.5 Clean Up Old Directory Structure

Once everything is working correctly, remove the old directory structure:

```
# Backup old structure
tar -czf old_structure_backup.tar.gz core memory api cli db config utils models integration infrastructure monitoring tools scripts

# Remove old directories
rm -rf core memory api cli db config utils models integration infrastructure monitoring tools scripts
```

## IMPLEMENTATION SCHEDULE

| Week | Phase | Key Deliverables |
|------|-------|-----------------|
| 1 | Package Restructuring | - New directory structure<br>- Base `__init__.py` files<br>- Fixed BOM characters<br>- Updated `pyproject.toml` |
| 2 | Import & Dependency Fixes | - Moved code to new structure<br>- Fixed import statements<br>- Resolved circular imports<br>- Updated dependencies |
| 3 | Entry Point & Script Fixes | - Updated CLI entry point<br>- Updated API entry point<br>- Updated Worker entry point<br>- Moved development scripts |
| 4 | Testing & Validation | - Package installation<br>- Entry point testing<br>- Integration tests<br>- Updated documentation<br>- Cleaned up old structure |

## RISK MITIGATION

1. **Backup Strategy**
   - Create full backup before starting
   - Commit changes to a separate branch
   - Create incremental backups after each phase

2. **Rollback Plan**
   - Keep old structure until validation is complete
   - Maintain compatibility layer during transition
   - Document all changes for potential rollback

3. **Testing Strategy**
   - Create smoke tests for each phase
   - Validate imports after each file move
   - Test entry points after each update
   - Run full test suite after completion

4. **Communication Plan**
   - Notify all team members of restructuring
   - Document changes in central repository
   - Provide migration guide for developers
   - Schedule review meetings after each phase

## SUCCESS CRITERIA

The dependency resolution will be considered successful when:

1. All imports resolve correctly without errors
2. All entry points (CLI, API, Worker) function properly
3. All tests pass with the new structure
4. Package can be installed via Poetry
5. No BOM characters or other encoding issues remain
6. Documentation is updated to reflect new structure
7. Old directory structure is safely removed

## CONCLUSION

This implementation plan provides a structured approach to resolving the critical dependency issues in the NCA codebase. By following this plan, we will create a properly structured Python package that follows best practices, resolves circular dependencies, and ensures all components work together seamlessly.

The four-phase approach allows for incremental progress with validation at each step, minimizing risk and ensuring a smooth transition to the new structure. Upon completion, the NCA system will have a solid foundation for future development and expansion. 