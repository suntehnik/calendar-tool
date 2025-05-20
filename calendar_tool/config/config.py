"""
Configuration management for Calendar Tool.
"""

import json
import os
from pathlib import Path


def get_config_path(app_dir):
    """Get the path to the configuration file."""
    return app_dir / "config.json"


def load_config(app_dir, args=None):
    """
    Load configuration from file and override with command-line arguments.
    
    Args:
        app_dir: Path to application directory
        args: Command-line arguments
        
    Returns:
        dict: Configuration dictionary
    """
    config_path = get_config_path(app_dir)
    
    # Default configuration
    config = {
        "server": "",
        "start_time": "09:00",
        "end_time": "18:00",
        "client_id": "",
        "tenant_id": "",
        "use_oauth": True  # Default to OAuth authentication
    }
    
    # Load from config file if it exists
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                file_config = json.load(f)
                config.update(file_config)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Failed to load config file: {e}")
    
    # Override with command-line arguments if provided
    if args:
        if hasattr(args, "server") and args.server:
            config["server"] = args.server
        if hasattr(args, "start_time") and args.start_time:
            config["start_time"] = args.start_time
        if hasattr(args, "end_time") and args.end_time:
            config["end_time"] = args.end_time
        if hasattr(args, "client_id") and args.client_id:
            config["client_id"] = args.client_id
        if hasattr(args, "tenant_id") and args.tenant_id:
            config["tenant_id"] = args.tenant_id
        if hasattr(args, "use_oauth") and args.use_oauth is not None:
            config["use_oauth"] = args.use_oauth
    
    return config


def update_config(app_dir, args):
    """
    Update configuration with provided arguments and save to file.
    
    Args:
        app_dir: Path to application directory
        args: Command-line arguments
        
    Returns:
        bool: True if configuration was successfully updated, False otherwise
    """
    config_path = get_config_path(app_dir)
    
    # Load existing config
    config = load_config(app_dir)
    
    # Update config with args
    if hasattr(args, "server") and args.server:
        config["server"] = args.server
    if hasattr(args, "start_time") and args.start_time:
        if not _is_valid_time_format(args.start_time):
            print(f"Error: Invalid start time format: {args.start_time}. Use HH:MM format.")
            return False
        config["start_time"] = args.start_time
    if hasattr(args, "end_time") and args.end_time:
        if not _is_valid_time_format(args.end_time):
            print(f"Error: Invalid end time format: {args.end_time}. Use HH:MM format.")
            return False
        config["end_time"] = args.end_time
    if hasattr(args, "client_id") and args.client_id:
        config["client_id"] = args.client_id
    if hasattr(args, "tenant_id") and args.tenant_id:
        config["tenant_id"] = args.tenant_id
    if hasattr(args, "use_oauth") and args.use_oauth is not None:
        config["use_oauth"] = args.use_oauth
    
    # Validate time configuration
    if "start_time" in config and "end_time" in config:
        start_hours, start_minutes = map(int, config["start_time"].split(":"))
        end_hours, end_minutes = map(int, config["end_time"].split(":"))
        
        start_minutes_total = start_hours * 60 + start_minutes
        end_minutes_total = end_hours * 60 + end_minutes
        
        if end_minutes_total <= start_minutes_total:
            print("Error: End time must be after start time.")
            return False
    
    # Save updated config
    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=4)
        print(f"Configuration saved to {config_path}")
        return True
    except IOError as e:
        print(f"Error: Failed to save config file: {e}")
        return False


def validate_config(config):
    """
    Validate configuration values.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        bool: True if configuration is valid, False otherwise
    """
    # Check time format
    for time_key in ["start_time", "end_time"]:
        time_value = config.get(time_key, "")
        if not time_value or not _is_valid_time_format(time_value):
            print(f"Error: Invalid {time_key.replace('_', ' ')} format: {time_value}")
            print(f"Use 'calendar-tool config --{time_key.replace('_', '-')} HH:MM' to set it.")
            return False
    
    # Validate time configuration
    start_hours, start_minutes = map(int, config["start_time"].split(":"))
    end_hours, end_minutes = map(int, config["end_time"].split(":"))
    
    start_minutes_total = start_hours * 60 + start_minutes
    end_minutes_total = end_hours * 60 + end_minutes
    
    if end_minutes_total <= start_minutes_total:
        print("Error: End time must be after start time.")
        return False
    
    # Check OAuth2 configuration if use_oauth is True
    if config.get("use_oauth", True):
        if not config.get("client_id"):
            print("Error: Microsoft Application (client) ID is not configured.")
            print("Use 'calendar-tool config --client-id CLIENT_ID' to set it.")
            return False
        
        if not config.get("tenant_id"):
            print("Error: Microsoft Tenant ID is not configured.")
            print("Use 'calendar-tool config --tenant-id TENANT_ID' to set it.")
            return False
    else:
        # If using legacy Exchange auth, check server
        if not config.get("server"):
            print("Error: Exchange server address is not configured.")
            print("Use 'calendar-tool config --server SERVER' to set it.")
            return False
    
    return True


def _is_valid_time_format(time_str):
    """
    Check if time string is in valid HH:MM format.
    
    Args:
        time_str: Time string to check
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        hours, minutes = time_str.split(":")
        hours, minutes = int(hours), int(minutes)
        return 0 <= hours < 24 and 0 <= minutes < 60
    except (ValueError, AttributeError):
        return False