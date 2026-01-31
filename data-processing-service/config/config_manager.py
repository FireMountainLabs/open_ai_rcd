"""
Configuration Manager for Data Processing Microservice

Handles loading and validation of configuration from YAML files and environment
variables. Provides a centralized way to manage all configuration settings for
the microservice.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Manages configuration for the data processing microservice.

    Loads configuration from YAML files and environment variables, providing
    a unified interface for accessing configuration values throughout the service.
    """

    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize the configuration manager.

        Args:
            config_file: Path to the configuration file. If None, uses default.
        """
        if config_file is None:
            config_file = Path(__file__).parent / "default_config.yaml"

        self.config_file = Path(config_file)
        self._config: Optional[Dict[str, Any]] = None

    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file and environment variables.

        Returns:
            Dictionary containing merged configuration

        Raises:
            FileNotFoundError: If configuration file doesn't exist
            yaml.YAMLError: If configuration file is invalid YAML
        """
        if self._config is not None:
            return self._config

        if not self.config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_file}")

        try:
            with open(self.config_file, "r") as f:
                file_config = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Invalid YAML in configuration file: {e}")

        # Merge with environment variables
        self._config = self._merge_with_environment(file_config)

        logger.info(f"Configuration loaded from {self.config_file}")
        return self._config

    def _merge_with_environment(self, file_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge file configuration with environment variables.

        Environment variables take precedence over file configuration.
        Environment variable names are converted from UPPER_CASE to nested dict keys.

        Args:
            file_config: Configuration loaded from file

        Returns:
            Merged configuration dictionary
        """
        env_mappings = {
            "DATA_SOURCES_RISKS_FILE": ["data_sources", "risks", "file"],
            "DATA_SOURCES_CONTROLS_FILE": ["data_sources", "controls", "file"],
            "DATA_SOURCES_QUESTIONS_FILE": ["data_sources", "questions", "file"],
            "DATABASE_FILE": ["database", "file"],
            "EXTRACTION_VALIDATE_FILES": ["extraction", "validate_files"],
            "EXTRACTION_REMOVE_DUPLICATES": ["extraction", "remove_duplicates"],
            "EXTRACTION_LOG_LEVEL": ["extraction", "log_level"],
            "OUTPUT_PRINT_SUMMARY": ["output", "print_summary"],
            "OUTPUT_COLLECT_METADATA": ["output", "collect_metadata"],
        }

        config = file_config.copy()

        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Navigate to the nested location and set the value
                current = config
                for key in config_path[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]

                # Convert string values to appropriate types
                if env_value.lower() in ("true", "false"):
                    current[config_path[-1]] = env_value.lower() == "true"
                else:
                    current[config_path[-1]] = env_value

                logger.debug(f"Set {'.'.join(config_path)} = {env_value} from environment")

        return config

    def get_data_source_config(self, source_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific data source.

        Args:
            source_name: Name of the data source (risks, controls, questions)

        Returns:
            Configuration dictionary for the data source

        Raises:
            KeyError: If data source configuration not found
        """
        config = self.load_config()
        data_sources = config.get("data_sources", {})

        if source_name not in data_sources:
            raise KeyError(f"Data source '{source_name}' not found in configuration")

        return data_sources[source_name]

    def get_database_config(self) -> Dict[str, Any]:
        """
        Get database configuration.

        Returns:
            Database configuration dictionary
        """
        config = self.load_config()
        return config.get("database", {})

    def get_extraction_config(self) -> Dict[str, Any]:
        """
        Get extraction process configuration.

        Returns:
            Extraction configuration dictionary
        """
        config = self.load_config()
        return config.get("extraction", {})

    def get_output_config(self) -> Dict[str, Any]:
        """
        Get output configuration.

        Returns:
            Output configuration dictionary
        """
        config = self.load_config()
        return config.get("output", {})

    def validate_config(self) -> bool:
        """
        Validate the loaded configuration.

        Returns:
            True if configuration is valid

        Raises:
            ValueError: If configuration is invalid
        """
        config = self.load_config()

        # Check required sections
        required_sections = ["data_sources", "database", "extraction"]
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required configuration section: {section}")

        # Check data sources
        data_sources = config["data_sources"]
        required_sources = ["risks", "controls", "questions"]
        for source in required_sources:
            if source not in data_sources:
                raise ValueError(f"Missing required data source: {source}")

            source_config = data_sources[source]
            if "file" not in source_config:
                raise ValueError(f"Missing 'file' configuration for data source: {source}")

            if "columns" not in source_config:
                raise ValueError(f"Missing 'columns' configuration for data source: {source}")

        # Check database configuration
        database = config["database"]
        if "file" not in database:
            raise ValueError("Missing 'file' configuration for database")

        logger.info("Configuration validation passed")
        return True
