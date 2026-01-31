"""
Configuration Manager for Dashboard Service

Handles loading and validation of configuration from YAML files and environment
variables. Provides a centralized way to manage all configuration settings for
the dashboard service.
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
    Manages configuration for the dashboard service.

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

        # Process shell variable substitution
        processed_config = self._process_shell_variables(file_config)

        # Merge with environment variables
        self._config = self._merge_with_environment(processed_config)

        logger.info(f"Configuration loaded from {self.config_file}")
        return self._config

    def _process_shell_variables(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process shell variable substitution syntax in configuration values.

        Handles patterns like ${VAR:-default} and ${VAR} in string values.

        Args:
            config: Configuration dictionary to process

        Returns:
            Processed configuration dictionary
        """

        def process_value(value):
            if isinstance(value, str):
                # Pattern: ${VAR:-default} or ${VAR}
                pattern = r"\$\{([^:}]+)(?::-([^}]*))?\}"

                def replace_var(match):
                    var_name = match.group(1)
                    default_value = match.group(2) if match.group(2) is not None else ""

                    # Get value from environment or use default
                    env_value = os.getenv(var_name)
                    result = env_value if env_value is not None else default_value
                    logger.debug(f"Shell variable substitution: {var_name} -> {result}")
                    return result

                result = re.sub(pattern, replace_var, value)
                if result != value:
                    logger.debug(f"Processed shell variable: {value} -> {result}")
                return result
            elif isinstance(value, dict):
                return {k: process_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [process_value(item) for item in value]
            else:
                return value

        return process_value(config)

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
            "HOST": ["server", "host"],
            "PORT": ["server", "port"],
            "DEBUG": ["server", "debug"],
            "BASE_URL": ["server", "base_url"],
            "DATABASE_URL": ["database_service", "url"],
            "AUTH_SERVICE_URL": ["authentication_service", "url"],
            "ENABLE_AUTH": ["authentication", "enabled"],
            "ENABLE_SIGNUP": ["authentication", "enable_signup"],
            "JWT_SECRET_KEY": ["authentication", "jwt_secret_key"],
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

    def get_database_service_config(self) -> Dict[str, Any]:
        """
        Get database service configuration.

        Returns:
            Database service configuration dictionary
        """
        config = self.load_config()
        return config.get("database_service", {})

    def get_api_config(self) -> Dict[str, Any]:
        """
        Get API configuration.

        Returns:
            API configuration dictionary
        """
        config = self.load_config()
        return config.get("api", {})

    def get_frontend_config(self) -> Dict[str, Any]:
        """
        Get frontend configuration.

        Returns:
            Frontend configuration dictionary
        """
        config = self.load_config()
        return config.get("frontend", {})

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

    def get_authentication_service_config(self) -> Dict[str, Any]:
        """
        Get authentication service configuration.

        Returns:
            Authentication service configuration dictionary
        """
        config = self.load_config()
        return config.get("authentication_service", {})

    def get_authentication_config(self) -> Dict[str, Any]:
        """
        Get authentication configuration.

        Returns:
            Authentication configuration dictionary
        """
        config = self.load_config()
        return config.get("authentication", {})

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
        required_sections = ["server", "database_service", "api", "frontend"]
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required configuration section: {section}")

        # Check server configuration
        server = config["server"]
        if "host" not in server or "port" not in server:
            raise ValueError("Missing required server configuration: host or port")

        # Check database service configuration
        database_service = config["database_service"]
        if "url" not in database_service:
            raise ValueError("Missing required database service configuration: url")

        # Check API configuration
        api = config["api"]
        if "limits" not in api:
            raise ValueError("Missing required API configuration: limits")

        # Check frontend configuration
        frontend = config["frontend"]
        if "visualization" not in frontend or "ui" not in frontend:
            raise ValueError("Missing required frontend configuration: visualization or ui")

        logger.info("Configuration validation passed")
        return True
