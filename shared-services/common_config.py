"""
Common Configuration Utility

Provides a centralized way to load and access configuration
from the master config files across all microservices.
"""

import os
import yaml
import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class CommonConfigManager:
    """
    Manages common configuration across microservices.

    Loads configuration from the master config files and provides
    easy access to port mappings, service URLs, and other shared settings.
    """

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize the common configuration manager.

        Args:
            config_dir: Path to the config directory. If None, uses default.
        """
        if config_dir is None:
            # Try /app/config first (common in Docker)
            app_config = Path("/app/config")
            if app_config.exists():
                config_dir = app_config
            else:
                # Try relative to this file
                config_dir = Path(__file__).parent.parent / "config"
                
                # If not found there, try looking for a config directory in CWD or parent of CWD
                if not config_dir.exists():
                    search_paths = [Path.cwd() / "config", Path.cwd().parent / "config"]
                    for path in search_paths:
                        if path.exists():
                            config_dir = path
                            break

        self.config_dir = Path(config_dir)
        self._config: Optional[Dict[str, Any]] = None

    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from common.yaml and other config files.

        Returns:
            Dictionary containing merged configuration
        """
        if self._config is not None:
            return self._config

        config = {}

        # Load common configuration
        common_config_path = self.config_dir / "common.yaml"
        if common_config_path.exists():
            try:
                with open(common_config_path, "r") as file:
                    common_config = yaml.safe_load(file)
                    config.update(common_config)
            except Exception as e:
                logger.error(f"Failed to load common config: {e}")

        # Load service-specific configuration if it exists
        service_config_path = self.config_dir / f"{self._get_service_name()}.yaml"
        if service_config_path.exists():
            try:
                with open(service_config_path, "r") as file:
                    service_config = yaml.safe_load(file)
                    config.update(service_config)
            except Exception as e:
                logger.error(f"Failed to load service config: {e}")

        # Apply environment variable overrides
        config = self._apply_env_overrides(config)

        # Substitute shell variables (${VAR:-default} or ${path.to.var})
        # We pass the same config as root to allow cross-references
        config = self._substitute_variables(config, config)

        self._config = config
        return config

    def get_port(self, service_name: str) -> int:
        """
        Get the configured port for a service.

        Args:
            service_name: Name of the service

        Returns:
            Port number for the service
        """
        config = self.load_config()
        ports = config.get("ports", {})
        return ports.get(service_name)  # No default port - must be configured

    def get_service_url(self, service_name: str) -> str:
        """
        Get the configured URL for a service.

        Args:
            service_name: Name of the service

        Returns:
            URL for the service
        """
        config = self.load_config()
        service_urls = config.get("service_urls", {})
        return service_urls.get(service_name, f"http://localhost:{self.get_port(service_name)}")

    def get_config_value(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.

        Args:
            key_path: Dot-separated path to the config value (e.g., 'ports.dashboard_service')
            default: Default value if key is not found

        Returns:
            Configuration value or default
        """
        config = self.load_config()
        keys = key_path.split(".")
        value = config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def _get_service_name(self) -> str:
        """Get the current service name from environment or path."""
        # Try to get from environment variable first
        service_name = os.getenv("SERVICE_NAME")
        if service_name:
            return service_name

        # Try to infer from current working directory
        cwd = Path.cwd()
        if cwd.name.endswith("-service") or cwd.name.endswith("_microservice"):
            return cwd.name

        # Default fallback
        return "unknown"

    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply environment variable overrides to configuration.

        Args:
            config: Configuration dictionary

        Returns:
            Updated configuration with environment overrides
        """
        # Environment variable overrides (legacy/fallback)
        env_mappings = {
            "LOG_LEVEL": "logging.level",
            "JWT_SECRET_KEY": "security.jwt_secret_key",
            "REQUIRE_HTTPS": "security.require_https",
            "DEBUG": "debug",
            # Note: Ports and URLs are primarily handled via ${} substitution in YAML
        }

        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Convert string values to appropriate types
                if env_value.lower() in ("true", "false"):
                    env_value = env_value.lower() == "true"
                elif env_value.isdigit():
                    env_value = int(env_value)

                # Set the value in the config using dot notation
                self._set_nested_value(config, config_path, env_value)

        return config

    def _substitute_variables(self, part: Any, root_config: Dict[str, Any], depth: int = 0) -> Any:
        """
        Process shell variable substitutions in configuration values.

        Handles syntax like:
        - ${ENV_VAR:-default} (Environment variable)
        - ${services.dashboard.port} (Nested reference within config)
        """
        # Prevent infinite recursion in case of circular references
        if depth > 5:
            return part

        if isinstance(part, str):
            # Pattern to match ${VAR:-default} or ${VAR}
            pattern = r"\$\{([^:}]+)(?::-([^}]*))?\}"

            def replace_var(match):
                var_name = match.group(1)
                default_value = match.group(2) if match.group(2) is not None else ""

                # 1. Check environment variables first (highest precedence)
                env_val = os.getenv(var_name)
                if env_val is not None:
                    return str(env_val)

                # 2. Check for nested reference (path.to.key)
                # Note: We resolve these against root_config
                ref_val = self._get_nested_value_local(root_config, var_name)
                if ref_val is not None:
                    # If the referenced value is itself a string with ${}, we resolve it recursively
                    if isinstance(ref_val, str) and "${" in ref_val:
                        return str(self._substitute_variables(ref_val, root_config, depth + 1))
                    return str(ref_val)

                return default_value

            return re.sub(pattern, replace_var, part)
        elif isinstance(part, dict):
            return {k: self._substitute_variables(v, root_config, depth) for k, v in part.items()}
        elif isinstance(part, list):
            return [self._substitute_variables(item, root_config, depth) for item in part]
        else:
            return part

    def _get_nested_value_local(self, config: Dict[str, Any], key_path: str) -> Any:
        """Local helper to get nested value without calling load_config."""
        keys = key_path.split(".")
        value = config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None

        return value

    def _set_nested_value(self, config: Dict[str, Any], key_path: str, value: Any):
        """Set a nested value in the config dictionary using dot notation."""
        keys = key_path.split(".")
        current = config

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value


# Global instance for easy access
common_config = CommonConfigManager()
