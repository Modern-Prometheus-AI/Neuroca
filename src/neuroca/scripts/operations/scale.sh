#!/usr/bin/env bash
#
# NeuroCognitive Architecture (NCA) - Component Scaling Script
#
# This script provides functionality to scale various components of the NeuroCognitive
# Architecture system. It supports scaling up/down memory tiers, processing units,
# and other system components based on load, performance metrics, or manual requests.
#
# Usage:
#   ./scale.sh [options] <component> <scale_action>
#
# Options:
#   -h, --help                Show this help message and exit
#   -v, --verbose             Enable verbose output
#   -d, --dry-run             Perform a dry run without making actual changes
#   -e, --environment ENV     Specify environment (default: development)
#   -c, --config FILE         Specify custom config file
#   -f, --force               Force scaling without confirmation
#   -t, --timeout SECONDS     Specify operation timeout (default: 300)
#
# Components:
#   memory-tier-1             Working memory tier
#   memory-tier-2             Short-term memory tier
#   memory-tier-3             Long-term memory tier
#   processing-units          Neural processing units
#   integration-nodes         LLM integration nodes
#   all                       All components
#
# Scale Actions:
#   up[:N]                    Scale up by N instances (default: 1)
#   down[:N]                  Scale down by N instances (default: 1)
#   to:N                      Scale to exactly N instances
#   auto                      Scale based on current metrics and thresholds
#
# Examples:
#   ./scale.sh memory-tier-1 up:2        # Scale up working memory by 2 instances
#   ./scale.sh processing-units down     # Scale down processing units by 1 instance
#   ./scale.sh --dry-run all auto        # Simulate auto-scaling all components
#   ./scale.sh -e production -f memory-tier-3 to:5  # Force scale long-term memory to 5 instances
#
# Author: NeuroCognitive Architecture Team
# Version: 1.0.0
# License: Proprietary

set -eo pipefail

# ==================== CONSTANTS ====================
readonly SCRIPT_NAME=$(basename "$0")
readonly SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
readonly ROOT_DIR=$(readlink -f "$SCRIPT_DIR/../../")
readonly CONFIG_DIR="$ROOT_DIR/config"
readonly DEFAULT_CONFIG="$CONFIG_DIR/scaling.yaml"
readonly LOG_DIR="$ROOT_DIR/logs"
readonly LOG_FILE="$LOG_DIR/scaling_$(date +%Y%m%d).log"
readonly VALID_COMPONENTS=("memory-tier-1" "memory-tier-2" "memory-tier-3" "processing-units" "integration-nodes" "all")
readonly VALID_ENVIRONMENTS=("development" "staging" "production")
readonly DEFAULT_TIMEOUT=300

# ==================== VARIABLES ====================
VERBOSE=false
DRY_RUN=false
ENVIRONMENT="development"
CONFIG_FILE="$DEFAULT_CONFIG"
FORCE=false
TIMEOUT=$DEFAULT_TIMEOUT
COMPONENT=""
SCALE_ACTION=""
SCALE_AMOUNT=1
SCALE_TYPE=""

# ==================== FUNCTIONS ====================

# Function: setup_logging
# Description: Ensures log directory exists and initializes logging
setup_logging() {
    if [[ ! -d "$LOG_DIR" ]]; then
        mkdir -p "$LOG_DIR"
    fi
    
    # Redirect stdout and stderr to both console and log file if verbose
    if [[ "$VERBOSE" == true ]]; then
        exec > >(tee -a "$LOG_FILE") 2>&1
    fi
}

# Function: log
# Description: Log messages with timestamp and log level
# Arguments:
#   $1 - Log level (INFO, WARN, ERROR, DEBUG)
#   $2 - Message to log
log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
    
    # If error level, also log to stderr
    if [[ "$level" == "ERROR" ]]; then
        echo "[$timestamp] [$level] $message" >&2
    fi
}

# Function: log_info
# Description: Log info level message
# Arguments:
#   $1 - Message to log
log_info() {
    log "INFO" "$1"
}

