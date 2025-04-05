"""
System Commands for NeuroCognitive Architecture (NCA)

This module provides command-line interface commands for system-level operations,
including diagnostics, health checks, configuration management, and system maintenance.
These commands are essential for operators and developers to monitor, maintain, and
troubleshoot the NCA system.

Usage:
    neuroca system status
    neuroca system health
    neuroca system config [--show | --reset | --update KEY=VALUE]
    neuroca system logs [--level LEVEL] [--component COMPONENT] [--tail N]
    neuroca system backup [--path PATH]
    neuroca system restore BACKUP_FILE
    neuroca system cleanup [--older-than DAYS] [--dry-run]
    neuroca system version

Examples:
    # Check system status
    $ neuroca system status
    
    # View and modify configuration
    $ neuroca system config --show
    $ neuroca system config --update memory.working_capacity=2048
    
    # View logs with filtering
    $ neuroca system logs --level ERROR --component memory.working
    
    # Create system backup
    $ neuroca system backup --path /path/to/backups/
"""

import datetime
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Optional

import click
import psutil
import yaml
from tabulate import tabulate

from neuroca.config import settings
from neuroca.core.exceptions import BackupRestoreError, ConfigurationError
from neuroca.core.utils.logging import configure_logger
from neuroca.memory import memory_manager
from neuroca.monitoring.health import HealthStatus, run_health_checks

# Configure logger for this module
logger = configure_logger(__name__)

# System component definitions for health checks
SYSTEM_COMPONENTS = [
    "database",
    "memory.working",
    "memory.episodic",
    "memory.semantic",
    "llm.integration",
    "api.service"
]

@click.group(name="system")
def system_commands():
    """System-level commands for NCA management and diagnostics."""
    pass


@system_commands.command(name="status")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format")
def status_command(json_output: bool):
    """
    Display the current status of the NCA system and its components.
    
    This command provides a comprehensive overview of the system's operational status,
    including component health, resource utilization, and configuration summary.
    """
    try:
        # Collect system information
        status_data = _collect_system_status()
        
        if json_output:
            click.echo(json.dumps(status_data, indent=2))
        else:
            _display_formatted_status(status_data)
        
        # Return appropriate exit code based on overall status
        if status_data["overall_status"] == "healthy":
            sys.exit(0)
        elif status_data["overall_status"] == "degraded":
            sys.exit(1)
        else:  # "unhealthy"
            sys.exit(2)
            
    except Exception as e:
        logger.error(f"Failed to retrieve system status: {str(e)}", exc_info=True)
        click.echo(f"Error: Failed to retrieve system status - {str(e)}")
        sys.exit(1)


@system_commands.command(name="health")
@click.option("--component", help="Check specific component health")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed health information")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format")
def health_command(component: Optional[str], verbose: bool, json_output: bool):
    """
    Run health checks on the NCA system or specific components.
    
    This command performs diagnostic checks to verify the operational status
    of system components and their dependencies. It helps identify issues
    that might affect system performance or reliability.
    """
    try:
        components_to_check = [component] if component else SYSTEM_COMPONENTS
        
        # Validate component name if specified
        if component and component not in SYSTEM_COMPONENTS:
            valid_components = ", ".join(SYSTEM_COMPONENTS)
            click.echo(f"Error: Unknown component '{component}'. Valid components: {valid_components}")
            sys.exit(1)
        
        # Run health checks
        health_results = run_health_checks(components_to_check, detailed=verbose)
        
        # Determine overall health status
        overall_status = _determine_overall_health(health_results)
        
        # Prepare output
        output_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "overall_status": overall_status.name.lower(),
            "components": health_results
        }
        
        if json_output:
            click.echo(json.dumps(output_data, indent=2))
        else:
            _display_formatted_health(output_data, verbose)
        
        # Return appropriate exit code based on overall status
        sys.exit(0 if overall_status == HealthStatus.HEALTHY else 1)
            
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        click.echo(f"Error: Health check failed - {str(e)}")
        sys.exit(1)


