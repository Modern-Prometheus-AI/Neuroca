#!/usr/bin/env bash
# ==============================================================================
# NeuroCognitive Architecture (NCA) - Linting Script
# ==============================================================================
# This script runs linting tools on the codebase to ensure code quality and
# consistency. It supports Python linting (flake8, black, isort, mypy),
# shell script linting (shellcheck), and YAML validation.
#
# Usage:
#   ./scripts/development/lint.sh [options] [paths]
#
# Options:
#   -h, --help              Show this help message
#   -f, --fix               Automatically fix issues where possible
#   -p, --python-only       Only run Python linters
#   -s, --shell-only        Only run shell script linters
#   -y, --yaml-only         Only run YAML validation
#   -v, --verbose           Increase verbosity
#   -c, --ci                Run in CI mode (exit on first error)
#   --skip-black            Skip black formatting check
#   --skip-flake8           Skip flake8 check
#   --skip-isort            Skip isort import sorting check
#   --skip-mypy             Skip mypy type checking
#   --skip-shellcheck       Skip shellcheck validation
#   --skip-yamllint         Skip YAML linting
#
# Examples:
#   ./scripts/development/lint.sh                     # Run all linters on the entire codebase
#   ./scripts/development/lint.sh -f                  # Run all linters and fix issues where possible
#   ./scripts/development/lint.sh -p ./neuroca/core/  # Run Python linters on the core module only
#   ./scripts/development/lint.sh --skip-mypy         # Run all linters except mypy
# ==============================================================================

set -eo pipefail

# ==============================================================================
# Configuration
# ==============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../" && pwd)"
LOG_FILE="${PROJECT_ROOT}/logs/lint.log"
PYTHON_FILES_PATTERN="\.py$"
SHELL_FILES_PATTERN="\.(sh|bash)$"
YAML_FILES_PATTERN="\.(yaml|yml)$"

# Default options
FIX_ISSUES=false
PYTHON_ONLY=false
SHELL_ONLY=false
YAML_ONLY=false
VERBOSE=false
CI_MODE=false
RUN_BLACK=true
RUN_FLAKE8=true
RUN_ISORT=true
RUN_MYPY=true
RUN_SHELLCHECK=true
RUN_YAMLLINT=true
PATHS=()

# ==============================================================================
# Helper Functions
# ==============================================================================

# Print colored output
print_color() {
    local color_code=$1
    local message=$2
    echo -e "\033[${color_code}m${message}\033[0m"
}

print_info() {
    print_color "1;34" "INFO: $1"  # Bold blue
    if [[ "${VERBOSE}" == true ]]; then
        echo "INFO: $1" >> "${LOG_FILE}"
    fi
}

print_success() {
    print_color "1;32" "SUCCESS: $1"  # Bold green
    echo "SUCCESS: $1" >> "${LOG_FILE}"
}

print_warning() {
    print_color "1;33" "WARNING: $1"  # Bold yellow
    echo "WARNING: $1" >> "${LOG_FILE}"
}

print_error() {
    print_color "1;31" "ERROR: $1"  # Bold red
    echo "ERROR: $1" >> "${LOG_FILE}"
}

print_header() {
    echo
    print_color "1;36" "==== $1 ===="  # Bold cyan
    echo
}

# Check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Exit with error
exit_with_error() {
    print_error "$1"
    exit 1
}

# Create log directory if it doesn't exist
setup_logging() {
    mkdir -p "$(dirname "${LOG_FILE}")"
    echo "=== Lint Run: $(date) ===" > "${LOG_FILE}"
}

