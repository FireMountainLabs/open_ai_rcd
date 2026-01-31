"""
Tests for data integrity and reliability.

This module ensures that the dashboard always presents accurate, consistent
information to users and handles errors gracefully without showing erroneous data.
"""

from unittest.mock import patch

import pytest


@pytest.mark.unit
@pytest.mark.integrity
class TestDataIntegrity:
    """Test data integrity and reliability."""

    def test_api_risks_data_consistency(self, client, mock_database_api_client, patch_api_client_methods):
        """Test that risks data is always consistent and complete."""
        # Mock database returns consistent risk data
        mock_database_api_client.get_risks.return_value = [
            {
                "id": "R.AIR.001",
                "title": "AI Model Bias Risk",
                "description": "Risk of bias in AI model outputs",
                "category": "AI Risk",
                "severity": "High",
                "status": "Active",
                "created_date": "2024-01-15T10:30:00Z",
                "last_updated": "2024-01-20T14:45:00Z",
            }
        ]

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/risks")

            assert response.status_code == 200
            data = response.get_json()

            # Verify data structure is complete and consistent
            assert len(data) == 1
            risk = data[0]
            assert risk["id"] == "R.AIR.001"
            assert risk["title"] == "AI Model Bias Risk"
            assert risk["category"] == "AI Risk"
            assert risk["severity"] == "High"
            assert risk["status"] == "Active"

            # Verify all required fields are present
            required_fields = [
                "id",
                "title",
                "description",
                "category",
                "severity",
                "status",
            ]
            for field in required_fields:
                assert field in risk, f"Missing required field: {field}"

    def test_api_risks_handles_empty_database(self, client, mock_database_api_client, patch_api_client_methods):
        """Test that risks API handles empty database gracefully."""
        mock_database_api_client.get_risks.return_value = []

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/risks")

            assert response.status_code == 200
            data = response.get_json()
            assert data == []
            # Should not crash or show error to user

    def test_api_risks_handles_database_error(self, client, mock_database_api_client, patch_api_client_methods):
        """Test that risks API handles database errors without showing erroneous data."""
        mock_database_api_client.get_risks.side_effect = Exception(
            "Database connection failed"
        )

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/risks")

            assert response.status_code == 200
            data = response.get_json()
            assert data == []  # Should return empty list, not crash
            # User should see empty state, not error message

    def test_api_controls_data_consistency(self, client, mock_database_api_client, patch_api_client_methods):
        """Test that controls data is always consistent and complete."""
        mock_database_api_client.get_controls.return_value = [
            {
                "id": "C.AIIM.1",
                "title": "Model Validation Controls",
                "description": "Controls for validating AI models",
                "domain": "AI Implementation",
                "type": "Preventive",
                "status": "Implemented",
                "created_date": "2024-01-10T09:15:00Z",
                "last_updated": "2024-01-18T16:20:00Z",
            }
        ]

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/controls")

            assert response.status_code == 200
            data = response.get_json()

            # Verify data structure is complete and consistent
            assert len(data) == 1
            control = data[0]
            assert control["id"] == "C.AIIM.1"
            assert control["title"] == "Model Validation Controls"
            assert control["domain"] == "AI Implementation"
            assert control["type"] == "Preventive"
            assert control["status"] == "Implemented"

            # Verify all required fields are present
            required_fields = ["id", "title", "description", "domain", "type", "status"]
            for field in required_fields:
                assert field in control, f"Missing required field: {field}"

    def test_api_controls_handles_database_error(
        self, client, mock_database_api_client, patch_api_client_methods
    ):
        """Test that controls API handles database errors without showing erroneous data."""
        mock_database_api_client.get_controls.side_effect = Exception(
            "Database connection failed"
        )

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/controls")

            assert response.status_code == 200
            data = response.get_json()
            assert data == []  # Should return empty list, not crash

    def test_api_questions_data_consistency(self, client, mock_database_api_client, patch_api_client_methods):
        """Test that questions data is always consistent and complete."""
        mock_database_api_client.get_questions.return_value = [
            {
                "id": "Q.CIR.1.1",
                "question": "How is AI model bias monitored?",
                "category": "AI Risk",
                "type": "Assessment",
                "priority": "High",
                "created_date": "2024-01-12T11:30:00Z",
                "last_updated": "2024-01-19T13:45:00Z",
            }
        ]

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/questions")

            assert response.status_code == 200
            data = response.get_json()

            # Verify data structure is complete and consistent
            assert len(data) == 1
            question = data[0]
            assert question["id"] == "Q.CIR.1.1"
            assert question["question"] == "How is AI model bias monitored?"
            assert question["category"] == "AI Risk"
            assert question["type"] == "Assessment"
            assert question["priority"] == "High"

            # Verify all required fields are present
            required_fields = ["id", "question", "category", "type", "priority"]
            for field in required_fields:
                assert field in question, f"Missing required field: {field}"

    def test_api_questions_handles_database_error(
        self, client, mock_database_api_client, patch_api_client_methods
    ):
        """Test that questions API handles database errors without showing erroneous data."""
        mock_database_api_client.get_questions.side_effect = Exception(
            "Database connection failed"
        )

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/questions")

            assert response.status_code == 200
            data = response.get_json()
            assert data == []  # Should return empty list, not crash

    def test_api_stats_data_consistency(self, client, mock_database_api_client, patch_api_client_methods):
        """Test that stats data is always consistent and mathematically correct."""
        mock_database_api_client.get_stats.return_value = {
            "total_risks": 25,
            "total_controls": 18,
            "total_questions": 42,
            "active_risks": 20,
            "implemented_controls": 15,
            "high_priority_questions": 8,
        }

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/stats")

            assert response.status_code == 200
            data = response.get_json()

            # Verify data consistency
            assert data["total_risks"] == 25
            assert data["total_controls"] == 18
            assert data["total_questions"] == 42
            assert data["active_risks"] == 20
            assert data["implemented_controls"] == 15
            assert data["high_priority_questions"] == 8

            # Verify mathematical consistency
            assert data["active_risks"] <= data["total_risks"]
            assert data["implemented_controls"] <= data["total_controls"]
            assert data["high_priority_questions"] <= data["total_questions"]

            # Verify all required fields are present
            required_fields = ["total_risks", "total_controls", "total_questions"]
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"

    def test_api_stats_handles_database_error(self, client, mock_database_api_client, patch_api_client_methods):
        """Test that stats API handles database errors with safe defaults."""
        mock_database_api_client.get_stats.side_effect = Exception(
            "Database connection failed"
        )

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/stats")

            assert response.status_code == 200
            data = response.get_json()

            # Should return safe defaults, not crash
            assert data["total_risks"] == 0
            assert data["total_controls"] == 0
            assert data["total_questions"] == 0

    def test_api_search_data_consistency(self, client, mock_database_api_client, patch_api_client_methods):
        """Test that search results are always consistent and relevant."""
        mock_database_api_client.search.return_value = [
            {
                "id": "R.AIR.001",
                "title": "AI Model Bias Risk",
                "type": "risk",
                "description": "Risk of bias in AI model outputs",
                "relevance_score": 0.95,
            },
            {
                "id": "C.AIIM.1",
                "title": "Model Validation Controls",
                "type": "control",
                "description": "Controls for validating AI models",
                "relevance_score": 0.87,
            },
        ]

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/search?q=bias")

            assert response.status_code == 200
            data = response.get_json()

            # Verify search results are consistent
            assert len(data) == 2
            assert data[0]["type"] == "risk"
            assert data[1]["type"] == "control"

            # Verify search results contain the search term
            assert (
                "bias" in data[0]["title"].lower()
                or "bias" in data[0]["description"].lower()
            )

            # Verify all required fields are present
            required_fields = ["id", "title", "type", "description"]
            for result in data:
                for field in required_fields:
                    assert field in result, f"Missing required field: {field}"

    def test_api_search_handles_empty_results(self, client, mock_database_api_client, patch_api_client_methods):
        """Test that search handles empty results gracefully."""
        mock_database_api_client.search.return_value = []

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/search?q=nonexistent")

            assert response.status_code == 200
            data = response.get_json()
            assert data == []  # Should return empty list, not crash

    def test_api_search_handles_database_error(self, client, mock_database_api_client, patch_api_client_methods):
        """Test that search handles database errors without showing erroneous data."""
        mock_database_api_client.search.side_effect = Exception(
            "Database connection failed"
        )

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/search?q=test")

            assert response.status_code == 200
            data = response.get_json()
            # Search API returns dict with query and results
            assert data["query"] == "test"
            assert data["results"] == []  # Should return empty results, not crash

    def test_api_risk_detail_data_consistency(self, client, mock_database_api_client, patch_api_client_methods):
        """Test that risk detail data is always consistent and complete."""
        mock_database_api_client.get_risk_detail.return_value = {
            "risk": {
                "id": "R.AIR.001",
                "title": "AI Model Bias Risk",
                "description": "Risk of bias in AI model outputs",
                "category": "AI Risk",
                "severity": "High",
                "status": "Active",
            },
            "associated_controls": [
                {
                    "id": "C.AIIM.1",
                    "title": "Model Validation Controls",
                    "status": "Implemented",
                    "effectiveness": "High",
                }
            ],
            "associated_questions": [
                {
                    "id": "Q.CIR.1.1",
                    "question": "How is AI model bias monitored?",
                    "priority": "High",
                }
            ],
        }

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/risk/R.AIR.001")

            assert response.status_code == 200
            data = response.get_json()

            # Verify data structure is complete and consistent
            assert "risk" in data
            assert "associated_controls" in data
            assert "associated_questions" in data

            risk = data["risk"]
            assert risk["id"] == "R.AIR.001"
            assert risk["title"] == "AI Model Bias Risk"

            # Verify associated data is consistent
            assert len(data["associated_controls"]) == 1
            assert data["associated_controls"][0]["id"] == "C.AIIM.1"
            assert len(data["associated_questions"]) == 1
            assert data["associated_questions"][0]["id"] == "Q.CIR.1.1"

    def test_api_risk_detail_handles_database_error(
        self, client, mock_database_api_client, patch_api_client_methods
    ):
        """Test that risk detail handles database errors with safe defaults."""
        mock_database_api_client.get_risk_detail.side_effect = Exception(
            "Database connection failed"
        )

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/risk/R.AIR.001")

            assert response.status_code == 200
            data = response.get_json()

            # Should return safe defaults, not crash
            assert data["risk"] == {}
            assert data["associated_controls"] == []
            assert data["associated_questions"] == []

    def test_api_health_data_consistency(self, client, mock_database_api_client, patch_api_client_methods):
        """Test that health data is always consistent and accurate."""
        mock_database_api_client.health_check.return_value = {
            "status": "healthy",
            "database_connected": True,
            "total_records": 150,
            "last_updated": "2024-01-20T15:30:00Z",
        }

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/health")

            assert response.status_code == 200
            data = response.get_json()

            # Verify health data is consistent
            assert data["status"] == "healthy"
            assert data["database_service"]["status"] == "healthy"
            assert data["dashboard_service"]["status"] == "healthy"
            assert data["database_service"]["database_connected"] is True
            assert data["database_service"]["total_records"] == 150

    def test_api_health_handles_database_error(self, client, mock_database_api_client, patch_api_client_methods):
        """Test that health handles database errors with accurate status."""
        mock_database_api_client.health_check.side_effect = Exception(
            "Database connection failed"
        )

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/health")

            assert response.status_code == 200
            data = response.get_json()

            # Should accurately reflect unhealthy status
            assert data["status"] == "unhealthy"
            assert data["database_service"]["status"] == "unhealthy"
            assert data["dashboard_service"]["status"] == "healthy"

    def test_api_pagination_consistency(self, client, mock_database_api_client, patch_api_client_methods):
        """Test that pagination always returns consistent results."""
        mock_database_api_client.get_risks.return_value = [
            {"id": f"R.AIR.{i:03d}", "title": f"Risk {i}"} for i in range(5)
        ]

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/risks?limit=5&offset=10")

            assert response.status_code == 200
            data = response.get_json()

            # Verify pagination parameters are respected
            assert len(data) == 5
            mock_database_api_client.get_risks.assert_called_with(
                limit=5, offset=10, category=None
            )

    def test_api_filtering_consistency(self, client, mock_database_api_client, patch_api_client_methods):
        """Test that filtering always returns consistent results."""
        mock_database_api_client.get_risks.return_value = [
            {"id": "R.AIR.001", "category": "AI Risk", "title": "AI Model Bias Risk"}
        ]

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/risks?category=AI Risk")

            assert response.status_code == 200
            data = response.get_json()

            # Verify filtering is applied correctly
            assert len(data) == 1
            assert data[0]["category"] == "AI Risk"
            mock_database_api_client.get_risks.assert_called_with(
                limit=100, offset=0, category="AI Risk"
            )

    def test_api_always_returns_json(self, client, mock_database_api_client, patch_api_client_methods):
        """Test that all API endpoints always return valid JSON."""
        mock_database_api_client.get_risks.return_value = []
        mock_database_api_client.get_controls.return_value = []
        mock_database_api_client.get_questions.return_value = []
        mock_database_api_client.get_stats.return_value = {
            "total_risks": 0,
            "total_controls": 0,
            "total_questions": 0,
        }

        api_endpoints = [
            "/api/risks",
            "/api/controls",
            "/api/questions",
            "/api/stats",
            "/api/health",
        ]

        with patch_api_client_methods(mock_database_api_client):
            for endpoint in api_endpoints:
                response = client.get(endpoint)
                assert response.status_code == 200
                assert response.is_json

                # Should be able to parse as JSON
                data = response.get_json()
                assert data is not None
