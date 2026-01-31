#!/usr/bin/env python3
"""
Configuration Reader Utility

A standalone utility for reading configuration from the data-processing-service
configuration file. Can be used by launcher scripts, CI/CD pipelines, and
other tools that need to access configuration data.

Usage:
    python3 config_reader.py                    # Print all configured files
    python3 config_reader.py --files           # Print file names only
    python3 config_reader.py --validate        # Validate configuration
    python3 config_reader.py --source risks    # Get specific source config
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add the parent directory to the path so we can import config_manager
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from config.config_manager import ConfigManager
except ImportError:
    # Fallback for when running as standalone script
    import os

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from config.config_manager import ConfigManager


class ConfigReader:
    """
    Standalone configuration reader for external tools.

    Provides a simple interface for reading configuration data without
    requiring the full data processing service to be initialized.
    """

    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize the configuration reader.

        Args:
            config_file: Path to configuration file. If None, uses default.
        """
        if config_file is None:
            config_file = Path(__file__).parent.parent / "config" / "default_config.yaml"

        self.config_manager = ConfigManager(config_file)

    def get_file_names(self) -> List[str]:
        """
        Get list of configured file names.

        Returns:
            List of file names from configuration
        """
        try:
            config = self.config_manager.load_config()
            data_sources = config.get("data_sources", {})

            files = []
            for source_name, source_config in data_sources.items():
                filename = source_config.get("file")
                if filename:
                    files.append(filename)

            return files
        except Exception as e:
            print(f"Error reading configuration: {e}", file=sys.stderr)
            return []

    def get_source_config(self, source_name: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific data source.

        Args:
            source_name: Name of the data source (risks, controls, questions)

        Returns:
            Configuration dictionary for the data source, or None if not found
        """
        try:
            return self.config_manager.get_data_source_config(source_name)
        except Exception as e:
            print(f"Error getting config for {source_name}: {e}", file=sys.stderr)
            return None

    def validate_config(self) -> bool:
        """
        Validate the configuration.

        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            self.config_manager.validate_config()
            return True
        except Exception as e:
            print(f"Configuration validation failed: {e}", file=sys.stderr)
            return False

    def get_full_config(self) -> Dict[str, Any]:
        """
        Get the full configuration.

        Returns:
            Complete configuration dictionary
        """
        try:
            return self.config_manager.load_config()
        except Exception as e:
            print(f"Error loading configuration: {e}", file=sys.stderr)
            return {}


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(description="Configuration reader utility for data-processing-service")
    parser.add_argument("--files", action="store_true", help="Print only file names (space-separated)")
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate configuration and exit with status code",
    )
    parser.add_argument(
        "--source",
        help="Get configuration for specific source (risks, controls, questions)",
    )
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument(
        "--config-file",
        help="Path to configuration file (default: config/default_config.yaml)",
    )
    parser.add_argument("--database", action="store_true", help="Print only database filename")

    args = parser.parse_args()

    # Initialize config reader
    config_file = Path(args.config_file) if args.config_file else None
    reader = ConfigReader(config_file)

    # Handle different modes
    if args.validate:
        if reader.validate_config():
            print("Configuration is valid")
            sys.exit(0)
        else:
            print("Configuration validation failed")
            sys.exit(1)

    elif args.source:
        config = reader.get_source_config(args.source)
        if config:
            if args.json:
                print(json.dumps(config, indent=2))
            else:
                print(f"Configuration for {args.source}:")
                for key, value in config.items():
                    print(f"  {key}: {value}")
        else:
            print(f"Source '{args.source}' not found in configuration")
            sys.exit(1)

    elif args.files:
        files = reader.get_file_names()
        if args.json:
            print(json.dumps(files))
        else:
            print(" ".join(files))

    elif args.database:
        config = reader.get_full_config()
        db_config = config.get("database", {})
        db_filename = db_config.get("file", "aiml_data.db")
        if args.json:
            print(json.dumps({"database_file": db_filename}))
        else:
            print(db_filename)

    else:
        # Default: print all configuration
        config = reader.get_full_config()
        if args.json:
            print(json.dumps(config, indent=2))
        else:
            print("Data Processing Service Configuration:")
            print("=" * 40)

            data_sources = config.get("data_sources", {})
            for source_name, source_config in data_sources.items():
                filename = source_config.get("file", "NOT SPECIFIED")
                description = source_config.get("description", "No description")
                print(f"{source_name}:")
                print(f"  File: {filename}")
                print(f"  Description: {description}")
                print()


if __name__ == "__main__":
    main()
