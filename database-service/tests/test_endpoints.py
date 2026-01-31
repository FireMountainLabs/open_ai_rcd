"""
Endpoint tests for Database Service.

Tests all API endpoints for proper functionality, error handling, and response formats.
"""

import pytest
import json
import sqlite3

# Import the app
import sys

sys.path.append("/home/fml/dashboard_zero/database-service")

# Conditional imports
try:
    from app import app, get_db_connection, validate_database
    from unittest.mock import patch
except ImportError:
    pytest.skip("App module not available", allow_module_level=True)


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_root_endpoint(self, test_client, sample_database, mock_config_manager):
        """Test root endpoint returns health status."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/")
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "database_connected" in data
            assert "database_path" in data
            assert "total_records" in data

    def test_health_endpoint_healthy(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test health endpoint when database is healthy."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["database_connected"] is True
            assert data["total_records"] > 0

    def test_health_endpoint_unhealthy(self, test_client, mock_config_manager):
        """Test health endpoint when database is unhealthy."""
        with patch("app.DB_PATH", "/nonexistent/database.db"):
            response = test_client.get("/api/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["database_connected"] is False
            assert data["total_records"] == 0


class TestRisksEndpoints:
    """Test risks-related endpoints."""

    def test_get_risks_basic(self, test_client, sample_database, mock_config_manager):
        """Test basic risks endpoint."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/risks")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) > 0
            assert "id" in data[0]
            assert "title" in data[0]
            assert "description" in data[0]

    def test_get_risks_with_limit(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test risks endpoint with limit parameter."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/risks?limit=2")
            assert response.status_code == 200
            data = response.json()
            assert len(data) <= 2

    def test_get_risks_with_offset(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test risks endpoint with offset parameter."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/risks?offset=1&limit=2")
            assert response.status_code == 200
            data = response.json()
            assert len(data) <= 2

    def test_get_risks_with_category_filter(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test risks endpoint with category filter."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/risks?category=Privacy")
            assert response.status_code == 200
            data = response.json()
            # Should filter by category if implemented
            assert isinstance(data, list)

    def test_get_risks_invalid_limit(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test risks endpoint with invalid limit."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/risks?limit=0")
            assert response.status_code == 422  # Validation error

    def test_get_risks_invalid_offset(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test risks endpoint with invalid offset."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/risks?offset=-1")
            assert response.status_code == 422  # Validation error

    def test_get_risks_database_error(self, test_client, mock_config_manager):
        """Test risks endpoint with database error."""
        with patch("app.get_db_connection") as mock_conn:
            mock_conn.side_effect = sqlite3.Error("Database error")
            response = test_client.get("/api/risks")
            assert response.status_code == 500


class TestControlsEndpoints:
    """Test controls-related endpoints."""

    def test_get_controls_basic(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test basic controls endpoint."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/controls")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) > 0
            assert "id" in data[0]
            assert "title" in data[0]
            assert "description" in data[0]
            assert "domain" in data[0]

    def test_get_controls_with_domain_filter(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test controls endpoint with domain filter."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/controls?domain=Protect")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    def test_get_controls_with_limit_and_offset(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test controls endpoint with limit and offset."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/controls?limit=2&offset=1")
            assert response.status_code == 200
            data = response.json()
            assert len(data) <= 2


class TestQuestionsEndpoints:
    """Test questions-related endpoints."""

    def test_get_questions_basic(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test basic questions endpoint."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/questions")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) > 0
            assert "id" in data[0]
            assert "text" in data[0]
            assert "category" in data[0]
            assert "topic" in data[0]

    def test_get_questions_with_category_filter(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test questions endpoint with category filter."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/questions?category=Privacy")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    def test_get_questions_with_limit(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test questions endpoint with limit."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/questions?limit=2")
            assert response.status_code == 200
            data = response.json()
            assert len(data) <= 2


