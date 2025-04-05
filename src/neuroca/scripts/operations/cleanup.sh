#!/usr/bin/env bash

###############################################################################
# NeuroCognitive Architecture (NCA) - Cleanup Script
# 
# This script performs comprehensive cleanup operations for the NeuroCognitive
# Architecture project, including:
#   - Removing temporary files and directories
#   - Cleaning up Docker resources
#   - Purging logs beyond retention period
#   - Removing orphaned data
#   - Cleaning up database backups beyond retention period
#
# Usage:
#   ./cleanup.sh [options]
#
# Options:
#   -h, --help              Display this help message
#   -v, --verbose           Enable verbose output
#   -d, --dry-run           Show what would be done without actually doing it
#   -f, --force             Skip confirmation prompts
#   --logs-only             Clean only log files
#   --docker-only           Clean only Docker resources
#   --temp-only             Clean only temporary files
#   --db-only               Clean only database backups
#   --retention=DAYS        Override default retention period (default: 30 days)
#
# Exit codes:
#   0 - Success
#   1 - General error
#   2 - Invalid arguments
#   3 - Required tools missing
#   4 - Permission error
#
# Author: NeuroCognitive Architecture Team
# Date: 2023
###############################################################################

set -eo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../" && pwd)"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
LOG_FILE="${PROJECT_ROOT}/logs/operations/cleanup_${TIMESTAMP}.log"
DEFAULT_RETENTION_DAYS=30
RETENTION_DAYS=${DEFAULT_RETENTION_DAYS}

# Directories to clean
TEMP_DIR="${PROJECT_ROOT}/tmp"
LOG_DIR="${PROJECT_ROOT}/logs"
DB_BACKUP_DIR="${PROJECT_ROOT}/db/backups"
CACHE_DIR="${PROJECT_ROOT}/cache"

# Flags
VERBOSE=false
DRY_RUN=false
FORCE=false
CLEAN_LOGS=true
CLEAN_DOCKER=true
CLEAN_TEMP=true
CLEAN_DB=true

# Create log directory if it doesn't exist
mkdir -p "$(dirname "${LOG_FILE}")"

# Function to display usage information
usage() {
    grep "^# " "${BASH_SOURCE[0]}" | cut -c 3- | sed -n '/^Usage:/,/^$/p'
    exit 0
}

# Function for logging
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    
    # Log to file
    echo "[${timestamp}] [${level}] ${message}" >> "${LOG_FILE}"
    
    # Log to console if verbose or if level is ERROR
    if [[ "${VERBOSE}" == true ]] || [[ "${level}" == "ERROR" ]]; then
        if [[ "${level}" == "ERROR" ]]; then
            echo -e "\e[31m[${level}] ${message}\e[0m" >&2
        elif [[ "${level}" == "WARNING" ]]; then
            echo -e "\e[33m[${level}] ${message}\e[0m"
        elif [[ "${level}" == "SUCCESS" ]]; then
            echo -e "\e[32m[${level}] ${message}\e[0m"
        else
            echo "[${level}] ${message}"
        fi
    fi
}

# Function to check required tools
check_requirements() {
    local missing_tools=()
    
    for tool in docker find grep sed awk date; do
        if ! command -v "${tool}" &> /dev/null; then
            missing_tools+=("${tool}")
        fi
    done
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log "ERROR" "Required tools missing: ${missing_tools[*]}"
        log "ERROR" "Please install the missing tools and try again."
        exit 3
    fi
}

# Function to check if running as root or with sufficient permissions
check_permissions() {
    if [[ "${EUID}" -ne 0 ]]; then
        # Try to access key directories to check permissions
        if ! touch "${TEMP_DIR}/.permission_check" 2>/dev/null || \
           ! touch "${LOG_DIR}/.permission_check" 2>/dev/null; then
            log "WARNING" "Not running with root privileges and may not have sufficient permissions."
            log "WARNING" "Some cleanup operations might fail."
            
            if [[ "${FORCE}" != true ]]; then
                read -p "Continue anyway? (y/N): " confirm
                if [[ "${confirm}" != "y" && "${confirm}" != "Y" ]]; then
                    log "INFO" "Cleanup aborted by user."
                    exit 0
                fi
            fi
        else
            # Clean up test files
            rm -f "${TEMP_DIR}/.permission_check" "${LOG_DIR}/.permission_check"
        fi
    fi
}

