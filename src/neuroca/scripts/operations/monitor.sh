#!/bin/bash
#
# NeuroCognitive Architecture (NCA) System Monitoring Script
#
# This script provides comprehensive monitoring capabilities for the NCA system,
# including system health checks, resource usage monitoring, component status,
# and alert notifications. It can be run manually or as a scheduled task.
#
# Usage:
#   ./monitor.sh [options]
#
# Options:
#   -h, --help                 Display this help message
#   -c, --config <file>        Specify custom config file (default: ../../config/monitoring.conf)
#   -o, --output <format>      Output format: text, json, csv (default: text)
#   -l, --log-level <level>    Log level: debug, info, warn, error (default: info)
#   -a, --alert                Send alerts for critical issues
#   -s, --service <name>       Monitor specific service only
#   -t, --timeout <seconds>    Timeout for operations (default: 30)
#   -q, --quiet                Suppress non-error output
#
# Examples:
#   ./monitor.sh                           # Run all checks with default settings
#   ./monitor.sh --service memory          # Monitor only memory subsystem
#   ./monitor.sh --output json --alert     # Output in JSON and send alerts
#
# Author: NCA Team
# Version: 1.0.0
# License: Proprietary

set -eo pipefail

# =====================================================================
# Configuration and Constants
# =====================================================================

# Default configuration values
CONFIG_FILE="../../config/monitoring.conf"
OUTPUT_FORMAT="text"
LOG_LEVEL="info"
SEND_ALERTS=false
SPECIFIC_SERVICE=""
OPERATION_TIMEOUT=30
QUIET_MODE=false
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
LOG_FILE="/var/log/neuroca/monitoring_$(date +"%Y%m%d").log"
ALERT_THRESHOLD_CPU=90
ALERT_THRESHOLD_MEMORY=90
ALERT_THRESHOLD_DISK=90
ALERT_THRESHOLD_API_LATENCY=2000  # milliseconds

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true

# =====================================================================
# Helper Functions
# =====================================================================

# Function: Display help message
show_help() {
    grep "^#" "$0" | grep -v "#!/bin/bash" | sed 's/^# \?//'
    exit 0
}

# Function: Log messages with timestamp and level
log() {
    local level="$1"
    local message="$2"
    local log_entry="[$TIMESTAMP] [$level] $message"
    
    # Log levels: debug=0, info=1, warn=2, error=3
    local level_num=1
    case "$level" in
        "DEBUG") level_num=0 ;;
        "INFO")  level_num=1 ;;
        "WARN")  level_num=2 ;;
        "ERROR") level_num=3 ;;
    esac
    
    local current_level_num=1
    case "$LOG_LEVEL" in
        "debug") current_level_num=0 ;;
        "info")  current_level_num=1 ;;
        "warn")  current_level_num=2 ;;
        "error") current_level_num=3 ;;
    esac
    
    if [ $level_num -ge $current_level_num ]; then
        echo "$log_entry" >> "$LOG_FILE"
        
        if [ "$QUIET_MODE" = false ] || [ "$level" = "ERROR" ]; then
            echo "$log_entry"
        fi
    fi
}

# Function: Send alert notification
send_alert() {
    local subject="$1"
    local message="$2"
    local severity="$3"
    
    log "WARN" "Alert triggered: $subject - $message (Severity: $severity)"
    
    if [ "$SEND_ALERTS" = true ]; then
        # Check if alert script exists and is executable
        if [ -x "../../scripts/operations/send_alert.sh" ]; then
            log "DEBUG" "Sending alert via send_alert.sh"
            "../../scripts/operations/send_alert.sh" "$subject" "$message" "$severity" || log "ERROR" "Failed to send alert"
        else
            # Fallback to email if configured
            if command -v mail &> /dev/null && [ -n "$ALERT_EMAIL" ]; then
                log "DEBUG" "Sending alert via email to $ALERT_EMAIL"
                echo "$message" | mail -s "[NCA Alert][$severity] $subject" "$ALERT_EMAIL" || log "ERROR" "Failed to send email alert"
            else
                log "ERROR" "No alert mechanism available. Alert not sent: $subject"
            fi
        fi
    fi
}

# Function: Format output based on selected format
format_output() {
    local title="$1"
    local data="$2"
    
    case "$OUTPUT_FORMAT" in
        "json")
            # Convert to JSON format
            echo "\"$title\": {"
            echo "$data" | sed 's/^\(.*\): \(.*\)$/  "\1": "\2",/' | sed '$ s/,$//'
            echo "}"
            ;;
        "csv")
            # Convert to CSV format
            echo "Component,Metric,Value"
            echo "$data" | sed "s/^\(.*\): \(.*\)$/$title,\1,\2/"
            ;;
        *)
            # Default text format
            echo "=== $title ==="
            echo "$data"
            echo ""
            ;;
    esac
}