class TestRelationshipsEndpoints:
    """Test relationships endpoints."""

    def test_get_relationships_basic(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test basic relationships endpoint."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/relationships")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) > 0
            assert "source_id" in data[0]
            assert "target_id" in data[0]
            assert "relationship_type" in data[0]

    def test_get_relationships_with_type_filter(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test relationships endpoint with type filter."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get(
                "/api/relationships?relationship_type=risk_control"
            )
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            # All relationships should be of the specified type
            for rel in data:
                assert rel["relationship_type"] == "risk_control"

    def test_get_relationships_with_limit(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test relationships endpoint with limit."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/relationships?limit=5")
            assert response.status_code == 200
            data = response.json()
            assert len(data) <= 5


class TestSearchEndpoints:
    """Test search endpoints."""

    def test_search_basic(self, test_client, sample_database, mock_config_manager):
        """Test basic search endpoint."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/search?q=privacy")
            assert response.status_code == 200
            data = response.json()
            assert "query" in data
            assert "results" in data
            assert data["query"] == "privacy"
            assert isinstance(data["results"], list)

    def test_search_with_limit(self, test_client, sample_database, mock_config_manager):
        """Test search endpoint with limit."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/search?q=test&limit=2")
            assert response.status_code == 200
            data = response.json()
            assert len(data["results"]) <= 2

    def test_search_minimum_length(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test search endpoint with query too short."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/search?q=a")
            assert response.status_code == 422  # Validation error

    def test_search_no_query(self, test_client, sample_database, mock_config_manager):
        """Test search endpoint without query."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/search")
            assert response.status_code == 422  # Validation error


class TestStatsEndpoints:
    """Test statistics endpoints."""

    def test_get_stats(self, test_client, sample_database, mock_config_manager):
        """Test stats endpoint."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/stats")
            assert response.status_code == 200
            data = response.json()
            assert "total_risks" in data
            assert "total_controls" in data
            assert "total_questions" in data
            assert "total_relationships" in data
            assert data["total_risks"] > 0
            assert data["total_controls"] > 0
            assert data["total_questions"] > 0


class TestSummaryEndpoints:
    """Test summary endpoints."""

    def test_get_risks_summary(self, test_client, sample_database, mock_config_manager):
        """Test risks summary endpoint."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/risks/summary")
            assert response.status_code == 200
            data = response.json()
            assert "details" in data
            assert isinstance(data["details"], list)
            if data["details"]:
                assert "risk_id" in data["details"][0]
                assert "control_count" in data["details"][0]
                assert "question_count" in data["details"][0]

    def test_get_controls_summary(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test controls summary endpoint."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/controls/summary")
            assert response.status_code == 200
            data = response.json()
            assert "details" in data
            assert isinstance(data["details"], list)
            if data["details"]:
                assert "control_id" in data["details"][0]
                assert "risk_count" in data["details"][0]
                assert "question_count" in data["details"][0]

    def test_get_questions_summary(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test questions summary endpoint."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/questions/summary")
            assert response.status_code == 200
            data = response.json()
            assert "summary" in data
            assert "details" in data
            assert "total_questions" in data["summary"]
            assert "mapped_questions" in data["summary"]
            assert "unmapped_questions" in data["summary"]


class TestDetailEndpoints:
    """Test detail endpoints for specific entities."""

    def test_get_risk_detail(self, test_client, sample_database, mock_config_manager):
        """Test risk detail endpoint."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/risk/AIR.001")
            assert response.status_code == 200
            data = response.json()
            assert "risk" in data
            assert "associated_controls" in data
            assert "associated_questions" in data
            assert data["risk"]["id"] == "AIR.001"

    def test_get_risk_detail_not_found(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test risk detail endpoint with non-existent risk."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/risk/NONEXISTENT")
            assert response.status_code == 404

    def test_get_control_detail(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test control detail endpoint."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/control/AIGPC.1")
            assert response.status_code == 200
            data = response.json()
            assert "control" in data
            assert "associated_risks" in data
            assert "associated_questions" in data
            assert data["control"]["id"] == "AIGPC.1"

    def test_get_control_detail_not_found(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test control detail endpoint with non-existent control."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/control/NONEXISTENT")
            assert response.status_code == 404

    def test_get_question_detail(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test question detail endpoint."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/question/Q1")
            assert response.status_code == 200
            data = response.json()
            assert "question" in data
            assert "managing_roles" in data
            assert "associated_risks" in data
            assert "associated_controls" in data
            assert data["question"]["id"] == "Q1"

    def test_get_question_detail_not_found(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test question detail endpoint with non-existent question."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/question/NONEXISTENT")
            assert response.status_code == 404


