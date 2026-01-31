"""
End-to-end tests for risks without questions functionality.

This module tests the complete end-to-end workflow of the risks without
questions feature, from database calculation to frontend display.
"""

import os
import pytest
import requests
import time
from unittest.mock import patch


@pytest.mark.e2e
@pytest.mark.risks_without_questions
@pytest.mark.slow
class TestRisksWithoutQuestionsE2E:
    """End-to-end tests for risks without questions functionality."""

    # Use environment variables for ports
    DASHBOARD_PORT = os.getenv("DASHBOARD_PORT")
    DATABASE_PORT = os.getenv("DATABASE_PORT")
    DASHBOARD_URL = f"http://localhost:{DASHBOARD_PORT}"
    DATABASE_URL = f"http://localhost:{DATABASE_PORT}"

    def test_complete_risks_without_questions_workflow(self, launcher_process):
        """Test the complete workflow from database to frontend display."""
        # Wait for services to be ready
        time.sleep(10)

        # 1. Test database service gaps API
        db_response = requests.get(f"{self.DATABASE_URL}/api/gaps", timeout=10)
        assert db_response.status_code == 200
        db_data = db_response.json()

        # Validate database service response
        assert "summary" in db_data
        assert "risks_without_questions" in db_data["summary"]
        assert "risks_without_questions_pct" in db_data["summary"]
        assert "risks_without_questions" in db_data

        # 2. Test dashboard service gaps API proxy
        dashboard_response = requests.get(f"{self.DASHBOARD_URL}/api/gaps", timeout=10)
        assert dashboard_response.status_code == 200
        dashboard_data = dashboard_response.json()

        # Validate dashboard service response matches database service
        assert (
            dashboard_data["summary"]["risks_without_questions"]
            == db_data["summary"]["risks_without_questions"]
        )
        assert (
            dashboard_data["summary"]["risks_without_questions_pct"]
            == db_data["summary"]["risks_without_questions_pct"]
        )
        assert len(dashboard_data["risks_without_questions"]) == len(
            db_data["risks_without_questions"]
        )

        # 4. Test that the data is actually populated (not just placeholders)
        if dashboard_data["summary"]["risks_without_questions"] > 0:
            # Should have actual risk data
            assert len(dashboard_data["risks_without_questions"]) > 0
            risk = dashboard_data["risks_without_questions"][0]
            assert "risk_id" in risk
            assert "risk_title" in risk
            assert "risk_description" in risk

    def test_risks_without_questions_data_consistency_across_services(
        self, launcher_process
    ):
        """Test that risks without questions data is consistent across all services."""
        time.sleep(10)

        # Get data from database service
        db_response = requests.get(f"{self.DATABASE_URL}/api/gaps", timeout=10)
        assert db_response.status_code == 200
        db_data = db_response.json()

        # Get data from dashboard service
        dashboard_response = requests.get(f"{self.DASHBOARD_URL}/api/gaps", timeout=10)
        assert dashboard_response.status_code == 200
        dashboard_data = dashboard_response.json()

        # Compare summary data
        db_summary = db_data["summary"]
        dashboard_summary = dashboard_data["summary"]

        assert db_summary["total_risks"] == dashboard_summary["total_risks"]
        assert (
            db_summary["risks_without_questions"]
            == dashboard_summary["risks_without_questions"]
        )
        assert (
            db_summary["risks_without_questions_pct"]
            == dashboard_summary["risks_without_questions_pct"]
        )

        # Compare risks without questions lists
        db_risks = db_data["risks_without_questions"]
        dashboard_risks = dashboard_data["risks_without_questions"]

        assert len(db_risks) == len(dashboard_risks)

        # Compare individual risk data
        for i, (db_risk, dashboard_risk) in enumerate(zip(db_risks, dashboard_risks)):
            assert db_risk["risk_id"] == dashboard_risk["risk_id"]
            assert db_risk["risk_title"] == dashboard_risk["risk_title"]
            assert db_risk["risk_description"] == dashboard_risk["risk_description"]

    def test_risks_without_questions_performance_under_load(self, launcher_process):
        """Test performance of risks without questions calculation under load."""
        time.sleep(10)

        # Make multiple concurrent requests
        import concurrent.futures

        def make_request():
            start_time = time.time()
            response = requests.get(f"{self.DASHBOARD_URL}/api/gaps", timeout=10)
            end_time = time.time()
            return response, end_time - start_time

        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [
                future.result() for future in concurrent.futures.as_completed(futures)
            ]

        # Validate all requests succeeded
        for response, response_time in results:
            assert response.status_code == 200
            assert response_time < 2.0  # Should respond within 2 seconds

        # Validate data consistency across requests
        responses = [result[0] for result in results]
        first_data = responses[0].json()

        for response in responses[1:]:
            data = response.json()
            assert (
                data["summary"]["risks_without_questions"]
                == first_data["summary"]["risks_without_questions"]
            )
            assert (
                data["summary"]["risks_without_questions_pct"]
                == first_data["summary"]["risks_without_questions_pct"]
            )

    def test_risks_without_questions_with_different_data_scenarios(
        self, launcher_process
    ):
        """Test risks without questions with different data scenarios."""
        time.sleep(10)

        # Test with current data
        response = requests.get(f"{self.DASHBOARD_URL}/api/gaps", timeout=10)
        assert response.status_code == 200
        data = response.json()

        # Validate current scenario
        summary = data["summary"]
        risks_without_questions = data["risks_without_questions"]

        # Should have reasonable data
        assert summary["total_risks"] > 0
        assert summary["risks_without_questions"] >= 0
        assert summary["risks_without_questions"] <= summary["total_risks"]
        assert 0 <= summary["risks_without_questions_pct"] <= 100

        # If there are risks without questions, validate the list
        if summary["risks_without_questions"] > 0:
            assert len(risks_without_questions) > 0
            for risk in risks_without_questions:
                assert "risk_id" in risk
                assert "risk_title" in risk
                assert "risk_description" in risk
        else:
            assert len(risks_without_questions) == 0

    def test_risks_without_questions_error_handling_e2e(self, launcher_process):
        """Test error handling for risks without questions in end-to-end scenario."""
        time.sleep(10)

        # Test with invalid endpoint
        response = requests.get(f"{self.DASHBOARD_URL}/api/gaps/invalid", timeout=10)
        assert response.status_code == 404

        # Test with malformed request
        response = requests.post(f"{self.DASHBOARD_URL}/api/gaps", timeout=10)
        assert response.status_code == 405  # Method not allowed

        # Test that normal endpoint still works after errors
        response = requests.get(f"{self.DASHBOARD_URL}/api/gaps", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "risks_without_questions" in data["summary"]
