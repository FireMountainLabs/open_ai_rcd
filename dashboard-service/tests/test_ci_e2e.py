"""
CI-compatible E2E tests for the dashboard service.

These tests simulate end-to-end workflows using Flask test client
instead of making real HTTP requests, making them suitable for CI.
"""

from unittest.mock import patch, Mock

import pytest
from app import app
import app as app_module


@pytest.mark.e2e
@pytest.mark.ci_compatible
class TestDashboardServiceCIE2E:
    """CI-compatible E2E tests using Flask test client."""

    @pytest.fixture
    def client(self):
        """Create a test client for the dashboard service."""
        app.config["TESTING"] = True
        with app.test_client() as client:
            yield client

    @pytest.fixture
    def mock_database_responses(self):
        """Mock database service responses for E2E testing."""
        return {
            "health": {
                "status": "healthy",
                "database_connected": True,
                "dashboard_service": "healthy",
                "database_service": "healthy",
            },
            "risks": {
                "risks": [
                    {
                        "id": "RISK-001",
                        "title": "Test Risk 1",
                        "description": "A test risk for E2E testing",
                        "category": "Security",
                        "likelihood": "Medium",
                        "impact": "High",
                    },
                    {
                        "id": "RISK-002",
                        "title": "Test Risk 2",
                        "description": "Another test risk for E2E testing",
                        "category": "Operational",
                        "likelihood": "Low",
                        "impact": "Medium",
                    },
                ],
                "total": 2,
                "page": 1,
                "per_page": 10,
            },
            "controls": {
                "controls": [
                    {
                        "id": "CTRL-001",
                        "title": "Test Control 1",
                        "description": "A test control for E2E testing",
                        "domain": "Access Control",
                        "type": "Preventive",
                    }
                ],
                "total": 1,
                "page": 1,
                "per_page": 10,
            },
            "stats": {
                "total_risks": 2,
                "total_controls": 1,
                "total_questions": 5,
                "coverage_percentage": 75.0,
            },
        }

    def test_complete_dashboard_workflow_ci(self, client, mock_database_responses, mock_database_api_client, patch_api_client_methods):
        """
        Test complete dashboard workflow using Flask test client.

        This simulates a real user workflow:
        1. Access dashboard home page
        2. Check health status
        3. View risks data
        4. View controls data
        5. Check statistics
        """
        # Configure mock responses
        mock_database_api_client.health_check.return_value = mock_database_responses["health"]
        mock_database_api_client.get_risks.return_value = mock_database_responses["risks"]
        mock_database_api_client.get_controls.return_value = mock_database_responses["controls"]
        mock_database_api_client.get_stats.return_value = mock_database_responses["stats"]
        
        # Mock the database API client responses
        # ENABLE_AUTH is set via app.config in the client fixture
        with patch_api_client_methods(mock_database_api_client):

            # 1. Test dashboard home page (when auth disabled, shows dashboard directly)
            response = client.get("/")
            # Main route shows dashboard directly (200)
            assert response.status_code == 200
            assert b"dashboard" in response.data.lower()

            # 2. Test health endpoint
            response = client.get("/api/health")
            assert response.status_code == 200
            health_data = response.get_json()
            assert health_data["status"] == "healthy"
            assert "database_service" in health_data
            assert "dashboard_service" in health_data

            # 3. Test risks API endpoint
            response = client.get("/api/risks")
            assert response.status_code == 200
            risks_data = response.get_json()
            assert "risks" in risks_data
            assert len(risks_data["risks"]) == 2
            assert risks_data["risks"][0]["id"] == "RISK-001"

            # 4. Test controls API endpoint
            response = client.get("/api/controls")
            assert response.status_code == 200
            controls_data = response.get_json()
            assert "controls" in controls_data
            assert len(controls_data["controls"]) == 1
            assert controls_data["controls"][0]["id"] == "CTRL-001"

            # 5. Test statistics API endpoint
            response = client.get("/api/stats")
            assert response.status_code == 200
            stats_data = response.get_json()
            assert stats_data["total_risks"] == 2
            assert stats_data["total_controls"] == 1
            assert stats_data["coverage_percentage"] == 75.0

            # Verify all expected API calls were made
            mock_database_api_client.health_check.assert_called_once()
            mock_database_api_client.get_risks.assert_called_once()
            mock_database_api_client.get_controls.assert_called_once()
            mock_database_api_client.get_stats.assert_called_once()

    def test_dashboard_error_handling_workflow_ci(
        self, client, mock_database_responses, mock_database_api_client, patch_api_client_methods
    ):
        """
        Test dashboard error handling workflow using Flask test client.

        This simulates error scenarios:
        1. Database service unavailable
        2. API endpoint errors
        3. Invalid requests
        4. Error page rendering
        """
        # Configure mock responses for error scenarios
        mock_database_api_client.health_check.return_value = {
            "status": "unhealthy",
            "error": "Database connection failed",
        }
        mock_database_api_client.get_risks.side_effect = Exception("Database connection error")
        
        # ENABLE_AUTH is set via app.config in the client fixture
        with patch_api_client_methods(mock_database_api_client):
            
            # Test 1: Database service unavailable
            response = client.get("/api/health")
            assert response.status_code == 200
            health_data = response.get_json()
            assert health_data["status"] == "unhealthy"
            assert health_data["database_service"]["status"] == "unhealthy"

            # Test 2: API endpoint with database error
            response = client.get("/api/risks")
            assert response.status_code == 200
            error_data = response.get_json()
            assert error_data == []  # Returns empty array on error

            # Test 3: Non-existent endpoint
            response = client.get("/api/nonexistent")
            assert response.status_code == 404

            # Test 4: Error page rendering (should not crash)
            response = client.get("/")
            assert response.status_code == 200
            # Dashboard should still load even with database errors

            # Verify error handling calls were made
            mock_database_api_client.health_check.assert_called()
            mock_database_api_client.get_risks.assert_called()
