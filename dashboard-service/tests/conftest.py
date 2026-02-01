"""
Pytest configuration and fixtures for dashboard service tests.
"""

import os
import sys
import pytest
from unittest.mock import patch, Mock
from pathlib import Path
import requests
import logging
from contextlib import contextmanager

# Add shared-services to path to load common config
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared-services"))

# Load port configuration from common config if not already set
try:
    from common_config import CommonConfigManager

    config_manager = CommonConfigManager()
    ports = config_manager.get_config_value("ports", {})

    # Map port config to environment variables
    port_env_mapping = {
        "database_service": "DATABASE_PORT",
        "dashboard_service": "DASHBOARD_PORT",
        "data_processing_service": "DATA_PROCESSING_PORT",
    }
    for config_key, env_key in port_env_mapping.items():
        if env_key not in os.environ and config_key in ports:
            os.environ[env_key] = str(ports[config_key])
except Exception:
    # If common_config is not available, use fallback defaults
    if "DATABASE_PORT" not in os.environ:
        os.environ["DATABASE_PORT"] = "5001"
    if "DASHBOARD_PORT" not in os.environ:
        os.environ["DASHBOARD_PORT"] = "5002"
    if "AUTH_PORT" not in os.environ:
        os.environ["AUTH_PORT"] = "5003"
    if "MAILER_PORT" not in os.environ:
        os.environ["MAILER_PORT"] = "5004"
    if "INVITE_PORT" not in os.environ:
        os.environ["INVITE_PORT"] = "5005"

import app as app_module
from app import app

logger = logging.getLogger(__name__)


@pytest.fixture
def patch_api_client_methods():
    """Factory fixture to patch api_client methods used by blueprint closures."""
    @contextmanager
    def _patch_methods(mock_client):
        # Patch all methods that might be called
        methods_to_patch = [
            'get_risks', 'get_risks_summary', 'get_controls', 'get_controls_summary',
            'get_definitions', 'get_relationships', 
            'search', 'get_stats', 'get_file_metadata', 'get_risk_detail', 'get_control_detail',
            'health_check'
        ]
        
        patches = []
        for method in methods_to_patch:
            if hasattr(mock_client, method):
                patches.append(patch.object(app_module.api_client, method, getattr(mock_client, method)))
        
        # Also patch session for routes that use it directly
        if hasattr(mock_client, 'session'):
            patches.append(patch.object(app_module.api_client, 'session', mock_client.session))
        
        # Start all patches
        for p in patches:
            p.start()
        
        try:
            yield
        finally:
            # Stop all patches
            for p in patches:
                p.stop()
    
    return _patch_methods


@pytest.fixture
def client():
    """Create a test client for the dashboard service."""
    app.config["TESTING"] = True
    app.config["ENABLE_AUTH"] = False
    with app.test_client() as client:
        yield client


@pytest.fixture
def auth_client():
    """Create a test client with authentication enabled."""
    app.config["TESTING"] = True
    app.config["ENABLE_AUTH"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_database_api_client():
    """Mock database API client for testing."""
    from unittest.mock import Mock

    mock_client = Mock()
    
    # Create a mock session for direct HTTP calls
    mock_session = Mock()
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "success"}
    mock_response.raise_for_status.return_value = None
    mock_session.get.return_value = mock_response
    mock_session.post.return_value = mock_response
    mock_client.session = mock_session
    mock_client.base_url = "http://localhost:5001"

    # Configure default mock responses
    mock_client.health_check.return_value = {
        "status": "healthy",
        "database_connected": True,
    }
    mock_client.get_risks.return_value = {
        "risks": [
            {"id": "RISK-001", "title": "Test Risk 1", "category": "Security"},
            {"id": "RISK-002", "title": "Test Risk 2", "category": "Privacy"},
        ],
        "total": 2,
    }
    mock_client.get_risks_summary.return_value = {
        "total_risks": 2,
        "risks": [
            {"id": "RISK-001", "title": "Test Risk 1", "category": "Security"},
            {"id": "RISK-002", "title": "Test Risk 2", "category": "Privacy"},
        ],
        "by_category": {"Security": 1, "Privacy": 1},
        "details": [
            {"category": "Security", "count": 1},
            {"category": "Privacy", "count": 1},
        ],
    }
    mock_client.get_controls.return_value = {
        "controls": [
            {"id": "CTRL-001", "title": "Test Control 1", "domain": "Access Control"},
            {"id": "CTRL-002", "title": "Test Control 2", "domain": "Data Protection"},
        ],
        "total": 2,
    }
    mock_client.get_controls_summary.return_value = {
        "total_controls": 2,
        "controls": [
            {"id": "CTRL-001", "title": "Test Control 1", "domain": "Access Control"},
            {"id": "CTRL-002", "title": "Test Control 2", "domain": "Data Protection"},
        ],
        "by_domain": {"Access Control": 1, "Data Protection": 1},
        "details": [
            {"domain": "Access Control", "count": 1},
            {"domain": "Data Protection", "count": 1},
        ],
    }
    mock_client.get_relationships.return_value = {
        "relationships": [
            {
                "id": "REL-001",
                "type": "mitigates",
                "source": "CTRL-001",
                "target": "RISK-001",
            },
            {
                "id": "REL-002",
                "type": "addresses",
                "source": "CTRL-002",
                "target": "RISK-002",
            },
        ],
        "total": 2,
    }
    mock_client.get_stats.return_value = {
        "total_risks": 2,
        "total_controls": 2,
        "total_relationships": 2,
        "coverage_percentage": 75.0,
    }
    mock_client.get_network.return_value = {
        "nodes": [{"id": "RISK-001", "label": "Test Risk", "type": "risk"}],
        "edges": [{"source": "CTRL-001", "target": "RISK-001", "type": "mitigates"}]
    }
    mock_client.get_gaps.return_value = {
        "summary": {
            "total_risks": 25,
            "total_controls": 18,
            "unmapped_risks": 5,
            "unmapped_controls": 2,
        },
        "gaps": [{"risk_id": "RISK-001", "missing_controls": ["CTRL-001"]}] * 25,
        "unmapped_risks": [],
        "unmapped_controls": [],
        "total": 25
    }
    mock_client.get_last_updated.return_value = {
        "risks": {"last_updated": "2024-01-01T00:00:00Z"},
        "controls": {"last_updated": "2024-01-01T00:00:00Z"},
        "risk_control_links": [],
    }
    mock_client.get_file_metadata.return_value = {
        "files": {
            "risks": {"file": "risks.xlsx", "last_modified": "2024-01-01T00:00:00Z"},
            "controls": {"file": "controls.xlsx", "last_modified": "2024-01-01T00:00:00Z"},
        }
    }
    mock_client.get_risk_detail.return_value = {
        "id": "RISK-001",
        "title": "Test Risk Detail",
        "description": "Test risk description",
    }
    mock_client.get_control_detail.return_value = {
        "control": {
            "id": "CTRL-001",
            "title": "Test Control Detail",
            "description": "Test control description",
        }
    }
    mock_client.search.return_value = {
        "query": "test",
        "results": [
            {"id": "RISK-001", "title": "Test Risk 1", "type": "risk"},
            {"id": "CTRL-001", "title": "Test Control 1", "type": "control"},
        ],
        "total": 2,
    }

    return mock_client


