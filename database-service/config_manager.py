"""
Configuration Manager for Database Service

Handles loading and validation of configuration from YAML files and environment
variables. Provides a centralized way to manage all configuration settings for
the database service.
"""

import os
import yaml
import re
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Manages configuration for the database service.

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
            config_file = Path(__file__).parent / "config.yaml"

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

        # Process shell variable substitutions
        processed_config = self._process_shell_variables(file_config)

        # Merge with environment variables
        self._config = self._merge_with_environment(processed_config)

        logger.info(f"Configuration loaded from {self.config_file}")
        return self._config

    def _process_shell_variables(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process shell variable substitutions in configuration values.

        Handles syntax like ${VAR:-default} where VAR is an environment variable
        and default is the fallback value if VAR is not set.

        Args:
            config: Configuration dictionary to process

        Returns:
            Configuration dictionary with shell variables substituted
        """

        def substitute_variables(value):
            if isinstance(value, str):
                # Pattern to match ${VAR:-default} or ${VAR}
                pattern = r"\$\{([^:}]+)(?::-([^}]*))?\}"

                def replace_var(match):
                    var_name = match.group(1)
                    default_value = match.group(2) if match.group(2) is not None else ""
                    return os.getenv(var_name, default_value)

                return re.sub(pattern, replace_var, value)
            elif isinstance(value, dict):
                return {k: substitute_variables(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [substitute_variables(item) for item in value]
            else:
                return value

        return substitute_variables(config)

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
            "API_HOST": ["server", "host"],
            "API_PORT": ["server", "port"],
            "DEBUG": ["server", "debug"],
            "BASE_URL": ["server", "base_url"],
            "DB_PATH": ["database", "path"],
            "DB_TIMEOUT": ["database", "timeout"],
            "LOG_LEVEL": ["logging", "level"],
            "LOG_FILE": ["logging", "file"],
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
                elif env_value.isdigit():
                    current[config_path[-1]] = int(env_value)
                else:
                    current[config_path[-1]] = env_value

                logger.debug(f"Set {'.'.join(config_path)} = {env_value} from environment")

        return config

    def get_server_config(self) -> Dict[str, Any]:
        """
        Get server configuration.

        Returns:
            Server configuration dictionary
        """
        config = self.load_config()
        return config.get("server", {})

    def get_database_config(self) -> Dict[str, Any]:
        """
        Get database configuration.

        Returns:
            Database configuration dictionary
        """
        config = self.load_config()
        return config.get("database", {})

    def get_api_config(self) -> Dict[str, Any]:
        """
        Get API configuration.

        Returns:
            API configuration dictionary
        """
        config = self.load_config()
        return config.get("api", {})

    def get_logging_config(self) -> Dict[str, Any]:
        """
        Get logging configuration.

        Returns:
            Logging configuration dictionary
        """
        config = self.load_config()
        return config.get("logging", {})

    def get_health_check_config(self) -> Dict[str, Any]:
        """
        Get health check configuration.

        Returns:
            Health check configuration dictionary
        """
        config = self.load_config()
        return config.get("health_check", {})

    def get_performance_config(self) -> Dict[str, Any]:
        """
        Get performance configuration.

        Returns:
            Performance configuration dictionary
        """
        config = self.load_config()
        return config.get("performance", {})

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
        required_sections = ["server", "database", "api"]
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required configuration section: {section}")

        # Check server configuration
        server = config["server"]
        if "host" not in server or "port" not in server:
            raise ValueError("Missing required server configuration: host or port")

        # Check database configuration
        database = config["database"]
        if "path" not in database:
            raise ValueError("Missing required database configuration: path")

        # Check API configuration
        api = config["api"]
        if "limits" not in api:
            raise ValueError("Missing required API configuration: limits")

        logger.info("Configuration validation passed")
        return True
