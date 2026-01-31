"""
Unit tests for the ConfigManager class.

Tests configuration loading, validation, and environment variable handling.
"""

import pytest
import os
from pathlib import Path
import yaml
from unittest.mock import patch

from config_manager import ConfigManager


@pytest.fixture
def temp_dir(tmp_path):
    """Fixture providing a temporary directory."""
    return tmp_path


@pytest.fixture
def test_config(tmp_path):
    """Fixture providing a test configuration file."""
    config_file = tmp_path / "test_config.yaml"
    config_data = {
        "server": {"host": "0.0.0.0", "port": 5002, "debug": False, "base_url": "http://localhost:5002"},
        "database_service": {"url": "http://localhost:5001", "timeout": 30, "retry_attempts": 3},
        "authentication": {"enabled": True, "enable_signup": True, "jwt_secret_key": "test-secret"},
        "api": {"limits": {"default_limit": 100}, "timeouts": {"request": 30}},
        "frontend": {"title": "Test Dashboard", "visualization": {"enabled": True}, "ui": {"theme": "default"}, "dependencies": {}},
        "logging": {"level": "INFO", "format": "standard", "file": "test.log"},
        "health_check": {"enabled": True, "interval": 60, "retries": 3},
        "performance": {"cache_ttl": 300, "max_connections": 100},
    }
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)
    return config_file