@system_commands.command(name="config")
@click.option("--show", is_flag=True, help="Show current configuration")
@click.option("--reset", is_flag=True, help="Reset configuration to defaults")
@click.option("--update", help="Update configuration (format: KEY=VALUE)")
@click.option("--file", type=click.Path(exists=True), help="Load configuration from file")
def config_command(show: bool, reset: bool, update: Optional[str], file: Optional[str]):
    """
    View or modify the NCA system configuration.
    
    This command allows operators to inspect the current configuration,
    reset to defaults, or update specific configuration values. Changes
    may require a system restart to take effect.
    """
    try:
        # Validate that only one operation is specified
        operations = sum([bool(show), bool(reset), bool(update), bool(file)])
        if operations > 1:
            click.echo("Error: Please specify only one operation (--show, --reset, --update, or --file)")
            sys.exit(1)
        elif operations == 0:
            # Default to showing configuration if no operation specified
            show = True
        
        # Handle configuration operations
        if show:
            _show_configuration()
        elif reset:
            _reset_configuration()
        elif update:
            _update_configuration(update)
        elif file:
            _load_configuration_from_file(file)
            
    except ConfigurationError as e:
        logger.error(f"Configuration error: {str(e)}")
        click.echo(f"Configuration error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error in config command: {str(e)}", exc_info=True)
        click.echo(f"Error: {str(e)}")
        sys.exit(1)


@system_commands.command(name="logs")
@click.option("--level", type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], 
              case_sensitive=False), help="Filter logs by level")
@click.option("--component", help="Filter logs by component")
@click.option("--tail", type=int, default=100, help="Number of recent log entries to show")
@click.option("--follow", "-f", is_flag=True, help="Follow log output")
@click.option("--since", help="Show logs since timestamp (format: YYYY-MM-DD[THH:MM:SS])")
def logs_command(level: Optional[str], component: Optional[str], tail: int, 
                follow: bool, since: Optional[str]):
    """
    View and filter system logs.
    
    This command provides access to the NCA system logs with filtering capabilities
    to help diagnose issues and monitor system behavior.
    """
    try:
        log_file = settings.LOGGING.LOG_FILE
        if not os.path.exists(log_file):
            click.echo(f"Error: Log file not found at {log_file}")
            sys.exit(1)
        
        # Parse the since timestamp if provided
        since_timestamp = None
        if since:
            try:
                since_timestamp = datetime.datetime.fromisoformat(since)
            except ValueError:
                click.echo("Error: Invalid timestamp format. Use YYYY-MM-DD[THH:MM:SS]")
                sys.exit(1)
        
        # Build the log filtering command
        cmd = ["tail"]
        if follow:
            cmd.append("-f")
        cmd.extend(["-n", str(tail), log_file])
        
        # Execute the command and filter the output
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
        
        try:
            for line in process.stdout:
                if _should_display_log_line(line, level, component, since_timestamp):
                    click.echo(line.rstrip())
                    
        except KeyboardInterrupt:
            process.terminate()
            process.wait()
            
    except Exception as e:
        logger.error(f"Error accessing logs: {str(e)}", exc_info=True)
        click.echo(f"Error: Failed to access logs - {str(e)}")
        sys.exit(1)


@system_commands.command(name="backup")
@click.option("--path", type=click.Path(file_okay=False), help="Backup destination directory")
@click.option("--include-logs", is_flag=True, help="Include log files in backup")
@click.option("--include-data", is_flag=True, default=True, help="Include database and memory data")
def backup_command(path: Optional[str], include_logs: bool, include_data: bool):
    """
    Create a backup of the NCA system.
    
    This command creates a comprehensive backup of the system configuration,
    database, and optionally log files. Backups are essential for disaster
    recovery and system migration.
    """
    try:
        # Determine backup path
        backup_path = path or settings.SYSTEM.BACKUP_DIR
        if not backup_path:
            backup_path = os.path.join(os.getcwd(), "backups")
        
        # Create backup directory if it doesn't exist
        os.makedirs(backup_path, exist_ok=True)
        
        # Generate backup filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"neuroca_backup_{timestamp}.zip"
        backup_file_path = os.path.join(backup_path, backup_filename)
        
        click.echo(f"Creating backup at: {backup_file_path}")
        
        # Perform the backup
        backup_result = _create_system_backup(
            backup_file_path, 
            include_logs=include_logs,
            include_data=include_data
        )
        
        if backup_result:
            click.echo(f"Backup completed successfully: {backup_file_path}")
            click.echo(f"Backup size: {_format_file_size(os.path.getsize(backup_file_path))}")
        else:
            click.echo("Backup failed. See logs for details.")
            sys.exit(1)
            
    except BackupRestoreError as e:
        logger.error(f"Backup error: {str(e)}")
        click.echo(f"Backup error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during backup: {str(e)}", exc_info=True)
        click.echo(f"Error: {str(e)}")
        sys.exit(1)


