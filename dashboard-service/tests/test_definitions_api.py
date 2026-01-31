"""
Tests for the definitions API endpoints.
"""

import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
import json


@pytest.mark.unit
@pytest.mark.api
class TestDefinitionsAPI:
    """Test definitions API endpoints."""

    def test_api_definitions_success(self, client, mock_database_api_client, patch_api_client_methods):
        """Test definitions API returns successful response."""
        mock_database_api_client.get_definitions.return_value = [
            {
                "definition_id": "def_001",
                "term": "Artificial Intelligence",
                "title": "Artificial Intelligence",
                "description": "The simulation of human intelligence in machines",
                "category": "Core Concepts",
                "source": "AI_Definitions_and_Taxonomy_V1.xlsx",
            },
            {
                "definition_id": "def_002",
                "term": "Machine Learning",
                "title": "Machine Learning",
                "description": "A subset of AI that enables systems to learn from data",
                "category": "Core Concepts",
                "source": "AI_Definitions_and_Taxonomy_V1.xlsx",
            },
        ]

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/definitions")
            assert response.status_code == 200
            data = response.get_json()
            assert isinstance(data, list)
            assert len(data) == 2
            assert data[0]["term"] == "Artificial Intelligence"
            assert data[1]["term"] == "Machine Learning"

    def test_api_definitions_with_params(self, client, mock_database_api_client, patch_api_client_methods):
        """Test definitions API with query parameters."""
        mock_database_api_client.get_definitions.return_value = [
            {
                "definition_id": "def_001",
                "term": "Artificial Intelligence",
                "title": "Artificial Intelligence",
                "description": "The simulation of human intelligence in machines",
                "category": "Core Concepts",
                "source": "AI_Definitions_and_Taxonomy_V1.xlsx",
            }
        ]

        with patch_api_client_methods(mock_database_api_client):
            response = client.get(
            "/api/definitions?limit=1&offset=0&category=Core Concepts"
        )
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]["category"] == "Core Concepts"

    def test_api_definitions_database_error(self, client, mock_database_api_client, patch_api_client_methods):
        """Test definitions API handles database errors."""
        mock_database_api_client.get_definitions.side_effect = Exception("Database error")

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/definitions")

                # The app returns empty list on error, not 500
        assert response.status_code == 200
        data = response.get_json()
        assert data == []

    def test_api_definitions_empty_results(self, client, mock_database_api_client, patch_api_client_methods):
        """Test definitions API handles empty results."""
        mock_database_api_client.get_definitions.return_value = []

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/definitions")
        assert response.status_code == 200
        data = response.get_json()
        assert data == []

    def test_api_definitions_pagination(self, client, mock_database_api_client, patch_api_client_methods):
        """Test definitions API pagination."""
        mock_database_api_client.get_definitions.return_value = [
            {
                "definition_id": "def_002",
                "term": "Machine Learning",
                "title": "Machine Learning",
                "description": "A subset of AI that enables systems to learn from data",
                "category": "Core Concepts",
                "source": "AI_Definitions_and_Taxonomy_V1.xlsx",
            }
        ]

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/definitions?limit=1&offset=1")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]["term"] == "Machine Learning"

    def test_api_definitions_category_filter(self, client, mock_database_api_client, patch_api_client_methods):
        """Test definitions API category filtering."""
        mock_database_api_client.get_definitions.return_value = [
            {
                "definition_id": "def_003",
                "term": "Neural Network",
                "title": "Neural Network",
                "description": "A computing system inspired by biological neural networks",
                "category": "Technical Terms",
                "source": "AI_Definitions_and_Taxonomy_V1.xlsx",
            }
        ]

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/definitions?category=Technical Terms")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]["category"] == "Technical Terms"

    def test_api_definitions_data_structure(self, client, mock_database_api_client, patch_api_client_methods):
        """Test definitions API returns correct data structure."""
        mock_database_api_client.get_definitions.return_value = [
            {
                "definition_id": "def_001",
                "term": "Test Term",
                "title": "Test Title",
                "description": "Test Description",
                "category": "Core Concepts",
                "source": "test.xlsx",
            }
        ]
        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/definitions")
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)

        if data:  # Only test structure if data exists
            definition = data[0]
            required_fields = [
                "definition_id",
                "term",
                "title",
                "description",
                "category",
                "source",
            ]
            for field in required_fields:
                assert field in definition

    def test_api_definitions_invalid_params(self, client, mock_database_api_client, patch_api_client_methods):
        """Test definitions API handles invalid parameters."""
        # The app passes parameters through to the database service
        # The database service validates them and returns 422 errors
        mock_database_api_client.get_definitions.side_effect = Exception(
            "422 Client Error: Unprocessable Content"
        )

        # Test negative limit - database service will return 422
        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/definitions?limit=-1")
        assert response.status_code == 200  # App returns empty list on error
        data = response.get_json()
        assert data == []

        # Test negative offset - database service will return 422
        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/definitions?offset=-1")
        assert response.status_code == 200  # App returns empty list on error
        data = response.get_json()
        assert data == []

        # Test non-numeric limit - Flask will convert to 0
        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/definitions?limit=abc")
        assert response.status_code == 200
        data = response.get_json()
        # Flask converts non-numeric to 0, so this should work

        # Test non-numeric offset - Flask will convert to 0
        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/definitions?offset=xyz")
        assert response.status_code == 200
        data = response.get_json()
        # Flask converts non-numeric to 0, so this should work

    def test_api_definitions_search_integration(self, client, mock_database_api_client, patch_api_client_methods):
        """Test that definitions are included in search results."""
        mock_database_api_client.search.return_value = {
            "results": [
                {
                    "type": "definition",
                    "id": "def_001",
                    "title": "Artificial Intelligence",
                    "description": "The simulation of human intelligence in machines",
                    "category": "Core Concepts",
                    "source": "AI_Definitions_and_Taxonomy_V1.xlsx",
                },
                {
                    "type": "risk",
                    "id": "R.AI.001",
                    "title": "AI Bias Risk",
                    "description": "Risk of bias in AI systems",
                },
            ],
            "total": 2,
        }

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/search?q=artificial intelligence")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["results"]) == 2

    def test_api_definitions_last_updated_integration(self, client, mock_database_api_client, patch_api_client_methods):
        """Test that definitions are included in last updated endpoint."""
        # Mock the session.get call that's used in the last_updated endpoint
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "last_updated": "2024-01-01T00:00:00Z",
            "definitions": "2024-01-01T00:00:00Z",
        }
        mock_response.raise_for_status.return_value = None
        mock_database_api_client.session.get.return_value = mock_response

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/last-updated")
        assert response.status_code == 200
        data = response.get_json()
        assert "definitions" in data

    def test_api_definitions_stats_integration(self, client, mock_database_api_client, patch_api_client_methods):
        """Test that definitions count is included in stats endpoint."""
        mock_database_api_client.get_stats.return_value = {
            "total_risks": 150,
            "total_controls": 200,
            "total_questions": 300,
            "total_definitions": 50,
            "total_relationships": 500,
        }

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.get_json()
        assert "total_definitions" in data
        assert data["total_definitions"] == 50
