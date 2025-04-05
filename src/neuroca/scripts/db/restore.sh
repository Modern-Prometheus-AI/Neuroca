#!/usr/bin/env bash
#
# Database Restoration Script for NeuroCognitive Architecture (NCA)
#
# This script restores a database backup to the NCA database system.
# It supports various database types (PostgreSQL, MongoDB) and handles
# different backup formats.
#
# Usage:
#   ./restore.sh [options]
#
# Options:
#   -f, --file <backup_file>       Path to backup file (required)
#   -t, --type <db_type>           Database type: postgres|mongodb (default: postgres)
#   -h, --host <hostname>          Database host (default: localhost)
#   -p, --port <port>              Database port (default: based on db type)
#   -d, --database <db_name>       Database name (default: neuroca)
#   -u, --user <username>          Database username
#   -c, --config <config_file>     Path to config file with DB credentials
#   -v, --verbose                  Enable verbose output
#   --help                         Display this help message
#   --dry-run                      Show commands without executing
#
# Examples:
#   ./restore.sh --file backup.sql --database neuroca_prod
#   ./restore.sh --file backup.tar.gz --type postgres --host db.example.com
#   ./restore.sh --file backup.archive --type mongodb --config /path/to/config.json
#
# Author: NeuroCognitive Architecture Team
# Version: 1.0.0
# License: Proprietary

set -o errexit  # Exit on error
set -o nounset  # Exit on unset variables
set -o pipefail # Exit on pipe failures

# Script constants
readonly SCRIPT_NAME=$(basename "$0")
readonly SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
readonly LOG_FILE="${SCRIPT_DIR}/../../logs/db_restore_$(date +%Y%m%d_%H%M%S).log"

# Default values
DB_TYPE="postgres"
DB_HOST="localhost"
DB_PORT=""
DB_NAME="neuroca"
DB_USER=""
DB_PASSWORD=""
BACKUP_FILE=""
CONFIG_FILE=""
VERBOSE=false
DRY_RUN=false

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log messages
log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
    
    # If not verbose, only show INFO and higher in console
    if [[ "$VERBOSE" == "false" && "$level" == "DEBUG" ]]; then
        return
    fi
}

# Function to log and exit on error
error_exit() {
    log "ERROR" "$1"
    exit 1
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
            -f|--file)
                BACKUP_FILE="$2"
                shift 2
                ;;
            -t|--type)
                DB_TYPE="$2"
                shift 2
                ;;
            -h|--host)
                DB_HOST="$2"
                shift 2
                ;;
            -p|--port)
                DB_PORT="$2"
                shift 2
                ;;
            -d|--database)
                DB_NAME="$2"
                shift 2
                ;;
            -u|--user)
                DB_USER="$2"
                shift 2
                ;;
            -c|--config)
                CONFIG_FILE="$2"
                shift 2
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            --help)
                show_help
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            *)
                error_exit "Unknown option: $1"
                ;;
        esac
    done
}

