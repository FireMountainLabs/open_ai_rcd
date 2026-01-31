"""
Test suite for gap card rendering functionality.

This tests the frontend rendering of gap cards and their data tables,
verifying that the API data structure is correctly consumed by the JavaScript.
"""

import pytest
from unittest.mock import patch


@pytest.mark.unit
class TestGapCardsRendering:
    """Test gap cards rendering functionality"""

    def test_gaps_api_response_structure(self, client, mock_database_api_client, patch_api_client_methods):
        """Test that the gaps API returns the expected structure without a 'details' wrapper."""
        # Mock the database service response with the correct structure
        mock_gaps_response = {
            "summary": {
                "total_risks": 108,
                "total_controls": 170,
                "total_questions": 296,
                "unmapped_risks": 0,
                "unmapped_controls": 0,
                "unmapped_questions": 2,
                "risks_without_questions": 46,
                "controls_without_questions": 131,
                "risk_coverage_pct": 100.0,
                "control_coverage_pct": 100.0,
                "question_coverage_pct": 99.3,
                "risks_without_questions_pct": 42.6,
                "controls_without_questions_pct": 73.6,
                "control_utilization_pct": 100.0,
            },
            # Data is at top level, not nested in 'details'
            "unmapped_risks": [],
            "unmapped_controls": [],
            "unmapped_questions": [
                {
                    "question_id": "Q1",
                    "question_text": "Test question 1",
                    "category": "Model Development",
                },
                {
                    "question_id": "Q2",
                    "question_text": "Test question 2",
                    "category": "Governance",
                },
            ],
            "risks_without_questions": [
                {
                    "risk_id": "AIR.001",
                    "risk_title": "Test Risk 1",
                    "risk_description": "Description 1",
                },
                {
                    "risk_id": "AIR.002",
                    "risk_title": "Test Risk 2",
                    "risk_description": "Description 2",
                },
            ],
            "controls_without_questions": [
                {
                    "control_id": "AIGPC.1",
                    "control_title": "Test Control 1",
                    "control_description": "Control Description 1",
                }
            ],
        }

        mock_database_api_client.session.get.return_value.json.return_value = (
            mock_gaps_response
        )
        mock_database_api_client.session.get.return_value.status_code = 200
        mock_database_api_client.session.get.return_value.raise_for_status.return_value = (
            None
        )

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/gaps")

            assert response.status_code == 200
            data = response.get_json()

            # Verify the structure matches what JavaScript expects
            assert "summary" in data
            assert "unmapped_risks" in data  # At top level, not in 'details'
            assert "unmapped_controls" in data
            assert "unmapped_questions" in data
            assert "risks_without_questions" in data
            assert "controls_without_questions" in data

            # Verify there is NO 'details' wrapper
            assert "details" not in data

            # Verify the data content
            assert len(data["unmapped_questions"]) == 2
            assert len(data["risks_without_questions"]) == 2
            assert len(data["controls_without_questions"]) == 1

    def test_unmapped_questions_data_structure(self, client, mock_database_api_client, patch_api_client_methods):
        """Test that unmapped questions have the required fields for rendering."""
        mock_gaps_response = {
            "summary": {
                "total_questions": 10,
                "unmapped_questions": 2,
                "question_coverage_pct": 80.0,
            },
            "unmapped_questions": [
                {
                    "question_id": "Q123",
                    "question_text": "What is the model's purpose?",
                    "category": "Model Development",
                }
            ],
            "unmapped_risks": [],
            "unmapped_controls": [],
            "risks_without_questions": [],
            "controls_without_questions": [],
        }

        mock_database_api_client.session.get.return_value.json.return_value = (
            mock_gaps_response
        )
        mock_database_api_client.session.get.return_value.status_code = 200
        mock_database_api_client.session.get.return_value.raise_for_status.return_value = (
            None
        )

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/gaps")
            data = response.get_json()

            # Verify structure for table rendering
            question = data["unmapped_questions"][0]
            assert "question_id" in question
            assert "question_text" in question
            assert "category" in question

    def test_risks_without_questions_data_structure(
        self, client, mock_database_api_client, patch_api_client_methods
    ):
        """Test that risks without questions have the required fields for rendering."""
        mock_gaps_response = {
            "summary": {
                "total_risks": 50,
                "risks_without_questions": 10,
                "risks_without_questions_pct": 20.0,
            },
            "risks_without_questions": [
                {
                    "risk_id": "AIR.042",
                    "risk_title": "Data Privacy Risk",
                    "risk_description": "Risk of unauthorized data access",
                }
            ],
            "unmapped_risks": [],
            "unmapped_controls": [],
            "unmapped_questions": [],
            "controls_without_questions": [],
        }

        mock_database_api_client.session.get.return_value.json.return_value = (
            mock_gaps_response
        )
        mock_database_api_client.session.get.return_value.status_code = 200
        mock_database_api_client.session.get.return_value.raise_for_status.return_value = (
            None
        )

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/gaps")
            data = response.get_json()

            # Verify structure for table rendering
            risk = data["risks_without_questions"][0]
            assert "risk_id" in risk
            assert "risk_title" in risk
            assert "risk_description" in risk

    def test_controls_without_questions_data_structure(
        self, client, mock_database_api_client, patch_api_client_methods
    ):
        """Test that controls without questions have the required fields for rendering."""
        mock_gaps_response = {
            "summary": {
                "total_controls": 100,
                "controls_without_questions": 50,
                "controls_without_questions_pct": 50.0,
            },
            "controls_without_questions": [
                {
                    "control_id": "AIGPC.25",
                    "control_title": "Model Monitoring Control",
                    "control_description": "Continuous monitoring of model performance",
                }
            ],
            "unmapped_risks": [],
            "unmapped_controls": [],
            "unmapped_questions": [],
            "risks_without_questions": [],
        }

        mock_database_api_client.session.get.return_value.json.return_value = (
            mock_gaps_response
        )
        mock_database_api_client.session.get.return_value.status_code = 200
        mock_database_api_client.session.get.return_value.raise_for_status.return_value = (
            None
        )

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/gaps")
            data = response.get_json()

            # Verify structure for table rendering
            control = data["controls_without_questions"][0]
            assert "control_id" in control
            assert "control_title" in control
            assert "control_description" in control

    def test_empty_gaps_response(self, client, mock_database_api_client, patch_api_client_methods):
        """Test gaps API with empty data (all entities are mapped)."""
        mock_gaps_response = {
            "summary": {
                "total_risks": 100,
                "total_controls": 150,
                "total_questions": 300,
                "unmapped_risks": 0,
                "unmapped_controls": 0,
                "unmapped_questions": 0,
                "risks_without_questions": 0,
                "controls_without_questions": 0,
                "risk_coverage_pct": 100.0,
                "control_coverage_pct": 100.0,
                "question_coverage_pct": 100.0,
                "risks_without_questions_pct": 0.0,
                "controls_without_questions_pct": 0.0,
                "control_utilization_pct": 100.0,
            },
            "unmapped_risks": [],
            "unmapped_controls": [],
            "unmapped_questions": [],
            "risks_without_questions": [],
            "controls_without_questions": [],
        }

        mock_database_api_client.session.get.return_value.json.return_value = (
            mock_gaps_response
        )
        mock_database_api_client.session.get.return_value.status_code = 200
        mock_database_api_client.session.get.return_value.raise_for_status.return_value = (
            None
        )

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/gaps")
            data = response.get_json()

            # Verify empty arrays are returned (not null or missing)
            assert data["unmapped_risks"] == []
            assert data["unmapped_controls"] == []
            assert data["unmapped_questions"] == []
            assert data["risks_without_questions"] == []
            assert data["controls_without_questions"] == []


@pytest.mark.integration
class TestGapCardsIntegration:
    """Integration tests for gap cards with actual API calls"""

    def test_dashboard_renders_gaps_html_structure(self, client):
        """Test that the dashboard HTML contains the necessary gap card structure."""
        response = client.get("/")
        assert response.status_code == 200
        html = response.data.decode("utf-8")

        # Verify gap card elements exist
        assert 'data-gap-type="risks"' in html
        assert 'data-gap-type="controls"' in html
        assert 'data-gap-type="questions"' in html
        assert 'data-gap-type="risks-without-questions"' in html
        assert 'data-gap-type="controls-without-questions"' in html

        # Verify table tbody elements exist with correct IDs
        assert 'id="unmappedRisksTable"' in html
        assert 'id="unmappedControlsTable"' in html
        assert 'id="unmappedQuestionsTable"' in html
        assert 'id="risksWithoutQuestionsTable"' in html
        assert 'id="controlsWithoutQuestionsTable"' in html

    def test_javascript_modules_loaded(self, client):
        """Test that the required JavaScript modules are loaded."""
        response = client.get("/")
        html = response.data.decode("utf-8")

        # Verify JavaScript module includes
        assert "DashboardGapsView.js" in html
        assert "DashboardEventHandlers.js" in html
