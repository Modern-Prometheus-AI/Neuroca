#!/usr/bin/env bash
#
# Database Backup Script for NeuroCognitive Architecture (NCA)
#
# This script performs automated database backups with the following features:
# - Configurable backup retention
# - Compression and encryption options
# - Multiple database support (PostgreSQL, MongoDB)
# - Backup verification
# - Comprehensive logging
# - Email notifications on failure
# - Secure handling of credentials
#
# Usage: ./backup.sh [options]
#   Options:
#     -c, --config CONFIG_FILE  Specify config file (default: ../config/backup.conf)
#     -t, --type TYPE           Database type (postgres, mongodb)
#     -d, --database DB_NAME    Database name to backup
#     -o, --output DIR          Output directory for backups
#     -r, --retain DAYS         Number of days to retain backups
#     -e, --encrypt             Encrypt the backup
#     -n, --notify EMAIL        Email to notify on failure
#     -v, --verbose             Enable verbose output
#     -h, --help                Display this help message
#
# Example:
#   ./backup.sh --type postgres --database neuroca_prod --retain 30 --encrypt
#
# Dependencies:
#   - PostgreSQL client tools (pg_dump)
#   - MongoDB tools (mongodump)
#   - gpg (for encryption)
#   - mail command (for notifications)
#
# Author: NeuroCognitive Architecture Team
# Date: 2023

set -o errexit  # Exit on error
set -o nounset  # Exit on unset variables
set -o pipefail # Exit if any command in a pipe fails

# Script constants
readonly SCRIPT_NAME=$(basename "$0")
readonly SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
readonly TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
readonly LOG_DIR="${SCRIPT_DIR}/../../logs/db"
readonly LOG_FILE="${LOG_DIR}/backup_${TIMESTAMP}.log"
readonly DEFAULT_CONFIG_FILE="${SCRIPT_DIR}/../../config/db/backup.conf"
readonly LOCK_FILE="/tmp/neuroca_db_backup.lock"

# Default values
DB_TYPE=""
DB_NAME=""
OUTPUT_DIR="${SCRIPT_DIR}/../../backups"
RETENTION_DAYS=14
ENCRYPT=false
NOTIFY_EMAIL=""
VERBOSE=false
CONFIG_FILE="${DEFAULT_CONFIG_FILE}"

# Create log directory if it doesn't exist
mkdir -p "${LOG_DIR}"

# Initialize log file
touch "${LOG_FILE}"

# Function to log messages
log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo "[${timestamp}] [${level}] ${message}" | tee -a "${LOG_FILE}"
    
    # If verbose mode is enabled, print to stdout
    if [[ "${VERBOSE}" == true && "${level}" == "DEBUG" ]]; then
        echo "[${timestamp}] [${level}] ${message}"
    fi
}

# Function to log and exit on error
error_exit() {
    local message="$1"
    local exit_code="${2:-1}"
    log "ERROR" "${message}"
    
    # Send notification if email is configured
    if [[ -n "${NOTIFY_EMAIL}" ]]; then
        echo "Database backup failed: ${message}" | mail -s "NeuroCognitive Architecture DB Backup Failed" "${NOTIFY_EMAIL}"
    fi
    
    # Release lock file
    if [[ -f "${LOCK_FILE}" ]]; then
        rm -f "${LOCK_FILE}"
    fi
    
    exit "${exit_code}"
}

# Function to display help message
show_help() {
    grep "^#" "$0" | grep -v "!/usr/bin/env" | sed 's/^# \?//'
    exit 0
}

# Function to parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -c|--config)
                CONFIG_FILE="$2"
                shift 2
                ;;
            -t|--type)
                DB_TYPE="$2"
                shift 2
                ;;
            -d|--database)
                DB_NAME="$2"
                shift 2
                ;;
            -o|--output)
                OUTPUT_DIR="$2"
                shift 2
                ;;
            -r|--retain)
                RETENTION_DAYS="$2"
                shift 2
                ;;
            -e|--encrypt)
                ENCRYPT=true
                shift
                ;;
            -n|--notify)
                NOTIFY_EMAIL="$2"
                shift 2
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -h|--help)
                show_help
                ;;
            *)
                error_exit "Unknown option: $1"
                ;;
        esac
    done
}

# Function to load configuration from file
load_config() {
    if [[ -f "${CONFIG_FILE}" ]]; then
        log "INFO" "Loading configuration from ${CONFIG_FILE}"
        # shellcheck source=/dev/null
        source "${CONFIG_FILE}"
    else
        log "WARN" "Configuration file ${CONFIG_FILE} not found, using defaults and command line options"
    fi
}