@system_commands.command(name="restore")
@click.argument("backup_file", type=click.Path(exists=True))
@click.option("--force", is_flag=True, help="Force restore without confirmation")
@click.option("--dry-run", is_flag=True, help="Verify backup without performing restore")
def restore_command(backup_file: str, force: bool, dry_run: bool):
    """
    Restore the NCA system from a backup.
    
    This command restores the system configuration and data from a previously
    created backup file. This operation will replace current system data.
    """
    try:
        # Verify backup file
        if not os.path.isfile(backup_file) or not backup_file.endswith(".zip"):
            click.echo("Error: Backup file must be a valid .zip archive")
            sys.exit(1)
        
        # Check backup integrity
        click.echo(f"Verifying backup file: {backup_file}")
        is_valid = _verify_backup_integrity(backup_file)
        
        if not is_valid:
            click.echo("Error: Backup file is corrupted or invalid")
            sys.exit(1)
            
        click.echo("Backup verification successful")
        
        if dry_run:
            click.echo("Dry run completed. Backup is valid and can be restored.")
            sys.exit(0)
        
        # Confirm restore operation
        if not force:
            click.confirm("This will replace your current system data. Continue?", abort=True)
        
        # Perform the restore
        click.echo("Restoring system from backup...")
        restore_result = _restore_system_from_backup(backup_file)
        
        if restore_result:
            click.echo("System successfully restored from backup")
            click.echo("Note: You may need to restart the system for changes to take effect")
        else:
            click.echo("Restore operation failed. See logs for details.")
            sys.exit(1)
            
    except BackupRestoreError as e:
        logger.error(f"Restore error: {str(e)}")
        click.echo(f"Restore error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during restore: {str(e)}", exc_info=True)
        click.echo(f"Error: {str(e)}")
        sys.exit(1)


@system_commands.command(name="cleanup")
@click.option("--older-than", type=int, default=30, 
              help="Remove files older than specified days")
@click.option("--include-logs", is_flag=True, help="Clean log files")
@click.option("--include-backups", is_flag=True, help="Clean old backups")
@click.option("--include-temp", is_flag=True, default=True, help="Clean temporary files")
@click.option("--dry-run", is_flag=True, help="Show what would be deleted without deleting")
def cleanup_command(older_than: int, include_logs: bool, include_backups: bool, 
                   include_temp: bool, dry_run: bool):
    """
    Clean up old files and temporary data.
    
    This command removes old log files, backups, and temporary data to free up
    disk space and maintain system performance.
    """
    try:
        if not any([include_logs, include_backups, include_temp]):
            click.echo("Error: Specify at least one type of files to clean up")
            sys.exit(1)
        
        # Calculate cutoff date
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=older_than)
        click.echo(f"Cleaning up files older than: {cutoff_date.strftime('%Y-%m-%d')}")
        
        if dry_run:
            click.echo("Dry run mode: No files will be deleted")
        
        deleted_count = 0
        freed_space = 0
        
        # Clean up log files
        if include_logs:
            log_dir = os.path.dirname(settings.LOGGING.LOG_FILE)
            log_results = _cleanup_directory(
                log_dir, 
                cutoff_date, 
                pattern="*.log*", 
                dry_run=dry_run
            )
            deleted_count += log_results[0]
            freed_space += log_results[1]
        
        # Clean up backup files
        if include_backups:
            backup_dir = settings.SYSTEM.BACKUP_DIR
            if backup_dir and os.path.exists(backup_dir):
                backup_results = _cleanup_directory(
                    backup_dir, 
                    cutoff_date, 
                    pattern="neuroca_backup_*.zip", 
                    dry_run=dry_run
                )
                deleted_count += backup_results[0]
                freed_space += backup_results[1]
        
        # Clean up temporary files
        if include_temp:
            temp_dir = settings.SYSTEM.TEMP_DIR
            if temp_dir and os.path.exists(temp_dir):
                temp_results = _cleanup_directory(
                    temp_dir, 
                    cutoff_date, 
                    pattern="*", 
                    dry_run=dry_run
                )
                deleted_count += temp_results[0]
                freed_space += temp_results[1]
        
        # Report results
        if dry_run:
            click.echo(f"Would delete {deleted_count} files, freeing {_format_file_size(freed_space)}")
        else:
            click.echo(f"Deleted {deleted_count} files, freed {_format_file_size(freed_space)}")
            
    except Exception as e:
        logger.error(f"Cleanup error: {str(e)}", exc_info=True)
        click.echo(f"Error: {str(e)}")
        sys.exit(1)


