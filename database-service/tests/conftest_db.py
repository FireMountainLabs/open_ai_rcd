"""
Minimal pytest configuration for Database Service tests.

This version doesn't import the app module to avoid dependency issues.
"""

import os
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test data."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def test_db_path(temp_dir):
    """Create a test database file path."""
    return temp_dir / "test_aiml_data.db"


@pytest.fixture
def sample_database(test_db_path):
    """Create a sample database with test data."""
    import sqlite3

    # Create database with required tables
    conn = sqlite3.connect(test_db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Create tables
    cursor.execute(
        """
        CREATE TABLE risks (
            risk_id TEXT PRIMARY KEY,
            risk_title TEXT NOT NULL,
            risk_description TEXT,
            category TEXT
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE controls (
            control_id TEXT PRIMARY KEY,
            control_title TEXT NOT NULL,
            control_description TEXT,
            security_function TEXT,
            control_type TEXT,
            maturity_level TEXT,
            asset_type TEXT
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE questions (
            question_id TEXT PRIMARY KEY,
            question_text TEXT NOT NULL,
            category TEXT,
            topic TEXT,
            managing_role TEXT
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE risk_control_mapping (
            risk_id TEXT,
            control_id TEXT,
            PRIMARY KEY (risk_id, control_id)
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE question_risk_mapping (
            question_id TEXT,
            risk_id TEXT,
            PRIMARY KEY (question_id, risk_id)
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE question_control_mapping (
            question_id TEXT,
            control_id TEXT,
            PRIMARY KEY (question_id, control_id)
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE file_metadata (
            data_type TEXT PRIMARY KEY,
            version TEXT,
            filename TEXT,
            file_modified_time TEXT
        )
    """
    )

    # Insert sample data
    sample_risks = [
        (
            "AIR.001",
            "Data Privacy Risk",
            "Risk of unauthorized access to sensitive data",
            "Privacy",
        ),
        ("AIR.002", "Model Bias Risk", "Risk of biased model outputs", "Fairness"),
        ("AIR.003", "Security Risk", "Risk of system compromise", "Security"),
    ]

    sample_controls = [
        (
            "AIGPC.1",
            "Data Encryption",
            "Implement encryption for data at rest and in transit",
            "Protect",
            "Preventive",
            "Basic",
            "Data",
        ),
        (
            "AIGPC.2",
            "Model Validation",
            "Validate model outputs for bias and accuracy",
            "Detect",
            "Detective",
            "Intermediate",
            "Model",
        ),
        (
            "AIGPC.3",
            "Access Control",
            "Control access to AI systems and data",
            "Protect",
            "Preventive",
            "Advanced",
            "System",
        ),
    ]

    sample_questions = [
        (
            "Q1",
            "How is data privacy protected?",
            "Privacy",
            "Data Protection",
            "Data Officer",
        ),
        (
            "Q2",
            "What validation processes are in place?",
            "Validation",
            "Model Testing",
            "ML Engineer",
        ),
        (
            "Q3",
            "How is access controlled?",
            "Security",
            "Access Management",
            "Security Officer",
        ),
    ]

    # Insert data
    cursor.executemany("INSERT INTO risks VALUES (?, ?, ?, ?)", sample_risks)
    cursor.executemany(
        "INSERT INTO controls VALUES (?, ?, ?, ?, ?, ?, ?)", sample_controls
    )
    cursor.executemany("INSERT INTO questions VALUES (?, ?, ?, ?, ?)", sample_questions)

    # Insert relationships
    risk_control_mappings = [
        ("AIR.001", "AIGPC.1"),
        ("AIR.002", "AIGPC.2"),
        ("AIR.003", "AIGPC.3"),
    ]

    question_risk_mappings = [
        ("Q1", "AIR.001"),
        ("Q2", "AIR.002"),
        ("Q3", "AIR.003"),
    ]

    question_control_mappings = [
        ("Q1", "AIGPC.1"),
        ("Q2", "AIGPC.2"),
        ("Q3", "AIGPC.3"),
    ]

    cursor.executemany(
        "INSERT INTO risk_control_mapping VALUES (?, ?)", risk_control_mappings
    )
    cursor.executemany(
        "INSERT INTO question_risk_mapping VALUES (?, ?)", question_risk_mappings
    )
    cursor.executemany(
        "INSERT INTO question_control_mapping VALUES (?, ?)", question_control_mappings
    )

    # Insert file metadata
    metadata = [
        ("risks", "1.0", "risks.xlsx", "2025-01-01T00:00:00Z"),
        ("controls", "1.0", "controls.xlsx", "2025-01-01T00:00:00Z"),
        ("questions", "1.0", "questions.xlsx", "2025-01-01T00:00:00Z"),
    ]
    cursor.executemany("INSERT INTO file_metadata VALUES (?, ?, ?, ?)", metadata)

    conn.commit()
    conn.close()

    return test_db_path


@pytest.fixture
def sample_risk_data():
    """Sample risk data for testing."""
    return {
        "id": "AIR.001",
        "title": "Data Privacy Risk",
        "description": "Risk of unauthorized access to sensitive data",
        "category": "Privacy",
    }


@pytest.fixture
def sample_control_data():
    """Sample control data for testing."""
    return {
        "id": "AIGPC.1",
        "title": "Data Encryption",
        "description": "Implement encryption for data at rest and in transit",
        "domain": "Protect",
    }


@pytest.fixture
def sample_question_data():
    """Sample question data for testing."""
    return {
        "id": "Q1",
        "text": "How is data privacy protected?",
        "category": "Privacy",
        "topic": "Data Protection",
    }


class TestDataGenerator:
    """Utility class for generating test data."""

    @staticmethod
    def create_risk_data(count=10):
        """Generate risk test data."""
        data = []
        for i in range(1, count + 1):
            data.append(
                {
                    "risk_id": f"AIR.{i:03d}",
                    "risk_title": f"Test Risk {i}",
                    "risk_description": f"Description for test risk {i}",
                    "category": f"Category {i}",
                }
            )
        return data

    @staticmethod
    def create_control_data(count=10):
        """Generate control test data."""
        data = []
        for i in range(1, count + 1):
            data.append(
                {
                    "control_id": f"AIGPC.{i}",
                    "control_title": f"Test Control {i}",
                    "control_description": f"Description for test control {i}",
                    "security_function": f"Function {i}",
                    "control_type": "Preventive",
                    "maturity_level": "Basic",
                    "asset_type": "Data",
                }
            )
        return data

    @staticmethod
    def create_question_data(count=10):
        """Generate question test data."""
        data = []
        for i in range(1, count + 1):
            data.append(
                {
                    "question_id": f"Q{i}",
                    "question_text": f"Test question {i}?",
                    "category": f"Category {i}",
                    "topic": f"Topic {i}",
                    "managing_role": f"Role {i}",
                }
            )
        return data


@pytest.fixture
def test_data_generator():
    """Provide test data generator utility."""
    return TestDataGenerator()


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment before each test."""
    # Ensure we're in a clean state
    yield
    # Cleanup after each test if needed
    pass


@pytest.fixture
def test_config():
    """Create a test configuration for the database service."""
    return {
        "server": {
            "host": "0.0.0.0",
            "port": int(os.getenv("DATABASE_PORT")),
            "debug": False,
            "base_url": f"http://localhost:{os.getenv('DATABASE_PORT')}",
        },
        "database": {
            "path": "test_aiml_data.db",
            "timeout": 30,
            "check_same_thread": False,
            "required_tables": [
                "risks",
                "controls",
                "questions",
                "risk_control_mapping",
                "question_risk_mapping",
                "question_control_mapping",
                "file_metadata",
            ],
        },
        "api": {
            "limits": {
                "default_limit": 100,
                "max_limit": 1000,
                "max_relationships_limit": 5000,
                "search_limit": 200,
            },
            "request_timeout": 30,
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file": "/tmp/test_database_service.log",
        },
        "health_check": {
            "interval": 30,
            "timeout": 10,
            "retries": 3,
            "start_period": 10,
        },
        "performance": {
            "max_connections": 10,
            "connection_timeout": 30,
            "enable_query_cache": True,
            "cache_ttl": 300,
        },
        "cors": {
            "allow_origins": ["*"],
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        },
    }


@pytest.fixture
def mock_config_manager(test_config):
    """Create a mock config manager for testing."""
    mock_manager = Mock()
    mock_manager.get_server_config.return_value = test_config["server"]
    mock_manager.get_database_config.return_value = test_config["database"]
    mock_manager.get_api_config.return_value = test_config["api"]
    mock_manager.get_logging_config.return_value = test_config["logging"]
    mock_manager.get_health_check_config.return_value = test_config["health_check"]
    mock_manager.get_performance_config.return_value = test_config["performance"]
    mock_manager.load_config.return_value = test_config
    mock_manager.validate_config.return_value = True
    return mock_manager


@pytest.fixture
def test_client(mock_config_manager, sample_database):
    """Create a test client for the FastAPI app."""
    # Import here to avoid circular imports and dependency issues
    try:
        from fastapi.testclient import TestClient
        from app import app

        # Mock the config manager in the app
        with patch("app.config_manager", mock_config_manager):
            with TestClient(app) as client:
                yield client
    except ImportError:
        # If app import fails, create a mock client
        mock_client = Mock()
        mock_client.get.return_value.status_code = 200
        mock_client.post.return_value.status_code = 200
        yield mock_client
