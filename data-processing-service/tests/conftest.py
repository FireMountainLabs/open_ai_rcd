import pandas as pd

"""
Pytest configuration and shared fixtures for data processing service tests.

This module provides common test fixtures, configuration, and utilities
used across all test modules.
"""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from config.config_manager import ConfigManager
from data_processor import DataProcessor
from database_manager import DatabaseManager


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test data."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_config(temp_dir):
    """Create a sample configuration file for testing."""
    config_data = {
        "data_sources": {
            "risks": {
                "file": "test_risks.xlsx",
                "columns": {
                    "id": "ID",
                    "title": "Risk",
                    "description": "Risk Description",
                },
            },
            "controls": {
                "file": "test_controls.xlsx",
                "columns": {"id": "Code", "title": "Purpose", "description": "Purpose"},
            },
            "questions": {
                "file": "test_questions.xlsx",
                "columns": {
                    "id": "Question Number",
                    "text": "Question Text",
                    "category": "Category",
                    "topic": "Topic",
                    "risk_mapping": "AIML_RISK_TAXONOMY",
                    "control_mapping": "AIML_CONTROL",
                },
            },
        },
        "database": {"file": "test_data.db"},
        "extraction": {
            "validate_files": True,
            "remove_duplicates": True,
            "log_level": "DEBUG",
        },
        "output": {"print_summary": False, "collect_metadata": True},
    }

    config_file = temp_dir / "test_config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    return config_file


@pytest.fixture
def sample_risks_data():
    """Create sample risk data for testing."""
    return pd.DataFrame(
        {
            "ID": ["AIR.001", "AIR.002", "AIR.003"],
            "Risk": ["Data Privacy Risk", "Model Bias Risk", "Security Risk"],
            "Risk Description": [
                "Risk of unauthorized access to sensitive data",
                "Risk of biased model outputs",
                "Risk of system compromise",
            ],
        }
    )


@pytest.fixture
def sample_controls_data():
    """Create sample control data for testing."""
    return pd.DataFrame(
        {
            "Code": ["AIGPC.1", "AIGPC.2", "AIGPC.3"],
            "Purpose": ["Data Encryption", "Model Validation", "Access Control"],
            "Description": [
                "Implement encryption for data at rest and in transit",
                "Validate model outputs for bias and accuracy",
                "Control access to AI systems and data",
            ],
            "Mapped Risks": ["AIR.001", "AIR.002", "AIR.003"],
        }
    )


@pytest.fixture
def sample_questions_data():
    """Create sample questions data for testing."""
    return pd.DataFrame(
        {
            "Question Number": ["Q1", "Q2", "Q3"],
            "Question Text": [
                "How is data privacy protected?",
                "What validation processes are in place?",
                "How is access controlled?",
            ],
            "Category": ["Privacy", "Validation", "Security"],
            "Topic": ["Data Protection", "Model Testing", "Access Management"],
            "AIML_RISK_TAXONOMY": ["AIR.001", "AIR.002", "AIR.003"],
            "AIML_CONTROL": ["AIGPC.1", "AIGPC.2", "AIGPC.3"],
        }
    )


@pytest.fixture
def mock_excel_files(
    temp_dir, sample_risks_data, sample_controls_data, sample_questions_data
):
    """Create mock Excel files for testing."""
    # Create Excel files
    risks_file = temp_dir / "test_risks.xlsx"
    controls_file = temp_dir / "test_controls.xlsx"
    questions_file = temp_dir / "test_questions.xlsx"

    sample_risks_data.to_excel(risks_file, index=False)
    sample_controls_data.to_excel(controls_file, index=False)
    sample_questions_data.to_excel(questions_file, index=False)

    return {"risks": risks_file, "controls": controls_file, "questions": questions_file}


@pytest.fixture
def config_manager(sample_config):
    """Create a ConfigManager instance for testing."""
    return ConfigManager(sample_config)


@pytest.fixture
def database_manager(temp_dir):
    """Create a DatabaseManager instance for testing."""
    db_path = temp_dir / "test.db"
    manager = DatabaseManager(db_path)
    yield manager
    # Ensure connection is closed after test
    manager.close_connection()


@pytest.fixture
def data_processor(temp_dir, sample_config):
    """Create a DataProcessor instance for testing."""
    processor = DataProcessor(
        data_dir=temp_dir,
        output_dir=temp_dir / "output",
        config_manager=ConfigManager(sample_config),
    )
    yield processor
    # Ensure database connection is closed after test
    if hasattr(processor, "database_manager") and processor.database_manager:
        processor.database_manager.close_connection()


