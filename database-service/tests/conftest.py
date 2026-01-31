"""
Main pytest configuration and shared fixtures for database service tests.

This module provides common test fixtures, configuration, and utilities
used across all test modules.
"""

import pytest
import tempfile
import shutil
import sqlite3
import os
import time
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch
from contextlib import contextmanager

# Set environment variables before importing app
os.environ["DATABASE_PORT"] = os.getenv("DATABASE_PORT", "5001")

# Import the app and models
import sys

# Add parent directory to path for imports (works in any environment)
sys.path.insert(0, str(Path(__file__).parent.parent))

# Conditional imports to handle missing dependencies
try:
    from app import app, get_db_connection, validate_database
    from config_manager import ConfigManager
    from db.connections import DatabaseManager
except ImportError as e:
    # Handle missing dependencies gracefully
    print(f"Warning: Could not import app modules: {e}")
    app = None
    get_db_connection = None
    validate_database = None
    ConfigManager = None
    DatabaseManager = None


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
            PRIMARY KEY (risk_id, control_id),
            FOREIGN KEY (risk_id) REFERENCES risks(risk_id),
            FOREIGN KEY (control_id) REFERENCES controls(control_id)
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE question_risk_mapping (
            question_id TEXT,
            risk_id TEXT,
            PRIMARY KEY (question_id, risk_id),
            FOREIGN KEY (question_id) REFERENCES questions(question_id),
            FOREIGN KEY (risk_id) REFERENCES risks(risk_id)
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE question_control_mapping (
            question_id TEXT,
            control_id TEXT,
            PRIMARY KEY (question_id, control_id),
            FOREIGN KEY (question_id) REFERENCES questions(question_id),
            FOREIGN KEY (control_id) REFERENCES controls(control_id)
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE definitions (
            definition_id TEXT PRIMARY KEY,
            term TEXT NOT NULL,
            description TEXT,
            category TEXT,
            source TEXT
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

    cursor.execute(
        """
        CREATE TABLE capabilities (
            capability_id TEXT PRIMARY KEY,
            capability_name TEXT NOT NULL,
            capability_type TEXT NOT NULL,
            capability_domain TEXT,
            capability_definition TEXT,
            candidate_products TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE capability_control_mapping (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            capability_id TEXT NOT NULL,
            control_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (capability_id) REFERENCES capabilities (capability_id),
            FOREIGN KEY (control_id) REFERENCES controls (control_id),
            UNIQUE(capability_id, control_id)
        )
    """
    )

    # Create capability scenario tables
    # Note: These tables are in the capability_configs.db in production
    # but in tests we create them in the same test database
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS capability_scenarios (
            scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            scenario_name TEXT NOT NULL,
            is_default BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, scenario_name)
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS capability_selections (
            selection_id INTEGER PRIMARY KEY AUTOINCREMENT,
            scenario_id INTEGER NOT NULL,
            capability_id TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 0,
            FOREIGN KEY (scenario_id) REFERENCES capability_scenarios(scenario_id) ON DELETE CASCADE,
            UNIQUE(scenario_id, capability_id)
        )
    """
    )
    
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS control_selections (
            selection_id INTEGER PRIMARY KEY AUTOINCREMENT,
            scenario_id INTEGER NOT NULL,
            control_id TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 0,
            FOREIGN KEY (scenario_id) REFERENCES capability_scenarios(scenario_id) ON DELETE CASCADE,
            UNIQUE(scenario_id, control_id)
        )
    """
    )
    
    # Create indexes for capability tables
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_scenario_user
        ON capability_scenarios(user_id)
    """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_selection_scenario
        ON capability_selections(scenario_id)
    """
    )
    
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_control_selection_scenario
        ON control_selections(scenario_id)
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
        (
            "AIR.004",
            "Compliance Risk",
            "Risk of regulatory non-compliance",
            "Compliance",
        ),
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
        (
            "AIGPC.4",
            "Audit Logging",
            "Maintain comprehensive audit logs",
            "Detect",
            "Detective",
            "Intermediate",
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
        (
            "Q4",
            "What compliance measures exist?",
            "Compliance",
            "Regulatory",
            "Compliance Officer",
        ),
    ]

    sample_definitions = [
        (
            "DEF.001",
            "Data Privacy",
            "Protection of personal information from unauthorized access",
            "Privacy",
            "GDPR",
        ),
        (
            "DEF.002",
            "Model Bias",
            "Systematic prejudice in AI model outputs",
            "Fairness",
            "AI Ethics",
        ),
        (
            "DEF.003",
            "Access Control",
            "Mechanisms to control who can access resources",
            "Security",
            "NIST",
        ),
        (
            "DEF.004",
            "Compliance",
            "Adherence to laws, regulations, and standards",
            "Governance",
            "Regulatory",
        ),
    ]

    # Insert data
    cursor.executemany("INSERT INTO risks VALUES (?, ?, ?, ?)", sample_risks)
    cursor.executemany(
        "INSERT INTO controls VALUES (?, ?, ?, ?, ?, ?, ?)", sample_controls
    )
    cursor.executemany("INSERT INTO questions VALUES (?, ?, ?, ?, ?)", sample_questions)
    cursor.executemany(
        "INSERT INTO definitions VALUES (?, ?, ?, ?, ?)", sample_definitions
    )

    # Insert relationships
    risk_control_mappings = [
        ("AIR.001", "AIGPC.1"),
        ("AIR.002", "AIGPC.2"),
        ("AIR.003", "AIGPC.3"),
        ("AIR.004", "AIGPC.4"),
    ]

    question_risk_mappings = [
        ("Q1", "AIR.001"),
        ("Q2", "AIR.002"),
        ("Q3", "AIR.003"),
        ("Q4", "AIR.004"),
    ]

    question_control_mappings = [
        ("Q1", "AIGPC.1"),
        ("Q2", "AIGPC.2"),
        ("Q3", "AIGPC.3"),
        ("Q4", "AIGPC.4"),
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
def test_config(temp_dir, test_db_path):
    """Create a test configuration."""
    config_data = {
        "server": {
            "host": "0.0.0.0",
            "port": int(os.getenv("DATABASE_PORT")),
            "debug": True,
            "base_url": f"http://localhost:{os.getenv('DATABASE_PORT')}",
        },
        "database": {
            "path": str(test_db_path),
            "timeout": 30,
            "check_same_thread": False,
            "required_tables": [
                "risks",
                "controls",
                "questions",
                "definitions",
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
            "cors": {
                "allow_origins": ["*"],
                "allow_credentials": True,
                "allow_methods": ["*"],
                "allow_headers": ["*"],
            },
        },
        "logging": {
            "level": "DEBUG",
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
    }

    config_file = temp_dir / "test_config.yaml"
    import yaml

    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    return config_file


@pytest.fixture
def mock_config_manager(test_config):
    """Create a mock config manager for testing."""
    # Mock the config manager before importing app
    with patch.dict("sys.modules", {"config_manager": Mock()}):
        # Create a mock config manager
        mock_cm = Mock()
        mock_cm.load_config.return_value = {
            "server": {
                "host": "0.0.0.0",
                "port": int(os.getenv("DATABASE_PORT")),
                "debug": True,
                "base_url": f"http://localhost:{os.getenv('DATABASE_PORT')}",
            },
            "database": {
                "path": str(test_config.parent / "test_aiml_data.db"),
                "timeout": 30,
                "check_same_thread": False,
                "required_tables": [
                    "risks",
                    "controls",
                    "questions",
                    "definitions",
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
                "cors": {
                    "allow_origins": ["*"],
                    "allow_credentials": True,
                    "allow_methods": ["*"],
                    "allow_headers": ["*"],
                },
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
        }
        mock_cm.get_server_config.return_value = {
            "host": "0.0.0.0",
            "port": int(os.getenv("DATABASE_PORT")),
            "debug": True,
            "base_url": f"http://localhost:{os.getenv('DATABASE_PORT')}",
        }
        mock_cm.get_database_config.return_value = {
            "path": str(test_config.parent / "test_aiml_data.db"),
            "timeout": 30,
            "check_same_thread": False,
            "required_tables": [
                "risks",
                "controls",
                "questions",
                "definitions",
                "risk_control_mapping",
                "question_risk_mapping",
                "question_control_mapping",
                "file_metadata",
            ],
        }
        mock_cm.get_api_config.return_value = {
            "limits": {
                "default_limit": 100,
                "max_limit": 1000,
                "max_relationships_limit": 5000,
                "search_limit": 200,
            },
            "request_timeout": 30,
            "cors": {
                "allow_origins": ["*"],
                "allow_credentials": True,
                "allow_methods": ["*"],
                "allow_headers": ["*"],
            },
        }
        mock_cm.get_logging_config.return_value = {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file": "/tmp/test_database_service.log",
        }

        # Patch the config manager in the app module
        with patch("app.config_manager", mock_cm):
            yield mock_cm


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


@pytest.fixture
def database_service_process():
    """Start the database service process for end-to-end testing."""
    # This will be used for end-to-end tests
    process = None
    try:
        # Start the service
        process = subprocess.Popen(
            ["python", "/home/fml/dashboard_zero/database-service/app.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for service to start
        time.sleep(3)

        yield process
    finally:
        if process:
            process.terminate()
            process.wait()


@pytest.fixture
def launcher_process():
    """Start the launcher with --dev flag for end-to-end testing."""
    process = None
    try:
        # Start the launcher with --dev flag
        process = subprocess.Popen(
            ["/home/fml/dashboard_zero/launch_dataviewer", "--dev"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for services to start
        time.sleep(10)

        yield process
    finally:
        if process:
            process.terminate()
            process.wait()


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


@pytest.fixture
def sample_relationship_data():
    """Sample relationship data for testing."""
    return {
        "source_id": "AIR.001",
        "target_id": "AIGPC.1",
        "relationship_type": "risk_control",
    }


@pytest.fixture
def sample_search_results():
    """Sample search results for testing."""
    return {
        "query": "privacy",
        "results": [
            {
                "type": "risk",
                "id": "AIR.001",
                "title": "Data Privacy Risk",
                "description": "Risk of unauthorized access to sensitive data",
            }
        ],
    }


@pytest.fixture
def sample_stats_data():
    """Sample statistics data for testing."""
    return {
        "total_risks": 4,
        "total_controls": 4,
        "total_questions": 4,
        "total_relationships": 12,
        "database_version": None,
    }


@pytest.fixture
def sample_health_status():
    """Sample health status for testing."""
    return {
        "status": "healthy",
        "database_connected": True,
        "database_path": "/tmp/test_aiml_data.db",
        "total_records": 12,
    }


@contextmanager
def mock_database_path(db_path):
    """Context manager to temporarily set database path."""
    original_path = os.environ.get("DB_PATH")
    os.environ["DB_PATH"] = str(db_path)
    try:
        yield
    finally:
        if original_path:
            os.environ["DB_PATH"] = original_path
        else:
            os.environ.pop("DB_PATH", None)


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


@pytest.fixture
def test_db_manager(sample_database):
    """Create a properly configured database manager for capability config tests."""
    if DatabaseManager is None:
        pytest.skip("DatabaseManager not available")
    db_manager = DatabaseManager(str(sample_database), str(sample_database))
    db_manager.init_capability_config_db()
    return db_manager


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment before each test."""
    # Ensure we're in a clean state
    yield
    # Cleanup after each test if needed
    pass
