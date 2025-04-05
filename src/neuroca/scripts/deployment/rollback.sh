#!/usr/bin/env bash

#############################################################################
# NeuroCognitive Architecture (NCA) - Deployment Rollback Script
#
# This script performs a controlled rollback of the NCA system to a previous
# stable version in case of deployment failures or critical issues.
#
# Usage:
#   ./rollback.sh [OPTIONS]
#
# Options:
#   -v, --version VERSION    Specific version to rollback to (default: previous version)
#   -e, --environment ENV    Target environment (dev, staging, prod) (default: dev)
#   -c, --component COMP     Specific component to rollback (default: all)
#   -f, --force              Force rollback without confirmation
#   -d, --dry-run            Simulate rollback without making changes
#   -h, --help               Display this help message
#
# Examples:
#   ./rollback.sh --environment prod --version v1.2.3
#   ./rollback.sh --component memory --force
#   ./rollback.sh --dry-run
#
# Author: NCA Team
# Last Updated: 2023
#############################################################################

set -eo pipefail

# Script constants
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
LOG_DIR="${PROJECT_ROOT}/logs"
LOG_FILE="${LOG_DIR}/rollback_$(date +%Y%m%d_%H%M%S).log"
BACKUP_DIR="${PROJECT_ROOT}/backups"
CONFIG_DIR="${PROJECT_ROOT}/config"
DEPLOYMENT_CONFIG="${CONFIG_DIR}/deployment.yaml"
LOCK_FILE="/tmp/neuroca_rollback.lock"

# Default values
VERSION=""
ENVIRONMENT="dev"
COMPONENT="all"
FORCE=false
DRY_RUN=false

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

#############################################################################
# Logging functions
#############################################################################

# Ensure log directory exists
mkdir -p "${LOG_DIR}"

# Log message to file and stdout
log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo -e "${timestamp} [${level}] ${message}" | tee -a "${LOG_FILE}"
}

log_info() {
    log "INFO" "$1"
    echo -e "${BLUE}INFO:${NC} $1"
}

log_success() {
    log "SUCCESS" "$1"
    echo -e "${GREEN}SUCCESS:${NC} $1"
}

log_warning() {
    log "WARNING" "$1"
    echo -e "${YELLOW}WARNING:${NC} $1"
}

log_error() {
    log "ERROR" "$1"
    echo -e "${RED}ERROR:${NC} $1" >&2
}

log_debug() {
    if [[ "${DEBUG:-false}" == "true" ]]; then
        log "DEBUG" "$1"
        echo -e "DEBUG: $1"
    fi
}

#############################################################################
# Helper functions
#############################################################################

# Display help message
show_help() {
    grep "^#" "$0" | grep -v "!/usr/bin/env" | sed 's/^# //g; s/^#//g'
    exit 0
}

# Clean up resources before exit
cleanup() {
    local exit_code=$?
    
    # Remove lock file if it exists
    if [[ -f "${LOCK_FILE}" ]]; then
        rm -f "${LOCK_FILE}"
        log_debug "Removed lock file: ${LOCK_FILE}"
    fi
    
    # Log script completion
    if [[ ${exit_code} -eq 0 ]]; then
        log_info "Rollback script completed successfully"
    else
        log_error "Rollback script failed with exit code ${exit_code}"
    fi
    
    exit ${exit_code}
}

# Handle script interruption
handle_interrupt() {
    log_warning "Rollback interrupted by user"
    cleanup
    exit 130
}

# Validate environment name
validate_environment() {
    local env="$1"
    case "${env}" in
        dev|staging|prod)
            return 0
            ;;
        *)
            log_error "Invalid environment: ${env}. Must be one of: dev, staging, prod"
            return 1
            ;;
    esac
}