# Show help message
show_help() {
    cat "${BASH_SOURCE[0]}" | grep -E '^# Usage:|^#   |^# Options:|^# Examples:' | sed -e 's/^# //' -e 's/^#//'
    exit 0
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                show_help
                ;;
            -f|--fix)
                FIX_ISSUES=true
                shift
                ;;
            -p|--python-only)
                PYTHON_ONLY=true
                shift
                ;;
            -s|--shell-only)
                SHELL_ONLY=true
                shift
                ;;
            -y|--yaml-only)
                YAML_ONLY=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -c|--ci)
                CI_MODE=true
                shift
                ;;
            --skip-black)
                RUN_BLACK=false
                shift
                ;;
            --skip-flake8)
                RUN_FLAKE8=false
                shift
                ;;
            --skip-isort)
                RUN_ISORT=false
                shift
                ;;
            --skip-mypy)
                RUN_MYPY=false
                shift
                ;;
            --skip-shellcheck)
                RUN_SHELLCHECK=false
                shift
                ;;
            --skip-yamllint)
                RUN_YAMLLINT=false
                shift
                ;;
            -*)
                exit_with_error "Unknown option: $1"
                ;;
            *)
                PATHS+=("$1")
                shift
                ;;
        esac
    done

    # If no paths specified, use the project root
    if [[ ${#PATHS[@]} -eq 0 ]]; then
        PATHS=("${PROJECT_ROOT}")
    fi
}

# Check if required tools are installed
check_dependencies() {
    local missing_deps=()

    if [[ "${PYTHON_ONLY}" == false && "${SHELL_ONLY}" == false && "${YAML_ONLY}" == false ]] || [[ "${PYTHON_ONLY}" == true ]]; then
        if [[ "${RUN_BLACK}" == true ]] && ! command_exists black; then
            missing_deps+=("black")
        fi
        if [[ "${RUN_FLAKE8}" == true ]] && ! command_exists flake8; then
            missing_deps+=("flake8")
        fi
        if [[ "${RUN_ISORT}" == true ]] && ! command_exists isort; then
            missing_deps+=("isort")
        fi
        if [[ "${RUN_MYPY}" == true ]] && ! command_exists mypy; then
            missing_deps+=("mypy")
        fi
    fi

    if [[ "${PYTHON_ONLY}" == false && "${SHELL_ONLY}" == false && "${YAML_ONLY}" == false ]] || [[ "${SHELL_ONLY}" == true ]]; then
        if [[ "${RUN_SHELLCHECK}" == true ]] && ! command_exists shellcheck; then
            missing_deps+=("shellcheck")
        fi
    fi

    if [[ "${PYTHON_ONLY}" == false && "${SHELL_ONLY}" == false && "${YAML_ONLY}" == false ]] || [[ "${YAML_ONLY}" == true ]]; then
        if [[ "${RUN_YAMLLINT}" == true ]] && ! command_exists yamllint; then
            missing_deps+=("yamllint")
        fi
    fi

    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        print_error "Missing dependencies: ${missing_deps[*]}"
        print_info "Please install missing dependencies with:"
        print_info "pip install ${missing_deps[*]}"
        exit 1
    fi
}

# Find files to lint
find_files() {
    local pattern=$1
    local files=()
    
    for path in "${PATHS[@]}"; do
        if [[ -f "${path}" ]]; then
            if [[ "${path}" =~ ${pattern} ]]; then
                files+=("${path}")
            fi
        else
            while IFS= read -r file; do
                files+=("$file")
            done < <(find "${path}" -type f -regextype posix-extended -regex ".*${pattern}" -not -path "*/\.*" -not -path "*/venv/*" -not -path "*/node_modules/*" -not -path "*/build/*" -not -path "*/dist/*" 2>/dev/null || true)
        fi
    done
    
    echo "${files[@]}"
}

# ==============================================================================
# Linting Functions
# ==============================================================================

# Run black formatter
run_black() {
    local files=("$@")
    if [[ ${#files[@]} -eq 0 ]]; then
        print_info "No Python files to format with black"
        return 0
    fi

    print_header "Running black formatter"
    
    local black_args=("--check")
    if [[ "${FIX_ISSUES}" == true ]]; then
        black_args=()
    fi
    
    if [[ "${VERBOSE}" == true ]]; then
        black_args+=("--verbose")
    fi
    
    if black "${black_args[@]}" "${files[@]}" 2>&1 | tee -a "${LOG_FILE}"; then
        print_success "Black formatting check passed"
        return 0
    else
        local msg="Black formatting check failed"
        if [[ "${FIX_ISSUES}" == false ]]; then
            msg+=" (run with -f to fix)"
        fi
        
        if [[ "${CI_MODE}" == true ]]; then
            exit_with_error "${msg}"
        else
            print_error "${msg}"
            return 1
        fi
    fi
}

# Run flake8 linter
run_flake8() {
    local files=("$@")
    if [[ ${#files[@]} -eq 0 ]]; then
        print_info "No Python files to check with flake8"
        return 0
    fi

    print_header "Running flake8 linter"
    
    if flake8 "${files[@]}" 2>&1 | tee -a "${LOG_FILE}"; then
        print_success "Flake8 check passed"
        return 0
    else
        if [[ "${CI_MODE}" == true ]]; then
            exit_with_error "Flake8 check failed"
        else
            print_error "Flake8 check failed"
            return 1
        fi
    fi
}

# Run isort import sorter
run_isort() {
    local files=("$@")
    if [[ ${#files[@]} -eq 0 ]]; then
        print_info "No Python files to check with isort"
        return 0
    fi

    print_header "Running isort import sorter"
    
    local isort_args=("--check-only")
    if [[ "${FIX_ISSUES}" == true ]]; then
        isort_args=()
    fi
    
    if [[ "${VERBOSE}" == true ]]; then
        isort_args+=("--verbose")
    fi
    
    if isort "${isort_args[@]}" "${files[@]}" 2>&1 | tee -a "${LOG_FILE}"; then
        print_success "Import sorting check passed"
        return 0
    else
        local msg="Import sorting check failed"
        if [[ "${FIX_ISSUES}" == false ]]; then
            msg+=" (run with -f to fix)"
        fi
        
        if [[ "${CI_MODE}" == true ]]; then
            exit_with_error "${msg}"
        else
            print_error "${msg}"
            return 1
        fi
    fi
}

# Run mypy type checker
run_mypy() {
    local files=("$@")
    if [[ ${#files[@]} -eq 0 ]]; then
        print_info "No Python files to check with mypy"
        return 0
    fi

    print_header "Running mypy type checker"
    
    local mypy_args=()
    if [[ "${VERBOSE}" == true ]]; then
        mypy_args+=("--verbose")
    fi
    
    if mypy "${mypy_args[@]}" "${files[@]}" 2>&1 | tee -a "${LOG_FILE}"; then
        print_success "Type checking passed"
        return 0
    else
        if [[ "${CI_MODE}" == true ]]; then
            exit_with_error "Type checking failed"
        else
            print_error "Type checking failed"
            return 1
        fi
    fi
}

# Run shellcheck
run_shellcheck() {
    local files=("$@")
    if [[ ${#files[@]} -eq 0 ]]; then
        print_info "No shell scripts to check with shellcheck"
        return 0
    fi

    print_header "Running shellcheck"
    
    local shellcheck_args=()
    if [[ "${VERBOSE}" == true ]]; then
        shellcheck_args+=("-v")
    fi
    
    if shellcheck "${shellcheck_args[@]}" "${files[@]}" 2>&1 | tee -a "${LOG_FILE}"; then
        print_success "Shell script check passed"
        return 0
    else
        if [[ "${CI_MODE}" == true ]]; then
            exit_with_error "Shell script check failed"
        else
            print_error "Shell script check failed"
            return 1
        fi
    fi
}

# Run yamllint
run_yamllint() {
    local files=("$@")
    if [[ ${#files[@]} -eq 0 ]]; then
        print_info "No YAML files to check with yamllint"
        return 0
    fi

    print_header "Running yamllint"
    
    local yamllint_args=()
    if [[ "${VERBOSE}" == true ]]; then
        yamllint_args+=("-v")
    fi
    
    if yamllint "${yamllint_args[@]}" "${files[@]}" 2>&1 | tee -a "${LOG_FILE}"; then
        print_success "YAML validation passed"
        return 0
    else
        if [[ "${CI_MODE}" == true ]]; then
            exit_with_error "YAML validation failed"
        else
            print_error "YAML validation failed"
            return 1
        fi
    fi
}

# ==============================================================================
# Main Script
# ==============================================================================

main() {
    # Setup
    setup_logging
    parse_args "$@"
    check_dependencies
    
    # Track overall success
    local success=true
    
    # Run Python linters
    if [[ "${PYTHON_ONLY}" == false && "${SHELL_ONLY}" == false && "${YAML_ONLY}" == false ]] || [[ "${PYTHON_ONLY}" == true ]]; then
        local python_files=($(find_files "${PYTHON_FILES_PATTERN}"))
        
        if [[ "${RUN_BLACK}" == true ]]; then
            run_black "${python_files[@]}" || success=false
        fi
        
        if [[ "${RUN_FLAKE8}" == true ]]; then
            run_flake8 "${python_files[@]}" || success=false
        fi
        
        if [[ "${RUN_ISORT}" == true ]]; then
            run_isort "${python_files[@]}" || success=false
        fi
        
        if [[ "${RUN_MYPY}" == true ]]; then
            run_mypy "${python_files[@]}" || success=false
        fi
    fi
    
    # Run shell script linters
    if [[ "${PYTHON_ONLY}" == false && "${SHELL_ONLY}" == false && "${YAML_ONLY}" == false ]] || [[ "${SHELL_ONLY}" == true ]]; then
        local shell_files=($(find_files "${SHELL_FILES_PATTERN}"))
        
        if [[ "${RUN_SHELLCHECK}" == true ]]; then
            run_shellcheck "${shell_files[@]}" || success=false
        fi
    fi
    
    # Run YAML validators
    if [[ "${PYTHON_ONLY}" == false && "${SHELL_ONLY}" == false && "${YAML_ONLY}" == false ]] || [[ "${YAML_ONLY}" == true ]]; then
        local yaml_files=($(find_files "${YAML_FILES_PATTERN}"))
        
        if [[ "${RUN_YAMLLINT}" == true ]]; then
            run_yamllint "${yaml_files[@]}" || success=false
        fi
    fi
    
    # Final summary
    echo
    if [[ "${success}" == true ]]; then
        print_success "All linting checks passed!"
        exit 0
    else
        print_error "Some linting checks failed. See log for details: ${LOG_FILE}"
        exit 1
    fi
}

# Run the script
main "$@"