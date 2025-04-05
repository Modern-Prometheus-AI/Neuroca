#!/bin/bash
#
# NeuroCognitive Architecture (NCA) Deployment Script
# 
# This script handles the deployment of the NCA system to various environments.
# It supports different deployment targets (dev, staging, prod) and handles
# configuration, validation, deployment, and post-deployment verification.
#
# Usage:
#   ./deploy.sh [options]
#
# Options:
#   -e, --environment ENV   Deployment environment (dev, staging, prod) [default: dev]
#   -v, --version VERSION   Version to deploy [default: latest]
#   -c, --config FILE       Custom config file path
#   -d, --dry-run           Perform a dry run without actual deployment
#   -f, --force             Force deployment without confirmation
#   -h, --help              Display this help message
#
# Examples:
#   ./deploy.sh --environment prod --version 1.2.3
#   ./deploy.sh -e staging -v latest -c custom-config.yaml
#   ./deploy.sh --dry-run --environment prod
#
# Author: NCA Team
# Date: $(date +%Y-%m-%d)

set -eo pipefail

# ==============================
# Configuration and Constants
# ==============================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
LOG_DIR="${PROJECT_ROOT}/logs"
LOG_FILE="${LOG_DIR}/deployment_$(date +%Y%m%d_%H%M%S).log"
CONFIG_DIR="${PROJECT_ROOT}/config"
DEFAULT_CONFIG="${CONFIG_DIR}/deployment.yaml"

# Default values
ENVIRONMENT="dev"
VERSION="latest"
CONFIG_FILE="${DEFAULT_CONFIG}"
DRY_RUN=false
FORCE=false

# Deployment targets
DEPLOYMENT_TARGETS=(
  "dev"
  "staging"
  "prod"
)

# Required tools
REQUIRED_TOOLS=(
  "docker"
  "docker-compose"
  "kubectl"
  "helm"
  "aws"
  "jq"
)

# ==============================
# Helper Functions
# ==============================

# Setup logging
setup_logging() {
  mkdir -p "${LOG_DIR}"
  touch "${LOG_FILE}"
  exec > >(tee -a "${LOG_FILE}") 2>&1
  echo "Logging to ${LOG_FILE}"
}

# Log message with timestamp and level
log() {
  local level=$1
  shift
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] [${level}] $*"
}

log_info() {
  log "INFO" "$@"
}

log_warn() {
  log "WARN" "$@"
}

log_error() {
  log "ERROR" "$@"
}

log_debug() {
  if [[ "${VERBOSE}" == "true" ]]; then
    log "DEBUG" "$@"
  fi
}

# Display help message
show_help() {
  grep "^#" "$0" | grep -v "!/bin/bash" | sed 's/^# //g; s/^#//g'
  exit 0
}