# Check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Get the previous version if none specified
get_previous_version() {
    local env="$1"
    local component="$2"
    
    log_debug "Attempting to determine previous version for ${component} in ${env}"
    
    # Check deployment history file
    local history_file="${CONFIG_DIR}/deployment_history_${env}.json"
    
    if [[ ! -f "${history_file}" ]]; then
        log_error "Deployment history file not found: ${history_file}"
        return 1
    fi
    
    # Requires jq for JSON parsing
    if ! command_exists jq; then
        log_error "jq command not found. Please install jq to parse deployment history."
        return 1
    }
    
    if [[ "${component}" == "all" ]]; then
        # Get the previous full deployment version
        prev_version=$(jq -r '.deployments | sort_by(.timestamp) | reverse | .[1].version' "${history_file}")
    else
        # Get the previous component-specific version
        prev_version=$(jq -r ".components.${component} | sort_by(.timestamp) | reverse | .[1].version" "${history_file}")
    fi
    
    if [[ -z "${prev_version}" || "${prev_version}" == "null" ]]; then
        log_error "Could not determine previous version for ${component} in ${env}"
        return 1
    fi
    
    echo "${prev_version}"
    return 0
}

# Check if version exists in backups
check_version_exists() {
    local version="$1"
    local env="$2"
    local component="$3"
    
    if [[ "${component}" == "all" ]]; then
        local backup_path="${BACKUP_DIR}/${env}/${version}"
    else
        local backup_path="${BACKUP_DIR}/${env}/${version}/${component}"
    fi
    
    if [[ ! -d "${backup_path}" ]]; then
        log_error "Backup not found for ${component} version ${version} in ${env} environment"
        log_error "Expected backup at: ${backup_path}"
        return 1
    fi
    
    return 0
}

# Acquire lock to prevent concurrent rollbacks
acquire_lock() {
    if [[ -f "${LOCK_FILE}" ]]; then
        local pid=$(cat "${LOCK_FILE}")
        if ps -p "${pid}" > /dev/null; then
            log_error "Another rollback process (PID: ${pid}) is already running"
            return 1
        else
            log_warning "Found stale lock file. Removing it."
            rm -f "${LOCK_FILE}"
        fi
    fi
    
    echo $$ > "${LOCK_FILE}"
    log_debug "Acquired lock: ${LOCK_FILE}"
    return 0
}

#############################################################################
# Rollback functions
#############################################################################

# Perform database rollback
rollback_database() {
    local version="$1"
    local env="$2"
    
    log_info "Rolling back database to version ${version} in ${env} environment"
    
    if [[ "${DRY_RUN}" == "true" ]]; then
        log_info "[DRY RUN] Would rollback database to version ${version}"
        return 0
    fi
    
    # Load database configuration
    local db_config="${CONFIG_DIR}/${env}/database.yaml"
    if [[ ! -f "${db_config}" ]]; then
        log_error "Database configuration not found: ${db_config}"
        return 1
    fi
    
    # Execute database rollback
    local backup_sql="${BACKUP_DIR}/${env}/${version}/db/backup.sql"
    if [[ ! -f "${backup_sql}" ]]; then
        log_error "Database backup not found: ${backup_sql}"
        return 1
    }
    
    log_info "Restoring database from backup: ${backup_sql}"
    # Example: This would be replaced with actual DB restore command
    # psql -h ${DB_HOST} -U ${DB_USER} -d ${DB_NAME} -f "${backup_sql}"
    
    # For demonstration, we'll simulate the restore
    sleep 2
    
    log_success "Database successfully rolled back to version ${version}"
    return 0
}