@pytest.fixture
def mock_environment():
    """Mock environment variables for testing."""
    env_vars = {
        "DATA_DIR": "/test/data",
        "OUTPUT_DIR": "/test/output",
        "CONFIG_FILE": "/test/config.yaml",
        "LOG_LEVEL": "DEBUG",
        "VALIDATE_FILES": "true",
        "REMOVE_DUPLICATES": "true",
    }

    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    return Mock()


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment before each test."""
    # Ensure we're in a clean state
    yield
    # Cleanup after each test if needed
    pass


class TestDataGenerator:
    """Utility class for generating test data."""

    @staticmethod
    def create_risk_data(count=10):
        """Generate risk test data."""
        data = []
        for i in range(1, count + 1):
            data.append(
                {
                    "ID": f"AIR.{i:03d}",
                    "Risk": f"Test Risk {i}",
                    "Risk Description": f"Description for test risk {i}",
                }
            )
        return pd.DataFrame(data)

    @staticmethod
    def create_control_data(count=10):
        """Generate control test data."""
        data = []
        for i in range(1, count + 1):
            data.append(
                {
                    "Code": f"AIGPC.{i}",
                    "Purpose": f"Test Control {i}",
                    "Description": f"Description for test control {i}",
                    "Mapped Risks": f"AIR.{i:03d}",
                }
            )
        return pd.DataFrame(data)

    @staticmethod
    def create_question_data(count=10):
        """Generate question test data."""
        data = []
        for i in range(1, count + 1):
            data.append(
                {
                    "Question Number": f"Q{i}",
                    "Question Text": f"Test question {i}?",
                    "Category": f"Category {i}",
                    "Topic": f"Topic {i}",
                    "AIML_RISK_TAXONOMY": f"AIR.{i:03d}",
                    "AIML_CONTROL": f"AIGPC.{i}",
                }
            )
        return pd.DataFrame(data)


@pytest.fixture
def test_data_generator():
    """Provide test data generator utility."""
    return TestDataGenerator()


@pytest.fixture
def sample_control_data_domains():
    """Sample data for Domains sheet in control extractor tests."""
    return pd.DataFrame(
        {
            "Code": ["AIIM.1", "AIIM.2", "AIIM.3"],
            "Purpose": ["Data Management", "Model Governance", "Security Controls"],
            "Mapped Risks": ["AIR.001", "AIR.002", "AIR.003"],
            "Asset Type": ["Data", "Model", "System"],
            "Control Type": ["Preventive", "Detective", "Corrective"],
            "Security Function": ["Protect", "Detect", "Respond"],
            "Maturity": ["Basic", "Intermediate", "Advanced"],
        }
    )


@pytest.fixture
def sample_control_data_individual():
    """Sample data for individual control sheet in control extractor tests."""
    return pd.DataFrame(
        {
            "Sub-Control": ["AIIM.1.1", "AIIM.1.2", "AIIM.2.1"],
            "Control Title": [
                "Data Classification",
                "Access Control",
                "Model Validation",
            ],
            "Control Description": [
                "Classify data by sensitivity",
                "Control access to systems",
                "Validate model outputs",
            ],
            "Mapped Risks": ["AIR.001", "AIR.002", "AIR.003"],
            "Asset Type": ["Data", "System", "Model"],
            "Control Type": ["Preventive", "Preventive", "Detective"],
            "Security Function": ["Protect", "Protect", "Detect"],
            "Maturity": ["Basic", "Intermediate", "Advanced"],
        }
    )


@pytest.fixture
def sample_question_data_extended():
    """Extended sample question data for extractor tests."""
    return pd.DataFrame(
        {
            "Question Number": ["Q1", "Q2", "Q3"],
            "Question Text": [
                "How is data privacy protected?",
                "What validation processes are in place?",
                "How is access controlled?",
            ],
            "Category": ["Privacy", "Validation", "Security"],
            "Topic": ["Data Protection", "Model Testing", "Access Management"],
            "AIML_RISK_TAXONOMY": ["AIR.001", "AIR.002", "AIR.003"],
            "AIML_CONTROL": ["AIGPC.1", "AIGPC.2", "AIGPC.3"],
        }
    )


@pytest.fixture
def sample_risks_data_extended():
    """Extended sample risks data for extractor tests."""
    return pd.DataFrame(
        {
            "risk_id": ["R.AIR.001", "R.AIR.002", "R.AIR.003"],
            "risk_title": ["Data Privacy Risk", "Model Bias Risk", "Security Risk"],
            "risk_description": [
                "Risk of unauthorized access to sensitive data",
                "Risk of biased model outputs",
                "Risk of system compromise",
            ],
        }
    )


@pytest.fixture
def sample_controls_data_extended():
    """Extended sample controls data for extractor tests."""
    return pd.DataFrame(
        {
            "control_id": ["C.AIGPC.1", "C.AIGPC.2", "C.AIGPC.3"],
            "control_title": ["Data Encryption", "Model Validation", "Access Control"],
            "control_description": [
                "Implement encryption for data at rest and in transit",
                "Validate model outputs for bias and accuracy",
                "Control access to AI systems and data",
            ],
            "mapped_risks": ["AIR.001", "AIR.002", "AIR.003"],
        }
    )
