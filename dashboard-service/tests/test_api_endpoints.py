"""
API endpoint tests for the dashboard service.

Tests all HTTP endpoints for proper functionality, error handling, and response formats.
"""

from unittest.mock import patch, Mock

import pytest
import app


@pytest.mark.unit
@pytest.mark.api
class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_health_endpoint_success(self, client, mock_database_api_client, patch_api_client_methods):
        """Test health endpoint when database service is healthy."""
        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/health")

            assert response.status_code == 200
            data = response.get_json()
            assert data["status"] == "healthy"
            assert "database_service" in data
            assert "dashboard_service" in data
            assert data["dashboard_service"]["status"] == "healthy"

    def test_health_endpoint_database_unhealthy(self, client, mock_database_api_client, patch_api_client_methods):
        """Test health endpoint when database service is unhealthy."""
        mock_database_api_client.health_check.return_value = {
            "status": "unhealthy",
            "error": "Connection failed",
        }

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/health")

            assert response.status_code == 200
            data = response.get_json()
            assert data["status"] == "unhealthy"
            assert data["database_service"]["status"] == "unhealthy"


@pytest.mark.unit
@pytest.mark.api
class TestRisksEndpoints:
    """Test risks-related endpoints."""

    def test_api_risks_success(self, client, mock_database_api_client, patch_api_client_methods):
        """Test successful risks API endpoint."""
        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/risks")

            assert response.status_code == 200
            data = response.get_json()
            assert "risks" in data
            assert "total" in data
            assert len(data["risks"]) == 2

    def test_api_risks_with_params(self, client, mock_database_api_client, patch_api_client_methods):
        """Test risks API endpoint with query parameters."""
        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/risks?limit=5&offset=10&category=Privacy")

            assert response.status_code == 200
            mock_database_api_client.get_risks.assert_called_once_with(
                limit=5, offset=10, category="Privacy"
            )

    def test_api_risks_summary_success(self, client, mock_database_api_client, patch_api_client_methods):
        """Test successful risks summary API endpoint."""
        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/risks/summary")

            assert response.status_code == 200
            data = response.get_json()
            assert "details" in data
            assert len(data["details"]) == 2

    def test_api_risks_database_error(self, client, mock_database_api_client, patch_api_client_methods):
        """Test risks API endpoint with database service error."""
        mock_database_api_client.get_risks.return_value = []

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/risks")

            assert response.status_code == 200
            data = response.get_json()
            assert data == []


@pytest.mark.unit
@pytest.mark.api
class TestControlsEndpoints:
    """Test controls-related endpoints."""

    def test_api_controls_success(self, client, mock_database_api_client, patch_api_client_methods):
        """Test successful controls API endpoint."""
        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/controls")

            assert response.status_code == 200
            data = response.get_json()
            assert "controls" in data
            assert "total" in data
            assert len(data["controls"]) == 2

    def test_api_controls_with_params(self, client, mock_database_api_client, patch_api_client_methods):
        """Test controls API endpoint with query parameters."""
        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/controls?limit=5&offset=10&domain=Protect")

            assert response.status_code == 200
            mock_database_api_client.get_controls.assert_called_once_with(
                limit=5, offset=10, domain="Protect"
            )

    def test_api_controls_summary_success(self, client, mock_database_api_client, patch_api_client_methods):
        """Test successful controls summary API endpoint."""
        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/controls/summary")

            assert response.status_code == 200
            data = response.get_json()
            assert "details" in data
            assert len(data["details"]) == 2


@pytest.mark.unit
@pytest.mark.api
class TestQuestionsEndpoints:
    """Test questions-related endpoints."""

    def test_api_questions_success(self, client, mock_database_api_client, patch_api_client_methods):
        """Test successful questions API endpoint."""
        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/questions")

            assert response.status_code == 200
            data = response.get_json()
            assert "questions" in data
            assert "total" in data
            assert len(data["questions"]) == 2

    def test_api_questions_with_params(self, client, mock_database_api_client, patch_api_client_methods):
        """Test questions API endpoint with query parameters."""
        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/questions?limit=5&offset=10&category=Privacy")

            assert response.status_code == 200
            mock_database_api_client.get_questions.assert_called_once_with(
                limit=5, offset=10, category="Privacy"
            )

    def test_api_questions_summary_success(self, client, mock_database_api_client, patch_api_client_methods):
        """Test successful questions summary API endpoint."""
        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/questions/summary")

            assert response.status_code == 200
            data = response.get_json()
            assert "details" in data
            assert len(data["details"]) == 2


