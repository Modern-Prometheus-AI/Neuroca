#!/usr/bin/env bash
#
# NeuroCognitive Architecture (NCA) Test Runner
#
# This script provides a comprehensive testing framework for the NeuroCognitive
# Architecture project. It supports running unit tests, integration tests,
# performance tests, and more with proper error handling and reporting.
#
# Usage:
#   ./scripts/development/test.sh [options] [test_path]
#
# Options:
#   -h, --help                 Display this help message
#   -u, --unit                 Run unit tests only
#   -i, --integration          Run integration tests only
#   -a, --all                  Run all tests (default)
#   -c, --coverage             Generate test coverage report
#   -v, --verbose              Enable verbose output
#   -p, --parallel [n]         Run tests in parallel with n workers (default: number of CPU cores)
#   -f, --failfast             Stop on first test failure
#   -s, --skip-slow            Skip tests marked as slow
#   -d, --debug                Run tests in debug mode with extra logging
#   -e, --environment ENV      Specify test environment (dev, staging, prod)
#
# Examples:
#   ./scripts/development/test.sh                     # Run all tests
#   ./scripts/development/test.sh -u                  # Run only unit tests
#   ./scripts/development/test.sh -c -v tests/memory  # Run tests in memory directory with coverage and verbose output
#   ./scripts/development/test.sh -p 4 -f             # Run tests in parallel with 4 workers and stop on first failure
#
# Author: NeuroCognitive Architecture Team
# Date: 2023

set -o errexit  # Exit on error
set -o nounset  # Exit on undefined variables
set -o pipefail # Exit on pipe failures

# Constants
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
readonly LOG_DIR="${PROJECT_ROOT}/logs"
readonly TEST_LOG="${LOG_DIR}/test_$(date +%Y%m%d_%H%M%S).log"
readonly COVERAGE_DIR="${PROJECT_ROOT}/coverage"
readonly COLOR_RED='\033[0;31m'
readonly COLOR_GREEN='\033[0;32m'
readonly COLOR_YELLOW='\033[0;33m'
readonly COLOR_BLUE='\033[0;34m'
readonly COLOR_RESET='\033[0m'

# Default configuration
TEST_TYPE="all"
GENERATE_COVERAGE=false
VERBOSE=false
PARALLEL_WORKERS=$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)
FAILFAST=false
SKIP_SLOW=false
DEBUG=false
TEST_ENV="dev"
TEST_PATH=""

# Create log directory if it doesn't exist
mkdir -p "${LOG_DIR}"

# Function to display usage information
show_help() {
    grep "^#" "${BASH_SOURCE[0]}" | grep -v "!/usr/bin/env" | sed 's/^# \?//'
    exit 0
}

# Function to log messages
log() {
    local level=$1
    local message=$2
    local color=$COLOR_RESET
    
    case $level in
        "INFO")
            color=$COLOR_BLUE
            ;;
        "SUCCESS")
            color=$COLOR_GREEN
            ;;
        "WARNING")
            color=$COLOR_YELLOW
            ;;
        "ERROR")
            color=$COLOR_RED
            ;;
    esac
    
    echo -e "${color}[$(date '+%Y-%m-%d %H:%M:%S')] [${level}] ${message}${COLOR_RESET}" | tee -a "${TEST_LOG}"
}

# Function to check dependencies
check_dependencies() {
    log "INFO" "Checking dependencies..."
    
    local missing_deps=()
    
    # Check for Python
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi
    
    # Check for pytest
    if ! python3 -c "import pytest" &> /dev/null; then
        missing_deps+=("pytest")
    fi
    
    # Check for coverage
    if $GENERATE_COVERAGE && ! python3 -c "import coverage" &> /dev/null; then
        missing_deps+=("python-coverage")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        log "ERROR" "Missing dependencies: ${missing_deps[*]}"
        log "INFO" "Please install missing dependencies and try again."
        exit 1
    fi
    
    log "SUCCESS" "All dependencies are installed."
}

# Function to clean previous test artifacts
clean_artifacts() {
    log "INFO" "Cleaning previous test artifacts..."
    
    # Remove previous coverage data if generating coverage
    if $GENERATE_COVERAGE; then
        rm -rf "${COVERAGE_DIR}"
        mkdir -p "${COVERAGE_DIR}"
        rm -f .coverage
        rm -f .coverage.*
    fi
    
    # Remove pytest cache
    rm -rf .pytest_cache
    
    # Remove any temporary test files
    find "${PROJECT_ROOT}" -name "*.pyc" -delete
    find "${PROJECT_ROOT}" -name "__pycache__" -type d -exec rm -rf {} +
    
    log "SUCCESS" "Test artifacts cleaned."
}