@system_commands.command(name="version")
def version_command():
    """
    Display version information for the NCA system and its components.
    
    This command shows the current version of the NCA system and its
    dependencies, which is useful for troubleshooting and ensuring
    compatibility.
    """
    try:
        # Get version information
        version_info = _get_version_info()
        
        # Display version information
        click.echo("NeuroCognitive Architecture (NCA) System")
        click.echo(f"Version: {version_info['version']}")
        click.echo(f"Build: {version_info['build']}")
        click.echo(f"Python: {version_info['python']}")
        click.echo(f"Platform: {version_info['platform']}")
        
        click.echo("\nComponent Versions:")
        for component, version in version_info['components'].items():
            click.echo(f"  {component}: {version}")
            
    except Exception as e:
        logger.error(f"Error retrieving version information: {str(e)}", exc_info=True)
        click.echo(f"Error: {str(e)}")
        sys.exit(1)


# Helper functions

def _collect_system_status() -> dict[str, Any]:
    """
    Collect comprehensive system status information.
    
    Returns:
        Dict containing system status information
    """
    # Get basic system information
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Get component status through health checks
    component_status = run_health_checks(SYSTEM_COMPONENTS)
    
    # Determine overall status based on component health
    overall_status = _determine_overall_health(component_status).name.lower()
    
    # Build the complete status data structure
    status_data = {
        "timestamp": datetime.datetime.now().isoformat(),
        "overall_status": overall_status,
        "system_resources": {
            "cpu_usage_percent": cpu_percent,
            "memory_usage_percent": memory.percent,
            "memory_available_mb": memory.available // (1024 * 1024),
            "disk_usage_percent": disk.percent,
            "disk_free_gb": disk.free // (1024 * 1024 * 1024)
        },
        "components": component_status,
        "uptime": _get_system_uptime()
    }
    
    return status_data


def _display_formatted_status(status_data: dict[str, Any]):
    """
    Display system status in a human-readable format.
    
    Args:
        status_data: Dictionary containing system status information
    """
    # Display overall status
    status_color = {
        "healthy": "green",
        "degraded": "yellow",
        "unhealthy": "red"
    }.get(status_data["overall_status"], "white")
    
    click.echo("System Status: ", nl=False)
    click.secho(f"{status_data['overall_status'].upper()}", fg=status_color, bold=True)
    click.echo(f"Timestamp: {status_data['timestamp']}")
    click.echo(f"Uptime: {status_data['uptime']}")
    
    # Display system resources
    click.echo("\nSystem Resources:")
    resources = status_data["system_resources"]
    resource_table = [
        ["CPU Usage", f"{resources['cpu_usage_percent']}%"],
        ["Memory Usage", f"{resources['memory_usage_percent']}% ({resources['memory_available_mb']} MB available)"],
        ["Disk Usage", f"{resources['disk_usage_percent']}% ({resources['disk_free_gb']} GB free)"]
    ]
    click.echo(tabulate(resource_table, tablefmt="simple"))
    
    # Display component status
    click.echo("\nComponent Status:")
    component_table = []
    for component, details in status_data["components"].items():
        status = details["status"]
        status_color = {"healthy": "green", "degraded": "yellow", "unhealthy": "red"}.get(status, "white")
        component_table.append([
            component,
            click.style(status.upper(), fg=status_color),
            details.get("message", "")
        ])
    
    click.echo(tabulate(component_table, headers=["Component", "Status", "Message"], tablefmt="simple"))


def _determine_overall_health(health_results: dict[str, dict[str, Any]]) -> HealthStatus:
    """
    Determine the overall health status based on component health checks.
    
    Args:
        health_results: Dictionary of component health check results
        
    Returns:
        HealthStatus enum value representing overall health
    """
    # Count components by status
    status_counts = {"healthy": 0, "degraded": 0, "unhealthy": 0}
    
    for component_result in health_results.values():
        status = component_result.get("status", "unhealthy").lower()
        if status in status_counts:
            status_counts[status] += 1
    
    # Determine overall status
    if status_counts["unhealthy"] > 0:
        return HealthStatus.UNHEALTHY
    elif status_counts["degraded"] > 0:
        return HealthStatus.DEGRADED
    else:
        return HealthStatus.HEALTHY