# Function to validate required parameters
validate_params() {
    if [[ -z "${DB_TYPE}" ]]; then
        error_exit "Database type (-t, --type) is required"
    fi
    
    if [[ -z "${DB_NAME}" ]]; then
        error_exit "Database name (-d, --database) is required"
    fi
    
    if [[ "${DB_TYPE}" != "postgres" && "${DB_TYPE}" != "mongodb" ]]; then
        error_exit "Invalid database type: ${DB_TYPE}. Supported types: postgres, mongodb"
    fi
    
    # Validate retention days is a positive integer
    if ! [[ "${RETENTION_DAYS}" =~ ^[0-9]+$ ]] || [[ "${RETENTION_DAYS}" -lt 1 ]]; then
        error_exit "Retention days must be a positive integer"
    fi
    
    # Create output directory if it doesn't exist
    mkdir -p "${OUTPUT_DIR}" || error_exit "Failed to create output directory: ${OUTPUT_DIR}"
    
    # Check if output directory is writable
    if [[ ! -w "${OUTPUT_DIR}" ]]; then
        error_exit "Output directory ${OUTPUT_DIR} is not writable"
    }
    
    # Check for required tools
    if [[ "${DB_TYPE}" == "postgres" ]]; then
        command -v pg_dump >/dev/null 2>&1 || error_exit "pg_dump is required but not installed"
    elif [[ "${DB_TYPE}" == "mongodb" ]]; then
        command -v mongodump >/dev/null 2>&1 || error_exit "mongodump is required but not installed"
    fi
    
    if [[ "${ENCRYPT}" == true ]]; then
        command -v gpg >/dev/null 2>&1 || error_exit "gpg is required for encryption but not installed"
    fi
}

# Function to acquire lock to prevent concurrent runs
acquire_lock() {
    if [[ -f "${LOCK_FILE}" ]]; then
        local pid
        pid=$(cat "${LOCK_FILE}")
        if ps -p "${pid}" > /dev/null; then
            error_exit "Another backup process (PID: ${pid}) is already running"
        else
            log "WARN" "Removing stale lock file from previous run"
            rm -f "${LOCK_FILE}"
        fi
    fi
    
    echo $$ > "${LOCK_FILE}" || error_exit "Failed to create lock file"
    log "DEBUG" "Acquired lock (PID: $$)"
}

# Function to release lock
release_lock() {
    if [[ -f "${LOCK_FILE}" ]]; then
        rm -f "${LOCK_FILE}" || log "WARN" "Failed to remove lock file"
        log "DEBUG" "Released lock"
    fi
}

# Function to perform PostgreSQL backup
backup_postgres() {
    local backup_file="${OUTPUT_DIR}/${DB_NAME}_${TIMESTAMP}.sql"
    local compressed_file="${backup_file}.gz"
    local final_file="${compressed_file}"
    
    log "INFO" "Starting PostgreSQL backup of database: ${DB_NAME}"
    
    # Use PGPASSFILE if defined in config, otherwise use environment variables
    local pg_env=""
    if [[ -n "${PGPASSFILE:-}" ]]; then
        pg_env="PGPASSFILE=${PGPASSFILE}"
    fi
    
    # Perform the backup
    if ! eval "${pg_env} pg_dump -h ${DB_HOST:-localhost} -p ${DB_PORT:-5432} -U ${DB_USER:-postgres} -d ${DB_NAME} -F p" > "${backup_file}" 2>> "${LOG_FILE}"; then
        error_exit "PostgreSQL backup failed"
    fi
    
    # Compress the backup
    log "DEBUG" "Compressing backup file"
    if ! gzip -f "${backup_file}" 2>> "${LOG_FILE}"; then
        error_exit "Failed to compress backup file"
    fi
    
    # Encrypt the backup if requested
    if [[ "${ENCRYPT}" == true ]]; then
        log "DEBUG" "Encrypting backup file"
        final_file="${compressed_file}.gpg"
        if ! gpg --batch --yes -e -r "${GPG_RECIPIENT:-backup@neuroca.ai}" -o "${final_file}" "${compressed_file}" 2>> "${LOG_FILE}"; then
            error_exit "Failed to encrypt backup file"
        fi
        # Remove the unencrypted compressed file
        rm -f "${compressed_file}"
    fi
    
    log "INFO" "PostgreSQL backup completed successfully: ${final_file}"
    return 0
}

