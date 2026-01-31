"""
Unit tests for the DatabaseAPIClient class.

Tests the API client functionality for communicating with the database service.
"""

import os
from unittest.mock import patch, Mock

import pytest
import requests
from app import DatabaseAPIClient


@pytest.mark.unit
@pytest.mark.api
class TestDatabaseAPIClient:
    """Test cases for DatabaseAPIClient class."""

    # Use environment variable for database port
    DATABASE_PORT = os.getenv("DATABASE_PORT")
    BASE_URL = f"http://localhost:{DATABASE_PORT}"

    def test_init_with_base_url(self):
        """Test initialization with base URL."""
        base_url = self.BASE_URL
        client = DatabaseAPIClient(base_url)

        assert client.base_url == base_url
        assert isinstance(client.session, requests.Session)
        assert client.session.timeout == 30  # Default timeout

    def test_init_with_trailing_slash(self):
        """Test initialization with URL containing trailing slash."""
        base_url = f"http://localhost:{self.DATABASE_PORT}/"
        client = DatabaseAPIClient(base_url)

        assert client.base_url == self.BASE_URL  # Should be stripped

    def test_health_check_success(self):
        """Test successful health check."""
        client = DatabaseAPIClient(self.BASE_URL)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "healthy",
            "database_connected": True,
        }
        mock_response.raise_for_status.return_value = None

        with patch.object(
            client.session, "get", return_value=mock_response
        ) as mock_get:
            result = client.health_check()

            mock_get.assert_called_once_with(f"{self.BASE_URL}/api/health")
            assert result == {"status": "healthy", "database_connected": True}

    def test_health_check_failure(self):
        """Test health check with connection failure."""
        client = DatabaseAPIClient(self.BASE_URL)

        with patch.object(
            client.session,
            "get",
            side_effect=requests.ConnectionError("Connection failed"),
        ):
            result = client.health_check()

            assert result["status"] == "unhealthy"
            assert "error" in result
            assert "Connection failed" in result["error"]

    def test_get_risks_success(self):
        """Test successful risks retrieval."""
        client = DatabaseAPIClient(self.BASE_URL)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "risks": [{"id": "AIR.001", "title": "Test Risk"}],
            "total": 1,
        }
        mock_response.raise_for_status.return_value = None

        with patch.object(
            client.session, "get", return_value=mock_response
        ) as mock_get:
            result = client.get_risks(limit=10, offset=0, category="Privacy")

            mock_get.assert_called_once_with(
                f"{self.BASE_URL}/api/risks",
                params={"limit": 10, "offset": 0, "category": "Privacy"},
            )
            assert result == {
                "risks": [{"id": "AIR.001", "title": "Test Risk"}],
                "total": 1,
            }

    def test_get_risks_with_default_params(self):
        """Test risks retrieval with default parameters."""
        client = DatabaseAPIClient(self.BASE_URL)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"risks": [], "total": 0}
        mock_response.raise_for_status.return_value = None

        with patch.object(
            client.session, "get", return_value=mock_response
        ) as mock_get:
            result = client.get_risks()

            mock_get.assert_called_once_with(
                f"{self.BASE_URL}/api/risks", params={"limit": 100, "offset": 0}
            )
            assert result == {"risks": [], "total": 0}

    def test_get_risks_failure(self):
        """Test risks retrieval with API failure."""
        client = DatabaseAPIClient(self.BASE_URL)

        with patch.object(
            client.session, "get", side_effect=requests.RequestException("API Error")
        ):
            result = client.get_risks()

            assert result == []

    def test_get_risks_summary_success(self):
        """Test successful risks summary retrieval."""
        client = DatabaseAPIClient(self.BASE_URL)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "details": [{"category": "Privacy", "count": 5}]
        }
        mock_response.raise_for_status.return_value = None

        with patch.object(
            client.session, "get", return_value=mock_response
        ) as mock_get:
            result = client.get_risks_summary()

            mock_get.assert_called_once_with(f"{self.BASE_URL}/api/risks/summary")
            assert result == {"details": [{"category": "Privacy", "count": 5}]}

    def test_get_risks_summary_failure(self):
        """Test risks summary retrieval with API failure."""
        client = DatabaseAPIClient(self.BASE_URL)

        with patch.object(
            client.session, "get", side_effect=requests.RequestException("API Error")
        ):
            result = client.get_risks_summary()

            assert result == {"details": []}

    def test_get_controls_success(self):
        """Test successful controls retrieval."""
        client = DatabaseAPIClient(self.BASE_URL)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "controls": [{"id": "AIGPC.1", "title": "Test Control"}],
            "total": 1,
        }
        mock_response.raise_for_status.return_value = None

        with patch.object(
            client.session, "get", return_value=mock_response
        ) as mock_get:
            result = client.get_controls(limit=10, offset=0, domain="Protect")

            mock_get.assert_called_once_with(
                f"{self.BASE_URL}/api/controls",
                params={"limit": 10, "offset": 0, "domain": "Protect"},
            )
            assert result == {
                "controls": [{"id": "AIGPC.1", "title": "Test Control"}],
                "total": 1,
            }

    def test_get_controls_failure(self):
        """Test controls retrieval with API failure."""
        client = DatabaseAPIClient(self.BASE_URL)

        with patch.object(
            client.session, "get", side_effect=requests.RequestException("API Error")
        ):
            result = client.get_controls()

            assert result == []

    def test_get_questions_success(self):
        """Test successful questions retrieval."""
        client = DatabaseAPIClient(self.BASE_URL)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "questions": [{"id": "Q1", "text": "Test Question?"}],
            "total": 1,
        }
        mock_response.raise_for_status.return_value = None

        with patch.object(
            client.session, "get", return_value=mock_response
        ) as mock_get:
            result = client.get_questions(limit=10, offset=0, category="Privacy")

            mock_get.assert_called_once_with(
                f"{self.BASE_URL}/api/questions",
                params={"limit": 10, "offset": 0, "category": "Privacy"},
            )
            assert result == {
                "questions": [{"id": "Q1", "text": "Test Question?"}],
                "total": 1,
            }

    def test_get_questions_failure(self):
        """Test questions retrieval with API failure."""
        client = DatabaseAPIClient(self.BASE_URL)

        with patch.object(
            client.session, "get", side_effect=requests.RequestException("API Error")
        ):
            result = client.get_questions()

            assert result == []

    def test_get_relationships_success(self):
        """Test successful relationships retrieval."""
        client = DatabaseAPIClient(self.BASE_URL)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "relationships": [{"risk_id": "AIR.001", "control_id": "AIGPC.1"}]
        }
        mock_response.raise_for_status.return_value = None

        with patch.object(
            client.session, "get", return_value=mock_response
        ) as mock_get:
            result = client.get_relationships(relationship_type="mitigates", limit=100)

            mock_get.assert_called_once_with(
                f"{self.BASE_URL}/api/relationships",
                params={"limit": 100, "relationship_type": "mitigates"},
            )
            assert result == {
                "relationships": [{"risk_id": "AIR.001", "control_id": "AIGPC.1"}]
            }

    def test_get_relationships_failure(self):
        """Test relationships retrieval with API failure."""
        client = DatabaseAPIClient(self.BASE_URL)

        with patch.object(
            client.session, "get", side_effect=requests.RequestException("API Error")
        ):
            result = client.get_relationships()

            assert result == []

    def test_search_success(self):
        """Test successful search."""
        client = DatabaseAPIClient(self.BASE_URL)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "query": "test",
            "results": [{"type": "risk", "id": "AIR.001", "title": "Test Risk"}],
        }
        mock_response.raise_for_status.return_value = None

        with patch.object(
            client.session, "get", return_value=mock_response
        ) as mock_get:
            result = client.search(query="test", limit=50)

            mock_get.assert_called_once_with(
                f"{self.BASE_URL}/api/search", params={"q": "test", "limit": 50}
            )
            assert result == {
                "query": "test",
                "results": [{"type": "risk", "id": "AIR.001", "title": "Test Risk"}],
            }

    def test_search_failure(self):
        """Test search with API failure."""
        client = DatabaseAPIClient(self.BASE_URL)

        with patch.object(
            client.session, "get", side_effect=requests.RequestException("API Error")
        ):
            result = client.search(query="test")

            assert result == {"query": "test", "results": []}

    def test_get_stats_success(self):
        """Test successful stats retrieval."""
        client = DatabaseAPIClient(self.BASE_URL)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "total_risks": 10,
            "total_controls": 8,
            "total_questions": 15,
        }
        mock_response.raise_for_status.return_value = None

        with patch.object(
            client.session, "get", return_value=mock_response
        ) as mock_get:
            result = client.get_stats()

            mock_get.assert_called_once_with(f"{self.BASE_URL}/api/stats")
            assert result == {
                "total_risks": 10,
                "total_controls": 8,
                "total_questions": 15,
            }

    def test_get_stats_failure(self):
        """Test stats retrieval with API failure."""
        client = DatabaseAPIClient(self.BASE_URL)

        with patch.object(
            client.session, "get", side_effect=requests.RequestException("API Error")
        ):
            result = client.get_stats()

            assert result == {}

    def test_get_file_metadata_success(self):
        """Test successful file metadata retrieval."""
        client = DatabaseAPIClient(self.BASE_URL)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "risks": {"version": "1.0", "last_updated": "2025-01-01T00:00:00Z"}
        }
        mock_response.raise_for_status.return_value = None

        with patch.object(
            client.session, "get", return_value=mock_response
        ) as mock_get:
            result = client.get_file_metadata()

            mock_get.assert_called_once_with(f"{self.BASE_URL}/api/file-metadata")
            assert result == {
                "risks": {"version": "1.0", "last_updated": "2025-01-01T00:00:00Z"}
            }

    def test_get_file_metadata_failure(self):
        """Test file metadata retrieval with API failure."""
        client = DatabaseAPIClient(self.BASE_URL)

        with patch.object(
            client.session, "get", side_effect=requests.RequestException("API Error")
        ):
            result = client.get_file_metadata()

            assert result == {}

    def test_get_risk_detail_success(self):
        """Test successful risk detail retrieval."""
        client = DatabaseAPIClient(self.BASE_URL)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "AIR.001",
            "title": "Test Risk",
            "description": "Test Description",
        }
        mock_response.raise_for_status.return_value = None

        with patch.object(
            client.session, "get", return_value=mock_response
        ) as mock_get:
            result = client.get_risk_detail("AIR.001")

            mock_get.assert_called_once_with(f"{self.BASE_URL}/api/risk/AIR.001")
            assert result == {
                "id": "AIR.001",
                "title": "Test Risk",
                "description": "Test Description",
            }

    def test_get_risk_detail_failure(self):
        """Test risk detail retrieval with API failure."""
        client = DatabaseAPIClient(self.BASE_URL)

        with patch.object(
            client.session, "get", side_effect=requests.RequestException("API Error")
        ):
            result = client.get_risk_detail("AIR.001")

            assert result == {"error": "API Error"}

    def test_get_control_detail_success(self):
        """Test successful control detail retrieval."""
        client = DatabaseAPIClient(self.BASE_URL)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "AIGPC.1",
            "title": "Test Control",
            "description": "Test Description",
        }
        mock_response.raise_for_status.return_value = None

        with patch.object(
            client.session, "get", return_value=mock_response
        ) as mock_get:
            result = client.get_control_detail("AIGPC.1")

            mock_get.assert_called_once_with(f"{self.BASE_URL}/api/control/AIGPC.1")
            assert result == {
                "id": "AIGPC.1",
                "title": "Test Control",
                "description": "Test Description",
            }

    def test_get_control_detail_failure(self):
        """Test control detail retrieval with API failure."""
        client = DatabaseAPIClient(self.BASE_URL)

        with patch.object(
            client.session, "get", side_effect=requests.RequestException("API Error")
        ):
            result = client.get_control_detail("AIGPC.1")

            assert result == {"error": "API Error"}

    def test_get_question_detail_success(self):
        """Test successful question detail retrieval."""
        client = DatabaseAPIClient(self.BASE_URL)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "Q1",
            "text": "Test Question?",
            "category": "Privacy",
        }
        mock_response.raise_for_status.return_value = None

        with patch.object(
            client.session, "get", return_value=mock_response
        ) as mock_get:
            result = client.get_question_detail("Q1")

            mock_get.assert_called_once_with(f"{self.BASE_URL}/api/question/Q1")
            assert result == {
                "id": "Q1",
                "text": "Test Question?",
                "category": "Privacy",
            }

    def test_get_question_detail_failure(self):
        """Test question detail retrieval with API failure."""
        client = DatabaseAPIClient(self.BASE_URL)

        with patch.object(
            client.session, "get", side_effect=requests.RequestException("API Error")
        ):
            result = client.get_question_detail("Q1")

            assert result == {"error": "API Error"}

    def test_get_managing_roles_success(self):
        """Test successful managing roles retrieval."""
        client = DatabaseAPIClient(self.BASE_URL)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "managing_roles": ["Data Officer", "Security Officer", "ML Engineer"]
        }
        mock_response.raise_for_status.return_value = None

        with patch.object(
            client.session, "get", return_value=mock_response
        ) as mock_get:
            result = client.get_managing_roles()

            mock_get.assert_called_once_with(f"{self.BASE_URL}/api/managing-roles")
            assert result == {
                "managing_roles": ["Data Officer", "Security Officer", "ML Engineer"]
            }

    def test_get_managing_roles_failure(self):
        """Test managing roles retrieval with API failure."""
        client = DatabaseAPIClient(self.BASE_URL)

        with patch.object(
            client.session, "get", side_effect=requests.RequestException("API Error")
        ):
            result = client.get_managing_roles()

            assert result == {"managing_roles": []}

    def test_custom_timeout_configuration(self):
        """Test custom timeout configuration."""
        client = DatabaseAPIClient(self.BASE_URL)

        # Test with custom timeout
        client.session.timeout = 60
        assert client.session.timeout == 60