# Check if required tools are installed
check_requirements() {
  log_info "Checking required tools..."
  local missing_tools=()
  
  for tool in "${REQUIRED_TOOLS[@]}"; do
    if ! command -v "${tool}" &> /dev/null; then
      missing_tools+=("${tool}")
    fi
  done
  
  if [[ ${#missing_tools[@]} -gt 0 ]]; then
    log_error "Missing required tools: ${missing_tools[*]}"
    log_error "Please install these tools before running the deployment script."
    exit 1
  fi
  
  log_info "All required tools are available."
}

# Validate environment
validate_environment() {
  local valid=false
  for env in "${DEPLOYMENT_TARGETS[@]}"; do
    if [[ "${ENVIRONMENT}" == "${env}" ]]; then
      valid=true
      break
    fi
  done
  
  if [[ "${valid}" != "true" ]]; then
    log_error "Invalid environment: ${ENVIRONMENT}"
    log_error "Valid environments are: ${DEPLOYMENT_TARGETS[*]}"
    exit 1
  fi
  
  log_info "Environment validated: ${ENVIRONMENT}"
}

# Validate configuration file
validate_config() {
  if [[ ! -f "${CONFIG_FILE}" ]]; then
    log_error "Configuration file not found: ${CONFIG_FILE}"
    exit 1
  fi
  
  # Basic YAML validation
  if command -v python3 &> /dev/null; then
    if ! python3 -c "import yaml; yaml.safe_load(open('${CONFIG_FILE}'))" &> /dev/null; then
      log_error "Invalid YAML in configuration file: ${CONFIG_FILE}"
      exit 1
    fi
  else
    log_warn "Python3 not found, skipping YAML validation"
  fi
  
  log_info "Configuration file validated: ${CONFIG_FILE}"
}

# Load configuration
load_config() {
  log_info "Loading configuration from ${CONFIG_FILE}..."
  
  # Extract environment-specific configuration
  # This is a simplified example - in production, use a proper YAML parser
  if command -v yq &> /dev/null; then
    DEPLOY_NAMESPACE=$(yq eval ".environments.${ENVIRONMENT}.namespace" "${CONFIG_FILE}")
    DEPLOY_REPLICAS=$(yq eval ".environments.${ENVIRONMENT}.replicas" "${CONFIG_FILE}")
    DEPLOY_RESOURCES=$(yq eval ".environments.${ENVIRONMENT}.resources" "${CONFIG_FILE}")
  else
    log_warn "yq not found, using grep/sed for config parsing (limited functionality)"
    DEPLOY_NAMESPACE=$(grep -A10 "${ENVIRONMENT}:" "${CONFIG_FILE}" | grep "namespace:" | head -1 | sed 's/.*namespace: *//g')
    DEPLOY_REPLICAS=$(grep -A10 "${ENVIRONMENT}:" "${CONFIG_FILE}" | grep "replicas:" | head -1 | sed 's/.*replicas: *//g')
  fi
  
  # Set defaults if values are empty
  DEPLOY_NAMESPACE=${DEPLOY_NAMESPACE:-"neuroca-${ENVIRONMENT}"}
  DEPLOY_REPLICAS=${DEPLOY_REPLICAS:-1}
  
  log_info "Loaded configuration for environment: ${ENVIRONMENT}"
  log_debug "Namespace: ${DEPLOY_NAMESPACE}"
  log_debug "Replicas: ${DEPLOY_REPLICAS}"
}

# Prepare deployment artifacts
prepare_deployment() {
  log_info "Preparing deployment artifacts..."
  
  # Create temporary directory for deployment artifacts
  DEPLOY_TMP_DIR=$(mktemp -d)
  log_debug "Created temporary directory: ${DEPLOY_TMP_DIR}"
  
  # Copy necessary files to the temporary directory
  cp -r "${PROJECT_ROOT}/infrastructure/kubernetes" "${DEPLOY_TMP_DIR}/"
  cp "${CONFIG_FILE}" "${DEPLOY_TMP_DIR}/config.yaml"
  
  # Replace placeholders in template files
  find "${DEPLOY_TMP_DIR}" -type f -name "*.yaml" -o -name "*.yml" | while read -r file; do
    sed -i.bak "s|{{ENVIRONMENT}}|${ENVIRONMENT}|g" "${file}"
    sed -i.bak "s|{{VERSION}}|${VERSION}|g" "${file}"
    sed -i.bak "s|{{NAMESPACE}}|${DEPLOY_NAMESPACE}|g" "${file}"
    sed -i.bak "s|{{REPLICAS}}|${DEPLOY_REPLICAS}|g" "${file}"
    rm "${file}.bak"
  done
  
  log_info "Deployment artifacts prepared in ${DEPLOY_TMP_DIR}"
}

# Execute deployment
execute_deployment() {
  if [[ "${DRY_RUN}" == "true" ]]; then
    log_info "DRY RUN: Would deploy to ${ENVIRONMENT} environment"
    log_info "DRY RUN: Deployment files would be applied from ${DEPLOY_TMP_DIR}"
    return 0
  fi
  
  log_info "Executing deployment to ${ENVIRONMENT} environment..."
  
  # Create namespace if it doesn't exist
  if ! kubectl get namespace "${DEPLOY_NAMESPACE}" &> /dev/null; then
    log_info "Creating namespace: ${DEPLOY_NAMESPACE}"
    kubectl create namespace "${DEPLOY_NAMESPACE}"
  fi
  
  # Apply Kubernetes manifests
  log_info "Applying Kubernetes manifests..."
  kubectl apply -f "${DEPLOY_TMP_DIR}/kubernetes" --namespace "${DEPLOY_NAMESPACE}"
  
  # Deploy using Helm if charts are available
  if [[ -d "${DEPLOY_TMP_DIR}/kubernetes/helm" ]]; then
    log_info "Deploying Helm charts..."
    helm upgrade --install neuroca "${DEPLOY_TMP_DIR}/kubernetes/helm" \
      --namespace "${DEPLOY_NAMESPACE}" \
      --set environment="${ENVIRONMENT}" \
      --set version="${VERSION}" \
      --set replicas="${DEPLOY_REPLICAS}"
  fi
  
  log_info "Deployment executed successfully"
}

# Verify deployment
verify_deployment() {
  if [[ "${DRY_RUN}" == "true" ]]; then
    log_info "DRY RUN: Would verify deployment in ${DEPLOY_NAMESPACE} namespace"
    return 0
  fi
  
  log_info "Verifying deployment..."
  
  # Wait for deployments to be ready
  kubectl get deployments -n "${DEPLOY_NAMESPACE}" -o name | while read -r deployment; do
    log_info "Waiting for ${deployment} to be ready..."
    kubectl rollout status "${deployment}" -n "${DEPLOY_NAMESPACE}" --timeout=300s
  done
  
  # Check pod status
  log_info "Checking pod status..."
  kubectl get pods -n "${DEPLOY_NAMESPACE}"
  
  # Verify services are running
  log_info "Checking service status..."
  kubectl get services -n "${DEPLOY_NAMESPACE}"
  
  log_info "Deployment verification completed"
}

# Cleanup resources
cleanup() {
  local exit_code=$?
  
  if [[ -n "${DEPLOY_TMP_DIR}" && -d "${DEPLOY_TMP_DIR}" ]]; then
    log_debug "Cleaning up temporary directory: ${DEPLOY_TMP_DIR}"
    rm -rf "${DEPLOY_TMP_DIR}"
  fi
  
  if [[ ${exit_code} -ne 0 ]]; then
    log_error "Deployment failed with exit code ${exit_code}"
    log_error "Check the log file for details: ${LOG_FILE}"
  else
    log_info "Deployment completed successfully"
  fi
  
  log_info "Deployment script finished at $(date '+%Y-%m-%d %H:%M:%S')"
  exit ${exit_code}
}

# ==============================
# Main Script
# ==============================

# Parse command line arguments
parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -e|--environment)
        ENVIRONMENT="$2"
        shift 2
        ;;
      -v|--version)
        VERSION="$2"
        shift 2
        ;;
      -c|--config)
        CONFIG_FILE="$2"
        shift 2
        ;;
      -d|--dry-run)
        DRY_RUN=true
        shift
        ;;
      -f|--force)
        FORCE=true
        shift
        ;;
      --verbose)
        VERBOSE=true
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
}

