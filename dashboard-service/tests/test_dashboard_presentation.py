"""
Tests for dashboard service presentation functionality.

This module tests the dashboard service's core responsibility: presenting
database information to users in a meaningful way through API endpoints
and web interfaces.
"""

from unittest.mock import patch, Mock

import pytest
import app as app_module


@pytest.mark.unit
@pytest.mark.presentation
class TestDashboardPresentation:
    """Test dashboard presentation functionality."""

    def test_dashboard_home_route(self, client):
        """Test the main dashboard home route."""
        response = client.get("/")
        assert response.status_code == 200
        # Should render the dashboard template with data

    def test_api_risks_presentation(self, client, mock_database_api_client, patch_api_client_methods):
        """Test risks API presents data meaningfully."""
        mock_database_api_client.get_risks.return_value = [
            {
                "id": "R.AIR.001",
                "title": "AI Model Bias Risk",
                "description": "Risk of bias in AI model outputs",
                "category": "AI Risk",
                "severity": "High",
                "status": "Active",
            },
            {
                "id": "R.AIR.002",
                "title": "Data Privacy Risk",
                "description": "Risk of data privacy violations",
                "category": "Data Risk",
                "severity": "Medium",
                "status": "Active",
            },
        ]

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/risks")

            assert response.status_code == 200
            data = response.get_json()
            assert len(data) == 2
            assert data[0]["id"] == "R.AIR.001"
            assert data[0]["title"] == "AI Model Bias Risk"
            assert data[1]["id"] == "R.AIR.002"
            assert data[1]["title"] == "Data Privacy Risk"

    def test_api_controls_presentation(self, client, mock_database_api_client, patch_api_client_methods):
        """Test controls API presents data meaningfully."""
        mock_database_api_client.get_controls.return_value = [
            {
                "id": "C.AIIM.1",
                "title": "Model Validation Controls",
                "description": "Controls for validating AI models",
                "domain": "AI Implementation",
                "type": "Preventive",
                "status": "Implemented",
            },
            {
                "id": "C.AIIM.2",
                "title": "Data Governance Controls",
                "description": "Controls for data governance",
                "domain": "Data Management",
                "type": "Detective",
                "status": "Planned",
            },
        ]

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/controls")

            assert response.status_code == 200
            data = response.get_json()
            assert len(data) == 2
            assert data[0]["id"] == "C.AIIM.1"
            assert data[0]["title"] == "Model Validation Controls"
            assert data[1]["id"] == "C.AIIM.2"
            assert data[1]["title"] == "Data Governance Controls"

    def test_api_questions_presentation(self, client, mock_database_api_client, patch_api_client_methods):
        """Test questions API presents data meaningfully."""
        mock_database_api_client.get_questions.return_value = [
            {
                "id": "Q.CIR.1.1",
                "question": "How is AI model bias monitored?",
                "category": "AI Risk",
                "type": "Assessment",
                "priority": "High",
            },
            {
                "id": "Q.CIR.1.2",
                "question": "What data privacy controls are in place?",
                "category": "Data Risk",
                "type": "Assessment",
                "priority": "Medium",
            },
        ]

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/questions")

            assert response.status_code == 200
            data = response.get_json()
            assert len(data) == 2
            assert data[0]["id"] == "Q.CIR.1.1"
            assert data[0]["question"] == "How is AI model bias monitored?"
            assert data[1]["id"] == "Q.CIR.1.2"
            assert data[1]["question"] == "What data privacy controls are in place?"

    def test_api_relationships_presentation(self, client, mock_database_api_client, patch_api_client_methods):
        """Test relationships API presents data meaningfully."""
        mock_database_api_client.get_relationships.return_value = [
            {
                "id": "REL.001",
                "type": "risk_control",
                "risk_id": "R.AIR.001",
                "control_id": "C.AIIM.1",
                "description": "Model validation controls address AI bias risk",
            },
            {
                "id": "REL.002",
                "type": "question_risk",
                "question_id": "Q.CIR.1.1",
                "risk_id": "R.AIR.001",
                "description": "Bias monitoring question relates to AI bias risk",
            },
        ]

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/relationships")

            assert response.status_code == 200
            data = response.get_json()
            assert len(data) == 2
            assert data[0]["type"] == "risk_control"
            assert data[1]["type"] == "question_risk"

    def test_api_search_presentation(self, client, mock_database_api_client, patch_api_client_methods):
        """Test search API presents data meaningfully."""
        mock_database_api_client.search.return_value = [
            {
                "id": "R.AIR.001",
                "title": "AI Model Bias Risk",
                "type": "risk",
                "description": "Risk of bias in AI model outputs",
            },
            {
                "id": "C.AIIM.1",
                "title": "Model Validation Controls",
                "type": "control",
                "description": "Controls for validating AI models",
            },
        ]

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/search?q=bias")

            assert response.status_code == 200
            data = response.get_json()
            # Search API returns results directly as a list
            assert len(data) == 2
            assert data[0]["type"] == "risk"
            assert data[1]["type"] == "control"

    def test_api_stats_presentation(self, client, mock_database_api_client, patch_api_client_methods):
        """Test stats API presents data meaningfully."""
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
            assert data["total_risks"] == 25
            assert data["total_controls"] == 18
            assert data["total_questions"] == 42
            assert data["active_risks"] == 20

    def test_api_network_presentation(self, client, mock_database_api_client, patch_api_client_methods):
        """Test network API presents data meaningfully."""
        mock_database_api_client.session.get.return_value.json.return_value = {
            "risk_control_links": [
                {"risk_id": "R.AIR.001", "control_id": "C.AIIM.1", "strength": "strong"}
            ],
            "question_risk_links": [
                {
                    "question_id": "Q.CIR.1.1",
                    "risk_id": "R.AIR.001",
                    "relevance": "high",
                }
            ],
            "question_control_links": [
                {
                    "question_id": "Q.CIR.1.1",
                    "control_id": "C.AIIM.1",
                    "relevance": "medium",
                }
            ],
        }
        mock_database_api_client.session.get.return_value.status_code = 200

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/network")

            assert response.status_code == 200
            data = response.get_json()
            assert "risk_control_links" in data
            assert "question_risk_links" in data
            assert "question_control_links" in data
            assert len(data["risk_control_links"]) == 1

    def test_api_gaps_presentation(self, client, mock_database_api_client, patch_api_client_methods):
        """Test gaps API presents data meaningfully."""
        mock_database_api_client.session.get.return_value.json.return_value = {
            "summary": {
                "total_risks": 25,
                "total_controls": 18,
                "unmapped_risks": 5,
                "unmapped_controls": 2,
                "control_coverage_pct": 80.0,
                "control_utilization_pct": 75.0,
            },
            "unmapped_risks": [
                {"id": "R.AIR.003", "title": "Unmapped Risk", "category": "AI Risk"}
            ],
            "unmapped_controls": [
                {
                    "id": "C.AIIM.3",
                    "title": "Unmapped Control",
                    "domain": "AI Implementation",
                }
            ],
        }
        mock_database_api_client.session.get.return_value.status_code = 200

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/gaps")

            assert response.status_code == 200
            data = response.get_json()
            assert data["summary"]["total_risks"] == 25
            assert data["summary"]["unmapped_risks"] == 5
            assert len(data["unmapped_risks"]) == 1
            assert data["unmapped_risks"][0]["title"] == "Unmapped Risk"

    def test_api_risk_detail_presentation(self, client, mock_database_api_client, patch_api_client_methods):
        """Test risk detail API presents data meaningfully."""
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
            assert data["risk"]["id"] == "R.AIR.001"
            assert data["risk"]["title"] == "AI Model Bias Risk"
            assert len(data["associated_controls"]) == 1
            assert len(data["associated_questions"]) == 1

    def test_api_control_detail_presentation(self, client, mock_database_api_client, patch_api_client_methods):
        """Test control detail API presents data meaningfully."""
        mock_database_api_client.get_control_detail.return_value = {
            "control": {
                "id": "C.AIIM.1",
                "title": "Model Validation Controls",
                "description": "Controls for validating AI models",
                "domain": "AI Implementation",
                "type": "Preventive",
                "status": "Implemented",
            },
            "associated_risks": [
                {"id": "R.AIR.001", "title": "AI Model Bias Risk", "severity": "High"}
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
            response = client.get("/api/control/C.AIIM.1")

            assert response.status_code == 200
            data = response.get_json()
            assert data["control"]["id"] == "C.AIIM.1"
            assert data["control"]["title"] == "Model Validation Controls"
            assert len(data["associated_risks"]) == 1
            assert len(data["associated_questions"]) == 1

    def test_api_question_detail_presentation(self, client, mock_database_api_client, patch_api_client_methods):
        """Test question detail API presents data meaningfully."""
        mock_database_api_client.get_question_detail.return_value = {
            "question": {
                "id": "Q.CIR.1.1",
                "question": "How is AI model bias monitored?",
                "category": "AI Risk",
                "type": "Assessment",
                "priority": "High",
            },
            "associated_risks": [
                {"id": "R.AIR.001", "title": "AI Model Bias Risk", "severity": "High"}
            ],
            "associated_controls": [
                {
                    "id": "C.AIIM.1",
                    "title": "Model Validation Controls",
                    "status": "Implemented",
                }
            ],
        }

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/question/Q.CIR.1.1")

            assert response.status_code == 200
            data = response.get_json()
            assert data["question"]["id"] == "Q.CIR.1.1"
            assert data["question"]["question"] == "How is AI model bias monitored?"
            assert len(data["associated_risks"]) == 1
            assert len(data["associated_controls"]) == 1

    def test_api_managing_roles_presentation(self, client, mock_database_api_client, patch_api_client_methods):
        """Test managing roles API presents data meaningfully."""
        mock_database_api_client.get_managing_roles.return_value = [
            {
                "id": "MR.001",
                "title": "AI Risk Manager",
                "description": "Manages AI-related risks and controls",
                "department": "Risk Management",
                "status": "Active",
            },
            {
                "id": "MR.002",
                "title": "Data Governance Officer",
                "description": "Oversees data governance and privacy controls",
                "department": "Data Management",
                "status": "Active",
            },
        ]

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/managing-roles")

            assert response.status_code == 200
            data = response.get_json()
            assert len(data) == 2
            assert data[0]["id"] == "MR.001"
            assert data[0]["title"] == "AI Risk Manager"
            assert data[1]["id"] == "MR.002"
            assert data[1]["title"] == "Data Governance Officer"

    def test_api_file_metadata_presentation(self, client, mock_database_api_client, patch_api_client_methods):
        """Test file metadata API presents data meaningfully."""
        mock_database_api_client.get_file_metadata.return_value = {
            "files": [
                {
                    "name": "AI_Definitions_and_Taxonomy_V1.xlsx",
                    "type": "Excel",
                    "size": "2.5MB",
                    "last_modified": "2024-01-15T10:30:00Z",
                    "description": "AI definitions and taxonomy",
                },
                {
                    "name": "AIML_RISK_TAXONOMY_V6.xlsx",
                    "type": "Excel",
                    "size": "1.8MB",
                    "last_modified": "2024-01-20T14:45:00Z",
                    "description": "AI/ML risk taxonomy",
                },
            ]
        }

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/file-metadata")

            assert response.status_code == 200
            data = response.get_json()
            assert len(data["files"]) == 2
            assert data["files"][0]["name"] == "AI_Definitions_and_Taxonomy_V1.xlsx"
            assert data["files"][1]["name"] == "AIML_RISK_TAXONOMY_V6.xlsx"

    def test_api_health_presentation(self, client, mock_database_api_client, patch_api_client_methods):
        """Test health API presents system status meaningfully."""
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
            assert data["status"] == "healthy"
            assert data["database_service"]["status"] == "healthy"
            assert data["dashboard_service"]["status"] == "healthy"

    def test_api_pagination_presentation(self, client, mock_database_api_client, patch_api_client_methods):
        """Test API pagination presents data meaningfully."""
        mock_database_api_client.get_risks.return_value = [
            {"id": f"R.AIR.{i:03d}", "title": f"Risk {i}"} for i in range(5)
        ]

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/risks?limit=5&offset=10")

            assert response.status_code == 200
            data = response.get_json()
            assert len(data) == 5
            mock_database_api_client.get_risks.assert_called_with(
                limit=5, offset=10, category=None
            )

    def test_api_filtering_presentation(self, client, mock_database_api_client, patch_api_client_methods):
        """Test API filtering presents data meaningfully."""
        mock_database_api_client.get_risks.return_value = [
            {"id": "R.AIR.001", "category": "AI Risk", "title": "AI Model Bias Risk"}
        ]

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/risks?category=AI Risk")

            assert response.status_code == 200
            data = response.get_json()
            assert len(data) == 1
            assert data[0]["category"] == "AI Risk"
            mock_database_api_client.get_risks.assert_called_with(
                limit=100, offset=0, category="AI Risk"
            )
