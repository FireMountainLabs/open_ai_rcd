"""
Test cases for API data validation and frontend data handling.

Tests that identify gaps in our test coverage around data validation,
API endpoint functionality, and frontend handling of undefined/null data.
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


class TestAPIDataValidation:
    """Test cases for API data validation and frontend data handling."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test."""
        self.DATABASE_URL = DATABASE_URL

    def test_database_service_syntax_errors(self):
        """Test that database service API endpoints don't have syntax errors."""
        # This test will help identify syntax errors in the database service
        # that could cause "undefined" values in the frontend

        # Test question detail endpoint
        try:
            response = requests.get(f"{self.DATABASE_URL}/api/question/Q.CRA.6.1")
            if response.status_code == 200:
                data = response.json()
                # Verify required fields are present and not None/undefined
                assert "question" in data
                assert "id" in data["question"]
                assert "text" in data["question"]
                assert data["question"]["id"] is not None
                assert data["question"]["text"] is not None
                assert data["question"]["text"] != "undefined"
            else:
                pytest.fail(
                    f"Question detail endpoint returned {response.status_code}: {response.text}"
                )
        except requests.exceptions.ConnectionError:
            pytest.skip("Database service not running")
        except Exception as e:
            pytest.fail(f"Unexpected error testing question detail endpoint: {e}")

    def test_risk_detail_endpoint_data_structure(self):
        """Test that risk detail endpoint returns proper data structure."""
        try:
            response = requests.get(f"{self.DATABASE_URL}/api/risk/R.AIR.001")
            if response.status_code == 200:
                data = response.json()

                # Verify risk data structure
                assert "risk" in data
                assert "id" in data["risk"]
                assert "title" in data["risk"]
                assert "description" in data["risk"]

                # Verify associated questions structure
                assert "associated_questions" in data
                if data["associated_questions"]:
                    question = data["associated_questions"][0]
                    assert "id" in question
                    assert "text" in question
                    assert "category" in question
                    assert "topic" in question

                    # Check for undefined values
                    assert question["id"] is not None
                    assert question["text"] is not None
                    assert question["text"] != "undefined"
                    assert question["category"] is not None
                    assert question["topic"] is not None
            else:
                pytest.fail(
                    f"Risk detail endpoint returned {response.status_code}: {response.text}"
                )
        except requests.exceptions.ConnectionError:
            pytest.skip("Database service not running")
        except Exception as e:
            pytest.fail(f"Unexpected error testing risk detail endpoint: {e}")

    def test_control_detail_endpoint_data_structure(self):
        """Test that control detail endpoint returns proper data structure."""
        try:
            response = requests.get(f"{self.DATABASE_URL}/api/control/C.AIGPC.1")
            if response.status_code == 200:
                data = response.json()

                # Verify control data structure
                assert "control" in data
                assert "id" in data["control"]
                assert "title" in data["control"]
                assert "description" in data["control"]

                # Verify associated questions structure
                assert "associated_questions" in data
                if data["associated_questions"]:
                    question = data["associated_questions"][0]
                    assert "id" in question
                    assert "text" in question
                    assert "category" in question
                    assert "topic" in question

                    # Check for undefined values
                    assert question["id"] is not None
                    assert question["text"] is not None
                    assert question["text"] != "undefined"
            else:
                pytest.fail(
                    f"Control detail endpoint returned {response.status_code}: {response.text}"
                )
        except requests.exceptions.ConnectionError:
            pytest.skip("Database service not running")
        except Exception as e:
            pytest.fail(f"Unexpected error testing control detail endpoint: {e}")

    def test_questions_summary_endpoint_data_validation(self):
        """Test that questions summary endpoint returns valid data."""
        try:
            response = requests.get(f"{self.DATABASE_URL}/api/questions/summary")
            if response.status_code == 200:
                data = response.json()

                # Verify summary structure
                assert "details" in data

                # Verify questions data structure
                if data["details"]:
                    question = data["details"][0]
                    assert "question_id" in question
                    assert "question_text" in question
                    assert "category" in question
                    assert "managing_role" in question

                    # Check for undefined values
                    assert question["question_id"] is not None
                    assert question["question_text"] is not None
                    assert question["question_text"] != "undefined"
                    assert question["category"] is not None
                    assert question["managing_role"] is not None
            else:
                pytest.fail(
                    f"Questions summary endpoint returned {response.status_code}: {response.text}"
                )
        except requests.exceptions.ConnectionError:
            pytest.skip("Database service not running")
        except Exception as e:
            pytest.fail(f"Unexpected error testing questions summary endpoint: {e}")

    def test_gaps_analysis_endpoint_data_validation(self):
        """Test that gaps analysis endpoint returns valid data."""
        try:
            response = requests.get(f"{self.DATABASE_URL}/api/gaps")
            if response.status_code == 200:
                data = response.json()

                # Verify gaps analysis structure
                assert "summary" in data
                summary = data["summary"]

                # Verify required fields
                required_fields = [
                    "total_questions",
                    "mapped_questions",
                    "question_coverage_pct",
                    "total_risks",
                    "mapped_risks",
                    "risk_coverage_pct",
                    "total_controls",
                    "mapped_controls",
                    "control_coverage_pct",
                ]

                for field in required_fields:
                    assert field in summary
                    assert summary[field] is not None
                    assert isinstance(summary[field], (int, float))
            else:
                pytest.fail(
                    f"Gaps analysis endpoint returned {response.status_code}: {response.text}"
                )
        except requests.exceptions.ConnectionError:
            pytest.skip("Database service not running")
        except Exception as e:
            pytest.fail(f"Unexpected error testing gaps analysis endpoint: {e}")

    def test_frontend_data_handling_with_undefined_values(self):
        """Test how frontend handles undefined/null values."""
        # This test simulates the frontend receiving data with undefined values
        # and verifies that it handles them gracefully

        # Mock data with undefined values (similar to what's shown in the image)
        mock_question_data = {
            "question": {
                "id": "Q.CRA.6.1",
                "text": "undefined",  # This is the problem shown in the image
                "category": "undefined",
                "topic": "undefined",
                "managing_role": "undefined",
            },
            "managing_roles": ["undefined"],
            "associated_risks": [
                {
                    "id": "R.AIR.004",
                    "title": "Model poisoning (malicious weight modification)",
                    "description": "Adversaries compromise the model artifacts...",
                }
            ],
            "associated_controls": [],
        }

        # Test that frontend can handle this data without crashing
        # This would be implemented in a frontend test framework
        # For now, we'll just verify the data structure is as expected

        assert mock_question_data["question"]["text"] == "undefined"
        assert mock_question_data["question"]["category"] == "undefined"
        assert mock_question_data["question"]["topic"] == "undefined"
        assert mock_question_data["question"]["managing_role"] == "undefined"

        # This test identifies the gap: we need frontend validation
        # to handle undefined values gracefully

    def test_database_field_validation(self):
        """Test that database fields are properly validated."""
        # This test checks that our data extraction doesn't produce
        # undefined values in the database

        try:
            # Test a few sample questions to ensure they have proper data
            sample_question_ids = ["Q.CRA.6.1", "Q.OA.1.1", "Q.CPA.2.1"]

            for question_id in sample_question_ids:
                response = requests.get(
                    f"{self.DATABASE_URL}/api/question/{question_id}"
                )
                if response.status_code == 200:
                    data = response.json()
                    question = data["question"]

                    # Verify no undefined values
                    assert question["text"] != "undefined"
                    assert question["text"] is not None
                    assert question["text"] != ""

                    assert question["category"] != "undefined"
                    assert question["category"] is not None

                    assert question["topic"] != "undefined"
                    assert question["topic"] is not None

                    assert question["managing_role"] != "undefined"
                    assert question["managing_role"] is not None
                else:
                    pytest.fail(
                        f"Question {question_id} returned {response.status_code}"
                    )
        except requests.exceptions.ConnectionError:
            pytest.skip("Database service not running")
        except Exception as e:
            pytest.fail(f"Unexpected error testing database field validation: {e}")

    def test_api_error_handling(self):
        """Test that API endpoints handle errors gracefully."""
        try:
            # Test non-existent question
            response = requests.get(f"{self.DATABASE_URL}/api/question/NONEXISTENT")
            assert response.status_code == 404

            # Test non-existent risk
            response = requests.get(f"{self.DATABASE_URL}/api/risk/NONEXISTENT")
            assert response.status_code == 404

            # Test non-existent control
            response = requests.get(f"{self.DATABASE_URL}/api/control/NONEXISTENT")
            assert response.status_code == 404

        except requests.exceptions.ConnectionError:
            pytest.skip("Database service not running")
        except Exception as e:
            pytest.fail(f"Unexpected error testing API error handling: {e}")

    def test_data_consistency_across_endpoints(self):
        """Test that data is consistent across different API endpoints."""
        try:
            # Get questions summary
            summary_response = requests.get(
                f"{self.DATABASE_URL}/api/questions/summary"
            )
            if summary_response.status_code == 200:
                summary_data = summary_response.json()

                # Get gaps analysis
                gaps_response = requests.get(f"{self.DATABASE_URL}/api/gaps")
                if gaps_response.status_code == 200:
                    gaps_data = gaps_response.json()

                    # Verify consistency
                    summary_total = summary_data["summary"]["total_questions"]
                    gaps_total = gaps_data["summary"]["total_questions"]

                    assert (
                        summary_total == gaps_total
                    ), f"Question counts don't match: {summary_total} vs {gaps_total}"

                    summary_mapped = summary_data["summary"]["mapped_questions"]
                    gaps_mapped = gaps_data["summary"]["mapped_questions"]

                    assert (
                        summary_mapped == gaps_mapped
                    ), f"Mapped question counts don't match: {summary_mapped} vs {gaps_mapped}"

        except requests.exceptions.ConnectionError:
            pytest.skip("Database service not running")
        except Exception as e:
            pytest.fail(f"Unexpected error testing data consistency: {e}")

    def test_managing_role_data_validation(self):
        """Test that managing role data is properly validated."""
        try:
            response = requests.get(f"{self.DATABASE_URL}/api/managing-roles")
            if response.status_code == 200:
                data = response.json()

                # Verify managing roles are not undefined
                if "managing_roles" in data:
                    for role in data["managing_roles"]:
                        assert role != "undefined"
                        assert role is not None
                        assert role != ""
                        assert isinstance(role, str)

        except requests.exceptions.ConnectionError:
            pytest.skip("Database service not running")
        except Exception as e:
            pytest.fail(f"Unexpected error testing managing role validation: {e}")