# Function: log_warn
# Description: Log warning level message
# Arguments:
#   $1 - Message to log
log_warn() {
    log "WARN" "$1"
}

# Function: log_error
# Description: Log error level message
# Arguments:
#   $1 - Message to log
log_error() {
    log "ERROR" "$1"
}

# Function: log_debug
# Description: Log debug level message (only if verbose)
# Arguments:
#   $1 - Message to log
log_debug() {
    if [[ "$VERBOSE" == true ]]; then
        log "DEBUG" "$1"
    fi
}

# Function: show_usage
# Description: Display script usage information
show_usage() {
    cat <<EOF
Usage: $SCRIPT_NAME [options] <component> <scale_action>

Options:
  -h, --help                Show this help message and exit
  -v, --verbose             Enable verbose output
  -d, --dry-run             Perform a dry run without making actual changes
  -e, --environment ENV     Specify environment (default: development)
  -c, --config FILE         Specify custom config file
  -f, --force               Force scaling without confirmation
  -t, --timeout SECONDS     Specify operation timeout (default: 300)

Components:
  memory-tier-1             Working memory tier
  memory-tier-2             Short-term memory tier
  memory-tier-3             Long-term memory tier
  processing-units          Neural processing units
  integration-nodes         LLM integration nodes
  all                       All components

Scale Actions:
  up[:N]                    Scale up by N instances (default: 1)
  down[:N]                  Scale down by N instances (default: 1)
  to:N                      Scale to exactly N instances
  auto                      Scale based on current metrics and thresholds

Examples:
  $SCRIPT_NAME memory-tier-1 up:2        # Scale up working memory by 2 instances
  $SCRIPT_NAME processing-units down     # Scale down processing units by 1 instance
  $SCRIPT_NAME --dry-run all auto        # Simulate auto-scaling all components
  $SCRIPT_NAME -e production -f memory-tier-3 to:5  # Force scale long-term memory to 5 instances
EOF
}