# Function to validate inputs
validate_inputs() {
    # Check if backup file is provided
    if [[ -z "$BACKUP_FILE" ]]; then
        error_exit "Backup file is required. Use -f or --file option."
    fi

    # Check if backup file exists
    if [[ ! -f "$BACKUP_FILE" ]]; then
        error_exit "Backup file does not exist: $BACKUP_FILE"
    fi

    # Validate database type
    if [[ "$DB_TYPE" != "postgres" && "$DB_TYPE" != "mongodb" ]]; then
        error_exit "Invalid database type: $DB_TYPE. Supported types: postgres, mongodb"
    fi

    # Set default port if not specified
    if [[ -z "$DB_PORT" ]]; then
        if [[ "$DB_TYPE" == "postgres" ]]; then
            DB_PORT="5432"
        elif [[ "$DB_TYPE" == "mongodb" ]]; then
            DB_PORT="27017"
        fi
    fi

    # Load config file if provided
    if [[ -n "$CONFIG_FILE" ]]; then
        if [[ ! -f "$CONFIG_FILE" ]]; then
            error_exit "Config file does not exist: $CONFIG_FILE"
        fi
        
        # Source the config file if it's a shell script
        if [[ "$CONFIG_FILE" == *.sh ]]; then
            source "$CONFIG_FILE"
        # Parse JSON config file
        elif [[ "$CONFIG_FILE" == *.json ]]; then
            if ! command -v jq &> /dev/null; then
                error_exit "jq is required to parse JSON config files but is not installed"
            fi
            
            DB_HOST=$(jq -r '.host // empty' "$CONFIG_FILE") || DB_HOST="$DB_HOST"
            DB_PORT=$(jq -r '.port // empty' "$CONFIG_FILE") || DB_PORT="$DB_PORT"
            DB_NAME=$(jq -r '.database // empty' "$CONFIG_FILE") || DB_NAME="$DB_NAME"
            DB_USER=$(jq -r '.username // empty' "$CONFIG_FILE") || DB_USER="$DB_USER"
            DB_PASSWORD=$(jq -r '.password // empty' "$CONFIG_FILE") || DB_PASSWORD="$DB_PASSWORD"
        else
            error_exit "Unsupported config file format: $CONFIG_FILE"
        fi
    fi

    # Check for required credentials
    if [[ "$DB_TYPE" == "postgres" && -z "$DB_USER" ]]; then
        error_exit "Database username is required for PostgreSQL. Use -u or --user option."
    fi
}

# Function to check required tools
check_dependencies() {
    log "INFO" "Checking dependencies..."
    
    if [[ "$DB_TYPE" == "postgres" ]]; then
        if ! command -v psql &> /dev/null; then
            error_exit "PostgreSQL client (psql) is not installed"
        fi
        if ! command -v pg_restore &> /dev/null; then
            error_exit "pg_restore is not installed"
        fi
    elif [[ "$DB_TYPE" == "mongodb" ]]; then
        if ! command -v mongorestore &> /dev/null; then
            error_exit "MongoDB tools (mongorestore) are not installed"
        fi
    fi
    
    # Check for compression tools based on file extension
    if [[ "$BACKUP_FILE" == *.gz ]]; then
        if ! command -v gunzip &> /dev/null; then
            error_exit "gunzip is not installed"
        fi
    elif [[ "$BACKUP_FILE" == *.xz ]]; then
        if ! command -v xz &> /dev/null; then
            error_exit "xz is not installed"
        fi
    elif [[ "$BACKUP_FILE" == *.bz2 ]]; then
        if ! command -v bunzip2 &> /dev/null; then
            error_exit "bunzip2 is not installed"
        fi
    fi
    
    log "DEBUG" "All required dependencies are installed"
}