def _display_formatted_health(health_data: dict[str, Any], verbose: bool):
    """
    Display health check results in a human-readable format.
    
    Args:
        health_data: Dictionary containing health check results
        verbose: Whether to show detailed information
    """
    # Display overall health status
    status_color = {
        "healthy": "green",
        "degraded": "yellow",
        "unhealthy": "red"
    }.get(health_data["overall_status"], "white")
    
    click.echo("Overall Health: ", nl=False)
    click.secho(f"{health_data['overall_status'].upper()}", fg=status_color, bold=True)
    click.echo(f"Timestamp: {health_data['timestamp']}")
    
    # Display component health
    click.echo("\nComponent Health:")
    
    for component, details in health_data["components"].items():
        status = details["status"]
        status_color = {"healthy": "green", "degraded": "yellow", "unhealthy": "red"}.get(status, "white")
        
        click.echo(f"  {component}: ", nl=False)
        click.secho(f"{status.upper()}", fg=status_color)
        
        if "message" in details and details["message"]:
            click.echo(f"    Message: {details['message']}")
            
        if verbose and "details" in details:
            click.echo("    Details:")
            for key, value in details["details"].items():
                click.echo(f"      {key}: {value}")
                
        if verbose and "metrics" in details:
            click.echo("    Metrics:")
            for metric, value in details["metrics"].items():
                click.echo(f"      {metric}: {value}")


def _show_configuration():
    """Display the current system configuration."""
    # Get configuration as dictionary
    config_dict = settings.as_dict()
    
    # Format and display configuration
    click.echo("Current Configuration:")
    
    # Convert to YAML for better readability
    config_yaml = yaml.dump(config_dict, default_flow_style=False, sort_keys=False)
    click.echo(config_yaml)


def _reset_configuration():
    """Reset the system configuration to default values."""
    try:
        # Implement configuration reset logic
        settings.reset_to_defaults()
        click.echo("Configuration has been reset to defaults.")
        click.echo("Note: Some changes may require a system restart to take effect.")
    except Exception as e:
        raise ConfigurationError(f"Failed to reset configuration: {str(e)}")


def _update_configuration(update_str: str):
    """
    Update a specific configuration value.
    
    Args:
        update_str: String in format "KEY=VALUE"
    """
    try:
        # Parse the key-value pair
        if "=" not in update_str:
            raise ConfigurationError("Update format must be KEY=VALUE")
        
        key, value = update_str.split("=", 1)
        key = key.strip()
        value = value.strip()
        
        # Convert value to appropriate type
        try:
            # Try to parse as JSON for complex types
            parsed_value = json.loads(value)
        except json.JSONDecodeError:
            # If not valid JSON, use the string value
            parsed_value = value
        
        # Update the configuration
        settings.update(key, parsed_value)
        
        click.echo(f"Updated configuration: {key} = {parsed_value}")
        click.echo("Note: Some changes may require a system restart to take effect.")
        
    except Exception as e:
        raise ConfigurationError(f"Failed to update configuration: {str(e)}")


def _load_configuration_from_file(file_path: str):
    """
    Load configuration from a file.
    
    Args:
        file_path: Path to configuration file (YAML or JSON)
    """
    try:
        with open(file_path) as f:
            if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                config_data = yaml.safe_load(f)
            elif file_path.endswith('.json'):
                config_data = json.load(f)
            else:
                raise ConfigurationError("Configuration file must be YAML or JSON")
        
        # Update configuration with file contents
        settings.update_from_dict(config_data)
        
        click.echo(f"Configuration loaded from {file_path}")
        click.echo("Note: Some changes may require a system restart to take effect.")
        
    except Exception as e:
        raise ConfigurationError(f"Failed to load configuration from file: {str(e)}")


def _should_display_log_line(line: str, level: Optional[str], 
                            component: Optional[str], 
                            since_timestamp: Optional[datetime.datetime]) -> bool:
    """
    Determine if a log line should be displayed based on filters.
    
    Args:
        line: The log line to check
        level: Log level filter
        component: Component name filter
        since_timestamp: Only show logs after this timestamp
        
    Returns:
        True if the line should be displayed, False otherwise
    """
    try:
        # Basic format check
        if not line or len(line.strip()) == 0:
            return False
        
        # Parse log line (assuming standard format)
        # Example: 2023-05-15 14:30:45,123 - INFO - neuroca.memory.working - Message
        parts = line.split(' - ', 3)
        if len(parts) < 3:
            return True  # Can't parse, show the line
        
        # Extract components
        timestamp_str = parts[0].strip()
        log_level = parts[1].strip()
        log_component = parts[2].strip()
        
        # Apply level filter
        if level and log_level.upper() != level.upper():
            return False
        
        # Apply component filter
        if component and component.lower() not in log_component.lower():
            return False
        
        # Apply timestamp filter
        if since_timestamp:
            try:
                # Parse timestamp (format may vary)
                log_timestamp = datetime.datetime.strptime(
                    timestamp_str, "%Y-%m-%d %H:%M:%S,%f"
                )
                if log_timestamp < since_timestamp:
                    return False
            except ValueError:
                # If we can't parse the timestamp, show the line
                pass
        
        return True
        
    except Exception:
        # If there's any error in parsing, show the line
        return True


