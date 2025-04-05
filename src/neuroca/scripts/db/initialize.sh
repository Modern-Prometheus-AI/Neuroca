#!/usr/bin/env bash

#############################################################################
# NeuroCognitive Architecture (NCA) - Database Initialization Script
#
# This script initializes the database for the NeuroCognitive Architecture.
# It performs the following operations:
# - Validates environment variables and configuration
# - Creates the database if it doesn't exist
# - Applies schema migrations
# - Sets up initial data and roles
# - Validates the database setup
#
# Usage:
#   ./initialize.sh [--force] [--no-seed] [--verbose]
#
# Options:
#   --force     Force reinitialization even if database exists
#   --no-seed   Skip seeding initial data
#   --verbose   Enable verbose output
#
# Environment variables:
#   DB_HOST     - Database host (default: localhost)
#   DB_PORT     - Database port (default: 5432)
#   DB_NAME     - Database name (required)
#   DB_USER     - Database user (required)
#   DB_PASSWORD - Database password (required)
#   DB_SSL_MODE - SSL mode (default: prefer)
#
# Exit codes:
#   0 - Success
#   1 - Configuration error
#   2 - Connection error
#   3 - Database creation error
#   4 - Schema migration error
#   5 - Data seeding error
#   6 - Validation error
#############################################################################

set -o errexit
set -o nounset
set -o pipefail

# Script directory for relative paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../" && pwd)"

# Default configuration
DB_HOST=${DB_HOST:-"localhost"}
DB_PORT=${DB_PORT:-5432}
DB_SSL_MODE=${DB_SSL_MODE:-"prefer"}
MIGRATIONS_DIR="${PROJECT_ROOT}/db/migrations"
SEED_DIR="${PROJECT_ROOT}/db/seeds"
LOG_FILE="${PROJECT_ROOT}/logs/db_initialize.log"
FORCE_INIT=false
SKIP_SEED=false
VERBOSE=false

# Ensure log directory exists
mkdir -p "$(dirname "${LOG_FILE}")"

# Logging functions
log_info() {
    local timestamp
    timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    echo "[INFO] ${timestamp} - $*" | tee -a "${LOG_FILE}"
}

log_error() {
    local timestamp
    timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    echo "[ERROR] ${timestamp} - $*" | tee -a "${LOG_FILE}" >&2
}

log_debug() {
    if [[ "${VERBOSE}" == true ]]; then
        local timestamp
        timestamp=$(date "+%Y-%m-%d %H:%M:%S")
        echo "[DEBUG] ${timestamp} - $*" | tee -a "${LOG_FILE}"
    fi
}

# Function to display usage information
show_usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Initialize the NeuroCognitive Architecture database.

Options:
  --force     Force reinitialization even if database exists
  --no-seed   Skip seeding initial data
  --verbose   Enable verbose output
  --help      Display this help message and exit

Environment variables:
  DB_HOST     - Database host (default: localhost)
  DB_PORT     - Database port (default: 5432)
  DB_NAME     - Database name (required)
  DB_USER     - Database user (required)
  DB_PASSWORD - Database password (required)
  DB_SSL_MODE - SSL mode (default: prefer)
EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --force)
                FORCE_INIT=true
                shift
                ;;
            --no-seed)
                SKIP_SEED=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
}

# Validate required environment variables
validate_config() {
    local missing_vars=()

    [[ -z "${DB_NAME:-}" ]] && missing_vars+=("DB_NAME")
    [[ -z "${DB_USER:-}" ]] && missing_vars+=("DB_USER")
    [[ -z "${DB_PASSWORD:-}" ]] && missing_vars+=("DB_PASSWORD")

    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_error "Missing required environment variables: ${missing_vars[*]}"
        return 1
    fi

    # Validate directories exist
    if [[ ! -d "${MIGRATIONS_DIR}" ]]; then
        log_error "Migrations directory not found: ${MIGRATIONS_DIR}"
        return 1
    fi

    if [[ "${SKIP_SEED}" == false ]] && [[ ! -d "${SEED_DIR}" ]]; then
        log_error "Seed directory not found: ${SEED_DIR}"
        return 1
    fi

    log_debug "Configuration validated successfully"
    return 0
}

# Test database connection
test_connection() {
    log_info "Testing connection to PostgreSQL server at ${DB_HOST}:${DB_PORT}"
    
    if ! PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" \
         -U "${DB_USER}" -c "SELECT 1" postgres > /dev/null 2>&1; then
        log_error "Failed to connect to PostgreSQL server"
        return 2
    fi
    
    log_debug "Successfully connected to PostgreSQL server"
    return 0
}

# Check if database exists
database_exists() {
    log_debug "Checking if database '${DB_NAME}' exists"
    
    if PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" \
       -U "${DB_USER}" -lqt | cut -d \| -f 1 | grep -qw "${DB_NAME}"; then
        return 0
    else
        return 1
    fi
}