# Function to restore PostgreSQL database
restore_postgres() {
    log "INFO" "Starting PostgreSQL database restoration..."
    
    # Prepare environment variables for PostgreSQL
    export PGHOST="$DB_HOST"
    export PGPORT="$DB_PORT"
    export PGDATABASE="$DB_NAME"
    export PGUSER="$DB_USER"
    
    # Use password file or environment variable to avoid password in command line
    if [[ -n "$DB_PASSWORD" ]]; then
        export PGPASSWORD="$DB_PASSWORD"
    fi
    
    # Create temporary directory for extraction if needed
    local temp_dir=""
    if [[ "$BACKUP_FILE" == *.tar.gz || "$BACKUP_FILE" == *.tgz || "$BACKUP_FILE" == *.tar || "$BACKUP_FILE" == *.tar.xz || "$BACKUP_FILE" == *.tar.bz2 ]]; then
        temp_dir=$(mktemp -d)
        log "DEBUG" "Created temporary directory: $temp_dir"
    fi
    
    # Cleanup function to remove temporary files and unset environment variables
    cleanup() {
        log "DEBUG" "Performing cleanup..."
        if [[ -n "$temp_dir" && -d "$temp_dir" ]]; then
            rm -rf "$temp_dir"
            log "DEBUG" "Removed temporary directory: $temp_dir"
        fi
        unset PGPASSWORD
        unset PGHOST
        unset PGPORT
        unset PGDATABASE
        unset PGUSER
    }
    
    # Set trap to ensure cleanup on exit
    trap cleanup EXIT
    
    # Determine restore command based on file extension
    local restore_cmd=""
    
    if [[ "$BACKUP_FILE" == *.sql ]]; then
        restore_cmd="psql -f \"$BACKUP_FILE\""
    elif [[ "$BACKUP_FILE" == *.sql.gz ]]; then
        restore_cmd="gunzip -c \"$BACKUP_FILE\" | psql"
    elif [[ "$BACKUP_FILE" == *.sql.xz ]]; then
        restore_cmd="xz -dc \"$BACKUP_FILE\" | psql"
    elif [[ "$BACKUP_FILE" == *.sql.bz2 ]]; then
        restore_cmd="bunzip2 -c \"$BACKUP_FILE\" | psql"
    elif [[ "$BACKUP_FILE" == *.dump || "$BACKUP_FILE" == *.custom ]]; then
        restore_cmd="pg_restore -d \"$DB_NAME\" --clean --if-exists \"$BACKUP_FILE\""
    elif [[ "$BACKUP_FILE" == *.dump.gz || "$BACKUP_FILE" == *.custom.gz ]]; then
        restore_cmd="gunzip -c \"$BACKUP_FILE\" | pg_restore -d \"$DB_NAME\" --clean --if-exists"
    elif [[ "$BACKUP_FILE" == *.tar || "$BACKUP_FILE" == *.tar.gz || "$BACKUP_FILE" == *.tgz || "$BACKUP_FILE" == *.tar.xz || "$BACKUP_FILE" == *.tar.bz2 ]]; then
        # Extract archive to temporary directory
        if [[ "$BACKUP_FILE" == *.tar ]]; then
            tar -xf "$BACKUP_FILE" -C "$temp_dir"
        elif [[ "$BACKUP_FILE" == *.tar.gz || "$BACKUP_FILE" == *.tgz ]]; then
            tar -xzf "$BACKUP_FILE" -C "$temp_dir"
        elif [[ "$BACKUP_FILE" == *.tar.xz ]]; then
            tar -xJf "$BACKUP_FILE" -C "$temp_dir"
        elif [[ "$BACKUP_FILE" == *.tar.bz2 ]]; then
            tar -xjf "$BACKUP_FILE" -C "$temp_dir"
        fi
        
        # Find SQL or dump files in the extracted directory
        local sql_file=$(find "$temp_dir" -name "*.sql" -type f | head -1)
        local dump_file=$(find "$temp_dir" -name "*.dump" -o -name "*.custom" -type f | head -1)
        
        if [[ -n "$sql_file" ]]; then
            restore_cmd="psql -f \"$sql_file\""
        elif [[ -n "$dump_file" ]]; then
            restore_cmd="pg_restore -d \"$DB_NAME\" --clean --if-exists \"$dump_file\""
        else
            error_exit "No SQL or dump files found in the archive"
        fi
    else
        error_exit "Unsupported backup file format: $BACKUP_FILE"
    fi
    
    # Execute or display the restore command
    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "DRY RUN: Would execute: $restore_cmd"
    else
        log "INFO" "Executing restore command..."
        log "DEBUG" "Command: $restore_cmd"
        
        # Execute the command
        if eval "$restore_cmd"; then
            log "INFO" "Database restoration completed successfully"
        else
            error_exit "Database restoration failed with exit code $?"
        fi
    fi
}