def _create_system_backup(backup_path: str, include_logs: bool = False, 
                         include_data: bool = True) -> bool:
    """
    Create a system backup archive.
    
    Args:
        backup_path: Path where the backup file will be created
        include_logs: Whether to include log files
        include_data: Whether to include database and memory data
        
    Returns:
        True if backup was successful, False otherwise
    """
    try:
        import zipfile
        
        # Create a temporary directory for collecting files
        temp_dir = os.path.join(settings.SYSTEM.TEMP_DIR, f"backup_temp_{int(time.time())}")
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            # Backup configuration
            config_dir = os.path.join(temp_dir, "config")
            os.makedirs(config_dir, exist_ok=True)
            
            # Save current configuration
            config_file = os.path.join(config_dir, "settings.yaml")
            with open(config_file, 'w') as f:
                yaml.dump(settings.as_dict(), f, default_flow_style=False)
            
            # Backup database if requested
            if include_data:
                # Create database dump
                db_dir = os.path.join(temp_dir, "database")
                os.makedirs(db_dir, exist_ok=True)
                
                # This would call the appropriate database backup method
                # The implementation depends on the database being used
                db_backup_file = os.path.join(db_dir, "database_dump.sql")
                _backup_database(db_backup_file)
                
                # Backup memory data
                memory_dir = os.path.join(temp_dir, "memory")
                os.makedirs(memory_dir, exist_ok=True)
                
                # This would call the appropriate memory backup method
                _backup_memory_data(memory_dir)
            
            # Backup logs if requested
            if include_logs:
                logs_dir = os.path.join(temp_dir, "logs")
                os.makedirs(logs_dir, exist_ok=True)
                
                # Copy log files
                log_file = settings.LOGGING.LOG_FILE
                if os.path.exists(log_file):
                    log_basename = os.path.basename(log_file)
                    shutil.copy2(log_file, os.path.join(logs_dir, log_basename))
                    
                    # Also copy rotated log files if they exist
                    log_dir = os.path.dirname(log_file)
                    log_name = os.path.splitext(log_basename)[0]
                    for filename in os.listdir(log_dir):
                        if filename.startswith(log_name) and filename != log_basename:
                            shutil.copy2(
                                os.path.join(log_dir, filename),
                                os.path.join(logs_dir, filename)
                            )
            
            # Create metadata file
            metadata = {
                "timestamp": datetime.datetime.now().isoformat(),
                "version": _get_version_info()["version"],
                "includes": {
                    "config": True,
                    "data": include_data,
                    "logs": include_logs
                },
                "system_info": {
                    "platform": platform.platform(),
                    "python": platform.python_version()
                }
            }
            
            with open(os.path.join(temp_dir, "backup_metadata.json"), 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Create zip archive
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, arcname)
            
            return True
            
        finally:
            # Clean up temporary directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                
    except Exception as e:
        logger.error(f"Backup creation failed: {str(e)}", exc_info=True)
        raise BackupRestoreError(f"Failed to create backup: {str(e)}")


def _verify_backup_integrity(backup_path: str) -> bool:
    """
    Verify the integrity of a backup file.
    
    Args:
        backup_path: Path to the backup file
        
    Returns:
        True if the backup is valid, False otherwise
    """
    try:
        import zipfile
        
        # Check if file exists and is a zip file
        if not os.path.isfile(backup_path) or not zipfile.is_zipfile(backup_path):
            return False
        
        # Open the zip file and check its contents
        with zipfile.ZipFile(backup_path, 'r') as zipf:
            # Check for required files
            required_files = ["backup_metadata.json", "config/settings.yaml"]
            for file in required_files:
                try:
                    zipf.getinfo(file)
                except KeyError:
                    logger.error(f"Backup is missing required file: {file}")
                    return False
            
            # Verify metadata
            try:
                with zipf.open("backup_metadata.json") as f:
                    metadata = json.load(f)
                
                # Check metadata structure
                required_keys = ["timestamp", "version", "includes"]
                for key in required_keys:
                    if key not in metadata:
                        logger.error(f"Backup metadata is missing required key: {key}")
                        return False
                
            except Exception as e:
                logger.error(f"Failed to parse backup metadata: {str(e)}")
                return False
            
            # Test the integrity of all files in the archive
            for info in zipf.infolist():
                try:
                    with zipf.open(info) as f:
                        f.read(1)  # Try to read a byte from each file
                except Exception as e:
                    logger.error(f"Corrupted file in backup: {info.filename} - {str(e)}")
                    return False
        
        return True
        
    except Exception as e:
        logger.error(f"Backup verification failed: {str(e)}", exc_info=True)
        return False


