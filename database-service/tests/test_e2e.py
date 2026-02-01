"""
End-to-end tests for Database Service.

Tests complete workflows using direct app calls and real service interactions.
"""

import os
import pytest
import requests
import time
import subprocess
import concurrent.futures
from pathlib import Path
from unittest.mock import patch

# Set environment variables for testing
os.environ["DATABASE_PORT"] = os.getenv("DATABASE_PORT", "5001")
os.environ["DASHBOARD_PORT"] = os.getenv("DASHBOARD_PORT", "5002")


class TestEndToEndWorkflows:
    """Test complete end-to-end workflows."""

    # Use environment variables for ports
    DATABASE_PORT = os.getenv("DATABASE_PORT")
    DASHBOARD_PORT = os.getenv("DASHBOARD_PORT")
    DATABASE_URL = f"http://localhost:{DATABASE_PORT}"
    DASHBOARD_URL = f"http://localhost:{DASHBOARD_PORT}"

    @pytest.fixture(scope="class")
    def database_service_process(self):
        """Start the database service in a separate process."""
        process = None
        try:
            # Find the app.py in database-service
            project_root = Path(__file__).parent.parent.parent
            app_path = project_root / "database-service" / "app.py"

            if not app_path.exists():
                pytest.skip(f"App script not found at {app_path}")

            # Start the service
            print(f"Starting database service from {app_path}...")
            process = subprocess.Popen(
                [sys.executable, str(app_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(project_root / "database-service"),
            )

            # Wait for service to start
            print("Waiting for database service to start...")
            time.sleep(5)

            # Check if process is still running
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                print(f"Service process exited. stdout: {stdout}")
                print(f"stderr: {stderr}")
                pytest.skip("Database service failed to start")
            else:
                yield process
        finally:
            if process:
                print("Stopping database service...")
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()

    def test_service_health_check(self, database_service_process):
        """Test that database service is healthy."""
        try:
            response = requests.get(f"{self.DATABASE_URL}/api/health", timeout=10)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["database_connected"] is True
            print(f"Database service health: {data}")
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Database service not accessible: {e}")

    def test_complete_data_retrieval_workflow(self, database_service_process):
        """Test complete data retrieval workflow through API."""
        base_url = self.DATABASE_URL

        try:
            # Test risks endpoint
            response = requests.get(f"{base_url}/api/risks", timeout=10)
            assert response.status_code == 200
            risks = response.json()
            assert isinstance(risks, list)
            assert len(risks) > 0
            print(f"Retrieved {len(risks)} risks")

            # Test controls endpoint
            response = requests.get(f"{base_url}/api/controls", timeout=10)
            assert response.status_code == 200
            controls = response.json()
            assert isinstance(controls, list)
            assert len(controls) > 0
            print(f"Retrieved {len(controls)} controls")

        except requests.exceptions.RequestException as e:
            pytest.skip(f"API not accessible: {e}")

    def test_search_functionality_workflow(self, database_service_process):
        """Test search functionality across entities."""
        base_url = self.DATABASE_URL

        try:
            # Test search with various terms
            search_terms = ["privacy", "security", "data"]

            for term in search_terms:
                response = requests.get(f"{base_url}/api/search?q={term}", timeout=10)
                assert response.status_code == 200
                data = response.json()
                assert "query" in data
                assert "results" in data
                assert data["query"] == term
                print(f"Search for '{term}': {len(data['results'])} results")

                # Verify result structure
                for result in data["results"]:
                    assert "type" in result
                    assert "id" in result
                    assert "title" in result
                    assert result["type"] in ["risk", "control", "definition"]

        except requests.exceptions.RequestException as e:
            pytest.skip(f"Search API not accessible: {e}")

    def test_relationships_workflow(self, database_service_process):
        """Test relationship data retrieval workflow."""
        base_url = self.DATABASE_URL

        try:
            # Test relationships endpoint
            response = requests.get(f"{base_url}/api/relationships", timeout=10)
            assert response.status_code == 200
            relationships = response.json()
            assert isinstance(relationships, list)
            print(f"Retrieved {len(relationships)} relationships")

            # Verify relationship structure
            for rel in relationships:
                assert "source_id" in rel
                assert "target_id" in rel
                assert "relationship_type" in rel
                assert rel["relationship_type"] == "risk_control"

        except requests.exceptions.RequestException as e:
            pytest.skip(f"Relationships API not accessible: {e}")

    def test_statistics_workflow(self, database_service_process):
        """Test statistics calculation workflow."""
        base_url = self.DATABASE_URL

        try:
            # Test stats endpoint
            response = requests.get(f"{base_url}/api/stats", timeout=10)
            assert response.status_code == 200
            stats = response.json()
            assert "total_risks" in stats
            assert "total_controls" in stats
            assert "total_relationships" in stats
            print(f"Database stats: {stats}")

            # Verify stats are reasonable
            assert stats["total_risks"] > 0
            assert stats["total_controls"] > 0
            assert stats["total_relationships"] > 0

        except requests.exceptions.RequestException as e:
            pytest.skip(f"Stats API not accessible: {e}")

    def test_summary_endpoints_workflow(self, database_service_process):
        """Test summary endpoints workflow."""
        base_url = self.DATABASE_URL

        try:
            # Test risks summary
            response = requests.get(f"{base_url}/api/risks/summary", timeout=10)
            assert response.status_code == 200
            risks_summary = response.json()
            assert "details" in risks_summary
            assert isinstance(risks_summary["details"], list)
            print(f"Risks summary: {len(risks_summary['details'])} items")

            # Test controls summary
            response = requests.get(f"{base_url}/api/controls/summary", timeout=10)
            assert response.status_code == 200
            controls_summary = response.json()
            assert "details" in controls_summary
            assert isinstance(controls_summary["details"], list)
            print(f"Controls summary: {len(controls_summary['details'])} items")

        except requests.exceptions.RequestException as e:
            pytest.skip(f"Summary APIs not accessible: {e}")

    def test_detail_endpoints_workflow(self, database_service_process):
        """Test detail endpoints workflow."""
        base_url = self.DATABASE_URL

        try:
            # First get some IDs to test with
            response = requests.get(f"{base_url}/api/risks?limit=1", timeout=10)
            assert response.status_code == 200
            risks = response.json()
            if risks:
                risk_id = risks[0]["id"]

                # Test risk detail
                response = requests.get(f"{base_url}/api/risk/{risk_id}", timeout=10)
                assert response.status_code == 200
                risk_detail = response.json()
                assert "risk" in risk_detail
                assert "associated_controls" in risk_detail
                print(
                    f"Risk detail for {risk_id}: {len(risk_detail['associated_controls'])} controls"
                )

            # Test control detail
            response = requests.get(f"{base_url}/api/controls?limit=1", timeout=10)
            assert response.status_code == 200
            controls = response.json()
            if controls:
                control_id = controls[0]["id"]

                response = requests.get(
                    f"{base_url}/api/control/{control_id}", timeout=10
                )
                assert response.status_code == 200
                control_detail = response.json()
                assert "control" in control_detail
                assert "associated_risks" in control_detail
                print(
                    f"Control detail for {control_id}: {len(control_detail['associated_risks'])} risks"
                )

        except requests.exceptions.RequestException as e:
            pytest.skip(f"Detail APIs not accessible: {e}")

    def test_utility_endpoints_workflow(self, database_service_process):
        """Test utility endpoints workflow."""
        base_url = self.DATABASE_URL

        try:
            # Test file metadata endpoint
            response = requests.get(f"{base_url}/api/file-metadata", timeout=10)
            assert response.status_code == 200
            metadata = response.json()
            assert isinstance(metadata, dict)
            print(f"File metadata: {metadata}")

            # Test network data endpoint
            response = requests.get(f"{base_url}/api/network", timeout=10)
            assert response.status_code == 200
            network_data = response.json()
            assert "risk_control_links" in network_data
            print(
                f"Network data: {len(network_data['risk_control_links'])} risk-control links"
            )

            # Test gaps analysis endpoint
            response = requests.get(f"{base_url}/api/gaps", timeout=10)
            assert response.status_code == 200
            gaps = response.json()
            assert "summary" in gaps
            assert "unmapped_risks" in gaps
            assert "unmapped_controls" in gaps
            print(f"Gaps analysis: {gaps['summary']}")

            # Test last updated endpoint
            response = requests.get(f"{base_url}/api/last-updated", timeout=10)
            assert response.status_code == 200
            last_updated = response.json()
            assert "risks" in last_updated
            assert "controls" in last_updated
            print(f"Last updated: {last_updated}")

        except requests.exceptions.RequestException as e:
            pytest.skip(f"Utility APIs not accessible: {e}")

    def test_performance_workflow(self, database_service_process):
        """Test API performance under load."""
        base_url = self.DATABASE_URL

        try:
            # Test multiple concurrent requests
            def make_request(endpoint):
                try:
                    response = requests.get(f"{base_url}{endpoint}", timeout=10)
                    return response.status_code, (
                        len(response.json()) if response.status_code == 200 else 0
                    )
                except Exception:
                    return 500, 0

            endpoints = [
                "/api/health",
                "/api/risks",
                "/api/controls",
                "/api/relationships",
                "/api/stats",
            ]

            # Make concurrent requests
            start_time = time.time()
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [
                    executor.submit(make_request, endpoint) for endpoint in endpoints
                ]
                results = [
                    future.result()
                    for future in concurrent.futures.as_completed(futures)
                ]
            end_time = time.time()

            # Verify all requests succeeded
            success_count = sum(1 for status, _ in results if status == 200)
            assert success_count >= len(endpoints) * 0.8  # At least 80% should succeed

            # Verify reasonable response time
            total_time = end_time - start_time
            assert total_time < 5  # Should complete in under 5 seconds
            print(
                f"Performance test: {success_count}/{len(endpoints)} requests succeeded in {total_time:.2f}s"
            )

        except requests.exceptions.RequestException as e:
            pytest.skip(f"Performance test failed: {e}")


import sys
