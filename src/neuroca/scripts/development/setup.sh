#!/usr/bin/env bash

#==============================================================================
# NeuroCognitive Architecture (NCA) Development Environment Setup Script
#
# This script sets up a complete development environment for the NeuroCognitive
# Architecture project. It handles:
#   - Dependency installation
#   - Python environment setup
#   - Pre-commit hooks configuration
#   - Database initialization
#   - Configuration file generation
#   - Docker environment setup
#   - Development tools installation
#
# Usage:
#   ./scripts/development/setup.sh [--no-docker] [--skip-deps] [--help]
#
# Options:
#   --no-docker    Skip Docker setup
#   --skip-deps    Skip system dependency installation
#   --help         Display this help message
#
# Requirements:
#   - Bash 4.0+
#   - sudo access (for system dependencies)
#   - Internet connection
#
# Author: NeuroCognitive Architecture Team
# License: See LICENSE file
# Version: 1.0.0
#==============================================================================

set -eo pipefail

# Script constants
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
readonly LOG_FILE="${PROJECT_ROOT}/logs/setup_$(date +%Y%m%d_%H%M%S).log"
readonly MIN_PYTHON_VERSION="3.9"
readonly MIN_DOCKER_VERSION="20.10.0"
readonly MIN_DOCKER_COMPOSE_VERSION="2.0.0"
readonly VENV_DIR="${PROJECT_ROOT}/.venv"
readonly CONFIG_DIR="${PROJECT_ROOT}/config"
readonly REQUIRED_SYSTEM_PACKAGES=(
  "git"
  "curl"
  "make"
  "python3"
  "python3-pip"
  "python3-venv"
)

# Command line arguments
NO_DOCKER=false
SKIP_DEPS=false

# Color codes for terminal output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[0;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

#==============================================================================
# Utility Functions
#==============================================================================

# Create log directory if it doesn't exist
mkdir -p "$(dirname "${LOG_FILE}")"

# Log message to both console and log file
log() {
  local level=$1
  local message=$2
  local color=$NC
  
  case $level in
    "INFO") color=$GREEN ;;
    "WARN") color=$YELLOW ;;
    "ERROR") color=$RED ;;
    "DEBUG") color=$BLUE ;;
  esac
  
  echo -e "${color}[$(date '+%Y-%m-%d %H:%M:%S')] [${level}] ${message}${NC}" | tee -a "${LOG_FILE}"
}

# Log error and exit
error_exit() {
  log "ERROR" "$1"
  exit 1
}

# Display help message
show_help() {
  cat << EOF
NeuroCognitive Architecture (NCA) Development Environment Setup

Usage:
  ./scripts/development/setup.sh [OPTIONS]

Options:
  --no-docker    Skip Docker setup
  --skip-deps    Skip system dependency installation
  --help         Display this help message

This script sets up a complete development environment for the NCA project.
EOF
  exit 0
}

# Check if command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Check version meets minimum requirement
# Args: current_version min_version
version_meets_minimum() {
  local current=$1
  local minimum=$2
  
  # Remove any leading non-numeric characters (like 'v')
  current=$(echo "$current" | sed 's/^[^0-9]*//')
  minimum=$(echo "$minimum" | sed 's/^[^0-9]*//')
  
  # Compare versions
  if [ "$(printf '%s\n' "$minimum" "$current" | sort -V | head -n1)" = "$minimum" ]; then
    return 0 # Current version is >= minimum
  else
    return 1 # Current version is < minimum
  fi
}

# Parse command line arguments
parse_args() {
  while [[ $# -gt 0 ]]; do
    case $1 in
      --no-docker)
        NO_DOCKER=true
        shift
        ;;
      --skip-deps)
        SKIP_DEPS=true
        shift
        ;;
      --help)
        show_help
        ;;
      *)
        log "ERROR" "Unknown option: $1"
        show_help
        ;;
    esac
  done
}

#==============================================================================
# System Dependency Installation
#==============================================================================

# Check and install system dependencies
install_system_dependencies() {
  if [ "$SKIP_DEPS" = true ]; then
    log "INFO" "Skipping system dependency installation as requested"
    return 0
  fi
  
  log "INFO" "Checking system dependencies..."
  
  # Detect OS
  if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
  elif command_exists sw_vers; then
    OS="macos"
  else
    error_exit "Unsupported operating system. Please install dependencies manually."
  fi
  
  case $OS in
    "ubuntu"|"debian")
      log "INFO" "Detected Debian-based system. Installing dependencies..."
      sudo apt-get update || error_exit "Failed to update package lists"
      sudo apt-get install -y "${REQUIRED_SYSTEM_PACKAGES[@]}" || error_exit "Failed to install required packages"
      ;;
    "fedora"|"rhel"|"centos")
      log "INFO" "Detected Red Hat-based system. Installing dependencies..."
      sudo dnf check-update || true  # This command returns non-zero if updates are available
      sudo dnf install -y "${REQUIRED_SYSTEM_PACKAGES[@]}" || error_exit "Failed to install required packages"
      ;;
    "macos")
      log "INFO" "Detected macOS. Checking for Homebrew..."
      if ! command_exists brew; then
        log "INFO" "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || error_exit "Failed to install Homebrew"
      fi
      
      log "INFO" "Installing dependencies with Homebrew..."
      brew update || error_exit "Failed to update Homebrew"
      brew install python@3.9 git curl make || error_exit "Failed to install required packages"
      ;;
    *)
      error_exit "Unsupported operating system: $OS. Please install dependencies manually."
      ;;
  esac
  
  log "INFO" "System dependencies installed successfully"
}