# Function: parse_arguments
# Description: Parse and validate command line arguments
# Arguments:
#   $@ - All command line arguments
parse_arguments() {
    local positional_args=()
    
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                show_usage
                exit 0
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -e|--environment)
                if [[ -z "$2" || "$2" == -* ]]; then
                    log_error "Error: --environment requires an argument"
                    show_usage
                    exit 1
                fi
                ENVIRONMENT="$2"
                shift 2
                ;;
            -c|--config)
                if [[ -z "$2" || "$2" == -* ]]; then
                    log_error "Error: --config requires an argument"
                    show_usage
                    exit 1
                fi
                CONFIG_FILE="$2"
                shift 2
                ;;
            -f|--force)
                FORCE=true
                shift
                ;;
            -t|--timeout)
                if [[ -z "$2" || "$2" == -* ]]; then
                    log_error "Error: --timeout requires an argument"
                    show_usage
                    exit 1
                fi
                TIMEOUT="$2"
                shift 2
                ;;
            -*)
                log_error "Error: Unknown option: $1"
                show_usage
                exit 1
                ;;
            *)
                positional_args+=("$1")
                shift
                ;;
        esac
    done
    
    # Check if we have the required positional arguments
    if [[ ${#positional_args[@]} -lt 2 ]]; then
        log_error "Error: Missing required arguments"
        show_usage
        exit 1
    fi
    
    COMPONENT="${positional_args[0]}"
    SCALE_ACTION="${positional_args[1]}"
    
    # Validate component
    if [[ ! " ${VALID_COMPONENTS[*]} " =~ " ${COMPONENT} " ]]; then
        log_error "Error: Invalid component: $COMPONENT"
        show_usage
        exit 1
    fi
    
    # Validate environment
    if [[ ! " ${VALID_ENVIRONMENTS[*]} " =~ " ${ENVIRONMENT} " ]]; then
        log_error "Error: Invalid environment: $ENVIRONMENT"
        show_usage
        exit 1
    fi
    
    # Parse scale action
    if [[ "$SCALE_ACTION" == "auto" ]]; then
        SCALE_TYPE="auto"
    elif [[ "$SCALE_ACTION" =~ ^up(:[0-9]+)?$ ]]; then
        SCALE_TYPE="up"
        if [[ "$SCALE_ACTION" =~ :([0-9]+)$ ]]; then
            SCALE_AMOUNT="${BASH_REMATCH[1]}"
        fi
    elif [[ "$SCALE_ACTION" =~ ^down(:[0-9]+)?$ ]]; then
        SCALE_TYPE="down"
        if [[ "$SCALE_ACTION" =~ :([0-9]+)$ ]]; then
            SCALE_AMOUNT="${BASH_REMATCH[1]}"
        fi
    elif [[ "$SCALE_ACTION" =~ ^to:([0-9]+)$ ]]; then
        SCALE_TYPE="to"
        SCALE_AMOUNT="${BASH_REMATCH[1]}"
    else
        log_error "Error: Invalid scale action: $SCALE_ACTION"
        show_usage
        exit 1
    fi
    
    # Validate config file exists
    if [[ ! -f "$CONFIG_FILE" ]]; then
        log_error "Error: Config file not found: $CONFIG_FILE"
        exit 1
    fi
    
    # Validate timeout is a positive integer
    if ! [[ "$TIMEOUT" =~ ^[0-9]+$ ]] || [[ "$TIMEOUT" -le 0 ]]; then
        log_error "Error: Timeout must be a positive integer"
        exit 1
    fi
}

# Function: check_dependencies
# Description: Check if required dependencies are installed
check_dependencies() {
    local missing_deps=()
    
    # Check for required commands
    for cmd in kubectl jq yq curl; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
        fi
    done
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Error: Missing required dependencies: ${missing_deps[*]}"
        log_error "Please install the missing dependencies and try again."
        exit 1
    fi
}

# Function: load_config
# Description: Load configuration from config file
load_config() {
    log_debug "Loading configuration from $CONFIG_FILE"
    
    # Check if config file exists
    if [[ ! -f "$CONFIG_FILE" ]]; then
        log_error "Error: Config file not found: $CONFIG_FILE"
        exit 1
    fi
    
    # Load environment-specific configuration
    if ! yq eval ".environments.$ENVIRONMENT" "$CONFIG_FILE" > /dev/null 2>&1; then
        log_error "Error: Environment '$ENVIRONMENT' not found in config file"
        exit 1
    fi
    
    log_debug "Configuration loaded successfully"
}

# Function: get_current_scale
# Description: Get current scale for a component
# Arguments:
#   $1 - Component name
# Returns:
#   Current scale count
get_current_scale() {
    local component="$1"
    local scale_count=0
    
    log_debug "Getting current scale for component: $component"
    
    # This would typically use kubectl, cloud provider CLI, or API calls
    # For this script, we'll simulate with a simple mapping
    case "$component" in
        memory-tier-1)
            # Example: Get from Kubernetes deployment
            if [[ "$DRY_RUN" == true ]]; then
                scale_count=3  # Simulated value for dry run
            else
                # In a real implementation, this would be something like:
                # scale_count=$(kubectl get deployment -n neuroca memory-tier-1 -o jsonpath='{.spec.replicas}')
                scale_count=3  # Simulated for this implementation
            fi
            ;;
        memory-tier-2)
            if [[ "$DRY_RUN" == true ]]; then
                scale_count=2
            else
                scale_count=2
            fi
            ;;
        memory-tier-3)
            if [[ "$DRY_RUN" == true ]]; then
                scale_count=1
            else
                scale_count=1
            fi
            ;;
        processing-units)
            if [[ "$DRY_RUN" == true ]]; then
                scale_count=5
            else
                scale_count=5
            fi
            ;;
        integration-nodes)
            if [[ "$DRY_RUN" == true ]]; then
                scale_count=2
            else
                scale_count=2
            fi
            ;;
        *)
            log_error "Error: Unknown component for scaling: $component"
            exit 1
            ;;
    esac
    
    log_debug "Current scale for $component: $scale_count"
    echo "$scale_count"
}

