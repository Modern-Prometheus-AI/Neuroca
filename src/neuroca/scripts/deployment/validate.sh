#!/usr/bin/env bash

#############################################################################
# NeuroCognitive Architecture (NCA) Deployment Validation Script
#
# This script performs comprehensive validation of the NCA deployment
# environment, checking for required dependencies, configuration integrity,
# connectivity to required services, and system resource availability.
#
# Usage:
#   ./validate.sh [--environment ENV] [--verbose] [--help]
#
# Options:
#   --environment ENV  Specify deployment environment (dev, staging, prod)
#   --verbose          Enable verbose output
#   --help             Display this help message
#
# Exit codes:
#   0 - All validation checks passed
#   1 - General error or invalid arguments
#   2 - Missing required dependencies
#   3 - Configuration validation failed
#   4 - Service connectivity issues
#   5 - Insufficient system resources
#   6 - Permission issues
#
# Author: NeuroCognitive Architecture Team
# Last updated: 2023
#############################################################################

set -o errexit  # Exit on error
set -o nounset  # Exit on unset variables
set -o pipefail # Exit if any command in a pipe fails

# Script constants
readonly SCRIPT_NAME=$(basename "$0")
readonly SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
readonly PROJECT_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd)
readonly LOG_FILE="${PROJECT_ROOT}/logs/deployment/validate_$(date +%Y%m%d_%H%M%S).log"
readonly CONFIG_DIR="${PROJECT_ROOT}/config"
readonly MIN_DISK_SPACE_MB=1024
readonly MIN_MEMORY_MB=2048
readonly REQUIRED_PORTS=(80 443 5432 6379)
readonly REQUIRED_COMMANDS=(docker docker-compose python3 pip curl jq)

# Default values
ENVIRONMENT="dev"
VERBOSE=false
SKIP_RESOURCE_CHECK=false

# Create log directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

#############################################################################
# Logging functions
#############################################################################

log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

log_info() {
    log "INFO" "$1"
}

log_warn() {
    log "WARNING" "$1" >&2
}

log_error() {
    log "ERROR" "$1" >&2
}

log_success() {
    log "SUCCESS" "$1"
}

log_debug() {
    if [[ "$VERBOSE" == true ]]; then
        log "DEBUG" "$1"
    fi
}

#############################################################################
# Helper functions
#############################################################################

print_help() {
    cat <<EOF
Usage: $SCRIPT_NAME [OPTIONS]

Validates the deployment environment for the NeuroCognitive Architecture system.

Options:
  --environment ENV  Specify deployment environment (dev, staging, prod)
  --verbose          Enable verbose output
  --skip-resources   Skip system resource validation checks
  --help             Display this help message

Examples:
  $SCRIPT_NAME --environment prod
  $SCRIPT_NAME --verbose
  $SCRIPT_NAME --environment staging --verbose

Exit codes:
  0 - All validation checks passed
  1 - General error or invalid arguments
  2 - Missing required dependencies
  3 - Configuration validation failed
  4 - Service connectivity issues
  5 - Insufficient system resources
  6 - Permission issues
EOF
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --environment)
                if [[ -z "${2:-}" ]]; then
                    log_error "Missing value for parameter: $1"
                    print_help
                    exit 1
                fi
                ENVIRONMENT="$2"
                shift 2
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --skip-resources)
                SKIP_RESOURCE_CHECK=true
                shift
                ;;
            --help)
                print_help
                exit 0
                ;;
            *)
                log_error "Unknown parameter: $1"
                print_help
                exit 1
                ;;
        esac
    done

    # Validate environment value
    if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
        log_error "Invalid environment: $ENVIRONMENT. Must be one of: dev, staging, prod"
        exit 1
    fi
}

check_root() {
    if [[ $EUID -ne 0 && "$ENVIRONMENT" == "prod" ]]; then
        log_warn "This script may need root privileges for some checks in production environment"
        log_warn "Consider running with sudo if validation fails due to permission issues"
    fi
}

#############################################################################
# Validation functions
#############################################################################

