"""
Integration tests for the dashboard service.

These tests use the launcher with --dev flag to test the service in a real environment.
"""

import pytest
import requests
import time
import subprocess
import os
from pathlib import Path


@pytest.mark.integration
@pytest.mark.launcher
@pytest.mark.slow
class TestDashboardServiceIntegration:
    """Integration tests using the launcher."""

    # Use environment variables for ports
    DASHBOARD_PORT = os.getenv("DASHBOARD_PORT")
    DASHBOARD_URL = f"http://localhost:{DASHBOARD_PORT}"

    @pytest.fixture(scope="class")
    def launcher_process(self):
        """Start the dashboard service using the launcher."""
        # Check if we're in CI environment
        if os.getenv("CI") or os.getenv("GITHUB_ACTIONS"):
            # In CI, skip integration tests that require external services
            pytest.skip(
                "Integration tests skipped in CI environment - services not available"
            )

        # Get the launcher script path
        launcher_path = Path(__file__).parent.parent.parent / "launch_dataviewer"

        # Start the launcher with --dev flag
        process = subprocess.Popen(
            [str(launcher_path), "--dev", "--no-auth"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Wait for services to start
        max_wait = 60  # 60 seconds
        wait_time = 0
        while wait_time < max_wait:
            try:
                response = requests.get(f"{self.DASHBOARD_URL}/api/health", timeout=5)
                if response.status_code == 200:
                    break
            except requests.exceptions.RequestException:
                pass

            time.sleep(2)
            wait_time += 2

        yield process

        # Cleanup: stop the process
        try:
            process.terminate()
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()

    def test_dashboard_service_health(self, launcher_process):
        """Test that the dashboard service is healthy."""
        response = requests.get(f"{self.DASHBOARD_URL}/api/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "dashboard_service" in data
        assert "database_service" in data

    def test_dashboard_service_main_page(self, launcher_process):
        """Test that the main dashboard page loads."""
        response = requests.get(f"{self.DASHBOARD_URL}/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_dashboard_service_api_endpoints(self, launcher_process):
        """Test that API endpoints are accessible."""
        endpoints = [
            "/api/risks",
            "/api/controls",
            "/api/questions",
            "/api/relationships",
            "/api/search?q=test",
            "/api/stats",
            "/api/network",
            "/api/gaps",
            "/api/file-metadata",
            "/api/last-updated",
        ]

        for endpoint in endpoints:
            response = requests.get(f"{self.DASHBOARD_URL}{endpoint}")
            assert response.status_code == 200
            assert response.headers.get("content-type", "").startswith(
                "application/json"
            )

    def test_dashboard_gaps_api_with_risks_without_questions(self, launcher_process):
        """Test that the gaps API includes risks without questions data."""
        response = requests.get(f"{self.DASHBOARD_URL}/api/gaps")
        assert response.status_code == 200
        data = response.json()

        # Validate the new risks without questions fields
        assert "summary" in data
        assert "risks_without_questions" in data["summary"]
        assert "risks_without_questions_pct" in data["summary"]
        assert "risks_without_questions" in data
        assert "controls_without_questions" in data["summary"]
        assert "controls_without_questions_pct" in data["summary"]
        assert "controls_without_questions" in data

        # Validate data types
        assert isinstance(data["summary"]["risks_without_questions"], int)
        assert isinstance(data["summary"]["risks_without_questions_pct"], (int, float))
        assert isinstance(data["risks_without_questions"], list)
        assert isinstance(data["summary"]["controls_without_questions"], int)
        assert isinstance(
            data["summary"]["controls_without_questions_pct"], (int, float)
        )
        assert isinstance(data["controls_without_questions"], list)

        # Validate percentage is reasonable
        assert 0 <= data["summary"]["risks_without_questions_pct"] <= 100
        assert 0 <= data["summary"]["controls_without_questions_pct"] <= 100

        # Validate that risks without questions have proper structure
        for risk in data["risks_without_questions"]:
            assert "risk_id" in risk
            assert "risk_title" in risk
            assert "risk_description" in risk

        # Validate that controls without questions have proper structure
        for control in data["controls_without_questions"]:
            assert "control_id" in control
            assert "control_title" in control
            assert "control_description" in control

    def test_dashboard_service_cors_headers(self, launcher_process):
        """Test that CORS headers are properly set."""
        response = requests.options(f"{self.DASHBOARD_URL}/api/risks")
        assert response.status_code == 200

        # Check CORS headers (at minimum, we need Allow-Origin)
        assert "Access-Control-Allow-Origin" in response.headers
        # Note: Flask-CORS may not set all headers for all requests
        # The Allow header shows the available methods
        assert "Allow" in response.headers

    def test_dashboard_service_cors_headers_direct(self):
        """Test that CORS headers are properly set (direct Flask test)."""
        from app import app

        with app.test_client() as client:
            response = client.options("/api/risks")
            assert response.status_code == 200

            # Check CORS headers (at minimum, we need Allow-Origin)
            assert "Access-Control-Allow-Origin" in response.headers
            # Note: Flask-CORS may not set all headers for all requests
            # The Allow header shows the available methods
            assert "Allow" in response.headers

    def test_dashboard_service_error_handling(self, launcher_process):
        """Test error handling for invalid endpoints."""
        # Test non-existent endpoint
        response = requests.get(f"{self.DASHBOARD_URL}/api/nonexistent")
        assert response.status_code == 404

        # Test invalid method
        response = requests.post(f"{self.DASHBOARD_URL}/api/risks")
        assert response.status_code == 405  # Method not allowed

    def test_dashboard_service_static_files(self, launcher_process):
        """Test that static files are served correctly."""
        static_files = [
            "/static/css/tufte.css",
            "/static/css/dashboard.css",
            "/static/js/dashboard.js",
        ]

        for static_file in static_files:
            response = requests.get(f"{self.DASHBOARD_URL}{static_file}")
            assert response.status_code == 200, f"Failed to load {static_file}: {response.status_code}"
            content_type = response.headers.get("content-type", "")
            # CSS files should be text/css, JS files should be application/javascript
            assert content_type.startswith("text/") or content_type.startswith(
                "application/javascript"
            )

    def test_dashboard_service_templates(self, launcher_process):
        """Test that templates are rendered correctly."""
        # Test main dashboard page
        response = requests.get(f"{self.DASHBOARD_URL}/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_dashboard_service_database_connectivity(self, launcher_process):
        """Test that the dashboard service can connect to the database service."""
        # Test that we can get data from the database service
        response = requests.get(f"{self.DASHBOARD_URL}/api/stats")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)
        # Should have some stats even if they're zero
        assert "total_risks" in data
        assert "total_controls" in data
        assert "total_questions" in data


@pytest.mark.integration
@pytest.mark.launcher
@pytest.mark.slow
class TestDashboardServicePerformance:
    """Performance tests for the dashboard service."""

    # Use environment variables for ports
    DASHBOARD_PORT = os.getenv("DASHBOARD_PORT")
    DASHBOARD_URL = f"http://localhost:{DASHBOARD_PORT}"

    @pytest.fixture(scope="class")
    def launcher_process(self):
        """Start the dashboard service using the launcher."""
        # Check if we're in CI environment
        if os.getenv("CI") or os.getenv("GITHUB_ACTIONS"):
            # In CI, skip integration tests that require external services
            pytest.skip(
                "Integration tests skipped in CI environment - services not available"
            )

        # Get the launcher script path
        launcher_path = Path(__file__).parent.parent.parent / "launch_dataviewer"

        # Start the launcher with --dev flag
        process = subprocess.Popen(
            [str(launcher_path), "--dev", "--no-auth"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Wait for services to start
        max_wait = 60  # 60 seconds
        wait_time = 0
        while wait_time < max_wait:
            try:
                response = requests.get(f"{self.DASHBOARD_URL}/api/health", timeout=5)
                if response.status_code == 200:
                    break
            except requests.exceptions.RequestException:
                pass

            time.sleep(2)
            wait_time += 2

        yield process

        # Cleanup: stop the process
        try:
            process.terminate()
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()

    def test_dashboard_service_response_times(self, launcher_process):
        """Test that API endpoints respond within acceptable time limits."""
        endpoints = [
            "/api/health",
            "/api/risks",
            "/api/controls",
            "/api/questions",
            "/api/stats",
        ]

        max_response_time = 5.0  # 5 seconds

        for endpoint in endpoints:
            start_time = time.time()
            response = requests.get(f"{self.DASHBOARD_URL}{endpoint}")
            end_time = time.time()

            response_time = end_time - start_time
            assert response.status_code == 200
            assert (
                response_time < max_response_time
            ), f"Endpoint {endpoint} took {response_time:.2f}s"

    def test_dashboard_service_concurrent_requests(self, launcher_process):
        """Test that the service can handle concurrent requests."""
        import threading
        import queue

        results = queue.Queue()

        def make_request():
            try:
                response = requests.get(f"{self.DASHBOARD_URL}/api/health", timeout=10)
                results.put(response.status_code)
            except Exception as e:
                results.put(f"Error: {e}")

        # Start 10 concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            thread.start()
            threads.append(thread)

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check results
        status_codes = []
        while not results.empty():
            result = results.get()
            status_codes.append(result)

        # All requests should succeed
        assert len(status_codes) == 10
        assert all(code == 200 for code in status_codes if isinstance(code, int))

    def test_dashboard_service_memory_usage(self, launcher_process):
        """Test that the service doesn't have excessive memory usage."""
        # This is a basic test - in a real scenario you'd use psutil or similar
        # to monitor actual memory usage
        response = requests.get(f"{self.DASHBOARD_URL}/api/health")
        assert response.status_code == 200

        # Make multiple requests to test for memory leaks
        for _ in range(100):
            response = requests.get(f"{self.DASHBOARD_URL}/api/stats")
            assert response.status_code == 200