@pytest.mark.unit
@pytest.mark.api
class TestRelationshipsEndpoints:
    """Test relationships-related endpoints."""

    def test_api_relationships_success(self, client, mock_database_api_client, patch_api_client_methods):
        """Test successful relationships API endpoint."""
        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/relationships")

            assert response.status_code == 200
            data = response.get_json()
            assert "relationships" in data
            assert len(data["relationships"]) == 2

    def test_api_relationships_with_params(self, client, mock_database_api_client, patch_api_client_methods):
        """Test relationships API endpoint with query parameters."""
        with patch_api_client_methods(mock_database_api_client):
            response = client.get(
                "/api/relationships?relationship_type=mitigates&limit=500"
            )

            assert response.status_code == 200
            mock_database_api_client.get_relationships.assert_called_once_with(
                relationship_type="mitigates", limit=500
            )


@pytest.mark.unit
@pytest.mark.api
class TestSearchEndpoints:
    """Test search-related endpoints."""

    def test_api_search_success(self, client, mock_database_api_client, patch_api_client_methods):
        """Test successful search API endpoint."""
        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/search?q=test&limit=25")

            assert response.status_code == 200
            data = response.get_json()
            assert "query" in data
            assert "results" in data
            assert data["query"] == "test"
            assert len(data["results"]) == 2

    def test_api_search_empty_query(self, client, mock_database_api_client, patch_api_client_methods):
        """Test search API endpoint with empty query."""
        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/search?q=")

            assert response.status_code == 200
            data = response.get_json()
            assert data == {"query": "", "results": []}

    def test_api_search_no_query(self, client, mock_database_api_client, patch_api_client_methods):
        """Test search API endpoint without query parameter."""
        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/search")

            assert response.status_code == 200
            data = response.get_json()
            assert data == {"query": "", "results": []}


@pytest.mark.unit
@pytest.mark.api
class TestStatsEndpoints:
    """Test statistics endpoints."""

    def test_api_stats_success(self, client, mock_database_api_client, patch_api_client_methods):
        """Test successful stats API endpoint."""
        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/stats")

            assert response.status_code == 200
            data = response.get_json()
            assert "total_risks" in data
            assert "total_controls" in data
            assert "total_questions" in data
            assert "total_relationships" in data


@pytest.mark.unit
@pytest.mark.api
class TestNetworkEndpoints:
    """Test network data endpoints."""

    def test_api_network_success(self, client, mock_database_api_client, patch_api_client_methods):
        """Test successful network API endpoint."""
        mock_database_api_client.session.get.return_value.status_code = 200
        mock_database_api_client.session.get.return_value.json.return_value = {
            "risk_control_links": [{"source": "AIR.001", "target": "AIGPC.1"}],
            "question_risk_links": [{"source": "Q1", "target": "AIR.001"}],
            "question_control_links": [{"source": "Q1", "target": "AIGPC.1"}],
        }
        mock_database_api_client.session.get.return_value.raise_for_status.return_value = (
            None
        )

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/network")

            assert response.status_code == 200
            data = response.get_json()
            assert "risk_control_links" in data
            assert "question_risk_links" in data
            assert "question_control_links" in data

    def test_api_network_database_error(self, client, mock_database_api_client, patch_api_client_methods):
        """Test network API endpoint with database service error."""
        mock_database_api_client.session.get.side_effect = Exception("Network error")

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/network")

            assert response.status_code == 200
            data = response.get_json()
            assert data == {
                "risk_control_links": [],
                "question_risk_links": [],
                "question_control_links": [],
            }


@pytest.mark.unit
@pytest.mark.api
class TestGapsEndpoints:
    """Test gaps analysis endpoints."""

    def test_api_gaps_success(self, client, mock_database_api_client, patch_api_client_methods):
        """Test successful gaps API endpoint."""
        mock_database_api_client.session.get.return_value.status_code = 200
        mock_database_api_client.session.get.return_value.json.return_value = {
            "summary": {"total_risks": 10, "total_controls": 8, "unmapped_risks": 2},
            "unmapped_risks": [{"id": "AIR.001", "title": "Unmapped Risk"}],
        }
        mock_database_api_client.session.get.return_value.raise_for_status.return_value = (
            None
        )

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/gaps")

            assert response.status_code == 200
            data = response.get_json()
            assert "summary" in data
            assert "unmapped_risks" in data
            assert data["summary"]["total_risks"] == 10

    def test_api_gaps_database_error(self, client, mock_database_api_client, patch_api_client_methods):
        """Test gaps API endpoint with database service error."""
        mock_database_api_client.session.get.side_effect = Exception("Gaps error")

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/gaps")

            assert response.status_code == 200
            data = response.get_json()
            assert "summary" in data
            assert data["summary"]["total_risks"] == 0


