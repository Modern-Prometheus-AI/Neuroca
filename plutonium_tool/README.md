<p align="center">
  <img src="plutonium_tool/plutonium/assets/plutonium-icon.png" alt="Plutonium Logo" width="150"/>
</p>

<h1 align="center">Plutonium</h1>

<p align="center">
  <strong>A cross-language dependency manager and analysis tool.</strong>
</p>

<p align="center">
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square" alt="License: MIT"/>
  </a>
  <a href="https://www.python.org/downloads/">
    <img src="https://img.shields.io/badge/python-3.9+-blue.svg?style=flat-square" alt="Requires Python 3.9+"/>
  </a>
   <a href="https://nodejs.org/">
    <img src="https://img.shields.io/badge/node-%3E%3D18-important.svg?style=flat-square" alt="Requires Node.js >=18"/>
  </a>
</p>

<p align="center">
  Plutonium helps you track, compare, and auto-fix dependencies across multiple programming environments. It analyzes dependencies, project structure, and performance, generates comprehensive reports, and assists in resolving conflicts and vulnerabilities.
</p>

---

## Overview

Plutonium is a comprehensive development toolkit designed to work with diverse codebases. It provides a unified command-line interface (CLI) to perform various analyses crucial for maintaining healthy and efficient projects, especially those involving multiple languages or complex dependency trees.

## Key Features

* **Multi-Language Dependency Analysis (`deps:check`)**: Analyzes dependencies in Node.js, Python, Ruby, Maven (Java), Go projects, and potentially more.
* **Dependency Harmonization (`deps:harmonize`)**: Identifies and suggests synchronization for versions of shared dependencies across different parts of a project.
* **Intelligent Dependency Updates (`deps:update`)**: (Planned) Updates dependencies while considering compatibility.
* **Performance Analysis (`perf:analyze`)**: Analyzes application performance metrics (implementation may vary by project type).
* **Project Structure Analysis (`struct:analyze`)**: Examines project layout, identifies potential issues, and suggests organizational improvements.
* **Language & Framework Detection (`lang:detect`)**: Automatically detects the primary languages, frameworks, and package managers used in the project.
* **Comprehensive Analysis (`analyze-all`)**: Runs a sequence of checks (dependencies, structure, tests, coverage, package versions, conflicts) and generates a unified HTML report.

## Installation

Currently, Plutonium is run directly from the cloned repository using Node.js.

**Prerequisites:**

* Node.js (Version 18 or higher recommended)
* Python (Version 3.9 or higher recommended, for Python-specific analysis and testing)
* `pip` (for Python dependency checks)
* Access to relevant package managers for the languages in your project (npm, pip, etc.)

**Steps:**

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd <your-repository-name>
    ```
2.  **Install Node.js dependencies for the tool itself:**
    ```bash
    # Navigate to the tool's directory
    cd Neuroca/plutonium_tool
    npm install
    # Navigate back to the project root
    cd ../..
    ```
3.  **Ensure Python environment is set up** for your project if analyzing Python code (e.g., activate a virtual environment, install project requirements).

## Usage

Run the Plutonium wrapper script from your project's root directory using Node.js:

```bash
node plutonium.js <command> [options]
Available Commands:deps:check: Analyze dependencies.--language=<lang>: Specify language (auto, python, js, etc.). Default: auto.--path=<dir>: Path to analyze (default: .).deps:harmonize: Check for conflicting versions of the same dependency.--fix: Attempt to apply harmonization changes.deps:update: (Planned) Update dependencies.perf:analyze: Analyze performance (may depend on project type).struct:analyze: Analyze project directory structure.lang:detect: Detect project languages and frameworks.analyze-all: Run a comprehensive suite of checks and generate a unified report.help [command]: Show help information.Global Options:--verbose: Show detailed output.--json: Output results in JSON format (for applicable commands).--path=<dir>: Specify the project directory to analyze (default: current directory .).Examples:# Detect languages in the current directory
node plutonium.js lang:detect

# Check Python dependencies in the current directory
node plutonium.js deps:check --language=python

# Run the full analysis suite
node plutonium.js analyze-all
The analyze-all CommandThis special command performs a sequence of analyses:Runs deps:check (currently hardcoded for Python).Runs struct:analyze.Runs tests using pytest and collects coverage data (requires pytest and coverage Python packages).Checks installed Python package versions using importlib.metadata or pkg_resources.Checks for Python dependency conflicts using pip check.Generates a unified HTML report (Neuroca/reports/unified_analysis.html) summarizing the findings and providing recommendations.DevelopmentSetup:Follow the Installation steps.Install development dependencies if any are specified (check Neuroca/plutonium_tool/package.json).Running Tests:The analyze-all command includes running tests via pytest. Ensure pytest and related packages (like pytest-cov) are installed in your Python environment. You can also run tests manually:# Make sure your Python environment is active
python -m pytest [options] [test_directory]
ContributingContributions are welcome! Please