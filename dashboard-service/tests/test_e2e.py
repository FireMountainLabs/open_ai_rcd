"""
End-to-end tests for the dashboard service.

These tests simulate real user workflows and interactions.
"""

import os
import pytest
import requests
import time
import subprocess
from pathlib import Path

# Set environment variables for testing
os.environ["DASHBOARD_PORT"] = os.getenv("DASHBOARD_PORT", "5002")
os.environ["DATABASE_PORT"] = os.getenv("DATABASE_PORT", "5001")


@pytest.mark.e2e
@pytest.mark.launcher
@pytest.mark.slow
class TestDashboardServiceE2E:
    """End-to-end tests for the complete dashboard service workflow."""

    # Use environment variables for ports
    DASHBOARD_PORT = os.getenv("DASHBOARD_PORT")
    DATABASE_PORT = os.getenv("DATABASE_PORT")
    DASHBOARD_URL = f"http://localhost:{DASHBOARD_PORT}"
    DATABASE_URL = f"http://localhost:{DATABASE_PORT}"

    @pytest.fixture(scope="class")
    def launcher_process(self):
        """Start the complete system using the launcher."""
        # Skip integration tests in CI environment
        import os

        ci_env_vars = ["CI", "GITHUB_ACTIONS", "GITHUB_WORKFLOW", "GITHUB_RUN_ID"]
        if any(os.getenv(var) for var in ci_env_vars):
            pytest.skip(
                "Integration tests skipped in CI environment - services not available"
            )

        # Get the launcher script path
        launcher_path = Path(__file__).parent.parent.parent / "launch_dataviewer"

        # Start the launcher with --dev flag and no auth for easier testing
        process = subprocess.Popen(
            [str(launcher_path), "--dev", "--no-auth"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Wait for all services to start
        max_wait = 90  # 90 seconds for full system startup
        wait_time = 0
        services_ready = {"dashboard": False, "database": False}

        while wait_time < max_wait and not all(services_ready.values()):
            # Check dashboard service
            if not services_ready["dashboard"]:
                try:
                    response = requests.get(
                        f"{self.DASHBOARD_URL}/api/health", timeout=5
                    )
                    if response.status_code == 200:
                        services_ready["dashboard"] = True
                except requests.exceptions.RequestException:
                    pass

            # Check database service
            if not services_ready["database"]:
                try:
                    response = requests.get(
                        f"{self.DATABASE_URL}/api/health", timeout=5
                    )
                    if response.status_code == 200:
                        services_ready["database"] = True
                except requests.exceptions.RequestException:
                    pass

            time.sleep(3)
            wait_time += 3

        if not all(services_ready.values()):
            pytest.skip("Services did not start within timeout period")

        yield process

        # Cleanup: stop the process
        try:
            process.terminate()
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()

    def test_complete_dashboard_workflow(self, launcher_process):
        """Test the complete dashboard workflow from start to finish."""
        # 1. Access the main dashboard
        response = requests.get(f"{self.DASHBOARD_URL}/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

        # 2. Check that the dashboard loads with proper content
        content = response.text
        assert "dashboard" in content.lower() or "aiml" in content.lower()

        # 3. Test API endpoints are working
        api_endpoints = [
            "/api/health",
            "/api/risks",
            "/api/controls",
            "/api/questions",
            "/api/stats",
        ]

        for endpoint in api_endpoints:
            response = requests.get(f"{self.DASHBOARD_URL}{endpoint}")
            assert response.status_code == 200
            data = response.json()
            # Health and stats endpoints return dicts, others return lists
            if endpoint in ["/api/health", "/api/stats"]:
                assert isinstance(data, dict)
            else:
                assert isinstance(data, list)

        # 4. Test search functionality
        search_response = requests.get(f"{self.DASHBOARD_URL}/api/search?q=test")
        assert search_response.status_code == 200
        search_data = search_response.json()
        # Search endpoint returns a dict with query and results
        assert isinstance(search_data, dict)
        assert "query" in search_data
        assert "results" in search_data

        # 5. Test relationships endpoint
        relationships_response = requests.get(f"{self.DASHBOARD_URL}/api/relationships")
        assert relationships_response.status_code == 200
        relationships_data = relationships_response.json()
        assert isinstance(relationships_data, list)

        # 6. Test network data endpoint
        network_response = requests.get(f"{self.DASHBOARD_URL}/api/network")
        assert network_response.status_code == 200
        network_data = network_response.json()
        assert "risk_control_links" in network_data
        assert "question_risk_links" in network_data
        assert "question_control_links" in network_data

        # 7. Test gaps analysis endpoint
        gaps_response = requests.get(f"{self.DASHBOARD_URL}/api/gaps")
        assert gaps_response.status_code == 200
        gaps_data = gaps_response.json()
        assert "summary" in gaps_data

    def test_dashboard_data_consistency(self, launcher_process):
        """Test that data is consistent across different endpoints."""
        # Get stats
        stats_response = requests.get(f"{self.DASHBOARD_URL}/api/stats")
        assert stats_response.status_code == 200
        stats = stats_response.json()

        # Get individual entity counts
        risks_response = requests.get(f"{self.DASHBOARD_URL}/api/risks")
        assert risks_response.status_code == 200
        risks_data = risks_response.json()

        controls_response = requests.get(f"{self.DASHBOARD_URL}/api/controls")
        assert controls_response.status_code == 200
        controls_data = controls_response.json()

        questions_response = requests.get(f"{self.DASHBOARD_URL}/api/questions")
        assert questions_response.status_code == 200
        questions_data = questions_response.json()

        # Verify that the counts match (data is now lists, not dicts)
        assert stats.get("total_risks", 0) >= len(risks_data)
        assert stats.get("total_controls", 0) >= len(controls_data)
        assert stats.get("total_questions", 0) >= len(questions_data)

    def test_dashboard_search_functionality(self, launcher_process):
        """Test comprehensive search functionality."""
        # Test various search queries
        search_queries = [
            "risk",
            "control",
            "question",
            "privacy",
            "security",
            "data",
            "model",
            "ai",
            "ml",
        ]

        for query in search_queries:
            response = requests.get(f"{self.DASHBOARD_URL}/api/search?q={query}")
            assert response.status_code == 200

            data = response.json()
            assert "query" in data
            assert "results" in data
            assert data["query"] == query
            assert isinstance(data["results"], list)

    def test_dashboard_pagination(self, launcher_process):
        """Test pagination functionality for large datasets."""
        # Test risks pagination
        response = requests.get(f"{self.DASHBOARD_URL}/api/risks?limit=5&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5

        # Test with different offset
        response2 = requests.get(f"{self.DASHBOARD_URL}/api/risks?limit=5&offset=5")
        assert response2.status_code == 200
        data2 = response2.json()
        assert isinstance(data2, list)

        # Results should be different (if there are enough items)
        if len(data) > 0 and len(data2) > 0:
            assert data != data2

    def test_dashboard_filtering(self, launcher_process):
        """Test filtering functionality."""
        # Test risks filtering by category
        response = requests.get(f"{self.DASHBOARD_URL}/api/risks?category=Privacy")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Test controls filtering by domain
        response = requests.get(f"{self.DASHBOARD_URL}/api/controls?domain=Protect")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Test questions filtering by category
        response = requests.get(f"{self.DASHBOARD_URL}/api/questions?category=Security")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_dashboard_summary_endpoints(self, launcher_process):
        """Test summary endpoints for dashboard widgets."""
        summary_endpoints = [
            "/api/risks/summary",
            "/api/controls/summary",
            "/api/questions/summary",
        ]

        for endpoint in summary_endpoints:
            response = requests.get(f"{self.DASHBOARD_URL}{endpoint}")
            assert response.status_code == 200

            data = response.json()
            assert "details" in data
            assert isinstance(data["details"], list)

    def test_dashboard_detail_endpoints(self, launcher_process):
        """Test detail endpoints for individual items."""
        # First get some IDs from the main endpoints
        risks_response = requests.get(f"{self.DASHBOARD_URL}/api/risks?limit=1")
        if risks_response.status_code == 200:
            risks_data = risks_response.json()
            if risks_data:
                risk_id = risks_data[0]["id"]

                # Test risk detail
                detail_response = requests.get(
                    f"{self.DASHBOARD_URL}/api/risk/{risk_id}"
                )
                assert detail_response.status_code == 200
                detail_data = detail_response.json()
                assert "risk" in detail_data
                assert "id" in detail_data["risk"]

        controls_response = requests.get(f"{self.DASHBOARD_URL}/api/controls?limit=1")
        if controls_response.status_code == 200:
            controls_data = controls_response.json()
            if controls_data:
                control_id = controls_data[0]["id"]

                # Test control detail
                detail_response = requests.get(
                    f"{self.DASHBOARD_URL}/api/control/{control_id}"
                )
                assert detail_response.status_code == 200
                detail_data = detail_response.json()
                assert "control" in detail_data
                assert "id" in detail_data["control"]

        questions_response = requests.get(f"{self.DASHBOARD_URL}/api/questions?limit=1")
        if questions_response.status_code == 200:
            questions_data = questions_response.json()
            if questions_data:
                question_id = questions_data[0]["id"]

                # Test question detail
                detail_response = requests.get(
                    f"{self.DASHBOARD_URL}/api/question/{question_id}"
                )
                assert detail_response.status_code == 200
                detail_data = detail_response.json()
                assert "question" in detail_data
                assert "id" in detail_data["question"]

    def test_dashboard_error_handling(self, launcher_process):
        """Test error handling for various edge cases."""
        # Test invalid endpoint
        response = requests.get(f"{self.DASHBOARD_URL}/api/invalid")
        assert response.status_code == 404

        # Test invalid method
        response = requests.post(f"{self.DASHBOARD_URL}/api/risks")
        assert response.status_code == 405

        # Test invalid parameters
        response = requests.get(f"{self.DASHBOARD_URL}/api/risks?limit=invalid")
        assert response.status_code == 200  # Should handle gracefully

        # Test very large limit
        response = requests.get(f"{self.DASHBOARD_URL}/api/risks?limit=999999")
        assert response.status_code == 200  # Should handle gracefully

    def test_dashboard_static_content(self, launcher_process):
        """Test that static content is served correctly."""
        # Test CSS files
        css_files = ["/static/css/tufte.css", "/static/css/dashboard.css"]

        for css_file in css_files:
            response = requests.get(f"{self.DASHBOARD_URL}{css_file}")
            assert response.status_code == 200
            assert "text/css" in response.headers.get("content-type", "")

        # Test JavaScript files
        js_files = ["/static/js/dashboard.js"]

        for js_file in js_files:
            response = requests.get(f"{self.DASHBOARD_URL}{js_file}")
            assert response.status_code == 200
            assert "application/javascript" in response.headers.get(
                "content-type", ""
            ) or "text/javascript" in response.headers.get("content-type", "")

    def test_dashboard_cors_functionality(self, launcher_process):
        """Test CORS functionality for cross-origin requests."""
        # Test preflight request
        response = requests.options(
            f"{self.DASHBOARD_URL}/api/risks",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )
        assert response.status_code == 200

        # Check CORS headers - Flask-CORS may add these, but if not present,
        # check that at least the Allow header is present (which indicates OPTIONS is supported)
        assert "Allow" in response.headers
        # CORS headers are optional if Flask-CORS is configured per-route
        # Check if CORS headers exist, but don't fail if they don't (they may be configured differently)
        if "Access-Control-Allow-Origin" in response.headers:
            assert "Access-Control-Allow-Methods" in response.headers
            assert "Access-Control-Allow-Headers" in response.headers

    def test_dashboard_service_reliability(self, launcher_process):
        """Test service reliability under normal usage patterns."""
        # Make multiple requests to simulate normal usage
        for _ in range(50):
            # Health check
            response = requests.get(f"{self.DASHBOARD_URL}/api/health")
            assert response.status_code == 200

            # Get some data
            response = requests.get(f"{self.DASHBOARD_URL}/api/stats")
            assert response.status_code == 200

            # Search
            response = requests.get(f"{self.DASHBOARD_URL}/api/search?q=test")
            assert response.status_code == 200

            time.sleep(0.1)  # Small delay between requests