# Function: Load configuration file
load_config() {
    if [ -f "$CONFIG_FILE" ]; then
        log "DEBUG" "Loading configuration from $CONFIG_FILE"
        # shellcheck source=/dev/null
        source "$CONFIG_FILE"
    else
        log "WARN" "Configuration file not found: $CONFIG_FILE. Using defaults."
    fi
}

# Function: Check if a service is running
check_service_status() {
    local service_name="$1"
    local status
    
    log "DEBUG" "Checking status of service: $service_name"
    
    if command -v systemctl &> /dev/null; then
        if systemctl is-active --quiet "$service_name"; then
            status="Running"
        else
            status="Stopped"
        fi
    elif command -v service &> /dev/null; then
        if service "$service_name" status &> /dev/null; then
            status="Running"
        else
            status="Stopped"
        fi
    else
        # Fallback to process checking
        if pgrep -f "$service_name" &> /dev/null; then
            status="Running (process found)"
        else
            status="Stopped (no process)"
        fi
    fi
    
    echo "Status: $status"
    
    if [ "$status" != "Running" ] && [ "$status" != "Running (process found)" ]; then
        send_alert "Service Down" "Service $service_name is not running" "HIGH"
    fi
}

# =====================================================================
# Monitoring Functions
# =====================================================================

# Function: Monitor system resources
monitor_system_resources() {
    log "DEBUG" "Monitoring system resources"
    local output=""
    
    # CPU usage
    if command -v mpstat &> /dev/null; then
        cpu_idle=$(mpstat 1 1 | grep -A 5 "%idle" | tail -n 1 | awk '{print $NF}')
        cpu_usage=$(echo "100 - $cpu_idle" | bc)
    else
        cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
    fi
    output+="CPU Usage: ${cpu_usage}%\n"
    
    # Memory usage
    if command -v free &> /dev/null; then
        memory_info=$(free -m | grep Mem)
        total_memory=$(echo "$memory_info" | awk '{print $2}')
        used_memory=$(echo "$memory_info" | awk '{print $3}')
        memory_usage=$(echo "scale=2; $used_memory * 100 / $total_memory" | bc)
        output+="Memory Usage: ${memory_usage}% (${used_memory}MB/${total_memory}MB)\n"
    fi
    
    # Disk usage
    if command -v df &> /dev/null; then
        disk_usage=$(df -h / | grep -v Filesystem | awk '{print $5}' | sed 's/%//')
        disk_available=$(df -h / | grep -v Filesystem | awk '{print $4}')
        output+="Disk Usage: ${disk_usage}% (${disk_available} available)\n"
    fi
    
    # Load average
    if [ -f /proc/loadavg ]; then
        load_avg=$(cat /proc/loadavg | awk '{print $1, $2, $3}')
        output+="Load Average: ${load_avg}\n"
    fi
    
    # Check for resource alerts
    if [ "${cpu_usage%.*}" -gt "$ALERT_THRESHOLD_CPU" ]; then
        send_alert "High CPU Usage" "CPU usage is at ${cpu_usage}%" "MEDIUM"
    fi
    
    if [ "${memory_usage%.*}" -gt "$ALERT_THRESHOLD_MEMORY" ]; then
        send_alert "High Memory Usage" "Memory usage is at ${memory_usage}%" "MEDIUM"
    fi
    
    if [ "$disk_usage" -gt "$ALERT_THRESHOLD_DISK" ]; then
        send_alert "High Disk Usage" "Disk usage is at ${disk_usage}%" "MEDIUM"
    fi
    
    format_output "System Resources" "${output%\\n}"
}

# Function: Monitor NCA core services
monitor_core_services() {
    log "DEBUG" "Monitoring NCA core services"
    local output=""
    
    # Core service status checks
    local services=("neuroca-api" "neuroca-memory" "neuroca-integration")
    
    for service in "${services[@]}"; do
        output+="$service: $(check_service_status "$service")\n"
    done
    
    format_output "Core Services" "${output%\\n}"
}