# Function to run tests
run_tests() {
    log "INFO" "Running tests with configuration:"
    log "INFO" "  - Test type: ${TEST_TYPE}"
    log "INFO" "  - Coverage: ${GENERATE_COVERAGE}"
    log "INFO" "  - Verbose: ${VERBOSE}"
    log "INFO" "  - Parallel workers: ${PARALLEL_WORKERS}"
    log "INFO" "  - Fail fast: ${FAILFAST}"
    log "INFO" "  - Skip slow: ${SKIP_SLOW}"
    log "INFO" "  - Debug: ${DEBUG}"
    log "INFO" "  - Environment: ${TEST_ENV}"
    log "INFO" "  - Test path: ${TEST_PATH:-'All tests'}"
    
    # Change to project root
    cd "${PROJECT_ROOT}"
    
    # Build pytest command
    local pytest_cmd="python3 -m pytest"
    
    # Add verbosity
    if $VERBOSE; then
        pytest_cmd="${pytest_cmd} -v"
    fi
    
    # Add parallel execution
    pytest_cmd="${pytest_cmd} -n ${PARALLEL_WORKERS}"
    
    # Add fail fast
    if $FAILFAST; then
        pytest_cmd="${pytest_cmd} -x"
    fi
    
    # Add coverage
    if $GENERATE_COVERAGE; then
        pytest_cmd="${pytest_cmd} --cov=neuroca --cov-report=term --cov-report=html:${COVERAGE_DIR}"
    fi
    
    # Add debug mode
    if $DEBUG; then
        pytest_cmd="${pytest_cmd} --log-cli-level=DEBUG"
    fi
    
    # Add test type markers
    case $TEST_TYPE in
        "unit")
            pytest_cmd="${pytest_cmd} -m unit"
            ;;
        "integration")
            pytest_cmd="${pytest_cmd} -m integration"
            ;;
        "all")
            # No marker needed for all tests
            ;;
    esac
    
    # Add skip slow marker if needed
    if $SKIP_SLOW; then
        pytest_cmd="${pytest_cmd} -m 'not slow'"
    fi
    
    # Add test path if specified
    if [ -n "${TEST_PATH}" ]; then
        pytest_cmd="${pytest_cmd} ${TEST_PATH}"
    fi
    
    # Set environment variables
    export NEUROCA_TEST_ENV="${TEST_ENV}"
    
    # Run the tests
    log "INFO" "Executing: ${pytest_cmd}"
    
    if eval "${pytest_cmd}"; then
        log "SUCCESS" "All tests passed successfully!"
        return 0
    else
        local exit_code=$?
        log "ERROR" "Tests failed with exit code ${exit_code}"
        return ${exit_code}
    fi
}

# Function to generate and display test summary
generate_summary() {
    local exit_code=$1
    
    log "INFO" "Generating test summary..."
    
    if [ ${exit_code} -eq 0 ]; then
        log "SUCCESS" "Test suite completed successfully!"
    else
        log "ERROR" "Test suite failed with exit code ${exit_code}"
    fi
    
    # Display coverage summary if generated
    if $GENERATE_COVERAGE; then
        log "INFO" "Coverage report available at: ${COVERAGE_DIR}/index.html"
        
        # Display coverage summary in terminal
        if command -v python3 &> /dev/null; then
            log "INFO" "Coverage Summary:"
            python3 -c "
import os
import json

try:
    with open('${COVERAGE_DIR}/coverage.json', 'r') as f:
        data = json.load(f)
        total = data.get('totals', {}).get('percent_covered', 0)
        print(f'Total coverage: {total:.2f}%')
except Exception as e:
    print(f'Could not read coverage data: {e}')
"
        fi
    fi
    
    log "INFO" "Test logs available at: ${TEST_LOG}"
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                ;;
            -u|--unit)
                TEST_TYPE="unit"
                shift
                ;;
            -i|--integration)
                TEST_TYPE="integration"
                shift
                ;;
            -a|--all)
                TEST_TYPE="all"
                shift
                ;;
            -c|--coverage)
                GENERATE_COVERAGE=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -p|--parallel)
                if [[ $# -gt 1 && $2 =~ ^[0-9]+$ ]]; then
                    PARALLEL_WORKERS=$2
                    shift 2
                else
                    log "WARNING" "No worker count specified for parallel execution, using default: ${PARALLEL_WORKERS}"
                    shift
                fi
                ;;
            -f|--failfast)
                FAILFAST=true
                shift
                ;;
            -s|--skip-slow)
                SKIP_SLOW=true
                shift
                ;;
            -d|--debug)
                DEBUG=true
                shift
                ;;
            -e|--environment)
                if [[ $# -gt 1 ]]; then
                    TEST_ENV=$2
                    shift 2
                else
                    log "WARNING" "No environment specified, using default: ${TEST_ENV}"
                    shift
                fi
                ;;
            *)
                # Assume it's a test path
                TEST_PATH=$1
                shift
                ;;
        esac
    done
}

# Main function
main() {
    log "INFO" "Starting NeuroCognitive Architecture test suite"
    
    # Parse command line arguments
    parse_args "$@"
    
    # Check dependencies
    check_dependencies
    
    # Clean previous test artifacts
    clean_artifacts
    
    # Run tests
    run_tests
    local exit_code=$?
    
    # Generate summary
    generate_summary ${exit_code}
    
    # Return the exit code from the tests
    return ${exit_code}
}

# Execute main function with all arguments
main "$@"