# Create database if it doesn't exist
create_database() {
    if database_exists; then
        if [[ "${FORCE_INIT}" == true ]]; then
            log_info "Database '${DB_NAME}' exists, dropping due to --force flag"
            PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" \
                -U "${DB_USER}" -c "DROP DATABASE IF EXISTS \"${DB_NAME}\"" postgres
        else
            log_info "Database '${DB_NAME}' already exists, skipping creation"
            return 0
        fi
    fi

    log_info "Creating database '${DB_NAME}'"
    
    if ! PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" \
         -U "${DB_USER}" -c "CREATE DATABASE \"${DB_NAME}\"" postgres; then
        log_error "Failed to create database '${DB_NAME}'"
        return 3
    fi
    
    log_info "Database '${DB_NAME}' created successfully"
    return 0
}

# Apply database migrations
apply_migrations() {
    log_info "Applying database migrations from ${MIGRATIONS_DIR}"
    
    # Get list of migration files sorted by name
    local migration_files
    migration_files=$(find "${MIGRATIONS_DIR}" -name "*.sql" | sort)
    
    if [[ -z "${migration_files}" ]]; then
        log_error "No migration files found in ${MIGRATIONS_DIR}"
        return 4
    fi
    
    # Create migrations tracking table if it doesn't exist
    PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" \
        -U "${DB_USER}" -d "${DB_NAME}" -c "
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version VARCHAR(255) PRIMARY KEY,
            applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );" || {
        log_error "Failed to create schema_migrations table"
        return 4
    }
    
    # Apply each migration if not already applied
    local count=0
    while IFS= read -r migration_file; do
        local migration_name
        migration_name=$(basename "${migration_file}" .sql)
        
        log_debug "Checking migration: ${migration_name}"
        
        # Check if migration has already been applied
        if PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" \
           -U "${DB_USER}" -d "${DB_NAME}" -t -c \
           "SELECT 1 FROM schema_migrations WHERE version = '${migration_name}'" | grep -q 1; then
            log_debug "Migration ${migration_name} already applied, skipping"
            continue
        fi
        
        log_info "Applying migration: ${migration_name}"
        
        # Apply the migration within a transaction
        if ! PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" \
             -U "${DB_USER}" -d "${DB_NAME}" -v ON_ERROR_STOP=1 -f "${migration_file}"; then
            log_error "Failed to apply migration: ${migration_name}"
            return 4
        fi
        
        # Record the migration as applied
        PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" \
            -U "${DB_USER}" -d "${DB_NAME}" -c \
            "INSERT INTO schema_migrations (version) VALUES ('${migration_name}')" || {
            log_error "Failed to record migration: ${migration_name}"
            return 4
        }
        
        count=$((count + 1))
    done <<< "${migration_files}"
    
    log_info "Successfully applied ${count} migrations"
    return 0
}

# Seed initial data
seed_data() {
    if [[ "${SKIP_SEED}" == true ]]; then
        log_info "Skipping data seeding due to --no-seed flag"
        return 0
    fi
    
    log_info "Seeding initial data from ${SEED_DIR}"
    
    # Get list of seed files sorted by name
    local seed_files
    seed_files=$(find "${SEED_DIR}" -name "*.sql" | sort)
    
    if [[ -z "${seed_files}" ]]; then
        log_info "No seed files found in ${SEED_DIR}, skipping"
        return 0
    fi
    
    # Apply each seed file
    local count=0
    while IFS= read -r seed_file; do
        local seed_name
        seed_name=$(basename "${seed_file}" .sql)
        
        log_info "Applying seed: ${seed_name}"
        
        # Apply the seed within a transaction
        if ! PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" \
             -U "${DB_USER}" -d "${DB_NAME}" -v ON_ERROR_STOP=1 -f "${seed_file}"; then
            log_error "Failed to apply seed: ${seed_name}"
            return 5
        fi
        
        count=$((count + 1))
    done <<< "${seed_files}"
    
    log_info "Successfully applied ${count} seed files"
    return 0
}

# Validate database setup
validate_database() {
    log_info "Validating database setup"
    
    # Check if we can connect to the database
    if ! PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" \
         -U "${DB_USER}" -d "${DB_NAME}" -c "SELECT 1" > /dev/null 2>&1; then
        log_error "Failed to connect to database '${DB_NAME}'"
        return 6
    fi
    
    # Check if schema_migrations table exists and has entries
    local migration_count
    migration_count=$(PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" \
                      -U "${DB_USER}" -d "${DB_NAME}" -t -c \
                      "SELECT COUNT(*) FROM schema_migrations" 2>/dev/null || echo "0")
    
    migration_count=$(echo "${migration_count}" | tr -d '[:space:]')
    
    if [[ "${migration_count}" == "0" ]]; then
        log_error "No migrations have been applied"
        return 6
    fi
    
    log_info "Database validation successful: ${migration_count} migrations applied"
    return 0
}

# Main function
main() {
    log_info "Starting database initialization for NeuroCognitive Architecture"
    
    parse_args "$@"
    
    # Run initialization steps
    validate_config || exit 1
    test_connection || exit 2
    create_database || exit 3
    apply_migrations || exit 4
    seed_data || exit 5
    validate_database || exit 6
    
    log_info "Database initialization completed successfully"
    return 0
}

# Execute main function
main "$@"