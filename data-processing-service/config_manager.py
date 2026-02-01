"""
Configuration Manager for Data Processing Microservice

Handles loading and validation of configuration from YAML files and environment
variables. Provides a centralized way to manage all configuration settings for
the microservice.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import yaml

# Try to import CommonConfigManager, fall back to standalone loading if not available
try:
    # Add shared-services to path if not already there
    shared_services_path = Path(__file__).parent.parent / "shared-services"
    if str(shared_services_path) not in sys.path:
        sys.path.insert(0, str(shared_services_path))
    from common_config import CommonConfigManager
    HAS_COMMON_CONFIG = True
except ImportError:
    HAS_COMMON_CONFIG = False

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Manages configuration for the data processing microservice.
    """

    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize the configuration manager.
        """
        if config_file is None:
            config_file = Path(__file__).parent / "default_config.yaml"

        self.config_file = Path(config_file)
        self._config: Optional[Dict[str, Any]] = None

    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file or CommonConfigManager.
        """
        if self._config is not None:
            return self._config

        if HAS_COMMON_CONFIG:
            # Use CommonConfigManager to load all configurations
            os.environ["SERVICE_NAME"] = "data_processing"
            common_mgr = CommonConfigManager()
            self._config = common_mgr.load_config()
            logger.info("Configuration loaded using CommonConfigManager")
        else:
            # Fallback: load from local config file
            if self.config_file.exists():
                with open(self.config_file, "r") as f:
                    self._config = yaml.safe_load(f) or {}
            else:
                self._config = {}
            self._config = self._merge_with_environment(self._config)
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