@pytest.mark.unit
@pytest.mark.config
class TestConfigManager:
    """Test cases for ConfigManager class."""

    def test_init_with_default_config_file(self):
        """Test initialization with default config file."""
        config_manager = ConfigManager()
        assert (
            config_manager.config_file == Path(__file__).parent.parent / "config.yaml"
        )

    def test_init_with_custom_config_file(self, temp_dir):
        """Test initialization with custom config file."""
        config_file = temp_dir / "custom_config.yaml"
        config_manager = ConfigManager(config_file)
        assert config_manager.config_file == config_file

    def test_load_config_success(self, test_config):
        """Test successful configuration loading."""
        config_manager = ConfigManager(test_config)
        config = config_manager.load_config()

        assert isinstance(config, dict)
        assert "server" in config
        assert "database_service" in config
        assert "authentication" in config
        assert "api" in config
        assert "frontend" in config

    def test_load_config_file_not_found(self, temp_dir):
        """Test configuration loading when file doesn't exist."""
        config_file = temp_dir / "nonexistent.yaml"
        config_manager = ConfigManager(config_file)

        with pytest.raises(FileNotFoundError):
            config_manager.load_config()

    def test_load_config_invalid_yaml(self, temp_dir):
        """Test configuration loading with invalid YAML."""
        config_file = temp_dir / "invalid.yaml"
        with open(config_file, "w") as f:
            f.write("invalid: yaml: content: [")

        config_manager = ConfigManager(config_file)

        with pytest.raises(yaml.YAMLError):
            config_manager.load_config()

    def test_merge_with_environment_variables(self, test_config):
        """Test merging configuration with environment variables."""
        config_manager = ConfigManager(test_config)

        with patch.dict(
            os.environ,
            {
                "HOST": "test-host",
                "PORT": "9999",
                "ENABLE_AUTH": "false",
                "LOG_LEVEL": "DEBUG",
            },
        ):
            config = config_manager.load_config()

            assert config["server"]["host"] == "test-host"
            assert config["server"]["port"] == 9999
            assert config["authentication"]["enabled"] is False
            assert config["logging"]["level"] == "DEBUG"

    def test_get_server_config(self, test_config):
        """Test getting server configuration."""
        config_manager = ConfigManager(test_config)
        server_config = config_manager.get_server_config()

        assert isinstance(server_config, dict)
        assert "host" in server_config
        assert "port" in server_config
        assert "debug" in server_config
        assert "base_url" in server_config

    def test_get_database_service_config(self, test_config):
        """Test getting database service configuration."""
        config_manager = ConfigManager(test_config)
        db_config = config_manager.get_database_service_config()

        assert isinstance(db_config, dict)
        assert "url" in db_config
        assert "timeout" in db_config
        assert "retry_attempts" in db_config

    def test_get_authentication_config(self, test_config):
        """Test getting authentication configuration."""
        config_manager = ConfigManager(test_config)
        auth_config = config_manager.get_authentication_config()

        assert isinstance(auth_config, dict)
        assert "enabled" in auth_config
        assert "enable_signup" in auth_config
        assert "jwt_secret_key" in auth_config

    def test_get_api_config(self, test_config):
        """Test getting API configuration."""
        config_manager = ConfigManager(test_config)
        api_config = config_manager.get_api_config()

        assert isinstance(api_config, dict)
        assert "limits" in api_config
        assert "timeouts" in api_config
        assert "default_limit" in api_config["limits"]

    def test_get_frontend_config(self, test_config):
        """Test getting frontend configuration."""
        config_manager = ConfigManager(test_config)
        frontend_config = config_manager.get_frontend_config()

        assert isinstance(frontend_config, dict)
        assert "visualization" in frontend_config
        assert "ui" in frontend_config
        assert "dependencies" in frontend_config

    def test_get_logging_config(self, test_config):
        """Test getting logging configuration."""
        config_manager = ConfigManager(test_config)
        logging_config = config_manager.get_logging_config()

        assert isinstance(logging_config, dict)
        assert "level" in logging_config
        assert "format" in logging_config
        assert "file" in logging_config

    def test_validate_config_success(self, test_config):
        """Test successful configuration validation."""
        config_manager = ConfigManager(test_config)
        assert config_manager.validate_config() is True

    def test_validate_config_missing_sections(self, temp_dir):
        """Test configuration validation with missing sections."""
        # Create config with missing required sections
        incomplete_config = {
            "server": {"host": "localhost", "port": int(os.getenv("DASHBOARD_PORT"))}
            # Missing database_service, api, frontend
        }

        config_file = temp_dir / "incomplete.yaml"
        with open(config_file, "w") as f:
            yaml.dump(incomplete_config, f)

        config_manager = ConfigManager(config_file)

        with pytest.raises(ValueError, match="Missing required configuration section"):
            config_manager.validate_config()

    def test_validate_config_missing_server_config(self, temp_dir):
        """Test configuration validation with missing server config."""
        incomplete_config = {
            "server": {"host": "localhost"},  # Missing port
            "database_service": {
                "url": f"http://localhost:{os.getenv('DATABASE_PORT')}"
            },
            "api": {"limits": {"default_limit": 100}},
            "frontend": {"visualization": {}, "ui": {}},
        }

        config_file = temp_dir / "incomplete_server.yaml"
        with open(config_file, "w") as f:
            yaml.dump(incomplete_config, f)

        config_manager = ConfigManager(config_file)

        with pytest.raises(ValueError, match="Missing required server configuration"):
            config_manager.validate_config()

    def test_validate_config_missing_database_url(self, temp_dir):
        """Test configuration validation with missing database URL."""
        incomplete_config = {
            "server": {"host": "localhost", "port": int(os.getenv("DASHBOARD_PORT"))},
            "database_service": {"timeout": 30},  # Missing url
            "api": {"limits": {"default_limit": 100}},
            "frontend": {"visualization": {}, "ui": {}},
        }

        config_file = temp_dir / "incomplete_db.yaml"
        with open(config_file, "w") as f:
            yaml.dump(incomplete_config, f)

        # Temporarily unset DATABASE_URL environment variable
        original_db_url = os.environ.get("DATABASE_URL")
        if "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]

        try:
            config_manager = ConfigManager(config_file)

            with pytest.raises(
                ValueError, match="Missing required database service configuration"
            ):
                config_manager.validate_config()
        finally:
            # Restore original environment variable
            if original_db_url is not None:
                os.environ["DATABASE_URL"] = original_db_url

    def test_environment_variable_type_conversion(self, test_config):
        """Test proper type conversion of environment variables."""
        config_manager = ConfigManager(test_config)

        with patch.dict(
            os.environ,
            {
                "PORT": "8080",  # Should be converted to int
                "DEBUG": "true",  # Should be converted to bool
                "ENABLE_AUTH": "false",  # Should be converted to bool
                "DATABASE_URL": f'http://test:{os.getenv("DATABASE_PORT")}',  # Should remain string
            },
        ):
            config = config_manager.load_config()

            assert isinstance(config["server"]["port"], int)
            assert config["server"]["port"] == 8080
            assert isinstance(config["server"]["debug"], bool)
            assert config["server"]["debug"] is True
            assert isinstance(config["authentication"]["enabled"], bool)
            assert config["authentication"]["enabled"] is False
            assert isinstance(config["database_service"]["url"], str)
            assert (
                config["database_service"]["url"]
                == f'http://test:{os.getenv("DATABASE_PORT")}'
            )

    def test_config_caching(self, test_config):
        """Test that configuration is cached after first load."""
        config_manager = ConfigManager(test_config)

        # First load
        config1 = config_manager.load_config()

        # Second load should return cached version
        config2 = config_manager.load_config()

        assert config1 is config2  # Same object reference

    def test_nested_environment_variable_creation(self, test_config):
        """Test creation of nested configuration from environment variables."""
        config_manager = ConfigManager(test_config)

        with patch.dict(os.environ, {"JWT_SECRET_KEY": "test-secret-key"}):
            config = config_manager.load_config()

            # Should create nested structure if it doesn't exist
            assert "authentication" in config
            assert "jwt_secret_key" in config["authentication"]
            assert config["authentication"]["jwt_secret_key"] == "test-secret-key"

    def test_get_health_check_config(self, test_config):
        """Test getting health check configuration."""
        config_manager = ConfigManager(test_config)
        health_config = config_manager.get_health_check_config()

        assert isinstance(health_config, dict)
        # Should return health check config from test config
        assert "interval" in health_config
        assert "retries" in health_config

    def test_get_performance_config(self, test_config):
        """Test getting performance configuration."""
        config_manager = ConfigManager(test_config)
        performance_config = config_manager.get_performance_config()

        assert isinstance(performance_config, dict)
        # Should return performance config from test config
        assert "cache_ttl" in performance_config
        assert "max_connections" in performance_config

    def test_validate_config_missing_health_check(self, test_config):
        """Test validation with missing health check configuration."""
        config_manager = ConfigManager(test_config)

        # Create incomplete config
        incomplete_config = {
            "server": {
                "host": "0.0.0.0",
                "port": int(os.getenv("DASHBOARD_PORT", "5002")),
            },
            "database_service": {
                "url": f"http://localhost:{os.getenv('DATABASE_PORT')}"
            },
            "api": {"limits": {"default_limit": 100}},
            "frontend": {"visualization": {}, "ui": {}},
        }

        with patch.object(
            config_manager, "load_config", return_value=incomplete_config
        ):
            # Should not raise error as health_check is optional
            result = config_manager.validate_config()
            assert result is True

    def test_validate_config_missing_performance(self, test_config):
        """Test validation with missing performance configuration."""
        config_manager = ConfigManager(test_config)

        # Create incomplete config
        incomplete_config = {
            "server": {
                "host": "0.0.0.0",
                "port": int(os.getenv("DASHBOARD_PORT", "5002")),
            },
            "database_service": {
                "url": f"http://localhost:{os.getenv('DATABASE_PORT')}"
            },
            "api": {"limits": {"default_limit": 100}},
            "frontend": {"visualization": {}, "ui": {}},
        }

        with patch.object(
            config_manager, "load_config", return_value=incomplete_config
        ):
            # Should not raise error as performance is optional
            result = config_manager.validate_config()
            assert result is True