@pytest.fixture
def mock_session():
    """Mock user session for testing."""
    return {
        "user": {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "role": "user",
        }
    }


@pytest.fixture
def mock_admin_session():
    """Mock admin user session for testing."""
    return {
        "user": {
            "id": 1,
            "username": "admin",
            "email": "admin@example.com",
            "role": "admin",
            "is_admin": True,
        }
    }


@pytest.fixture
def mock_auth_service():
    """Mock authentication service for testing."""
    with patch("app.requests.post") as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = {
            "success": True,
            "user": {
                "id": 1,
                "username": "testuser",
                "email": "test@example.com",
                "role": "user",
            },
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        yield mock_post


@pytest.fixture
def mock_environment():
    """Mock environment variables for testing."""
    env_vars = {
        "DATABASE_URL": f'http://localhost:{os.getenv("DATABASE_PORT")}',
        "AUTH_SERVICE_URL": f'http://localhost:{os.getenv("AUTH_PORT")}',
        "JWT_SECRET_KEY": "test-secret-key",
    }

    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture
def mock_authenticated_user():
    """Mock authenticated user for tests that need authentication."""
    with patch("app.get_current_user") as mock_get_user:
        mock_get_user.return_value = {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "role": "user",
        }
        yield mock_get_user




@pytest.fixture
def mock_admin_user():
    """Mock admin user for tests that need admin authentication."""
    with patch("app.get_current_user") as mock_get_user:
        mock_get_user.return_value = {
            "id": 1,
            "username": "admin",
            "email": "admin@example.com",
            "role": "admin",
            "is_admin": True,
        }
        yield mock_get_user


@pytest.fixture
def launcher_process():
    """Mock launcher process for integration tests."""
    # Skip integration tests in CI environment
    ci_env_vars = ["CI", "GITHUB_ACTIONS", "GITHUB_WORKFLOW", "GITHUB_RUN_ID"]
    if any(os.getenv(var) for var in ci_env_vars):
        pytest.skip(
            "Integration tests skipped in CI environment - services not available"
        )

    # Return a mock process for local testing
    mock_process = Mock()
    mock_process.returncode = 0
    return mock_process


@pytest.fixture
def account_cleanup():
    """
    Fixture to track and clean up accounts created during tests.
    
    This fixture tracks usernames of accounts created during tests and
    attempts to delete them in teardown. Use this fixture in tests that
    actually create real accounts (not mocked).
    
    Usage:
        def test_create_user(account_cleanup):
            # Create account
            response = client.post("/register", json={...})
            username = response.json()["user"]["username"]
            account_cleanup.add(username)
    """
    created_accounts = []
    auth_service_url = os.getenv("AUTH_SERVICE_URL", f'http://localhost:{os.getenv("AUTH_PORT", "5003")}')
    dashboard_url = os.getenv("DASHBOARD_URL", f'http://localhost:{os.getenv("DASHBOARD_PORT", "5002")}')
    
    class AccountCleanup:
        def __init__(self):
            self.accounts = []
            self.auth_token = None
        
        def add(self, username):
            """Add a username to the cleanup list."""
            if username and username not in self.accounts:
                self.accounts.append(username)
                logger.info(f"Tracking account for cleanup: {username}")
        
        def set_auth_token(self, token):
            """Set auth token for cleanup operations."""
            self.auth_token = token
        
        def cleanup(self):
            """Clean up all tracked accounts."""
            if not self.accounts:
                return
            
            # Try to get auth token if not set
            if not self.auth_token:
                # Try to login as admin to get token
                try:
                    admin_username = os.getenv("ADMIN_USERNAME", "admin")
                    admin_password = os.getenv("ADMIN_PASSWORD", "admin")
                    login_response = requests.post(
                        f"{auth_service_url}/api/auth/login",
                        json={"username": admin_username, "password": admin_password},
                        timeout=5
                    )
                    if login_response.status_code == 200:
                        self.auth_token = login_response.json().get("token")
                except Exception as e:
                    logger.warning(f"Could not get auth token for cleanup: {e}")
            
            # Delete each tracked account
            for username in self.accounts:
                try:
                    if self.auth_token:
                        # Use dashboard service delete endpoint
                        response = requests.delete(
                            f"{dashboard_url}/api/admin/users/{username}",
                            headers={"Authorization": f"Bearer {self.auth_token}"},
                            timeout=5
                        )
                        if response.status_code == 200:
                            logger.info(f"Cleaned up account: {username}")
                        else:
                            logger.warning(f"Failed to cleanup account {username}: {response.status_code}")
                    else:
                        # Try direct auth service call
                        try:
                            # Get user ID first
                            users_response = requests.get(
                                f"{auth_service_url}/api/admin/users",
                                headers={"Authorization": f"Bearer {self.auth_token}" if self.auth_token else None},
                                timeout=5
                            )
                            if users_response.status_code == 200:
                                users = users_response.json().get("users", [])
                                for user in users:
                                    if user.get("username") == username:
                                        user_id = user.get("id")
                                        delete_response = requests.delete(
                                            f"{auth_service_url}/api/admin/users/{user_id}",
                                            headers={"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {},
                                            timeout=5
                                        )
                                        if delete_response.status_code == 200:
                                            logger.info(f"Cleaned up account: {username}")
                                        break
                        except Exception as e:
                            logger.warning(f"Could not cleanup account {username} via auth service: {e}")
                except Exception as e:
                    logger.warning(f"Error cleaning up account {username}: {e}")
    
    cleanup = AccountCleanup()
    yield cleanup
    
    # Teardown: clean up all accounts
    cleanup.cleanup()


@pytest.fixture(autouse=True)
def cleanup_test_accounts(account_cleanup, request):
    """
    Auto-use fixture that ensures test accounts are cleaned up.
    
    This fixture automatically tracks accounts created via registration
    endpoints and cleans them up after tests. It patches the registration
    endpoint to track created accounts.
    
    For tests that create accounts manually, use the account_cleanup fixture
    directly:
    
        def test_create_user(account_cleanup):
            response = client.post("/register", json={...})
            username = response.json()["user"]["username"]
            account_cleanup.add(username)
    
    Note: This fixture only activates for integration/e2e tests, not unit tests.
    """
    # Only track if we're using real services (integration/e2e tests)
    # For unit tests with mocks, this won't do anything
    use_real_services = os.getenv("USE_REAL_SERVICES", "false").lower() == "true"
    
    # Check if this is an integration or e2e test
    test_markers = [mark.name for mark in request.node.iter_markers()]
    is_integration_test = "integration" in test_markers or "e2e" in test_markers
    
    # Also check if CI environment is set (but still skip for unit tests)
    is_ci = os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true"
    
    # Only activate for integration/e2e tests, not unit tests
    if not use_real_services and not is_integration_test:
        # Unit tests with mocks - no cleanup needed, just yield
        yield
        return
    
    # For integration/e2e tests, track account creation
    # But only if we're not in CI (where services aren't available)
    if is_ci and not use_real_services:
        # In CI, skip cleanup tracking since services aren't available
        yield
        return
    
    # For local integration tests, track account creation
    original_post = requests.post
    
    def tracked_post(*args, **kwargs):
        """Track account creation in registration requests."""
        response = original_post(*args, **kwargs)
        
        # Check if this is a registration request
        url = args[0] if args else kwargs.get("url", "")
        if "/register" in str(url) or "/api/auth/register" in str(url) or "/api/admin/create-user" in str(url):
            try:
                if response.status_code in [200, 201]:
                    data = response.json()
                    # Check for user in response
                    user_data = data.get("user") or data
                    username = user_data.get("username")
                    if username:
                        account_cleanup.add(username)
                        logger.info(f"Auto-tracked account for cleanup: {username}")
            except Exception as e:
                logger.debug(f"Could not track account creation: {e}")
        
        return response
    
    # Patch requests.post for the test
    with patch("requests.post", side_effect=tracked_post):
        yield
