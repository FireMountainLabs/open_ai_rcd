"""
Configuration Manager for Dashboard Service

Handles loading and validation of configuration from YAML files and environment
variables. Provides a centralized way to manage all configuration settings for
the dashboard service.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from common_config import CommonConfigManager

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

        # Use CommonConfigManager to load all configurations (common + dashboard)
        os.environ["SERVICE_NAME"] = "dashboard"
        common_mgr = CommonConfigManager()
        self._config = common_mgr.load_config()

        logger.info(f"Configuration loaded using CommonConfigManager (service: dashboard)")
        return self._config

    # These methods are now handled by CommonConfigManager in shared-services

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