def _restore_system_from_backup(backup_path: str) -> bool:
    """
    Restore the system from a backup file.
    
    Args:
        backup_path: Path to the backup file
        
    Returns:
        True if restore was successful, False otherwise
    """
    try:
        import zipfile
        
        # Create a temporary directory for extraction
        temp_dir = os.path.join(settings.SYSTEM.TEMP_DIR, f"restore_temp_{int(time.time())}")
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            # Extract the backup
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            # Read metadata
            with open(os.path.join(temp_dir, "backup_metadata.json")) as f:
                metadata = json.load(f)
            
            # Restore configuration
            config_file = os.path.join(temp_dir, "config/settings.yaml")
            if os.path.exists(config_file):
                with open(config_file) as f:
                    config_data = yaml.safe_load(f)
                
                # Update configuration
                settings.update_from_dict(config_data)
            
            # Restore database if included
            if metadata["includes"].get("data", False):
                db_dump_file = os.path.join(temp_dir, "database/database_dump.sql")
                if os.path.exists(db_dump_file):
                    _restore_database(db_dump_file)
                
                # Restore memory data if included
                memory_dir = os.path.join(temp_dir, "memory")
                if os.path.exists(memory_dir):
                    _restore_memory_data(memory_dir)
            
            # Restore logs if included
            if metadata["includes"].get("logs", False):
                logs_dir = os.path.join(temp_dir, "logs")
                if os.path.exists(logs_dir):
                    log_file = settings.LOGGING.LOG_FILE
                    log_dir = os.path.dirname(log_file)
                    
                    # Create log directory if it doesn't exist
                    os.makedirs(log_dir, exist_ok=True)
                    
                    # Copy log files
                    for filename in os.listdir(logs_dir):
                        src_path = os.path.join(logs_dir, filename)
                        dst_path = os.path.join(log_dir, filename)
                        shutil.copy2(src_path, dst_path)
            
            return True
            
        finally:
            # Clean up temporary directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                
    except Exception as e:
        logger.error(f"Restore operation failed: {str(e)}", exc_info=True)
        raise BackupRestoreError(f"Failed to restore from backup: {str(e)}")


def _backup_database(output_file: str):
    """
    Create a backup of the database.
    
    Args:
        output_file: Path where the database dump will be saved
    """
    # This implementation would depend on the database being used
    # For example, for PostgreSQL:
    try:
        db_config = settings.DATABASE
        
        if db_config.ENGINE.endswith('postgresql'):
            # PostgreSQL backup
            cmd = [
                "pg_dump",
                f"--host={db_config.HOST}",
                f"--port={db_config.PORT}",
                f"--username={db_config.USER}",
                f"--file={output_file}",
                db_config.NAME
            ]
            
            # Set PGPASSWORD environment variable
            env = os.environ.copy()
            env["PGPASSWORD"] = db_config.PASSWORD
            
            subprocess.run(cmd, env=env, check=True)
            
        elif db_config.ENGINE.endswith('sqlite3'):
            # SQLite backup - just copy the file
            db_path = db_config.NAME
            if os.path.isfile(db_path):
                shutil.copy2(db_path, output_file)
                
        else:
            logger.warning(f"Database backup not implemented for engine: {db_config.ENGINE}")
            
    except Exception as e:
        logger.error(f"Database backup failed: {str(e)}", exc_info=True)
        raise BackupRestoreError(f"Database backup failed: {str(e)}")


def _restore_database(input_file: str):
    """
    Restore the database from a backup.
    
    Args:
        input_file: Path to the database dump file
    """
    # This implementation would depend on the database being used
    try:
        db_config = settings.DATABASE
        
        if db_config.ENGINE.endswith('postgresql'):
            # PostgreSQL restore
            cmd = [
                "psql",
                f"--host={db_config.HOST}",
                f"--port={db_config.PORT}",
                f"--username={db_config.USER}",
                f"--dbname={db_config.NAME}",
                f"--file={input_file}"
            ]
            
            # Set PGPASSWORD environment variable
            env = os.environ.copy()
            env["PGPASSWORD"] = db_config.PASSWORD
            
            subprocess.run(cmd, env=env, check=True)
            
        elif db_config.ENGINE.endswith('sqlite3'):
            # SQLite restore - just copy the file
            db_path = db_config.NAME
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            shutil.copy2(input_file, db_path)
                
        else:
            logger.warning(f"Database restore not implemented for engine: {db_config.ENGINE}")
            
    except Exception as e:
        logger.error(f"Database restore failed: {str(e)}", exc_info=True)
        raise BackupRestoreError(f"Database restore failed: {str(e)}")