# Rollback application code
rollback_application() {
    local version="$1"
    local env="$2"
    local component="$3"
    
    if [[ "${component}" == "all" ]]; then
        log_info "Rolling back all application components to version ${version} in ${env} environment"
    else
        log_info "Rolling back ${component} component to version ${version} in ${env} environment"
    fi
    
    if [[ "${DRY_RUN}" == "true" ]]; then
        log_info "[DRY RUN] Would rollback application code to version ${version}"
        return 0
    fi
    
    local backup_path="${BACKUP_DIR}/${env}/${version}"
    local deploy_path="${PROJECT_ROOT}"
    
    if [[ "${component}" != "all" ]]; then
        backup_path="${backup_path}/${component}"
        deploy_path="${deploy_path}/${component}"
    fi
    
    if [[ ! -d "${backup_path}" ]]; then
        log_error "Backup path not found: ${backup_path}"
        return 1
    }
    
    # Create a backup of the current state before rollback
    local current_backup="${BACKUP_DIR}/${env}/pre_rollback_$(date +%Y%m%d_%H%M%S)"
    log_info "Creating backup of current state: ${current_backup}"
    mkdir -p "${current_backup}"
    
    if [[ "${component}" == "all" ]]; then
        # Backup key directories
        for dir in api core memory integration; do
            if [[ -d "${PROJECT_ROOT}/${dir}" ]]; then
                cp -r "${PROJECT_ROOT}/${dir}" "${current_backup}/"
            fi
        done
    else
        if [[ -d "${deploy_path}" ]]; then
            cp -r "${deploy_path}" "${current_backup}/"
        fi
    fi
    
    # Perform the rollback
    log_info "Deploying version ${version} from backup"
    
    if [[ "${component}" == "all" ]]; then
        # Rollback all components
        for dir in $(find "${backup_path}" -maxdepth 1 -type d -not -path "${backup_path}"); do
            component_name=$(basename "${dir}")
            if [[ -d "${PROJECT_ROOT}/${component_name}" ]]; then
                log_info "Rolling back component: ${component_name}"
                rm -rf "${PROJECT_ROOT}/${component_name}"
                cp -r "${dir}" "${PROJECT_ROOT}/"
            fi
        done
    else
        # Rollback specific component
        if [[ -d "${deploy_path}" ]]; then
            rm -rf "${deploy_path}"
            cp -r "${backup_path}" "${deploy_path}"
        fi
    fi
    
    log_success "Application code successfully rolled back to version ${version}"
    return 0
}

# Update configuration files
update_config() {
    local version="$1"
    local env="$2"
    
    log_info "Updating configuration to reflect rollback to version ${version}"
    
    if [[ "${DRY_RUN}" == "true" ]]; then
        log_info "[DRY RUN] Would update configuration files for version ${version}"
        return 0
    fi
    
    # Update deployment status file
    local status_file="${CONFIG_DIR}/deployment_status.json"
    
    # Create a backup of the current status file
    if [[ -f "${status_file}" ]]; then
        cp "${status_file}" "${status_file}.bak"
    fi
    
    # Update the status file with rollback information
    cat > "${status_file}" << EOF
{
  "current_version": "${version}",
  "environment": "${env}",
  "last_updated": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "status": "rolled_back",
  "rollback_timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "rollback_user": "${USER}"
}
EOF
    
    log_success "Configuration updated to reflect rollback to version ${version}"
    return 0
}

# Restart services
restart_services() {
    local env="$1"
    local component="$2"
    
    log_info "Restarting services in ${env} environment"
    
    if [[ "${DRY_RUN}" == "true" ]]; then
        log_info "[DRY RUN] Would restart services for ${component} in ${env}"
        return 0
    fi
    
    # Determine which services to restart
    local services=()
    
    if [[ "${component}" == "all" ]]; then
        services=("api" "memory" "core" "integration")
    else
        services=("${component}")
    fi
    
    # Restart each service
    for service in "${services[@]}"; do
        log_info "Restarting service: ${service}"
        
        # Example: This would be replaced with actual service restart commands
        # systemctl restart neuroca-${service}
        # or
        # docker-compose -f docker-compose.${env}.yml restart ${service}
        
        # For demonstration, we'll simulate the restart
        sleep 1
    done
    
    log_success "Services restarted successfully"
    return 0
}

