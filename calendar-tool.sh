#!/bin/bash

# Calendar Tool Launch Script
# This script runs the calendar-tool from source without installing it system-wide

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Make the script executable
chmod +x "$SCRIPT_DIR/calendar-tool.sh"

# Setup Python environment if needed
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "Virtual environment not found. Setting up..."
    python3 -m venv "$SCRIPT_DIR/venv"
    source "$SCRIPT_DIR/venv/bin/activate"
    pip install -e "$SCRIPT_DIR"
    echo "Environment setup complete."
else
    source "$SCRIPT_DIR/venv/bin/activate"
    
    # Check if dependencies need updating
    pip install -e "$SCRIPT_DIR" --upgrade
fi

# Run the main module with arguments
python -m calendar_tool.main "$@"

# Deactivate virtual environment
deactivate