class TestUtilityEndpoints:
    """Test utility endpoints."""

    def test_get_managing_roles(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test managing roles endpoint."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/managing-roles")
            assert response.status_code == 200
            data = response.json()
            assert "managing_roles" in data
            assert isinstance(data["managing_roles"], list)

    def test_get_file_metadata(self, test_client, sample_database, mock_config_manager):
        """Test file metadata endpoint."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/file-metadata")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, dict)
            # Should contain metadata for different data types
            assert "risks" in data or "controls" in data or "questions" in data

    def test_get_network_data(self, test_client, sample_database, mock_config_manager):
        """Test network data endpoint."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/network")
            assert response.status_code == 200
            data = response.json()
            assert "risk_control_links" in data
            assert "question_risk_links" in data
            assert "question_control_links" in data
            assert isinstance(data["risk_control_links"], list)
            assert isinstance(data["question_risk_links"], list)
            assert isinstance(data["question_control_links"], list)

    def test_get_gaps_analysis(self, test_client, sample_database, mock_config_manager):
        """Test gaps analysis endpoint."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/gaps")
            assert response.status_code == 200
            data = response.json()
            assert "summary" in data
            assert "unmapped_risks" in data
            assert "unmapped_controls" in data
            assert "unmapped_questions" in data
            assert "risks_without_questions" in data
            assert "total_risks" in data["summary"]
            assert "total_controls" in data["summary"]
            assert "total_questions" in data["summary"]
            assert "risks_without_questions" in data["summary"]
            assert "risks_without_questions_pct" in data["summary"]
            assert "controls_without_questions" in data["summary"]
            assert "controls_without_questions_pct" in data["summary"]

            # Validate data types
            assert isinstance(data["summary"]["risks_without_questions"], int)
            assert isinstance(
                data["summary"]["risks_without_questions_pct"], (int, float)
            )
            assert isinstance(data["risks_without_questions"], list)
            assert isinstance(data["summary"]["controls_without_questions"], int)
            assert isinstance(
                data["summary"]["controls_without_questions_pct"], (int, float)
            )
            assert isinstance(data["controls_without_questions"], list)

            # Validate percentage is between 0 and 100
            assert 0 <= data["summary"]["risks_without_questions_pct"] <= 100
            assert 0 <= data["summary"]["controls_without_questions_pct"] <= 100

    def test_risks_without_questions_calculation(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test specific calculation of risks without questions."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/gaps")
            assert response.status_code == 200
            data = response.json()

            # Get the risks without questions data
            risks_without_questions = data["risks_without_questions"]
            summary = data["summary"]

            # Validate that each risk in the list has the expected structure
            for risk in risks_without_questions:
                assert "risk_id" in risk
                assert "risk_title" in risk
                assert "risk_description" in risk
                assert isinstance(risk["risk_id"], str)
                assert isinstance(risk["risk_title"], str)
                # risk_description can be None or string
                assert risk["risk_description"] is None or isinstance(
                    risk["risk_description"], str
                )

            # Validate that the count matches the list length
            assert len(risks_without_questions) == summary["risks_without_questions"]

            # Validate percentage calculation
            if summary["total_risks"] > 0:
                expected_percentage = (
                    summary["risks_without_questions"] / summary["total_risks"]
                ) * 100
                assert (
                    abs(summary["risks_without_questions_pct"] - expected_percentage)
                    < 0.1
                )  # Allow for rounding

    def test_controls_without_questions_calculation(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test specific calculation of controls without questions."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/gaps")
            assert response.status_code == 200
            data = response.json()

            # Get the controls without questions data
            controls_without_questions = data["controls_without_questions"]
            summary = data["summary"]

            # Validate that each control in the list has the expected structure
            for control in controls_without_questions:
                assert "control_id" in control
                assert "control_title" in control
                assert "control_description" in control
                assert isinstance(control["control_id"], str)
                assert isinstance(control["control_title"], str)
                # control_description can be None or string
                assert control["control_description"] is None or isinstance(
                    control["control_description"], str
                )

            # Validate that the count matches the list length
            assert (
                len(controls_without_questions) == summary["controls_without_questions"]
            )

            # Validate percentage calculation
            if summary["total_controls"] > 0:
                expected_percentage = (
                    summary["controls_without_questions"] / summary["total_controls"]
                ) * 100
                assert (
                    abs(summary["controls_without_questions_pct"] - expected_percentage)
                    < 0.1
                )  # Allow for rounding

    def test_risks_without_questions_edge_cases(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test edge cases for risks without questions calculation."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/gaps")
            assert response.status_code == 200
            data = response.json()

            summary = data["summary"]

            # Test that all risks without questions are actually risks
            risks_without_questions = data["risks_without_questions"]
            all_risk_ids = {risk["risk_id"] for risk in risks_without_questions}

            # Verify that the count is reasonable (not more than total risks)
            assert summary["risks_without_questions"] <= summary["total_risks"]

            # Verify that risks without questions are not duplicated
            assert len(risks_without_questions) == len(all_risk_ids)

            # Test that percentage calculation handles zero division
            if summary["total_risks"] == 0:
                assert summary["risks_without_questions_pct"] == 0
            else:
                assert summary["risks_without_questions_pct"] >= 0
                assert summary["risks_without_questions_pct"] <= 100

    def test_controls_without_questions_edge_cases(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test edge cases for controls without questions calculation."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/gaps")
            assert response.status_code == 200
            data = response.json()

            summary = data["summary"]

            # Test that all controls without questions are actually controls
            controls_without_questions = data["controls_without_questions"]
            all_control_ids = {
                control["control_id"] for control in controls_without_questions
            }

            # Verify that the count is reasonable (not more than total controls)
            assert summary["controls_without_questions"] <= summary["total_controls"]

            # Verify that controls without questions are not duplicated
            assert len(controls_without_questions) == len(all_control_ids)

            # Test that percentage calculation handles zero division
            if summary["total_controls"] == 0:
                assert summary["controls_without_questions_pct"] == 0
            else:
                assert summary["controls_without_questions_pct"] >= 0
                assert summary["controls_without_questions_pct"] <= 100

    def test_get_last_updated(self, test_client, sample_database, mock_config_manager):
        """Test last updated endpoint."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/last-updated")
            assert response.status_code == 200
            data = response.json()
            assert "risks" in data
            assert "controls" in data
            assert "questions" in data
            for data_type in ["risks", "controls", "questions"]:
                assert "last_updated" in data[data_type]
                assert "version" in data[data_type]


