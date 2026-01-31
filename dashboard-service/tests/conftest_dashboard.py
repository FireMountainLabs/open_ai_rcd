"""
Pytest configuration and shared fixtures for dashboard service tests.

This module provides common test fixtures, configuration, and utilities
used across all test modules for the dashboard service.
"""

import pytest
import tempfile
import shutil
import os
from pathlib import Path
import yaml
from unittest.mock import patch, Mock

# Set test environment variables before importing app
os.environ["TESTING"] = "true"
os.environ["ENABLE_AUTH"] = "false"  # Disable auth for most tests
os.environ["ENABLE_SIGNUP"] = "true"  # Enable signup for registration tests
os.environ["DATABASE_PORT"] = os.getenv("DATABASE_PORT", "5001")
os.environ["AUTH_PORT"] = os.getenv("AUTH_PORT", "5003")
os.environ["DATABASE_URL"] = f'http://localhost:{os.getenv("DATABASE_PORT")}'
os.environ["AUTH_SERVICE_URL"] = f'http://localhost:{os.getenv("AUTH_PORT")}'
os.environ["LOG_LEVEL"] = "INFO"  # Set proper log level

# Import after setting environment variables
from app import app, DatabaseAPIClient, ConfigManager


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test data."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def test_config(temp_dir):
    """Create a test configuration for the dashboard service."""
    config_data = {
        "server": {
            "host": "0.0.0.0",
            "port": int(os.getenv("DASHBOARD_PORT")),
            "debug": False,
            "base_url": f"http://localhost:{os.getenv('DASHBOARD_PORT')}",
        },
        "database_service": {
            "url": f"http://localhost:{os.getenv('DATABASE_PORT')}",
            "timeout": 30,
            "retry_attempts": 3,
            "retry_delay": 1,
        },
        "authentication_service": {
            "url": f"http://localhost:{os.getenv('AUTH_PORT')}",
            "timeout": 10,
            "retry_attempts": 2,
            "retry_delay": 1,
        },
        "authentication": {
            "enabled": False,
            "enable_signup": True,
            "jwt_secret_key": "test-secret-key",
            "session_timeout": 3600,
        },
        "api": {
            "limits": {
                "default_limit": 100,
                "max_limit": 1000,
                "search_limit": 50,
                "relationships_limit": 1000,
            },
            "timeouts": {
                "request_timeout": 30,
                "search_timeout": 5000,
                "debounce_delay": 300,
            },
        },
        "frontend": {
            "visualization": {
                "max_items": 50,
                "animation_duration": 750,
                "chart_height": 200,
                "chart_width": 600,
            },
            "ui": {
                "theme": "light",
                "show_legends": True,
                "max_table_rows": 1000,
                "tooltip_delay": 500,
            },
            "dependencies": {
                "d3_js": "https://d3js.org/d3.v7.min.js",
                "d3_sankey": "https://unpkg.com/d3-sankey@0.12.3/dist/d3-sankey.min.js",
            },
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file": "/tmp/test_dashboard_service.log",
        },
        "health_check": {
            "interval": 30,
            "timeout": 10,
            "retries": 3,
            "start_period": 10,
        },
        "performance": {
            "enable_response_cache": True,
            "cache_ttl": 300,
            "max_connections": 10,
            "keep_alive": True,
        },
        "cors": {
            "allow_origins": ["*"],
            "allow_credentials": True,
            "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
        },
    }

    config_file = temp_dir / "test_config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    return config_file


@pytest.fixture
def mock_config_manager(test_config):
    """Create a mock config manager for testing."""
    config_manager = ConfigManager(test_config)
    return config_manager


@pytest.fixture
def flask_app(mock_config_manager):
    """Create a Flask app instance for testing."""
    # Configure app for testing
    app.config.update(
        {"TESTING": True, "WTF_CSRF_ENABLED": False, "SECRET_KEY": "test-secret-key"}
    )

    # Mock the config manager
    with patch("app.config_manager", mock_config_manager):
        yield app


@pytest.fixture
def client(flask_app):
    """Create a test client for the Flask app."""
    return flask_app.test_client()