# Function to clean temporary files and directories
clean_temp_files() {
    log "INFO" "Cleaning temporary files and directories..."
    
    # List of patterns to match temporary files
    local temp_patterns=(
        "*.tmp"
        "*.temp"
        "*.bak"
        "*.swp"
        ".DS_Store"
        "Thumbs.db"
        "__pycache__"
        "*.pyc"
        ".pytest_cache"
        ".coverage"
        "htmlcov"
    )
    
    # Find and remove temporary files
    for pattern in "${temp_patterns[@]}"; do
        if [[ "${DRY_RUN}" == true ]]; then
            log "INFO" "Would remove files matching pattern: ${pattern}"
            find "${PROJECT_ROOT}" -name "${pattern}" -type f -print
        else
            find "${PROJECT_ROOT}" -name "${pattern}" -type f -print | while read -r file; do
                log "INFO" "Removing temporary file: ${file}"
                rm -f "${file}" || log "WARNING" "Failed to remove file: ${file}"
            done
        fi
    done
    
    # Clean the dedicated temp directory
    if [[ -d "${TEMP_DIR}" ]]; then
        if [[ "${DRY_RUN}" == true ]]; then
            log "INFO" "Would clean temp directory: ${TEMP_DIR}"
        else
            log "INFO" "Cleaning temp directory: ${TEMP_DIR}"
            find "${TEMP_DIR}" -type f -mtime +${RETENTION_DAYS} -print | while read -r file; do
                log "INFO" "Removing old temp file: ${file}"
                rm -f "${file}" || log "WARNING" "Failed to remove file: ${file}"
            done
        fi
    else
        log "INFO" "Temp directory does not exist: ${TEMP_DIR}"
    fi
    
    # Clean the cache directory
    if [[ -d "${CACHE_DIR}" ]]; then
        if [[ "${DRY_RUN}" == true ]]; then
            log "INFO" "Would clean cache directory: ${CACHE_DIR}"
        else
            log "INFO" "Cleaning cache directory: ${CACHE_DIR}"
            find "${CACHE_DIR}" -type f -mtime +${RETENTION_DAYS} -print | while read -r file; do
                log "INFO" "Removing old cache file: ${file}"
                rm -f "${file}" || log "WARNING" "Failed to remove file: ${file}"
            done
        fi
    else
        log "INFO" "Cache directory does not exist: ${CACHE_DIR}"
    fi
    
    log "SUCCESS" "Temporary files cleanup completed."
}

# Function to clean log files
clean_logs() {
    log "INFO" "Cleaning log files older than ${RETENTION_DAYS} days..."
    
    if [[ -d "${LOG_DIR}" ]]; then
        if [[ "${DRY_RUN}" == true ]]; then
            log "INFO" "Would remove log files older than ${RETENTION_DAYS} days from: ${LOG_DIR}"
            find "${LOG_DIR}" -type f -name "*.log" -mtime +${RETENTION_DAYS} -print
        else
            find "${LOG_DIR}" -type f -name "*.log" -mtime +${RETENTION_DAYS} -print | while read -r file; do
                log "INFO" "Removing old log file: ${file}"
                rm -f "${file}" || log "WARNING" "Failed to remove log file: ${file}"
            done
            
            # Compress logs older than 7 days but younger than retention period
            find "${LOG_DIR}" -type f -name "*.log" -mtime +7 -mtime -${RETENTION_DAYS} -not -name "*.gz" -print | while read -r file; do
                log "INFO" "Compressing log file: ${file}"
                gzip -f "${file}" || log "WARNING" "Failed to compress log file: ${file}"
            done
        fi
    else
        log "INFO" "Log directory does not exist: ${LOG_DIR}"
    fi
    
    log "SUCCESS" "Log files cleanup completed."
}

# Function to clean Docker resources
clean_docker() {
    log "INFO" "Cleaning Docker resources..."
    
    if command -v docker &> /dev/null; then
        if [[ "${DRY_RUN}" == true ]]; then
            log "INFO" "Would remove unused Docker resources"
        else
            # Remove stopped containers related to the project
            log "INFO" "Removing stopped containers..."
            docker ps -a --filter "name=neuroca" --filter "status=exited" -q | xargs -r docker rm
            
            # Remove dangling images
            log "INFO" "Removing dangling images..."
            docker images -f "dangling=true" -q | xargs -r docker rmi
            
            # Remove unused volumes
            log "INFO" "Removing unused volumes..."
            docker volume ls -qf "dangling=true" | xargs -r docker volume rm
            
            # Remove unused networks
            log "INFO" "Removing unused networks..."
            docker network prune -f
        fi
    else
        log "WARNING" "Docker command not found, skipping Docker cleanup."
    fi
    
    log "SUCCESS" "Docker resources cleanup completed."
}