# Function to perform MongoDB backup
backup_mongodb() {
    local backup_dir="${OUTPUT_DIR}/${DB_NAME}_${TIMESTAMP}"
    local compressed_file="${backup_dir}.tar.gz"
    local final_file="${compressed_file}"
    
    log "INFO" "Starting MongoDB backup of database: ${DB_NAME}"
    
    # Create temporary directory for MongoDB dump
    mkdir -p "${backup_dir}" || error_exit "Failed to create temporary backup directory"
    
    # Perform the backup
    local mongo_cmd="mongodump --host ${DB_HOST:-localhost} --port ${DB_PORT:-27017} --db ${DB_NAME}"
    
    # Add authentication if credentials are provided
    if [[ -n "${DB_USER:-}" && -n "${DB_PASSWORD:-}" ]]; then
        mongo_cmd="${mongo_cmd} --username ${DB_USER} --password ${DB_PASSWORD} --authenticationDatabase ${AUTH_DB:-admin}"
    fi
    
    mongo_cmd="${mongo_cmd} --out ${backup_dir}"
    
    if ! eval "${mongo_cmd}" 2>> "${LOG_FILE}"; then
        error_exit "MongoDB backup failed"
    fi
    
    # Compress the backup
    log "DEBUG" "Compressing backup directory"
    if ! tar -czf "${compressed_file}" -C "$(dirname "${backup_dir}")" "$(basename "${backup_dir}")" 2>> "${LOG_FILE}"; then
        error_exit "Failed to compress backup directory"
    fi
    
    # Remove the uncompressed backup directory
    rm -rf "${backup_dir}"
    
    # Encrypt the backup if requested
    if [[ "${ENCRYPT}" == true ]]; then
        log "DEBUG" "Encrypting backup file"
        final_file="${compressed_file}.gpg"
        if ! gpg --batch --yes -e -r "${GPG_RECIPIENT:-backup@neuroca.ai}" -o "${final_file}" "${compressed_file}" 2>> "${LOG_FILE}"; then
            error_exit "Failed to encrypt backup file"
        fi
        # Remove the unencrypted compressed file
        rm -f "${compressed_file}"
    fi
    
    log "INFO" "MongoDB backup completed successfully: ${final_file}"
    return 0
}

# Function to verify backup integrity
verify_backup() {
    local backup_file="$1"
    
    log "INFO" "Verifying backup integrity: ${backup_file}"
    
    # Check if file exists and has non-zero size
    if [[ ! -f "${backup_file}" ]]; then
        error_exit "Backup file does not exist: ${backup_file}"
    fi
    
    if [[ ! -s "${backup_file}" ]]; then
        error_exit "Backup file is empty: ${backup_file}"
    fi
    
    # For encrypted files, verify GPG can read the header
    if [[ "${backup_file}" == *.gpg ]]; then
        if ! gpg --list-packets "${backup_file}" > /dev/null 2>> "${LOG_FILE}"; then
            error_exit "Backup file encryption verification failed: ${backup_file}"
        fi
    fi
    
    log "INFO" "Backup verification successful"
    return 0
}

# Function to clean up old backups
cleanup_old_backups() {
    log "INFO" "Cleaning up backups older than ${RETENTION_DAYS} days"
    
    # Find and delete old backup files
    find "${OUTPUT_DIR}" -name "${DB_NAME}_*" -type f -mtime +${RETENTION_DAYS} -exec rm -f {} \; 2>> "${LOG_FILE}" || {
        log "WARN" "Failed to clean up some old backups"
    }
    
    log "INFO" "Cleanup completed"
}

# Main function
main() {
    log "INFO" "Starting database backup process"
    
    # Parse command line arguments
    parse_args "$@"
    
    # Load configuration
    load_config
    
    # Validate parameters
    validate_params
    
    # Acquire lock
    acquire_lock
    
    # Trap for cleanup on exit
    trap release_lock EXIT INT TERM
    
    # Create backup based on database type
    local final_backup_file=""
    
    if [[ "${DB_TYPE}" == "postgres" ]]; then
        backup_postgres
        final_backup_file="${OUTPUT_DIR}/${DB_NAME}_${TIMESTAMP}.sql.gz"
        if [[ "${ENCRYPT}" == true ]]; then
            final_backup_file="${final_backup_file}.gpg"
        fi
    elif [[ "${DB_TYPE}" == "mongodb" ]]; then
        backup_mongodb
        final_backup_file="${OUTPUT_DIR}/${DB_NAME}_${TIMESTAMP}.tar.gz"
        if [[ "${ENCRYPT}" == true ]]; then
            final_backup_file="${final_backup_file}.gpg"
        fi
    fi
    
    # Verify backup
    verify_backup "${final_backup_file}"
    
    # Clean up old backups
    cleanup_old_backups
    
    # Log success
    log "INFO" "Database backup process completed successfully"
    
    # Release lock (also handled by trap)
    release_lock
    
    return 0
}

# Execute main function
main "$@"