#==============================================================================
# Python Environment Setup
#==============================================================================

# Check Python version
check_python_version() {
  if ! command_exists python3; then
    error_exit "Python 3 is not installed. Please install Python $MIN_PYTHON_VERSION or higher."
  fi
  
  local python_version=$(python3 --version | cut -d ' ' -f 2)
  log "INFO" "Detected Python version: $python_version"
  
  if ! version_meets_minimum "$python_version" "$MIN_PYTHON_VERSION"; then
    error_exit "Python version $python_version is below the required minimum $MIN_PYTHON_VERSION"
  fi
}

# Set up Python virtual environment
setup_python_environment() {
  log "INFO" "Setting up Python virtual environment..."
  
  # Create virtual environment if it doesn't exist
  if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR" || error_exit "Failed to create virtual environment"
    log "INFO" "Created virtual environment at $VENV_DIR"
  else
    log "INFO" "Virtual environment already exists at $VENV_DIR"
  fi
  
  # Activate virtual environment
  # shellcheck disable=SC1091
  source "${VENV_DIR}/bin/activate" || error_exit "Failed to activate virtual environment"
  
  # Upgrade pip
  pip install --upgrade pip || error_exit "Failed to upgrade pip"
  
  # Install Poetry if not already installed
  if ! command_exists poetry; then
    log "INFO" "Installing Poetry..."
    pip install poetry || error_exit "Failed to install Poetry"
  else
    log "INFO" "Poetry is already installed"
  fi
  
  # Install project dependencies using Poetry
  log "INFO" "Installing project dependencies with Poetry..."
  cd "$PROJECT_ROOT"
  poetry install || error_exit "Failed to install project dependencies"
  
  log "INFO" "Python environment setup completed successfully"
}

#==============================================================================
# Pre-commit Hooks Setup
#==============================================================================

# Set up pre-commit hooks
setup_precommit_hooks() {
  log "INFO" "Setting up pre-commit hooks..."
  
  if [ ! -f "${PROJECT_ROOT}/.pre-commit-config.yaml" ]; then
    error_exit "Pre-commit configuration file not found at ${PROJECT_ROOT}/.pre-commit-config.yaml"
  fi
  
  # Install pre-commit if not already installed
  if ! command_exists pre-commit; then
    pip install pre-commit || error_exit "Failed to install pre-commit"
  fi
  
  # Install the git hook scripts
  cd "$PROJECT_ROOT"
  pre-commit install || error_exit "Failed to install pre-commit hooks"
  
  log "INFO" "Pre-commit hooks installed successfully"
}

#==============================================================================
# Docker Environment Setup
#==============================================================================

# Check Docker installation
check_docker() {
  if [ "$NO_DOCKER" = true ]; then
    log "INFO" "Skipping Docker setup as requested"
    return 0
  fi
  
  log "INFO" "Checking Docker installation..."
  
  if ! command_exists docker; then
    log "WARN" "Docker is not installed. Some features may not work properly."
    log "INFO" "Please install Docker from https://docs.docker.com/get-docker/"
    return 1
  fi
  
  local docker_version=$(docker --version | cut -d ' ' -f 3 | sed 's/,//')
  log "INFO" "Detected Docker version: $docker_version"
  
  if ! version_meets_minimum "$docker_version" "$MIN_DOCKER_VERSION"; then
    log "WARN" "Docker version $docker_version is below the recommended minimum $MIN_DOCKER_VERSION"
  fi
  
  if ! command_exists docker-compose; then
    log "WARN" "Docker Compose is not installed. Some features may not work properly."
    log "INFO" "Please install Docker Compose from https://docs.docker.com/compose/install/"
    return 1
  fi
  
  local compose_version=$(docker-compose --version | cut -d ' ' -f 3 | sed 's/,//')
  log "INFO" "Detected Docker Compose version: $compose_version"
  
  if ! version_meets_minimum "$compose_version" "$MIN_DOCKER_COMPOSE_VERSION"; then
    log "WARN" "Docker Compose version $compose_version is below the recommended minimum $MIN_DOCKER_COMPOSE_VERSION"
  fi
  
  return 0
}