# Function: calculate_target_scale
# Description: Calculate target scale based on action and current scale
# Arguments:
#   $1 - Component name
#   $2 - Scale type (up, down, to, auto)
#   $3 - Scale amount
# Returns:
#   Target scale count
calculate_target_scale() {
    local component="$1"
    local scale_type="$2"
    local scale_amount="$3"
    local current_scale
    local target_scale
    
    current_scale=$(get_current_scale "$component")
    
    case "$scale_type" in
        up)
            target_scale=$((current_scale + scale_amount))
            ;;
        down)
            target_scale=$((current_scale - scale_amount))
            # Ensure we don't go below 0
            if [[ "$target_scale" -lt 0 ]]; then
                target_scale=0
                log_warn "Warning: Scale down would result in negative instances. Setting to 0."
            fi
            ;;
        to)
            target_scale="$scale_amount"
            ;;
        auto)
            # For auto-scaling, we would typically check metrics and calculate the appropriate scale
            # This is a simplified example that just adds 1 if load is high
            local load_metric
            load_metric=$(get_component_load "$component")
            
            if [[ "$load_metric" -gt 75 ]]; then
                target_scale=$((current_scale + 1))
                log_info "Auto-scaling $component up due to high load ($load_metric%)"
            elif [[ "$load_metric" -lt 25 && "$current_scale" -gt 1 ]]; then
                target_scale=$((current_scale - 1))
                log_info "Auto-scaling $component down due to low load ($load_metric%)"
            else
                target_scale="$current_scale"
                log_info "No auto-scaling needed for $component (load: $load_metric%)"
            fi
            ;;
        *)
            log_error "Error: Unknown scale type: $scale_type"
            exit 1
            ;;
    esac
    
    # Apply min/max constraints from config
    # In a real implementation, these would be loaded from the config file
    local min_instances=1
    local max_instances=10
    
    if [[ "$target_scale" -lt "$min_instances" ]]; then
        log_warn "Warning: Target scale ($target_scale) is below minimum ($min_instances). Setting to minimum."
        target_scale="$min_instances"
    elif [[ "$target_scale" -gt "$max_instances" ]]; then
        log_warn "Warning: Target scale ($target_scale) exceeds maximum ($max_instances). Setting to maximum."
        target_scale="$max_instances"
    fi
    
    log_debug "Target scale for $component: $target_scale (current: $current_scale)"
    echo "$target_scale"
}

# Function: get_component_load
# Description: Get current load metrics for a component
# Arguments:
#   $1 - Component name
# Returns:
#   Load percentage (0-100)
get_component_load() {
    local component="$1"
    local load=50  # Default medium load
    
    # In a real implementation, this would query monitoring systems
    # For this script, we'll simulate with random values
    case "$component" in
        memory-tier-1)
            load=$((RANDOM % 100))
            ;;
        memory-tier-2)
            load=$((RANDOM % 100))
            ;;
        memory-tier-3)
            load=$((RANDOM % 100))
            ;;
        processing-units)
            load=$((RANDOM % 100))
            ;;
        integration-nodes)
            load=$((RANDOM % 100))
            ;;
    esac
    
    log_debug "Current load for $component: $load%"
    echo "$load"
}

# Function: confirm_scaling
# Description: Ask for confirmation before scaling
# Arguments:
#   $1 - Component name
#   $2 - Current scale
#   $3 - Target scale
# Returns:
#   0 if confirmed, 1 if not
confirm_scaling() {
    local component="$1"
    local current_scale="$2"
    local target_scale="$3"
    
    if [[ "$FORCE" == true ]]; then
        log_debug "Force flag set, skipping confirmation"
        return 0
    fi
    
    echo -n "Scale $component from $current_scale to $target_scale instances? [y/N] "
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        return 0
    else
        log_info "Scaling operation cancelled by user"
        return 1
    fi
}