@pytest.mark.unit
@pytest.mark.api
class TestFileMetadataEndpoints:
    """Test file metadata endpoints."""

    def test_api_file_metadata_success(self, client, mock_database_api_client, patch_api_client_methods):
        """Test successful file metadata API endpoint."""
        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/file-metadata")

            assert response.status_code == 200
            data = response.get_json()
            assert "files" in data
            assert "risks" in data["files"]
            assert "controls" in data["files"]
            assert "questions" in data["files"]


@pytest.mark.unit
@pytest.mark.api
class TestDetailEndpoints:
    """Test detail endpoints for individual items."""

    def test_api_risk_detail_success(self, client, mock_database_api_client, patch_api_client_methods):
        """Test successful risk detail API endpoint."""
        mock_database_api_client.get_risk_detail.return_value = {
            "id": "AIR.001",
            "title": "Test Risk",
            "description": "Test Description",
        }

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/risk/AIR.001")

            assert response.status_code == 200
            data = response.get_json()
            assert data["id"] == "AIR.001"
            assert data["title"] == "Test Risk"

    def test_api_control_detail_success(self, client, mock_database_api_client, patch_api_client_methods):
        """Test successful control detail API endpoint."""
        mock_database_api_client.get_control_detail.return_value = {
            "id": "AIGPC.1",
            "title": "Test Control",
            "description": "Test Description",
        }

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/control/AIGPC.1")

            assert response.status_code == 200
            data = response.get_json()
            assert data["id"] == "AIGPC.1"
            assert data["title"] == "Test Control"

    def test_api_question_detail_success(self, client, mock_database_api_client, patch_api_client_methods):
        """Test successful question detail API endpoint."""
        mock_database_api_client.get_question_detail.return_value = {
            "id": "Q1",
            "text": "Test Question?",
            "category": "Privacy",
        }

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/question/Q1")

            assert response.status_code == 200
            data = response.get_json()
            assert data["id"] == "Q1"
            assert data["text"] == "Test Question?"


@pytest.mark.unit
@pytest.mark.api
class TestManagingRolesEndpoints:
    """Test managing roles endpoints."""

    def test_api_managing_roles_success(self, client, mock_database_api_client, patch_api_client_methods):
        """Test successful managing roles API endpoint."""
        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/managing-roles")

            assert response.status_code == 200
            data = response.get_json()
            assert isinstance(data, list)
            assert len(data) == 3
            assert data[0]["id"] == "ROLE-001"


@pytest.mark.unit
@pytest.mark.api
class TestLastUpdatedEndpoints:
    """Test last updated timestamps endpoints."""

    def test_api_last_updated_success(self, client, mock_database_api_client, patch_api_client_methods):
        """Test successful last updated API endpoint."""
        mock_database_api_client.session.get.return_value.status_code = 200
        mock_database_api_client.session.get.return_value.json.return_value = {
            "risks": {"last_updated": "2025-01-01T00:00:00Z", "version": "1.0"},
            "controls": {"last_updated": "2025-01-01T00:00:00Z", "version": "1.0"},
            "questions": {"last_updated": "2025-01-01T00:00:00Z", "version": "1.0"},
        }
        mock_database_api_client.session.get.return_value.raise_for_status.return_value = (
            None
        )

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/last-updated")

            assert response.status_code == 200
            data = response.get_json()
            assert "risks" in data
            assert "controls" in data
            assert "questions" in data

    def test_api_last_updated_database_error(self, client, mock_database_api_client, patch_api_client_methods):
        """Test last updated API endpoint with database service error."""
        mock_database_api_client.session.get.side_effect = Exception(
            "Last updated error"
        )

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/last-updated")

            assert response.status_code == 200
            data = response.get_json()
            assert "risk_control_links" in data
            assert "question_risk_links" in data
            assert "question_control_links" in data
            assert data["risk_control_links"] == []