validate_dependencies() {
    log_info "Checking required dependencies..."
    local missing_deps=()

    for cmd in "${REQUIRED_COMMANDS[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
            log_error "Missing required command: $cmd"
        else
            log_debug "Found required command: $cmd ($(command -v "$cmd"))"
        fi
    done

    # Check Python version
    local python_version
    if python3 --version &> /dev/null; then
        python_version=$(python3 --version | awk '{print $2}')
        log_debug "Python version: $python_version"
        
        # Compare version numbers
        if [[ "$(printf '%s\n' "3.8" "$python_version" | sort -V | head -n1)" != "3.8" ]]; then
            log_warn "Python version $python_version may be too old. Recommended: >= 3.8"
        fi
    fi

    # Check Docker version
    if command -v docker &> /dev/null; then
        local docker_version
        docker_version=$(docker --version | awk '{print $3}' | tr -d ',')
        log_debug "Docker version: $docker_version"
    fi

    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        return 2
    fi

    log_success "All required dependencies are installed"
    return 0
}

validate_configuration() {
    log_info "Validating configuration files..."
    local config_errors=0

    # Check if config directory exists
    if [[ ! -d "$CONFIG_DIR" ]]; then
        log_error "Configuration directory not found: $CONFIG_DIR"
        return 3
    fi

    # Check environment-specific config file
    local env_config="$CONFIG_DIR/$ENVIRONMENT.yaml"
    if [[ ! -f "$env_config" ]]; then
        log_error "Environment config file not found: $env_config"
        config_errors=$((config_errors + 1))
    else
        log_debug "Found environment config: $env_config"
        
        # Basic YAML syntax validation
        if command -v python3 &> /dev/null; then
            if ! python3 -c "import yaml; yaml.safe_load(open('$env_config'))" &> /dev/null; then
                log_error "Invalid YAML syntax in config file: $env_config"
                config_errors=$((config_errors + 1))
            fi
        fi
    fi

    # Check for .env file
    local env_file="$PROJECT_ROOT/.env"
    if [[ ! -f "$env_file" ]]; then
        if [[ -f "$PROJECT_ROOT/.env.example" ]]; then
            log_warn "No .env file found, but .env.example exists. Consider creating .env from the example."
        else
            log_error "No .env or .env.example file found in project root"
            config_errors=$((config_errors + 1))
        fi
    else
        log_debug "Found .env file: $env_file"
        
        # Check for required environment variables
        local required_vars=("DATABASE_URL" "REDIS_URL" "SECRET_KEY")
        for var in "${required_vars[@]}"; do
            if ! grep -q "^$var=" "$env_file"; then
                log_warn "Missing recommended environment variable in .env: $var"
            fi
        done
    fi

    # Check Docker Compose file
    local docker_compose="$PROJECT_ROOT/docker-compose.yml"
    if [[ ! -f "$docker_compose" ]]; then
        log_error "Docker Compose file not found: $docker_compose"
        config_errors=$((config_errors + 1))
    else
        log_debug "Found Docker Compose file: $docker_compose"
        
        # Basic validation of docker-compose.yml
        if ! docker-compose -f "$docker_compose" config --quiet &> /dev/null; then
            log_error "Invalid Docker Compose configuration: $docker_compose"
            config_errors=$((config_errors + 1))
        fi
    fi

    if [[ $config_errors -gt 0 ]]; then
        log_error "Configuration validation failed with $config_errors errors"
        return 3
    fi

    log_success "Configuration validation passed"
    return 0
}

