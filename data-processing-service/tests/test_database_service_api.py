"""
Test cases for database service API endpoints.

Tests that verify database service API endpoints work correctly and catch
common issues like SQL syntax errors, missing columns, and data structure problems.
"""

import os
import pytest
import requests
import sys
from pathlib import Path

# Add shared-services to path to import CommonConfigManager
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared-services"))
from common_config import CommonConfigManager

# Load configuration at module level
config_manager = CommonConfigManager()
DATABASE_PORT = config_manager.get_port("database_service")
DATABASE_URL = f"http://localhost:{DATABASE_PORT}"


class TestDatabaseServiceAPI:
    """Test cases for database service API endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test."""
        self.base_url = DATABASE_URL
        self.test_control_id = "C.AGAS.1"
        self.test_risk_id = "R.AIR.052"
        self.test_question_id = "Q.CRA.6.1"

    def test_control_detail_endpoint_success(self):
        """Test that control detail endpoint returns proper data structure."""
        try:
            response = requests.get(
                f"{self.base_url}/api/control/{self.test_control_id}"
            )

            if response.status_code == 200:
                data = response.json()

                # Verify response structure
                assert "control" in data
                assert "associated_risks" in data
                assert "associated_questions" in data

                # Verify control data structure
                control = data["control"]
                required_fields = [
                    "id",
                    "title",
                    "description",
                    "domain",
                    "type",
                    "maturity",
                ]
                for field in required_fields:
                    assert field in control, f"Missing required field: {field}"
                    assert control[field] is not None, f"Field {field} is None"
                    assert (
                        control[field] != "undefined"
                    ), f"Field {field} is 'undefined'"

                # Verify associated risks structure
                for risk in data["associated_risks"]:
                    assert "id" in risk
                    assert "title" in risk
                    assert "description" in risk
                    assert risk["id"] is not None
                    assert risk["title"] is not None
                    assert risk["description"] is not None

                # Verify associated questions structure
                for question in data["associated_questions"]:
                    assert "id" in question
                    assert "text" in question
                    assert question["id"] is not None
                    assert question["text"] is not None

            elif response.status_code == 500:
                pytest.fail(
                    f"Control detail endpoint returned 500 error: {response.text}"
                )
            else:
                pytest.fail(
                    f"Control detail endpoint returned {response.status_code}: {response.text}"
                )

        except requests.exceptions.ConnectionError:
            pytest.skip("Database service not running")
        except Exception as e:
            pytest.fail(f"Unexpected error testing control detail endpoint: {e}")

    def test_risk_detail_endpoint_success(self):
        """Test that risk detail endpoint returns proper data structure."""
        try:
            response = requests.get(f"{self.base_url}/api/risk/{self.test_risk_id}")

            if response.status_code == 200:
                data = response.json()

                # Verify response structure
                assert "risk" in data
                assert "associated_controls" in data
                assert "associated_questions" in data

                # Verify risk data structure
                risk = data["risk"]
                required_fields = ["id", "title", "description"]
                for field in required_fields:
                    assert field in risk, f"Missing required field: {field}"
                    assert risk[field] is not None, f"Field {field} is None"
                    assert risk[field] != "undefined", f"Field {field} is 'undefined'"

            elif response.status_code == 500:
                pytest.fail(f"Risk detail endpoint returned 500 error: {response.text}")
            else:
                pytest.fail(
                    f"Risk detail endpoint returned {response.status_code}: {response.text}"
                )

        except requests.exceptions.ConnectionError:
            pytest.skip("Database service not running")
        except Exception as e:
            pytest.fail(f"Unexpected error testing risk detail endpoint: {e}")

    def test_question_detail_endpoint_success(self):
        """Test that question detail endpoint returns proper data structure."""
        try:
            response = requests.get(
                f"{self.base_url}/api/question/{self.test_question_id}"
            )

            if response.status_code == 200:
                data = response.json()

                # Verify response structure
                assert "question" in data
                assert "associated_risks" in data
                assert "associated_controls" in data

                # Verify question data structure
                question = data["question"]
                required_fields = ["id", "text"]
                for field in required_fields:
                    assert field in question, f"Missing required field: {field}"
                    assert question[field] is not None, f"Field {field} is None"
                    assert (
                        question[field] != "undefined"
                    ), f"Field {field} is 'undefined'"

            elif response.status_code == 500:
                pytest.fail(
                    f"Question detail endpoint returned 500 error: {response.text}"
                )
            else:
                pytest.fail(
                    f"Question detail endpoint returned {response.status_code}: {response.text}"
                )

        except requests.exceptions.ConnectionError:
            pytest.skip("Database service not running")
        except Exception as e:
            pytest.fail(f"Unexpected error testing question detail endpoint: {e}")

    def test_api_endpoints_no_sql_errors(self):
        """Test that all API endpoints don't have SQL syntax errors."""
        endpoints = [
            f"/api/control/{self.test_control_id}",
            f"/api/risk/{self.test_risk_id}",
            f"/api/question/{self.test_question_id}",
            "/api/risks",
            "/api/controls",
            "/api/questions",
            "/api/stats",
            "/api/relationships",
        ]

        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}")

                if response.status_code == 500:
                    # Check if it's a SQL error
                    error_text = response.text.lower()
                    if any(
                        keyword in error_text
                        for keyword in ["sql", "database", "column", "table", "syntax"]
                    ):
                        pytest.fail(
                            f"SQL error in endpoint {endpoint}: {response.text}"
                        )
                    else:
                        pytest.fail(
                            f"500 error in endpoint {endpoint}: {response.text}"
                        )
                elif response.status_code not in [200, 404]:
                    pytest.fail(
                        f"Unexpected status code {response.status_code} for endpoint {endpoint}: {response.text}"
                    )

            except requests.exceptions.ConnectionError:
                pytest.skip("Database service not running")
            except Exception as e:
                pytest.fail(f"Unexpected error testing endpoint {endpoint}: {e}")

    def test_control_endpoint_specific_columns(self):
        """Test that control endpoint doesn't reference non-existent columns."""
        try:
            response = requests.get(
                f"{self.base_url}/api/control/{self.test_control_id}"
            )

            if response.status_code == 500:
                error_text = response.text.lower()
                # Check for common column name errors
                if "no such column" in error_text:
                    pytest.fail(
                        f"Database column error in control endpoint: {response.text}"
                    )
                else:
                    pytest.fail(f"500 error in control endpoint: {response.text}")

        except requests.exceptions.ConnectionError:
            pytest.skip("Database service not running")
        except Exception as e:
            pytest.fail(f"Unexpected error testing control endpoint: {e}")

    def test_api_response_data_quality(self):
        """Test that API responses don't contain undefined or null values inappropriately."""
        try:
            # Test controls endpoint
            response = requests.get(f"{self.base_url}/api/controls")
            if response.status_code == 200:
                data = response.json()
                if "details" in data:
                    for control in data["details"]:
                        # Check for undefined values in key fields
                        for field in ["control_id", "control_title", "control_type"]:
                            if field in control:
                                assert (
                                    control[field] is not None
                                ), f"Field {field} is None in control"
                                assert (
                                    control[field] != "undefined"
                                ), f"Field {field} is 'undefined' in control"
                                assert (
                                    control[field] != ""
                                ), f"Field {field} is empty string in control"

            # Test risks endpoint
            response = requests.get(f"{self.base_url}/api/risks")
            if response.status_code == 200:
                data = response.json()
                if "details" in data:
                    for risk in data["details"]:
                        # Check for undefined values in key fields
                        for field in ["risk_id", "risk_title"]:
                            if field in risk:
                                assert (
                                    risk[field] is not None
                                ), f"Field {field} is None in risk"
                                assert (
                                    risk[field] != "undefined"
                                ), f"Field {field} is 'undefined' in risk"
                                assert (
                                    risk[field] != ""
                                ), f"Field {field} is empty string in risk"

        except requests.exceptions.ConnectionError:
            pytest.skip("Database service not running")
        except Exception as e:
            pytest.fail(f"Unexpected error testing API data quality: {e}")

    @pytest.mark.parametrize(
        "entity_type,entity_id",
        [
            ("control", "C.AGAS.1"),
            ("risk", "R.AIR.052"),
            ("question", "Q.CRA.6.1"),
        ],
    )
    def test_entity_detail_endpoints_consistency(self, entity_type, entity_id):
        """Test that entity detail endpoints return consistent data structures."""
        try:
            response = requests.get(f"{self.base_url}/api/{entity_type}/{entity_id}")

            if response.status_code == 200:
                data = response.json()

                # Verify the main entity object exists
                assert entity_type in data, f"Missing {entity_type} object in response"
                entity = data[entity_type]

                # Verify ID field exists and matches
                assert "id" in entity, f"Missing id field in {entity_type}"
                assert entity["id"] == entity_id, f"ID mismatch in {entity_type}"

                # Verify no undefined values in the main entity
                for key, value in entity.items():
                    if value is not None:
                        assert (
                            value != "undefined"
                        ), f"Field {key} is 'undefined' in {entity_type}"

            elif response.status_code == 500:
                pytest.fail(
                    f"{entity_type.title()} detail endpoint returned 500 error: {response.text}"
                )
            else:
                pytest.fail(
                    f"{entity_type.title()} detail endpoint returned {response.status_code}: {response.text}"
                )

        except requests.exceptions.ConnectionError:
            pytest.skip("Database service not running")
        except Exception as e:
            pytest.fail(f"Unexpected error testing {entity_type} detail endpoint: {e}")