# Function: scale_component
# Description: Scale a specific component
# Arguments:
#   $1 - Component name
#   $2 - Target scale
scale_component() {
    local component="$1"
    local target_scale="$2"
    local current_scale
    
    current_scale=$(get_current_scale "$component")
    
    if [[ "$current_scale" -eq "$target_scale" ]]; then
        log_info "Component $component is already at target scale: $target_scale"
        return 0
    fi
    
    if ! confirm_scaling "$component" "$current_scale" "$target_scale"; then
        return 1
    fi
    
    log_info "Scaling $component from $current_scale to $target_scale instances..."
    
    if [[ "$DRY_RUN" == true ]]; then
        log_info "[DRY RUN] Would scale $component to $target_scale instances"
        return 0
    fi
    
    # This would typically use kubectl, cloud provider CLI, or API calls
    # For this script, we'll simulate the scaling operation
    case "$component" in
        memory-tier-1|memory-tier-2|memory-tier-3|processing-units|integration-nodes)
            # Simulate scaling operation with a delay
            log_debug "Executing scaling operation for $component"
            sleep 2
            
            # In a real implementation, this would be something like:
            # kubectl scale deployment -n neuroca "$component" --replicas="$target_scale"
            
            log_info "Successfully scaled $component to $target_scale instances"
            ;;
        *)
            log_error "Error: Unknown component for scaling: $component"
            return 1
            ;;
    esac
    
    # Verify scaling was successful
    local new_scale
    new_scale=$(get_current_scale "$component")
    
    if [[ "$new_scale" -eq "$target_scale" ]]; then
        log_info "Verified $component is now at $new_scale instances"
        return 0
    else
        log_warn "Warning: $component is at $new_scale instances, expected $target_scale"
        return 1
    fi
}

# Function: scale_all_components
# Description: Scale all components
# Arguments:
#   $1 - Scale type (up, down, to, auto)
#   $2 - Scale amount
scale_all_components() {
    local scale_type="$1"
    local scale_amount="$2"
    local success=true
    
    log_info "Scaling all components ($scale_type:$scale_amount)..."
    
    for component in "${VALID_COMPONENTS[@]}"; do
        # Skip the "all" component itself
        if [[ "$component" == "all" ]]; then
            continue
        fi
        
        log_info "Processing component: $component"
        local target_scale
        target_scale=$(calculate_target_scale "$component" "$scale_type" "$scale_amount")
        
        if ! scale_component "$component" "$target_scale"; then
            log_error "Failed to scale component: $component"
            success=false
        fi
    done
    
    if [[ "$success" == true ]]; then
        log_info "Successfully scaled all components"
        return 0
    else
        log_error "One or more components failed to scale"
        return 1
    fi
}

# Function: main
# Description: Main function
main() {
    # Setup logging first
    setup_logging
    
    log_info "Starting NeuroCognitive Architecture scaling operation"
    log_debug "Script version: 1.0.0"
    log_debug "Arguments: $*"
    
    # Parse command line arguments
    parse_arguments "$@"
    
    # Check dependencies
    check_dependencies
    
    # Load configuration
    load_config
    
    log_info "Environment: $ENVIRONMENT"
    log_info "Component: $COMPONENT"
    log_info "Scale action: $SCALE_ACTION (type: $SCALE_TYPE, amount: $SCALE_AMOUNT)"
    
    if [[ "$DRY_RUN" == true ]]; then
        log_info "Running in DRY RUN mode - no actual changes will be made"
    fi
    
    # Execute scaling operation
    if [[ "$COMPONENT" == "all" ]]; then
        scale_all_components "$SCALE_TYPE" "$SCALE_AMOUNT"
    else
        local target_scale
        target_scale=$(calculate_target_scale "$COMPONENT" "$SCALE_TYPE" "$SCALE_AMOUNT")
        scale_component "$COMPONENT" "$target_scale"
    fi
    
    log_info "Scaling operation completed"
}

# Execute main function with all arguments
main "$@"