# Function: Monitor memory subsystem
monitor_memory_subsystem() {
    log "DEBUG" "Monitoring memory subsystem"
    local output=""
    
    # Check memory tiers
    local memory_tiers=("working" "episodic" "semantic")
    
    for tier in "${memory_tiers[@]}"; do
        # Check if memory tier API endpoint is accessible
        if command -v curl &> /dev/null; then
            response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/api/memory/$tier/status" 2>/dev/null || echo "000")
            if [ "$response" = "200" ]; then
                status="Healthy"
            else
                status="Unhealthy (HTTP $response)"
                send_alert "Memory Tier Issue" "Memory tier $tier is unhealthy" "HIGH"
            fi
        else
            # Fallback to process check
            if pgrep -f "neuroca-memory-$tier" &> /dev/null; then
                status="Process running (API check unavailable)"
            else
                status="Process not found"
                send_alert "Memory Tier Issue" "Memory tier $tier process not found" "HIGH"
            fi
        fi
        
        output+="$tier Memory: $status\n"
    done
    
    # Check memory database connection
    if command -v pg_isready &> /dev/null && [ -n "$DB_HOST" ]; then
        if pg_isready -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t 5 &> /dev/null; then
            output+="Database Connection: Connected\n"
        else
            output+="Database Connection: Failed\n"
            send_alert "Database Connection Issue" "Cannot connect to memory database" "HIGH"
        fi
    else
        output+="Database Connection: Check unavailable\n"
    fi
    
    format_output "Memory Subsystem" "${output%\\n}"
}

# Function: Monitor API health
monitor_api_health() {
    log "DEBUG" "Monitoring API health"
    local output=""
    
    if command -v curl &> /dev/null; then
        # Check API endpoints
        local endpoints=("/health" "/api/status" "/api/memory/status")
        
        for endpoint in "${endpoints[@]}"; do
            start_time=$(date +%s%N)
            response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000$endpoint" 2>/dev/null || echo "000")
            end_time=$(date +%s%N)
            latency=$(( (end_time - start_time) / 1000000 ))
            
            if [ "$response" = "200" ]; then
                status="OK (${latency}ms)"
                
                if [ "$latency" -gt "$ALERT_THRESHOLD_API_LATENCY" ]; then
                    send_alert "API Latency Issue" "Endpoint $endpoint response time: ${latency}ms" "MEDIUM"
                fi
            else
                status="Failed (HTTP $response)"
                send_alert "API Endpoint Issue" "Endpoint $endpoint returned HTTP $response" "HIGH"
            fi
            
            output+="Endpoint $endpoint: $status\n"
        done
    else
        output+="API Check: curl not available\n"
    fi
    
    format_output "API Health" "${output%\\n}"
}

# Function: Monitor LLM integration
monitor_llm_integration() {
    log "DEBUG" "Monitoring LLM integration"
    local output=""
    
    # Check LLM service status
    output+="LLM Service: $(check_service_status "neuroca-llm-integration")\n"
    
    # Check LLM API connectivity
    if command -v curl &> /dev/null; then
        response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/api/llm/status" 2>/dev/null || echo "000")
        if [ "$response" = "200" ]; then
            output+="LLM API: Connected\n"
        else
            output+="LLM API: Disconnected (HTTP $response)\n"
            send_alert "LLM Integration Issue" "LLM API returned HTTP $response" "HIGH"
        fi
    else
        output+="LLM API: Check unavailable\n"
    fi
    
    format_output "LLM Integration" "${output%\\n}"
}

# Function: Run all monitoring checks
run_all_checks() {
    log "INFO" "Starting comprehensive system monitoring"
    
    # Run all monitoring functions
    monitor_system_resources
    monitor_core_services
    monitor_memory_subsystem
    monitor_api_health
    monitor_llm_integration
    
    log "INFO" "Monitoring completed successfully"
}

# =====================================================================
# Main Script Execution
# =====================================================================

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            show_help
            ;;
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_FORMAT="$2"
            shift 2
            ;;
        -l|--log-level)
            LOG_LEVEL="$2"
            shift 2
            ;;
        -a|--alert)
            SEND_ALERTS=true
            shift
            ;;
        -s|--service)
            SPECIFIC_SERVICE="$2"
            shift 2
            ;;
        -t|--timeout)
            OPERATION_TIMEOUT="$2"
            shift 2
            ;;
        -q|--quiet)
            QUIET_MODE=true
            shift
            ;;
        *)
            log "ERROR" "Unknown option: $1"
            show_help
            ;;
    esac
done

# Load configuration
load_config

# Set timeout for operations
export TIMEOUT="$OPERATION_TIMEOUT"

# Execute monitoring based on specified service or run all checks
if [ -n "$SPECIFIC_SERVICE" ]; then
    log "INFO" "Monitoring specific service: $SPECIFIC_SERVICE"
    case "$SPECIFIC_SERVICE" in
        "system")
            monitor_system_resources
            ;;
        "core")
            monitor_core_services
            ;;
        "memory")
            monitor_memory_subsystem
            ;;
        "api")
            monitor_api_health
            ;;
        "llm")
            monitor_llm_integration
            ;;
        *)
            log "ERROR" "Unknown service: $SPECIFIC_SERVICE"
            exit 1
            ;;
    esac
else
    run_all_checks
fi

exit 0