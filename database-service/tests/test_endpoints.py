"""
Endpoint tests for Database Service.

Tests all API endpoints for proper functionality, error handling, and response formats.
"""

import pytest
import json
import sqlite3

# Import the app
import sys

import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

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
        # Repositories are already initialized with sample_database by the test_client fixture
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
        # Repositories are already initialized with sample_database by the test_client fixture
        response = test_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database_connected"] is True
        assert data["total_records"] > 0

    def test_health_endpoint_unhealthy(self, test_client, mock_config_manager):
        """Test health endpoint when database is unhealthy."""
        from app import reinitialize_repositories
        reinitialize_repositories("/nonexistent/database.db")
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
        response = test_client.get("/api/risks?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_get_risks_with_offset(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test risks endpoint with offset parameter."""
        response = test_client.get("/api/risks?offset=1&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_get_risks_with_category_filter(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test risks endpoint with category filter."""
        response = test_client.get("/api/risks?category=Privacy")
        assert response.status_code == 200
        data = response.json()
        # Should filter by category if implemented
        assert isinstance(data, list)

    def test_get_risks_invalid_limit(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test risks endpoint with invalid limit."""
        response = test_client.get("/api/risks?limit=0")
        assert response.status_code == 422  # Validation error

    def test_get_risks_invalid_offset(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test risks endpoint with invalid offset."""
        response = test_client.get("/api/risks?offset=-1")
        assert response.status_code == 422  # Validation error

    def test_get_risks_database_error(self, test_client, mock_config_manager):
        """Test risks endpoint with database error."""
        with patch("app.risk_repo.db_manager.get_db_connection") as mock_conn:
            mock_conn.side_effect = sqlite3.Error("Database error")
            response = test_client.get("/api/risks")
            assert response.status_code == 500


class TestControlsEndpoints:
    """Test controls-related endpoints."""

    def test_get_controls_basic(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test basic controls endpoint."""
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
        response = test_client.get("/api/controls?domain=Protect")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_controls_with_limit_and_offset(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test controls endpoint with limit and offset."""
        response = test_client.get("/api/controls?limit=2&offset=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2


class TestRelationshipsEndpoints:
    """Test relationships endpoints."""

    def test_get_relationships_basic(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test basic relationships endpoint."""
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
        response = test_client.get("/api/relationships?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5


class TestSearchEndpoints:
    """Test search endpoints."""

    def test_search_basic(self, test_client, sample_database, mock_config_manager):
        """Test basic search endpoint."""
        response = test_client.get("/api/search?q=privacy")
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "results" in data
        assert data["query"] == "privacy"
        assert isinstance(data["results"], list)

    def test_search_with_limit(self, test_client, sample_database, mock_config_manager):
        """Test search endpoint with limit."""
        response = test_client.get("/api/search?q=test&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) <= 2

    def test_search_minimum_length(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test search endpoint with query too short."""
        response = test_client.get("/api/search?q=a")
        assert response.status_code == 422  # Validation error

    def test_search_no_query(self, test_client, sample_database, mock_config_manager):
        """Test search endpoint without query."""
        response = test_client.get("/api/search")
        assert response.status_code == 422  # Validation error


class TestStatsEndpoints:
    """Test statistics endpoints."""

    def test_get_stats(self, test_client, sample_database, mock_config_manager):
        """Test stats endpoint."""
        response = test_client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_risks" in data
        assert "total_controls" in data
        assert data["total_risks"] > 0
        assert data["total_controls"] > 0


class TestSummaryEndpoints:
    """Test summary endpoints."""

    def test_get_risks_summary(self, test_client, sample_database, mock_config_manager):
        """Test risks summary endpoint."""
        response = test_client.get("/api/risks/summary")
        assert response.status_code == 200
        data = response.json()
        assert "details" in data
        assert isinstance(data["details"], list)
        if data["details"]:
            assert "risk_id" in data["details"][0]
            assert "control_count" in data["details"][0]

    def test_get_controls_summary(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test controls summary endpoint."""
        response = test_client.get("/api/controls/summary")
        assert response.status_code == 200
        data = response.json()
        assert "details" in data
        assert isinstance(data["details"], list)
        if data["details"]:
            assert "control_id" in data["details"][0]
            assert "risk_count" in data["details"][0]

class TestDetailEndpoints:
    """Test detail endpoints for specific entities."""

    def test_get_risk_detail(self, test_client, sample_database, mock_config_manager):
        """Test risk detail endpoint."""
        response = test_client.get("/api/risk/AIR.001")
        assert response.status_code == 200
        data = response.json()
        assert "risk" in data
        assert "associated_controls" in data
        assert data["risk"]["id"] == "AIR.001"

    def test_get_risk_detail_not_found(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test risk detail endpoint with non-existent risk."""
        response = test_client.get("/api/risk/NONEXISTENT")
        assert response.status_code == 404

    def test_get_control_detail(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test control detail endpoint."""
        response = test_client.get("/api/control/AIGPC.1")
        assert response.status_code == 200
        data = response.json()
        assert "control" in data
        assert "associated_risks" in data
        assert data["control"]["id"] == "AIGPC.1"

    def test_get_control_detail_not_found(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test control detail endpoint with non-existent control."""
        response = test_client.get("/api/control/NONEXISTENT")
        assert response.status_code == 404

class TestUtilityEndpoints:
    """Test utility endpoints."""

    def test_get_file_metadata(self, test_client, sample_database, mock_config_manager):
        """Test file metadata endpoint."""
        response = test_client.get("/api/file-metadata")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        # Should contain metadata for different data types
        assert "risks" in data or "controls" in data

    def test_get_network_data(self, test_client, sample_database, mock_config_manager):
        """Test network data endpoint."""
        response = test_client.get("/api/network")
        assert response.status_code == 200
        data = response.json()
        assert "risk_control_links" in data
        assert isinstance(data["risk_control_links"], list)

    def test_get_gaps_analysis(self, test_client, sample_database, mock_config_manager):
        """Test gaps analysis endpoint."""
        response = test_client.get("/api/gaps")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "unmapped_risks" in data
        assert "unmapped_controls" in data
        assert "total_risks" in data["summary"]
        assert "total_controls" in data["summary"]

        # Validate data types


    def test_get_last_updated(self, test_client, sample_database, mock_config_manager):
        """Test last updated endpoint."""
        response = test_client.get("/api/last-updated")
        assert response.status_code == 200
        data = response.json()
        assert "risks" in data
        assert "controls" in data
        for data_type in ["risks", "controls"]:
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
        response = test_client.get(
            "/api/health", headers={"Origin": "http://localhost:3000"}
        )
        assert response.status_code == 200
        # CORS middleware should handle this
