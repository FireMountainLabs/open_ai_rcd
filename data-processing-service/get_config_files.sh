#!/bin/bash
# Simple wrapper script for CI/CD pipelines to get configuration files
# This script provides a clean interface for external tools to access configuration

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_READER="$SCRIPT_DIR/utils/config_reader.py"

# Check if the config reader exists
if [ ! -f "$CONFIG_READER" ]; then
    echo "ERROR: Configuration reader not found: $CONFIG_READER" >&2
    exit 1
fi

# Run the configuration reader with the requested arguments
python3 "$CONFIG_READER" "$@"