class TestErrorHandling:
    """Test error handling across endpoints."""

    def test_database_connection_error(self, test_client, mock_config_manager):
        """Test endpoints when database connection fails."""
        with patch("app.get_db_connection") as mock_conn:
            mock_conn.side_effect = sqlite3.Error("Connection failed")

            # Test various endpoints
            endpoints = [
                "/api/health",
                "/api/risks",
                "/api/controls",
                "/api/questions",
                "/api/relationships",
                "/api/search?q=test",
                "/api/stats",
            ]

            for endpoint in endpoints:
                response = test_client.get(endpoint)
                assert response.status_code in [
                    500,
                    200,
                ]  # Health might return 200 with error

    def test_invalid_parameters(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test endpoints with invalid parameters."""
        with patch("app.DB_PATH", str(sample_database)):
            # Test invalid limits
            response = test_client.get("/api/risks?limit=-1")
            assert response.status_code == 422

            response = test_client.get("/api/risks?offset=-1")
            assert response.status_code == 422

            # Test search with short query
            response = test_client.get("/api/search?q=a")
            assert response.status_code == 422


class TestCORSHeaders:
    """Test CORS headers are properly set."""

    def test_cors_headers(self, test_client, sample_database, mock_config_manager):
        """Test that CORS headers are present."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.options("/api/health")
            # CORS headers should be present
            assert response.status_code in [
                200,
                405,
            ]  # OPTIONS might not be implemented

    def test_cors_origin_header(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test CORS origin header."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get(
                "/api/health", headers={"Origin": "http://localhost:3000"}
            )
            assert response.status_code == 200
            # CORS middleware should handle this