def _backup_memory_data(output_dir: str):
    """
    Backup memory data to the specified directory.
    
    Args:
        output_dir: Directory where memory data will be saved
    """
    try:
        # This would call the appropriate memory backup methods
        # The implementation depends on how memory is stored
        
        # Example: backup working memory
        working_memory_file = os.path.join(output_dir, "working_memory.json")
        memory_manager.backup_working_memory(working_memory_file)
        
        # Example: backup episodic memory
        episodic_memory_file = os.path.join(output_dir, "episodic_memory.json")
        memory_manager.backup_episodic_memory(episodic_memory_file)
        
        # Example: backup semantic memory
        semantic_memory_file = os.path.join(output_dir, "semantic_memory.json")
        memory_manager.backup_semantic_memory(semantic_memory_file)
        
    except Exception as e:
        logger.error(f"Memory data backup failed: {str(e)}", exc_info=True)
        raise BackupRestoreError(f"Memory data backup failed: {str(e)}")


def _restore_memory_data(input_dir: str):
    """
    Restore memory data from the specified directory.
    
    Args:
        input_dir: Directory containing memory data backups
    """
    try:
        # This would call the appropriate memory restore methods
        # The implementation depends on how memory is stored
        
        # Example: restore working memory
        working_memory_file = os.path.join(input_dir, "working_memory.json")
        if os.path.exists(working_memory_file):
            memory_manager.restore_working_memory(working_memory_file)
        
        # Example: restore episodic memory
        episodic_memory_file = os.path.join(input_dir, "episodic_memory.json")
        if os.path.exists(episodic_memory_file):
            memory_manager.restore_episodic_memory(episodic_memory_file)
        
        # Example: restore semantic memory
        semantic_memory_file = os.path.join(input_dir, "semantic_memory.json")
        if os.path.exists(semantic_memory_file):
            memory_manager.restore_semantic_memory(semantic_memory_file)
        
    except Exception as e:
        logger.error(f"Memory data restore failed: {str(e)}", exc_info=True)
        raise BackupRestoreError(f"Memory data restore failed: {str(e)}")


def _cleanup_directory(directory: str, cutoff_date: datetime.datetime, 
                      pattern: str = "*", dry_run: bool = False) -> tuple[int, int]:
    """
    Clean up old files in a directory.
    
    Args:
        directory: Directory to clean
        cutoff_date: Remove files older than this date
        pattern: File pattern to match
        dry_run: If True, don't actually delete files
        
    Returns:
        Tuple of (number of files deleted, bytes freed)
    """
    if not os.path.exists(directory):
        return 0, 0
    
    deleted_count = 0
    freed_space = 0
    
    for filename in Path(directory).glob(pattern):
        if not filename.is_file():
            continue
        
        file_time = datetime.datetime.fromtimestamp(filename.stat().st_mtime)
        
        if file_time < cutoff_date:
            file_size = filename.stat().st_size
            
            if dry_run:
                logger.info(f"Would delete: {filename} ({_format_file_size(file_size)})")
            else:
                try:
                    filename.unlink()
                    logger.info(f"Deleted: {filename} ({_format_file_size(file_size)})")
                    deleted_count += 1
                    freed_space += file_size
                except Exception as e:
                    logger.error(f"Failed to delete {filename}: {str(e)}")
    
    return deleted_count, freed_space


def _get_system_uptime() -> str:
    """
    Get the system uptime in a human-readable format.
    
    Returns:
        String representing system uptime
    """
    try:
        # Get system boot time
        boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.datetime.now() - boot_time
        
        # Format uptime
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m {seconds}s"
        elif hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
            
    except Exception as e:
        logger.error(f"Failed to get system uptime: {str(e)}")
        return "Unknown"


def _get_version_info() -> dict[str, Any]:
    """
    Get version information for the system and its components.
    
    Returns:
        Dictionary containing version information
    """
    # This would be populated with actual version information
    version_info = {
        "version": "0.1.0",  # This would come from the package version
        "build": "dev",      # This would be set during the build process
        "python": platform.python_version(),
        "platform": platform.platform(),
        "components": {
            "database": "PostgreSQL 14.5",  # Example
            "memory_manager": "0.1.0",
            "llm_integration": "0.1.0",
            "api_service": "0.1.0"
        }
    }
    
    return version_info


def _format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Human-readable size string
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"