validate_connectivity() {
    log_info "Checking service connectivity..."
    local connectivity_errors=0

    # Check database connectivity if configured
    if [[ -f "$PROJECT_ROOT/.env" ]] && grep -q "^DATABASE_URL=" "$PROJECT_ROOT/.env"; then
        local db_url
        db_url=$(grep "^DATABASE_URL=" "$PROJECT_ROOT/.env" | cut -d= -f2-)
        log_debug "Testing database connectivity to: $db_url"
        
        # Extract host and port from DATABASE_URL
        if [[ "$db_url" =~ ://([^:]+):([0-9]+) ]]; then
            local db_host="${BASH_REMATCH[1]}"
            local db_port="${BASH_REMATCH[2]}"
            
            if ! timeout 5 bash -c ">/dev/tcp/$db_host/$db_port" &> /dev/null; then
                log_error "Cannot connect to database at $db_host:$db_port"
                connectivity_errors=$((connectivity_errors + 1))
            else
                log_debug "Successfully connected to database at $db_host:$db_port"
            fi
        else
            log_warn "Could not parse DATABASE_URL for connectivity check"
        fi
    fi

    # Check Redis connectivity if configured
    if [[ -f "$PROJECT_ROOT/.env" ]] && grep -q "^REDIS_URL=" "$PROJECT_ROOT/.env"; then
        local redis_url
        redis_url=$(grep "^REDIS_URL=" "$PROJECT_ROOT/.env" | cut -d= -f2-)
        log_debug "Testing Redis connectivity to: $redis_url"
        
        # Extract host and port from REDIS_URL
        if [[ "$redis_url" =~ ://([^:]+):([0-9]+) ]]; then
            local redis_host="${BASH_REMATCH[1]}"
            local redis_port="${BASH_REMATCH[2]}"
            
            if ! timeout 5 bash -c ">/dev/tcp/$redis_host/$redis_port" &> /dev/null; then
                log_error "Cannot connect to Redis at $redis_host:$redis_port"
                connectivity_errors=$((connectivity_errors + 1))
            else
                log_debug "Successfully connected to Redis at $redis_host:$redis_port"
            fi
        else
            log_warn "Could not parse REDIS_URL for connectivity check"
        fi
    fi

    # Check required ports availability on localhost
    log_debug "Checking if required ports are available on localhost..."
    for port in "${REQUIRED_PORTS[@]}"; do
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then
            log_debug "Port $port is already in use"
        else
            log_debug "Port $port is available"
        fi
    done

    # Check internet connectivity
    if ! curl -s --connect-timeout 5 https://www.google.com > /dev/null; then
        log_warn "Internet connectivity check failed"
        # Not counting as an error since local development might be offline
    else
        log_debug "Internet connectivity check passed"
    fi

    if [[ $connectivity_errors -gt 0 ]]; then
        log_error "Service connectivity validation failed with $connectivity_errors errors"
        return 4
    fi

    log_success "Service connectivity validation passed"
    return 0
}

validate_system_resources() {
    if [[ "$SKIP_RESOURCE_CHECK" == true ]]; then
        log_info "Skipping system resource validation as requested"
        return 0
    fi

    log_info "Validating system resources..."
    local resource_errors=0

    # Check disk space
    local available_disk
    available_disk=$(df -m "$PROJECT_ROOT" | awk 'NR==2 {print $4}')
    log_debug "Available disk space: ${available_disk}MB"
    
    if [[ $available_disk -lt $MIN_DISK_SPACE_MB ]]; then
        log_error "Insufficient disk space: ${available_disk}MB available, ${MIN_DISK_SPACE_MB}MB required"
        resource_errors=$((resource_errors + 1))
    fi

    # Check memory
    if command -v free &> /dev/null; then
        local available_memory
        available_memory=$(free -m | awk '/^Mem:/ {print $7}')
        log_debug "Available memory: ${available_memory}MB"
        
        if [[ $available_memory -lt $MIN_MEMORY_MB ]]; then
            log_error "Insufficient memory: ${available_memory}MB available, ${MIN_MEMORY_MB}MB required"
            resource_errors=$((resource_errors + 1))
        fi
    else
        log_warn "Cannot check available memory: 'free' command not available"
    fi

    # Check CPU load
    if command -v uptime &> /dev/null; then
        local load
        load=$(uptime | awk -F'[a-z]:' '{ print $2}' | awk -F',' '{ print $1}' | tr -d ' ')
        local cpu_count
        cpu_count=$(nproc 2>/dev/null || echo 1)
        log_debug "Current CPU load: $load (on $cpu_count cores)"
        
        # Warning if load is higher than number of cores
        if (( $(echo "$load > $cpu_count" | bc -l) )); then
            log_warn "High CPU load detected: $load (on $cpu_count cores)"
        fi
    else
        log_warn "Cannot check CPU load: 'uptime' command not available"
    fi

    # Check for Docker resource constraints in production
    if [[ "$ENVIRONMENT" == "prod" ]] && command -v docker &> /dev/null; then
        if ! docker info 2>/dev/null | grep -q "Memory Limit: true"; then
            log_warn "Docker memory limits not enabled. Recommended for production deployments."
        fi
    fi

    if [[ $resource_errors -gt 0 ]]; then
        log_error "System resource validation failed with $resource_errors errors"
        return 5
    fi

    log_success "System resource validation passed"
    return 0
}

validate_permissions() {
    log_info "Checking file and directory permissions..."
    local permission_errors=0

    # Check write permissions to key directories
    local dirs_to_check=(
        "$PROJECT_ROOT/logs"
        "$PROJECT_ROOT/db"
        "$PROJECT_ROOT/config"
    )

    for dir in "${dirs_to_check[@]}"; do
        if [[ -d "$dir" ]]; then
            if [[ ! -w "$dir" ]]; then
                log_error "No write permission to directory: $dir"
                permission_errors=$((permission_errors + 1))
            else
                log_debug "Write permission confirmed for: $dir"
            fi
        else
            log_debug "Directory does not exist (will be created if needed): $dir"
        fi
    done

    # Check executable permissions for scripts
    local scripts_dir="$PROJECT_ROOT/scripts"
    if [[ -d "$scripts_dir" ]]; then
        while IFS= read -r script; do
            if [[ ! -x "$script" ]]; then
                log_warn "Script is not executable: $script"
                # Attempt to fix if we have permission
                if [[ -w "$script" ]]; then
                    chmod +x "$script"
                    log_info "Fixed permissions for: $script"
                else
                    permission_errors=$((permission_errors + 1))
                fi
            fi
        done < <(find "$scripts_dir" -name "*.sh")
    fi

    # Check Docker socket permissions if using Docker
    if [[ -S /var/run/docker.sock ]]; then
        if [[ ! -r /var/run/docker.sock ]]; then
            log_warn "No read permission to Docker socket. Docker operations may fail."
            if [[ "$ENVIRONMENT" == "prod" ]]; then
                permission_errors=$((permission_errors + 1))
            fi
        else
            log_debug "Docker socket is accessible"
        fi
    fi

    if [[ $permission_errors -gt 0 ]]; then
        log_error "Permission validation failed with $permission_errors errors"
        return 6
    fi

    log_success "Permission validation passed"
    return 0
}

#############################################################################
# Main execution
#############################################################################

main() {
    log_info "Starting deployment validation for environment: $ENVIRONMENT"
    log_info "Validation log will be saved to: $LOG_FILE"
    
    local exit_code=0
    local validation_results=()
    
    # Run validation checks
    if ! validate_dependencies; then
        validation_results+=("Dependencies: FAILED")
        exit_code=2
    else
        validation_results+=("Dependencies: PASSED")
    fi
    
    if ! validate_configuration; then
        validation_results+=("Configuration: FAILED")
        [[ $exit_code -eq 0 ]] && exit_code=3
    else
        validation_results+=("Configuration: PASSED")
    fi
    
    if ! validate_connectivity; then
        validation_results+=("Connectivity: FAILED")
        [[ $exit_code -eq 0 ]] && exit_code=4
    else
        validation_results+=("Connectivity: PASSED")
    fi
    
    if ! validate_system_resources; then
        validation_results+=("System Resources: FAILED")
        [[ $exit_code -eq 0 ]] && exit_code=5
    else
        validation_results+=("System Resources: PASSED")
    fi
    
    if ! validate_permissions; then
        validation_results+=("Permissions: FAILED")
        [[ $exit_code -eq 0 ]] && exit_code=6
    else
        validation_results+=("Permissions: PASSED")
    fi
    
    # Print summary
    log_info "Validation Summary:"
    for result in "${validation_results[@]}"; do
        log_info "  $result"
    done
    
    if [[ $exit_code -eq 0 ]]; then
        log_success "All validation checks passed successfully!"
        log_info "The environment is ready for deployment."
    else
        log_error "Validation failed with exit code $exit_code"
        log_info "Please fix the reported issues before proceeding with deployment."
    fi
    
    log_info "Detailed validation log available at: $LOG_FILE"
    return $exit_code
}

# Parse command line arguments
parse_args "$@"

# Check if running as root (for production)
check_root

# Execute main function
main

exit $?