# Main function
main() {
  # Setup error handling and cleanup
  trap cleanup EXIT
  
  # Setup logging
  setup_logging
  
  log_info "Starting deployment script at $(date '+%Y-%m-%d %H:%M:%S')"
  log_info "Deployment parameters:"
  log_info "  Environment: ${ENVIRONMENT}"
  log_info "  Version: ${VERSION}"
  log_info "  Config file: ${CONFIG_FILE}"
  log_info "  Dry run: ${DRY_RUN}"
  
  # Check requirements
  check_requirements
  
  # Validate environment and configuration
  validate_environment
  validate_config
  
  # Load configuration
  load_config
  
  # Confirm deployment for production
  if [[ "${ENVIRONMENT}" == "prod" && "${FORCE}" != "true" && "${DRY_RUN}" != "true" ]]; then
    read -rp "You are about to deploy to PRODUCTION. Are you sure? (y/N): " confirm
    if [[ "${confirm}" != "y" && "${confirm}" != "Y" ]]; then
      log_info "Deployment to production cancelled by user"
      exit 0
    fi
  fi
  
  # Prepare deployment artifacts
  prepare_deployment
  
  # Execute deployment
  execute_deployment
  
  # Verify deployment
  verify_deployment
  
  log_info "Deployment process completed successfully"
}

# Parse arguments and run main function
parse_args "$@"
main