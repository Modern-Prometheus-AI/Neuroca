import os
import ast
import importlib.util
import pkg_resources
import datetime
from typing import List, Dict, Set
from pathlib import Path

def get_python_files(directory: str) -> List[str]:
    """Recursively find all .py files in the directory, excluding certain paths."""
    python_files = []
    exclude_dirs = {'__pycache__', 'venv', '.git', 'node_modules', '.venv'}
    
    for root, dirs, files in os.walk(directory):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    return python_files

def extract_imports(file_path: str) -> Set[str]:
    """Extract all imported modules from a Python file using ast."""
    imports = set()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        imports.add(name.name.split('.')[0])  # Get top-level module
                elif isinstance(node, ast.ImportFrom):
                    if node.module:  # Check if module is not None
                        imports.add(node.module.split('.')[0])  # Get top-level module
    except Exception as e:
        print(f"Error parsing {file_path}: {str(e)}")
    
    return imports

def check_module_availability(module_name: str) -> bool:
    """Check if a module is available in the current Python environment."""
    return importlib.util.find_spec(module_name) is not None

def get_installed_packages() -> Dict[str, str]:
    """Get a dictionary of installed packages and their versions."""
    installed = {}
    for package in pkg_resources.working_set:
        installed[package.key] = package.version
    return installed

def get_project_dependencies(project_root: str) -> Dict[str, str]:
    """Parse pyproject.toml or requirements.txt for project dependencies and versions."""
    dependencies = {}
    
    # Check pyproject.toml (Poetry)
    pyproject_path = os.path.join(project_root, 'pyproject.toml')
    if os.path.exists(pyproject_path):
        try:
            import tomli
            with open(pyproject_path, 'rb') as f:
                data = tomli.load(f)
            if 'tool' in data and 'poetry' in data['tool'] and 'dependencies' in data['tool']['poetry']:
                for dep, version in data['tool']['poetry']['dependencies'].items():
                    if isinstance(version, str):
                        dependencies[dep] = version
        except (ImportError, KeyError, ValueError) as e:
            print(f"Error parsing pyproject.toml: {str(e)}")
    
    # Check requirements.txt (Pip)
    requirements_path = os.path.join(project_root, 'requirements.txt')
    if os.path.exists(requirements_path):
        try:
            with open(requirements_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split('==')
                        if len(parts) == 2:
                            dependencies[parts[0]] = parts[1]
        except Exception as e:
            print(f"Error parsing requirements.txt: {str(e)}")
    
    return dependencies

def check_dependencies(project_root: str) -> Dict[str, List[str]]:
    """Recursively check all Python files for dependencies and identify missing/mismatched ones."""
    results = {
        "missing": [],
        "mismatched": [],
        "unused": []
    }
    
    python_files = get_python_files(project_root)
    all_imports = set()
    installed_packages = get_installed_packages()
    project_deps = get_project_dependencies(project_root)
    
    # Collect all imports from Python files
    for file_path in python_files:
        imports = extract_imports(file_path)
        all_imports.update(imports)
    
    # Check for missing dependencies
    for module in all_imports:
        if module in {'os', 'sys', 'time', 'datetime', 'uuid', 'json', 'pathlib', 'logging', 'ast', 'importlib', 'pkg_resources'}:
            continue  # Skip standard library modules
        if not check_module_availability(module):
            results["missing"].append(module)
        elif module in project_deps:
            # Check for version mismatches
            installed_version = installed_packages.get(module, "0.0.0")
            required_version = project_deps.get(module, "0.0.0")
            if installed_version != required_version and required_version != "*":
                results["mismatched"].append(f"{module}: Installed={installed_version}, Required={required_version}")
    
    # Check for unused dependencies (in project_deps but not imported)
    for dep in project_deps:
        if dep not in all_imports and dep not in installed_packages:
            results["unused"].append(dep)
    
    return results

def write_to_log(results, log_file):
    """Write the results to a log file."""
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(f"Dependency Check Results - {timestamp}\n")
        f.write("="*50 + "\n\n")
        
        f.write("Missing Dependencies:\n")
        if results["missing"]:
            for dep in results["missing"]:
                f.write(f"- {dep}\n")
        else:
            f.write("No missing dependencies found.\n")
        
        f.write("\nVersion Mismatches:\n")
        if results["mismatched"]:
            for mismatch in results["mismatched"]:
                f.write(f"- {mismatch}\n")
        else:
            f.write("No version mismatches found.\n")
        
        f.write("\nPotentially Unused Dependencies:\n")
        if results["unused"]:
            for dep in results["unused"]:
                f.write(f"- {dep}\n")
        else:
            f.write("No unused dependencies found.\n")
        
        # Add python files analyzed
        f.write("\nPython Files Analyzed:\n")
        for file_path in get_python_files(os.getcwd()):
            rel_path = os.path.relpath(file_path, os.getcwd())
            f.write(f"- {rel_path}\n")
        
        # Add installed packages
        f.write("\nInstalled Packages:\n")
        for pkg, version in get_installed_packages().items():
            f.write(f"- {pkg}=={version}\n")

def main():
    """Main function to run the dependency checker."""
    project_root = os.getcwd()  # Use current directory as project root
    results = check_dependencies(project_root)
    
    # Define log file path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join(script_dir, 'dependency_check.log')
    
    # Write to log file
    write_to_log(results, log_file)
    
    print("\nDependency Check Results:")
    print("-----------------------")
    
    if results["missing"]:
        print("\nMissing Dependencies:")
        for dep in results["missing"]:
            print(f"- {dep}")
    else:
        print("\nNo missing dependencies found.")
    
    if results["mismatched"]:
        print("\nVersion Mismatches:")
        for mismatch in results["mismatched"]:
            print(f"- {mismatch}")
    else:
        print("\nNo version mismatches found.")
    
    if results["unused"]:
        print("\nPotentially Unused Dependencies:")
        for dep in results["unused"]:
            print(f"- {dep}")
    else:
        print("\nNo unused dependencies found.")
    
    print(f"\nDetailed results have been written to: {log_file}")

if __name__ == "__main__":
    main()