# Function to restore MongoDB database
restore_mongodb() {
    log "INFO" "Starting MongoDB database restoration..."
    
    # Prepare connection string parts
    local auth_part=""
    if [[ -n "$DB_USER" ]]; then
        if [[ -z "$DB_PASSWORD" ]]; then
            error_exit "Password is required when username is provided for MongoDB"
        fi
        auth_part="--username \"$DB_USER\" --password \"$DB_PASSWORD\" --authenticationDatabase admin"
    fi
    
    # Create temporary directory for extraction if needed
    local temp_dir=""
    if [[ "$BACKUP_FILE" == *.tar.gz || "$BACKUP_FILE" == *.tgz || "$BACKUP_FILE" == *.tar || "$BACKUP_FILE" == *.tar.xz || "$BACKUP_FILE" == *.tar.bz2 ]]; then
        temp_dir=$(mktemp -d)
        log "DEBUG" "Created temporary directory: $temp_dir"
    fi
    
    # Cleanup function
    cleanup() {
        log "DEBUG" "Performing cleanup..."
        if [[ -n "$temp_dir" && -d "$temp_dir" ]]; then
            rm -rf "$temp_dir"
            log "DEBUG" "Removed temporary directory: $temp_dir"
        fi
    }
    
    # Set trap to ensure cleanup on exit
    trap cleanup EXIT
    
    # Determine restore command based on file extension
    local restore_cmd=""
    local restore_path=""
    
    if [[ "$BACKUP_FILE" == *.gz && "$BACKUP_FILE" != *.tar.gz && "$BACKUP_FILE" != *.tgz ]]; then
        # Extract .gz file to temporary directory
        temp_dir=$(mktemp -d)
        gunzip -c "$BACKUP_FILE" > "$temp_dir/backup.archive"
        restore_path="$temp_dir/backup.archive"
    elif [[ "$BACKUP_FILE" == *.tar || "$BACKUP_FILE" == *.tar.gz || "$BACKUP_FILE" == *.tgz || "$BACKUP_FILE" == *.tar.xz || "$BACKUP_FILE" == *.tar.bz2 ]]; then
        # Extract archive to temporary directory
        if [[ "$BACKUP_FILE" == *.tar ]]; then
            tar -xf "$BACKUP_FILE" -C "$temp_dir"
        elif [[ "$BACKUP_FILE" == *.tar.gz || "$BACKUP_FILE" == *.tgz ]]; then
            tar -xzf "$BACKUP_FILE" -C "$temp_dir"
        elif [[ "$BACKUP_FILE" == *.tar.xz ]]; then
            tar -xJf "$BACKUP_FILE" -C "$temp_dir"
        elif [[ "$BACKUP_FILE" == *.tar.bz2 ]]; then
            tar -xjf "$BACKUP_FILE" -C "$temp_dir"
        fi
        restore_path="$temp_dir"
    else
        # Use the backup file directly
        restore_path="$BACKUP_FILE"
    fi
    
    # Build the mongorestore command
    restore_cmd="mongorestore --host \"$DB_HOST\" --port \"$DB_PORT\" --db \"$DB_NAME\" $auth_part --drop \"$restore_path\""
    
    # Execute or display the restore command
    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "DRY RUN: Would execute: $restore_cmd"
    else
        log "INFO" "Executing restore command..."
        log "DEBUG" "Command: $restore_cmd"
        
        # Execute the command
        if eval "$restore_cmd"; then
            log "INFO" "Database restoration completed successfully"
        else
            error_exit "Database restoration failed with exit code $?"
        fi
    fi
}

# Main function
main() {
    log "INFO" "Starting database restore script"
    
    # Parse command line arguments
    parse_args "$@"
    
    # Validate inputs
    validate_inputs
    
    # Check dependencies
    check_dependencies
    
    # Display configuration
    log "INFO" "Configuration:"
    log "INFO" "  Database Type: $DB_TYPE"
    log "INFO" "  Database Host: $DB_HOST"
    log "INFO" "  Database Port: $DB_PORT"
    log "INFO" "  Database Name: $DB_NAME"
    log "INFO" "  Backup File: $BACKUP_FILE"
    log "DEBUG" "  Verbose Mode: $VERBOSE"
    log "DEBUG" "  Dry Run Mode: $DRY_RUN"
    
    # Restore database based on type
    if [[ "$DB_TYPE" == "postgres" ]]; then
        restore_postgres
    elif [[ "$DB_TYPE" == "mongodb" ]]; then
        restore_mongodb
    fi
    
    log "INFO" "Database restore script completed successfully"
}

# Execute main function with all arguments
main "$@"