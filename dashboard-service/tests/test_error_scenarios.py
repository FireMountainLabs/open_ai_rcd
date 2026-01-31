"""
Test error scenarios and edge cases for the dashboard service.

This module contains tests for error handling paths, edge cases, and
scenarios that are not covered by the main test suite.
"""

from unittest.mock import patch

import pytest


@pytest.mark.unit
@pytest.mark.error
class TestAPIErrorScenarios:
    """Test API error handling scenarios."""

    def test_api_risks_database_exception(self, client, mock_database_api_client, patch_api_client_methods):
        """Test risks API when database client raises exception."""
        mock_database_api_client.get_risks.side_effect = Exception(
            "Database connection failed"
        )

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/risks")

            assert response.status_code == 200
            data = response.get_json()
            assert data == []

    def test_api_controls_database_exception(self, client, mock_database_api_client, patch_api_client_methods):
        """Test controls API when database client raises exception."""
        mock_database_api_client.get_controls.side_effect = Exception(
            "Database connection failed"
        )

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/controls")

            assert response.status_code == 200
            data = response.get_json()
            assert data == []

    def test_api_questions_database_exception(self, client, mock_database_api_client, patch_api_client_methods):
        """Test questions API when database client raises exception."""
        mock_database_api_client.get_questions.side_effect = Exception(
            "Database connection failed"
        )

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/questions")

            assert response.status_code == 200
            data = response.get_json()
            assert data == []

    def test_api_relationships_database_exception(
        self, client, mock_database_api_client, patch_api_client_methods
    ):
        """Test relationships API when database client raises exception."""
        mock_database_api_client.get_relationships.side_effect = Exception(
            "Database connection failed"
        )

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/relationships")

            assert response.status_code == 200
            data = response.get_json()
            assert data == []

    def test_api_search_database_exception(self, client, mock_database_api_client, patch_api_client_methods):
        """Test search API when database client raises exception."""
        mock_database_api_client.search.side_effect = Exception(
            "Database connection failed"
        )

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/search?q=test")

            assert response.status_code == 200
            data = response.get_json()
            assert data == {"query": "test", "results": []}

    def test_api_stats_database_exception(self, client, mock_database_api_client, patch_api_client_methods):
        """Test stats API when database client raises exception."""
        mock_database_api_client.get_stats.side_effect = Exception(
            "Database connection failed"
        )

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/stats")

            assert response.status_code == 200
            data = response.get_json()
            assert data == {"total_risks": 0, "total_controls": 0, "total_questions": 0}

    def test_api_network_database_exception(self, client, mock_database_api_client, patch_api_client_methods):
        """Test network API when database client raises exception."""
        mock_database_api_client.session.get.side_effect = Exception(
            "Database connection failed"
        )

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/network")

            assert response.status_code == 200
            data = response.get_json()
            assert data == {
                "risk_control_links": [],
                "question_risk_links": [],
                "question_control_links": [],
            }

    def test_api_gaps_database_exception(self, client, mock_database_api_client, patch_api_client_methods):
        """Test gaps API when database client raises exception."""
        mock_database_api_client.session.get.side_effect = Exception(
            "Database connection failed"
        )

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/gaps")

            assert response.status_code == 200
            data = response.get_json()
            assert data == {
                "summary": {"total_risks": 0, "total_controls": 0, "unmapped_risks": 0},
                "unmapped_risks": [],
            }

    def test_api_last_updated_database_exception(
        self, client, mock_database_api_client, patch_api_client_methods
    ):
        """Test last updated API when database client raises exception."""
        mock_database_api_client.session.get.side_effect = Exception(
            "Database connection failed"
        )

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/last-updated")

            assert response.status_code == 200
            data = response.get_json()
            assert data == {
                "risk_control_links": [],
                "question_risk_links": [],
                "question_control_links": [],
            }


@pytest.mark.unit
@pytest.mark.error
class TestHealthCheckErrorScenarios:
    """Test health check error scenarios."""

    def test_health_check_database_unhealthy(self, client, mock_database_api_client, patch_api_client_methods):
        """Test health check when database is unhealthy."""
        mock_database_api_client.health_check.return_value = {
            "status": "unhealthy",
            "database_connected": False,
            "total_records": 0,
        }

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/health")

            assert response.status_code == 200
            data = response.get_json()
            assert data["status"] == "unhealthy"
            assert data["database_service"]["status"] == "unhealthy"

    def test_health_check_database_exception(self, client, mock_database_api_client, patch_api_client_methods):
        """Test health check when database client raises exception."""
        mock_database_api_client.health_check.side_effect = Exception(
            "Database connection failed"
        )

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/health")

            assert response.status_code == 200
            data = response.get_json()
            assert data["status"] == "unhealthy"
            assert data["database_service"]["status"] == "unhealthy"


@pytest.mark.unit
@pytest.mark.error
class TestFileMetadataErrorScenarios:
    """Test file metadata error scenarios."""

    def test_file_metadata_database_exception(self, client, mock_database_api_client, patch_api_client_methods):
        """Test file metadata when database client raises exception."""
        mock_database_api_client.get_file_metadata.side_effect = Exception(
            "Database connection failed"
        )

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/file-metadata")

            assert response.status_code == 200
            data = response.get_json()
            assert data == {"files": []}


@pytest.mark.unit
@pytest.mark.error
class TestDetailEndpointsErrorScenarios:
    """Test detail endpoints error scenarios."""

    def test_risk_detail_database_exception(self, client, mock_database_api_client, patch_api_client_methods):
        """Test risk detail when database client raises exception."""
        mock_database_api_client.get_risk_detail.side_effect = Exception(
            "Database connection failed"
        )

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/risk/R.AIR.001")

            assert response.status_code == 200
            data = response.get_json()
            assert data == {
                "risk": {},
                "associated_controls": [],
                "associated_questions": [],
            }

    def test_control_detail_database_exception(self, client, mock_database_api_client, patch_api_client_methods):
        """Test control detail when database client raises exception."""
        mock_database_api_client.get_control_detail.side_effect = Exception(
            "Database connection failed"
        )

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/control/C.AIIM.1")

            assert response.status_code == 200
            data = response.get_json()
            assert data == {
                "control": {},
                "associated_risks": [],
                "associated_questions": [],
            }

    def test_question_detail_database_exception(self, client, mock_database_api_client, patch_api_client_methods):
        """Test question detail when database client raises exception."""
        mock_database_api_client.get_question_detail.side_effect = Exception(
            "Database connection failed"
        )

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/question/Q.CIR.1.1")

            assert response.status_code == 200
            data = response.get_json()
            assert data == {
                "question": {},
                "associated_risks": [],
                "associated_controls": [],
            }


@pytest.mark.unit
@pytest.mark.error
class TestManagingRolesErrorScenarios:
    """Test managing roles error scenarios."""

    def test_managing_roles_database_exception(self, client, mock_database_api_client, patch_api_client_methods):
        """Test managing roles when database client raises exception."""
        mock_database_api_client.get_managing_roles.side_effect = Exception(
            "Database connection failed"
        )

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/managing-roles")

            assert response.status_code == 200
            data = response.get_json()
            assert data == {"managing_roles": []}
