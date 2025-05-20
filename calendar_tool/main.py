#!/usr/bin/env python3
"""
Main module for Calendar Tool application.
Provides CLI interface and orchestrates the application flow.
"""

import argparse
import os
import sys
from pathlib import Path

from calendar_tool.config import config
from calendar_tool.auth import auth
from calendar_tool.analysis import analysis


def setup_directories():
    """Create necessary directories for application data."""
    app_dir = Path.home() / ".calendar-tool"
    app_dir.mkdir(exist_ok=True)
    return app_dir


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Calendar Tool - A utility for optimizing employee work time"
    )
    
    # Create subparsers for different modes
    subparsers = parser.add_subparsers(dest="mode", help="Operation mode")
    
    # Authentication mode
    auth_parser = subparsers.add_parser("auth", help="Authenticate with Exchange server")
    auth_parser.add_argument(
        "--server", help="Exchange server address (for legacy auth)", default=None
    )
    auth_parser.add_argument(
        "--username", help="Exchange username (for legacy auth)", default=None
    )
    auth_parser.add_argument(
        "--password", help="Exchange password (for legacy auth, not recommended, use prompt instead)", default=None
    )
    auth_parser.add_argument(
        "--client-id", help="Microsoft Application (client) ID for OAuth", default=None
    )
    auth_parser.add_argument(
        "--tenant-id", help="Microsoft tenant ID for OAuth", default=None
    )
    auth_parser.add_argument(
        "--use-oauth", help="Use OAuth authentication (default: True)", 
        action="store_true", dest="use_oauth", default=None
    )
    auth_parser.add_argument(
        "--no-oauth", help="Do not use OAuth authentication, use legacy auth instead", 
        action="store_false", dest="use_oauth"
    )
    
    # Analysis mode
    analysis_parser = subparsers.add_parser("analyze", help="Analyze calendar and find free time slots")
    analysis_parser.add_argument(
        "--start-time", help="Work day start time (format: HH:MM)", default=None
    )
    analysis_parser.add_argument(
        "--end-time", help="Work day end time (format: HH:MM)", default=None
    )
    analysis_parser.add_argument(
        "--server", help="Exchange server address (for legacy auth)", default=None
    )
    analysis_parser.add_argument(
        "--client-id", help="Microsoft Application (client) ID for OAuth", default=None
    )
    analysis_parser.add_argument(
        "--tenant-id", help="Microsoft tenant ID for OAuth", default=None
    )
    
    # Config mode
    config_parser = subparsers.add_parser("config", help="Set configuration options")
    config_parser.add_argument(
        "--server", help="Exchange server address (for legacy auth)", default=None
    )
    config_parser.add_argument(
        "--start-time", help="Work day start time (format: HH:MM)", default=None
    )
    config_parser.add_argument(
        "--end-time", help="Work day end time (format: HH:MM)", default=None
    )
    config_parser.add_argument(
        "--client-id", help="Microsoft Application (client) ID for OAuth", default=None
    )
    config_parser.add_argument(
        "--tenant-id", help="Microsoft tenant ID for OAuth", default=None
    )
    config_parser.add_argument(
        "--use-oauth", help="Use OAuth authentication (default: True)", 
        action="store_true", dest="use_oauth", default=None
    )
    config_parser.add_argument(
        "--no-oauth", help="Do not use OAuth authentication, use legacy auth instead", 
        action="store_false", dest="use_oauth"
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the application."""
    # Setup application directories
    app_dir = setup_directories()
    
    # Parse command line arguments
    args = parse_arguments()
    
    if not args.mode:
        print("Error: No mode specified. Use 'auth', 'analyze', or 'config'.")
        print("Run with --help for more information.")
        sys.exit(1)
    
    # Load configuration
    conf = config.load_config(app_dir, args)
    
    # Execute appropriate mode
    if args.mode == "auth":
        success = auth.authenticate(app_dir, conf, args)
        if not success:
            sys.exit(1)
    elif args.mode == "analyze":
        # Check if token exists
        if not auth.token_exists(app_dir):
            print("Error: Not authenticated. Please run 'calendar-tool auth' first.")
            sys.exit(1)
        
        # Validate configuration
        if not config.validate_config(conf):
            sys.exit(1)
        
        # Run analysis
        analysis.analyze_calendar(app_dir, conf)
    elif args.mode == "config":
        if config.update_config(app_dir, args):
            print("Configuration updated successfully.")
        else:
            print("Error: Failed to update configuration.")
            sys.exit(1)
    else:
        print(f"Error: Unknown mode '{args.mode}'. Use 'auth', 'analyze', or 'config'.")
        sys.exit(1)


if __name__ == "__main__":
    main()