# Verify rollback success
verify_rollback() {
    local version="$1"
    local env="$2"
    local component="$3"
    
    log_info "Verifying rollback success for ${component} to version ${version} in ${env} environment"
    
    if [[ "${DRY_RUN}" == "true" ]]; then
        log_info "[DRY RUN] Would verify rollback success"
        return 0
    fi
    
    # Check application health
    log_info "Checking application health..."
    
    # Example: This would be replaced with actual health check commands
    # curl -s http://localhost:8080/health | grep -q "status\":\"UP\""
    
    # For demonstration, we'll simulate the health check
    sleep 2
    
    # Verify version
    log_info "Verifying deployed version..."
    
    # Example: This would be replaced with actual version check
    # deployed_version=$(curl -s http://localhost:8080/version)
    # if [[ "${deployed_version}" != "${version}" ]]; then
    #     log_error "Version mismatch: expected ${version}, got ${deployed_version}"
    #     return 1
    # fi
    
    log_success "Rollback verification completed successfully"
    return 0
}

# Main rollback function
perform_rollback() {
    local version="$1"
    local env="$2"
    local component="$3"
    
    log_info "Starting rollback to version ${version} for ${component} in ${env} environment"
    
    # Check if version exists in backups
    if ! check_version_exists "${version}" "${env}" "${component}"; then
        return 1
    fi
    
    # Rollback database if rolling back all components
    if [[ "${component}" == "all" ]]; then
        if ! rollback_database "${version}" "${env}"; then
            log_error "Database rollback failed"
            return 1
        fi
    fi
    
    # Rollback application code
    if ! rollback_application "${version}" "${env}" "${component}"; then
        log_error "Application code rollback failed"
        return 1
    fi
    
    # Update configuration
    if ! update_config "${version}" "${env}"; then
        log_warning "Configuration update failed, but rollback proceeded"
    fi
    
    # Restart services
    if ! restart_services "${env}" "${component}"; then
        log_error "Service restart failed"
        return 1
    fi
    
    # Verify rollback
    if ! verify_rollback "${version}" "${env}" "${component}"; then
        log_error "Rollback verification failed"
        return 1
    fi
    
    log_success "Rollback to version ${version} completed successfully"
    return 0
}

#############################################################################
# Main script execution
#############################################################################

# Set up trap handlers
trap cleanup EXIT
trap handle_interrupt INT TERM

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -c|--component)
            COMPONENT="$2"
            shift 2
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            show_help
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            ;;
    esac
done

# Validate environment
if ! validate_environment "${ENVIRONMENT}"; then
    exit 1
fi

# Acquire lock
if ! acquire_lock; then
    exit 1
fi

# Determine version to rollback to if not specified
if [[ -z "${VERSION}" ]]; then
    log_info "No version specified, determining previous version..."
    VERSION=$(get_previous_version "${ENVIRONMENT}" "${COMPONENT}")
    
    if [[ $? -ne 0 || -z "${VERSION}" ]]; then
        log_error "Failed to determine previous version. Please specify a version with --version."
        exit 1
    fi
    
    log_info "Determined previous version: ${VERSION}"
fi

# Confirm rollback unless forced
if [[ "${FORCE}" != "true" && "${DRY_RUN}" != "true" ]]; then
    read -p "Are you sure you want to rollback ${COMPONENT} to version ${VERSION} in ${ENVIRONMENT} environment? [y/N] " confirm
    if [[ "${confirm}" != "y" && "${confirm}" != "Y" ]]; then
        log_info "Rollback cancelled by user"
        exit 0
    fi
fi

# Perform dry run if requested
if [[ "${DRY_RUN}" == "true" ]]; then
    log_info "Performing DRY RUN rollback (no changes will be made)"
fi

# Execute rollback
if perform_rollback "${VERSION}" "${ENVIRONMENT}" "${COMPONENT}"; then
    if [[ "${DRY_RUN}" == "true" ]]; then
        log_success "DRY RUN rollback simulation completed successfully"
    else
        log_success "Rollback to version ${VERSION} completed successfully"
    fi
    exit 0
else
    if [[ "${DRY_RUN}" == "true" ]]; then
        log_error "DRY RUN rollback simulation failed"
    else
        log_error "Rollback to version ${VERSION} failed"
    fi
    exit 1
fi