# Set up Docker environment
setup_docker_environment() {
  if [ "$NO_DOCKER" = true ]; then
    return 0
  fi
  
  if ! check_docker; then
    log "WARN" "Skipping Docker environment setup due to missing prerequisites"
    return 1
  fi
  
  log "INFO" "Setting up Docker environment..."
  
  # Check if docker-compose.yml exists
  if [ ! -f "${PROJECT_ROOT}/docker-compose.yml" ]; then
    error_exit "Docker Compose file not found at ${PROJECT_ROOT}/docker-compose.yml"
  fi
  
  # Create .env file from example if it doesn't exist
  if [ ! -f "${PROJECT_ROOT}/.env" ] && [ -f "${PROJECT_ROOT}/.env.example" ]; then
    log "INFO" "Creating .env file from example..."
    cp "${PROJECT_ROOT}/.env.example" "${PROJECT_ROOT}/.env" || error_exit "Failed to create .env file"
    log "INFO" "Created .env file. Please review and update the values as needed."
  fi
  
  # Build Docker images
  log "INFO" "Building Docker images..."
  cd "$PROJECT_ROOT"
  docker-compose build || error_exit "Failed to build Docker images"
  
  log "INFO" "Docker environment setup completed successfully"
}

#==============================================================================
# Database Initialization
#==============================================================================

# Initialize database
initialize_database() {
  log "INFO" "Initializing database..."
  
  # Check if we're using Docker for database
  if [ "$NO_DOCKER" = false ] && [ -f "${PROJECT_ROOT}/docker-compose.yml" ]; then
    log "INFO" "Starting database container..."
    cd "$PROJECT_ROOT"
    docker-compose up -d db || error_exit "Failed to start database container"
    
    # Wait for database to be ready
    log "INFO" "Waiting for database to be ready..."
    sleep 5
  fi
  
  # Run database migrations
  log "INFO" "Running database migrations..."
  cd "$PROJECT_ROOT"
  
  # Check if we have a db directory with migrations
  if [ -d "${PROJECT_ROOT}/db/migrations" ]; then
    # Activate virtual environment if not already activated
    if [ -z "$VIRTUAL_ENV" ]; then
      # shellcheck disable=SC1091
      source "${VENV_DIR}/bin/activate" || error_exit "Failed to activate virtual environment"
    fi
    
    # Run migrations (assuming we have a command for this)
    python -m neuroca.db.migrate || error_exit "Failed to run database migrations"
  else
    log "INFO" "No database migrations found. Skipping this step."
  fi
  
  log "INFO" "Database initialization completed successfully"
}

#==============================================================================
# Configuration Setup
#==============================================================================

# Set up configuration files
setup_configuration() {
  log "INFO" "Setting up configuration files..."
  
  # Create config directory if it doesn't exist
  mkdir -p "$CONFIG_DIR"
  
  # Create default configuration files if they don't exist
  if [ ! -f "${CONFIG_DIR}/development.yaml" ]; then
    log "INFO" "Creating default development configuration..."
    cat > "${CONFIG_DIR}/development.yaml" << EOF
# NeuroCognitive Architecture (NCA) Development Configuration

# Database configuration
database:
  host: localhost
  port: 5432
  name: neuroca_dev
  user: neuroca
  password: neuroca_dev_password

# API configuration
api:
  host: 0.0.0.0
  port: 8000
  debug: true
  cors_origins:
    - http://localhost:3000
    - http://127.0.0.1:3000

# Memory system configuration
memory:
  working_memory:
    capacity: 10
  episodic_memory:
    retention_factor: 0.8
  semantic_memory:
    consolidation_threshold: 0.6

# Logging configuration
logging:
  level: DEBUG
  file: logs/neuroca.log
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# LLM integration configuration
llm:
  provider: openai
  model: gpt-4
  api_key: your_api_key_here
  temperature: 0.7
  max_tokens: 1000
EOF
    log "INFO" "Created default development configuration at ${CONFIG_DIR}/development.yaml"
  fi
  
  log "INFO" "Configuration setup completed successfully"
}

#==============================================================================
# Main Execution
#==============================================================================

main() {
  log "INFO" "Starting NeuroCognitive Architecture (NCA) development environment setup..."
  
  # Parse command line arguments
  parse_args "$@"
  
  # Change to project root directory
  cd "$PROJECT_ROOT"
  
  # Execute setup steps
  install_system_dependencies
  check_python_version
  setup_python_environment
  setup_precommit_hooks
  setup_docker_environment
  setup_configuration
  initialize_database
  
  log "INFO" "NeuroCognitive Architecture (NCA) development environment setup completed successfully!"
  log "INFO" "To activate the virtual environment, run: source ${VENV_DIR}/bin/activate"
  
  if [ "$NO_DOCKER" = false ]; then
    log "INFO" "To start the development environment with Docker, run: docker-compose up"
  fi
  
  log "INFO" "For more information, see the documentation in the docs/ directory"
}

# Execute main function with all arguments
main "$@"