@pytest.fixture
def mock_database_api_client():
    """Create a mock database API client."""
    mock_client = Mock(spec=DatabaseAPIClient)

    # Mock session for direct HTTP calls
    mock_session = Mock()
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "success"}
    mock_response.raise_for_status.return_value = None
    mock_session.get.return_value = mock_response
    mock_session.post.return_value = mock_response
    mock_client.session = mock_session

    # Mock health check response
    mock_client.health_check.return_value = {
        "status": "healthy",
        "database_connected": True,
        "total_records": 100,
    }

    # Mock API responses
    mock_client.get_risks.return_value = {
        "risks": [
            {
                "id": "AIR.001",
                "title": "Test Risk 1",
                "description": "Test Description 1",
            },
            {
                "id": "AIR.002",
                "title": "Test Risk 2",
                "description": "Test Description 2",
            },
        ],
        "total": 2,
    }

    mock_client.get_risks_summary.return_value = {
        "details": [
            {"category": "Privacy", "count": 5},
            {"category": "Security", "count": 3},
        ]
    }

    mock_client.get_controls.return_value = {
        "controls": [
            {
                "id": "AIGPC.1",
                "title": "Test Control 1",
                "description": "Test Control Description 1",
            },
            {
                "id": "AIGPC.2",
                "title": "Test Control 2",
                "description": "Test Control Description 2",
            },
        ],
        "total": 2,
    }

    mock_client.get_controls_summary.return_value = {
        "details": [{"domain": "Protect", "count": 4}, {"domain": "Detect", "count": 2}]
    }

    mock_client.get_questions.return_value = {
        "questions": [
            {"id": "Q1", "text": "Test Question 1?", "category": "Privacy"},
            {"id": "Q2", "text": "Test Question 2?", "category": "Security"},
        ],
        "total": 2,
    }

    mock_client.get_questions_summary.return_value = {
        "details": [
            {"category": "Privacy", "count": 3},
            {"category": "Security", "count": 2},
        ]
    }

    mock_client.get_relationships.return_value = {
        "relationships": [
            {"risk_id": "AIR.001", "control_id": "AIGPC.1", "type": "mitigates"},
            {"question_id": "Q1", "risk_id": "AIR.001", "type": "assesses"},
        ]
    }

    mock_client.search.return_value = {
        "query": "test",
        "results": [
            {"type": "risk", "id": "AIR.001", "title": "Test Risk 1"},
            {"type": "control", "id": "AIGPC.1", "title": "Test Control 1"},
        ],
    }

    mock_client.get_stats.return_value = {
        "total_risks": 10,
        "total_controls": 8,
        "total_questions": 15,
        "total_relationships": 25,
    }

    mock_client.get_file_metadata.return_value = {
        "risks": {"version": "1.0", "last_updated": "2025-01-01T00:00:00Z"},
        "controls": {"version": "1.0", "last_updated": "2025-01-01T00:00:00Z"},
        "questions": {"version": "1.0", "last_updated": "2025-01-01T00:00:00Z"},
    }

    mock_client.get_managing_roles.return_value = {
        "managing_roles": ["Data Officer", "Security Officer", "ML Engineer"]
    }

    # Mock session responses for network, gaps, and last-updated endpoints
    mock_client.session.get.return_value.json.return_value = {
        "risk_control_links": [{"source": "AIR.001", "target": "AIGPC.1"}],
        "question_risk_links": [{"source": "Q1", "target": "AIR.001"}],
        "question_control_links": [{"source": "Q1", "target": "AIGPC.1"}],
    }

    # Add base_url attribute for direct session calls
    mock_client.base_url = f"http://localhost:{os.getenv('DATABASE_PORT')}"

    return mock_client


@pytest.fixture
def mock_auth_service():
    """Create a mock authentication service."""
    mock_service = Mock()

    # Mock login response
    mock_service.post.return_value.status_code = 200
    mock_service.post.return_value.json.return_value = {
        "user": {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "is_admin": False,
            "is_active": True,
        },
        "access_token": "test-access-token",
        "refresh_token": "test-refresh-token",
    }

    return mock_service


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
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "is_admin": False,
        "is_active": True,
    }


@pytest.fixture
def sample_admin_user_data():
    """Sample admin user data for testing."""
    return {
        "id": 2,
        "username": "admin",
        "email": "admin@example.com",
        "is_admin": True,
        "is_active": True,
    }


@pytest.fixture
def mock_requests():
    """Mock the requests library."""
    with patch("app.requests") as mock_req:
        # Mock successful responses by default
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_response.raise_for_status.return_value = None

        mock_req.get.return_value = mock_response
        mock_req.post.return_value = mock_response
        mock_req.put.return_value = mock_response
        mock_req.delete.return_value = mock_response

        yield mock_req


@pytest.fixture
def mock_jwt_token():
    """Mock JWT token for testing."""
    return "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJ1c2VybmFtZSI6InRlc3R1c2VyIn0.test-signature"


@pytest.fixture
def authenticated_headers(mock_jwt_token):
    """Headers for authenticated requests."""
    return {
        "Authorization": f"Bearer {mock_jwt_token}",
        "Content-Type": "application/json",
    }


@pytest.fixture
def mock_session():
    """Mock Flask session."""
    return {
        "user": {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "is_admin": False,
            "is_active": True,
        }
    }


@pytest.fixture
def mock_admin_session():
    """Mock Flask session for admin user."""
    return {
        "user": {
            "id": 2,
            "username": "admin",
            "email": "admin@example.com",
            "is_admin": True,
            "is_active": True,
        }
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
                    "id": f"AIR.{i:03d}",
                    "title": f"Test Risk {i}",
                    "description": f"Description for test risk {i}",
                    "category": f"Category {i % 3}",  # Cycle through 3 categories
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
                    "id": f"AIGPC.{i}",
                    "title": f"Test Control {i}",
                    "description": f"Description for test control {i}",
                    "domain": f"Domain {i % 3}",  # Cycle through 3 domains
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
                    "id": f"Q{i}",
                    "text": f"Test question {i}?",
                    "category": f"Category {i % 3}",
                    "topic": f"Topic {i % 3}",
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


# Register custom pytest marks
def pytest_configure(config):
    """Register custom pytest marks."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "e2e: mark test as an end-to-end test")
    config.addinivalue_line("markers", "api: mark test as an API test")
    config.addinivalue_line("markers", "auth: mark test as an authentication test")
    config.addinivalue_line("markers", "config: mark test as a configuration test")
    config.addinivalue_line("markers", "frontend: mark test as a frontend test")
    config.addinivalue_line(
        "markers", "database: mark test as requiring database service"
    )
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "launcher: mark test as requiring launcher")
    config.addinivalue_line("markers", "ci_compatible: mark test as CI compatible")
    config.addinivalue_line("markers", "presentation: mark test as a presentation test")
    config.addinivalue_line("markers", "integrity: mark test as a data integrity test")
    config.addinivalue_line("markers", "error: mark test as an error scenario test")
    config.addinivalue_line("markers", "coverage: mark test as a coverage test")
