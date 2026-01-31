"""
Unit tests for ConfigManager class.

Tests configuration loading, validation, and environment variable handling.
"""

from unittest.mock import patch

import pytest
import yaml

from config.config_manager import ConfigManager


class TestConfigManager:
    """Test cases for ConfigManager class."""

    def test_init_with_config_file(self, temp_dir):
        """Test ConfigManager initialization with config file."""
        config_file = temp_dir / "test_config.yaml"
        config_data = {"test": "value"}

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(config_file)
        assert manager.config_file == config_file

    def test_init_without_config_file(self):
        """Test ConfigManager initialization without config file."""
        manager = ConfigManager()
        assert manager.config_file.name == "default_config.yaml"

    def test_load_config_success(self, sample_config):
        """Test successful configuration loading."""
        manager = ConfigManager(sample_config)
        config = manager.load_config()

        assert "data_sources" in config
        assert "database" in config
        assert "extraction" in config
        assert "output" in config

    def test_load_config_file_not_found(self, temp_dir):
        """Test configuration loading with non-existent file."""
        config_file = temp_dir / "nonexistent.yaml"
        manager = ConfigManager(config_file)

        with pytest.raises(FileNotFoundError):
            manager.load_config()

    def test_load_config_invalid_yaml(self, temp_dir):
        """Test configuration loading with invalid YAML."""
        config_file = temp_dir / "invalid.yaml"
        with open(config_file, "w") as f:
            f.write("invalid: yaml: content: [")

        manager = ConfigManager(config_file)

        with pytest.raises(yaml.YAMLError):
            manager.load_config()

    def test_get_data_source_config(self, config_manager):
        """Test getting data source configuration."""
        risks_config = config_manager.get_data_source_config("risks")

        assert "file" in risks_config
        assert "columns" in risks_config
        assert risks_config["file"] == "test_risks.xlsx"

    def test_get_data_source_config_invalid(self, config_manager):
        """Test getting invalid data source configuration."""
        with pytest.raises(KeyError):
            config_manager.get_data_source_config("invalid_source")

    def test_get_database_config(self, config_manager):
        """Test getting database configuration."""
        db_config = config_manager.get_database_config()

        assert "file" in db_config
        assert db_config["file"] == "test_data.db"

    def test_get_extraction_config(self, config_manager):
        """Test getting extraction configuration."""
        extraction_config = config_manager.get_extraction_config()

        assert "validate_files" in extraction_config
        assert "remove_duplicates" in extraction_config
        assert extraction_config["validate_files"] is True

    def test_get_output_config(self, config_manager):
        """Test getting output configuration."""
        output_config = config_manager.get_output_config()

        assert "print_summary" in output_config
        assert "collect_metadata" in output_config
        assert output_config["collect_metadata"] is True

    def test_validate_config_success(self, config_manager):
        """Test successful configuration validation."""
        assert config_manager.validate_config() is True

    def test_validate_config_missing_sections(self, temp_dir):
        """Test configuration validation with missing sections."""
        config_data = {"database": {"file": "test.db"}}
        config_file = temp_dir / "incomplete_config.yaml"

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(config_file)

        with pytest.raises(ValueError, match="Missing required configuration section"):
            manager.validate_config()

    def test_environment_variable_override(self, temp_dir):
        """Test environment variable override functionality."""
        config_data = {
            "data_sources": {"risks": {"file": "default_risks.xlsx"}},
            "database": {"file": "default.db"},
            "extraction": {"validate_files": False},
        }

        config_file = temp_dir / "env_test_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        env_vars = {
            "DATA_SOURCES_RISKS_FILE": "env_risks.xlsx",
            "DATABASE_FILE": "env_db.db",
            "EXTRACTION_VALIDATE_FILES": "true",
        }

        with patch.dict("os.environ", env_vars):
            manager = ConfigManager(config_file)
            config = manager.load_config()

            assert config["data_sources"]["risks"]["file"] == "env_risks.xlsx"
            assert config["database"]["file"] == "env_db.db"
            assert config["extraction"]["validate_files"] is True

    def test_environment_variable_type_conversion(self, temp_dir):
        """Test environment variable type conversion."""
        config_data = {
            "extraction": {"validate_files": False, "remove_duplicates": False}
        }

        config_file = temp_dir / "type_test_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        env_vars = {
            "EXTRACTION_VALIDATE_FILES": "true",
            "EXTRACTION_REMOVE_DUPLICATES": "false",
        }

        with patch.dict("os.environ", env_vars):
            manager = ConfigManager(config_file)
            config = manager.load_config()

            assert config["extraction"]["validate_files"] is True
            assert config["extraction"]["remove_duplicates"] is False

    def test_config_caching(self, config_manager):
        """Test that configuration is cached after first load."""
        # First load
        config1 = config_manager.load_config()

        # Second load should return cached version
        config2 = config_manager.load_config()

        assert config1 is config2  # Same object reference

    def test_config_reload(self, config_manager):
        """Test configuration reloading."""
        # Load initial config
        config1 = config_manager.load_config()

        # Force reload by clearing cache
        config_manager._config = None
        config2 = config_manager.load_config()

        # Should be different objects but same content
        assert config1 is not config2
        assert config1 == config2