# Function to clean database backups
clean_db_backups() {
    log "INFO" "Cleaning database backups older than ${RETENTION_DAYS} days..."
    
    if [[ -d "${DB_BACKUP_DIR}" ]]; then
        if [[ "${DRY_RUN}" == true ]]; then
            log "INFO" "Would remove database backups older than ${RETENTION_DAYS} days from: ${DB_BACKUP_DIR}"
            find "${DB_BACKUP_DIR}" -type f \( -name "*.sql" -o -name "*.dump" -o -name "*.bak" -o -name "*.gz" \) -mtime +${RETENTION_DAYS} -print
        else
            find "${DB_BACKUP_DIR}" -type f \( -name "*.sql" -o -name "*.dump" -o -name "*.bak" -o -name "*.gz" \) -mtime +${RETENTION_DAYS} -print | while read -r file; do
                log "INFO" "Removing old database backup: ${file}"
                rm -f "${file}" || log "WARNING" "Failed to remove database backup: ${file}"
            done
        fi
    else
        log "INFO" "Database backup directory does not exist: ${DB_BACKUP_DIR}"
    fi
    
    log "SUCCESS" "Database backups cleanup completed."
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                usage
                ;;
            -v|--verbose)
                VERBOSE=true
                ;;
            -d|--dry-run)
                DRY_RUN=true
                ;;
            -f|--force)
                FORCE=true
                ;;
            --logs-only)
                CLEAN_DOCKER=false
                CLEAN_TEMP=false
                CLEAN_DB=false
                ;;
            --docker-only)
                CLEAN_LOGS=false
                CLEAN_TEMP=false
                CLEAN_DB=false
                ;;
            --temp-only)
                CLEAN_LOGS=false
                CLEAN_DOCKER=false
                CLEAN_DB=false
                ;;
            --db-only)
                CLEAN_LOGS=false
                CLEAN_DOCKER=false
                CLEAN_TEMP=false
                ;;
            --retention=*)
                RETENTION_DAYS="${1#*=}"
                if ! [[ "${RETENTION_DAYS}" =~ ^[0-9]+$ ]]; then
                    log "ERROR" "Invalid retention period: ${RETENTION_DAYS}. Must be a positive integer."
                    exit 2
                fi
                ;;
            *)
                log "ERROR" "Unknown option: $1"
                usage
                exit 2
                ;;
        esac
        shift
    done
}

# Main function
main() {
    log "INFO" "Starting cleanup process..."
    log "INFO" "Project root: ${PROJECT_ROOT}"
    log "INFO" "Retention period: ${RETENTION_DAYS} days"
    
    if [[ "${DRY_RUN}" == true ]]; then
        log "INFO" "Running in DRY RUN mode. No files will be actually removed."
    fi
    
    # Check requirements
    check_requirements
    
    # Check permissions
    check_permissions
    
    # Confirm cleanup if not forced
    if [[ "${FORCE}" != true && "${DRY_RUN}" != true ]]; then
        echo "This will clean up the following:"
        [[ "${CLEAN_TEMP}" == true ]] && echo "- Temporary files and directories"
        [[ "${CLEAN_LOGS}" == true ]] && echo "- Log files older than ${RETENTION_DAYS} days"
        [[ "${CLEAN_DOCKER}" == true ]] && echo "- Unused Docker resources"
        [[ "${CLEAN_DB}" == true ]] && echo "- Database backups older than ${RETENTION_DAYS} days"
        
        read -p "Continue with cleanup? (y/N): " confirm
        if [[ "${confirm}" != "y" && "${confirm}" != "Y" ]]; then
            log "INFO" "Cleanup aborted by user."
            exit 0
        fi
    fi
    
    # Perform cleanup operations
    [[ "${CLEAN_TEMP}" == true ]] && clean_temp_files
    [[ "${CLEAN_LOGS}" == true ]] && clean_logs
    [[ "${CLEAN_DOCKER}" == true ]] && clean_docker
    [[ "${CLEAN_DB}" == true ]] && clean_db_backups
    
    log "SUCCESS" "Cleanup process completed successfully."
    
    # Print summary
    if [[ "${VERBOSE}" == true || "${DRY_RUN}" == true ]]; then
        echo "Cleanup Summary:"
        echo "----------------"
        echo "Log file: ${LOG_FILE}"
        [[ "${DRY_RUN}" == true ]] && echo "Mode: DRY RUN (no files were actually removed)"
        echo "See the log file for details."
    fi
}

# Parse arguments and run main function
parse_args "$@"
main

exit 0