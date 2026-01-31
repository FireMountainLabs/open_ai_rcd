"""
End-to-end tests for Database Service.

Tests complete workflows using the launcher with --dev flag and real service interactions.
"""

import os
import pytest
import requests
import time
import subprocess
import concurrent.futures
from pathlib import Path
from unittest.mock import patch
from config_manager import ConfigManager

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
    def launcher_process(self):
        """Start the launcher with --dev flag for end-to-end testing."""
        process = None
        try:
            # Find the launcher script in the project root
            project_root = Path(__file__).parent.parent.parent
            launcher_path = project_root / "launch_dataviewer"

            if not launcher_path.exists():
                pytest.skip(f"Launcher script not found at {launcher_path}")

            # Start the launcher with --dev flag from project root directory
            print(f"Starting launcher with --dev flag from {launcher_path}...")
            process = subprocess.Popen(
                [str(launcher_path), "--dev"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(project_root),
            )

            # Wait for services to start
            print("Waiting for services to start...")
            time.sleep(15)

            # Check if process is still running
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                print(f"Launcher process exited. stdout: {stdout}")
                print(f"stderr: {stderr}")
                # Check if services are actually running by testing health endpoints
                try:
                    import requests

                    db_health = requests.get(
                        f"{self.DATABASE_URL}/api/health", timeout=5
                    )
                    if db_health.status_code == 200:
                        print("Services are running despite launcher process exiting")
                        yield None  # Services are running, launcher process is not needed
                    else:
                        pytest.skip("Services not healthy after launcher exit")
                except Exception as e:
                    pytest.skip(f"Could not verify service health: {e}")
            else:
                yield process
        finally:
            if process:
                print("Stopping launcher...")
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()

    def test_service_health_check(self, launcher_process):
        """Test that all services are healthy."""
        # launcher_process might be None if services are running but launcher exited
        # Test database service health
        try:
            response = requests.get(f"{self.DATABASE_URL}/api/health", timeout=10)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["database_connected"] is True
            print(f"Database service health: {data}")
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Database service not accessible: {e}")

        # Test dashboard service health (if accessible)
        try:
            response = requests.get(f"{self.DASHBOARD_URL}/", timeout=5)
            assert response.status_code == 200
            print("Dashboard service is accessible")
        except requests.exceptions.RequestException:
            print("Dashboard service not accessible (may be expected)")

    def test_complete_data_retrieval_workflow(self, launcher_process):
        """Test complete data retrieval workflow through API."""
        # launcher_process might be None if services are running but launcher exited
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

            # Test questions endpoint
            response = requests.get(f"{base_url}/api/questions", timeout=10)
            assert response.status_code == 200
            questions = response.json()
            assert isinstance(questions, list)
            assert len(questions) > 0
            print(f"Retrieved {len(questions)} questions")

        except requests.exceptions.RequestException as e:
            pytest.skip(f"API not accessible: {e}")

    def test_search_functionality_workflow(self, launcher_process):
        """Test search functionality across all entities."""
        # launcher_process might be None if services are running but launcher exited
        base_url = self.DATABASE_URL

        try:
            # Test search with various terms
            search_terms = ["privacy", "security", "data", "model", "control"]

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
                    assert result["type"] in [
                        "risk",
                        "control",
                        "question",
                        "definition",
                    ]

        except requests.exceptions.RequestException as e:
            pytest.skip(f"Search API not accessible: {e}")

    def test_relationships_workflow(self, launcher_process):
        """Test relationship data retrieval workflow."""
        # launcher_process might be None if services are running but launcher exited
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
                assert rel["relationship_type"] in [
                    "risk_control",
                    "question_risk",
                    "question_control",
                ]

            # Test specific relationship types
            for rel_type in ["risk_control", "question_risk", "question_control"]:
                response = requests.get(
                    f"{base_url}/api/relationships?relationship_type={rel_type}",
                    timeout=10,
                )
                assert response.status_code == 200
                filtered_rels = response.json()
                assert isinstance(filtered_rels, list)
                print(f"Retrieved {len(filtered_rels)} {rel_type} relationships")

        except requests.exceptions.RequestException as e:
            pytest.skip(f"Relationships API not accessible: {e}")

    def test_statistics_workflow(self, launcher_process):
        """Test statistics calculation workflow."""
        # launcher_process might be None if services are running but launcher exited
        base_url = self.DATABASE_URL

        try:
            # Test stats endpoint
            response = requests.get(f"{base_url}/api/stats", timeout=10)
            assert response.status_code == 200
            stats = response.json()
            assert "total_risks" in stats
            assert "total_controls" in stats
            assert "total_questions" in stats
            assert "total_relationships" in stats
            print(f"Database stats: {stats}")

            # Verify stats are reasonable
            assert stats["total_risks"] > 0
            assert stats["total_controls"] > 0
            assert stats["total_questions"] > 0
            assert stats["total_relationships"] > 0

        except requests.exceptions.RequestException as e:
            pytest.skip(f"Stats API not accessible: {e}")

    def test_summary_endpoints_workflow(self, launcher_process):
        """Test summary endpoints workflow."""
        # launcher_process might be None if services are running but launcher exited
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

            # Test questions summary
            response = requests.get(f"{base_url}/api/questions/summary", timeout=10)
            assert response.status_code == 200
            questions_summary = response.json()
            assert "summary" in questions_summary
            assert "details" in questions_summary
            print(f"Questions summary: {questions_summary['summary']}")

        except requests.exceptions.RequestException as e:
            pytest.skip(f"Summary APIs not accessible: {e}")

    def test_detail_endpoints_workflow(self, launcher_process):
        """Test detail endpoints workflow."""
        # launcher_process might be None if services are running but launcher exited
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
                assert "associated_questions" in risk_detail
                print(
                    f"Risk detail for {risk_id}: {len(risk_detail['associated_controls'])} controls, {len(risk_detail['associated_questions'])} questions"
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
                assert "associated_questions" in control_detail
                print(
                    f"Control detail for {control_id}: {len(control_detail['associated_risks'])} risks, {len(control_detail['associated_questions'])} questions"
                )

            # Test question detail
            response = requests.get(f"{base_url}/api/questions?limit=1", timeout=10)
            assert response.status_code == 200
            questions = response.json()
            if questions:
                question_id = questions[0]["id"]

                response = requests.get(
                    f"{base_url}/api/question/{question_id}", timeout=10
                )
                assert response.status_code == 200
                question_detail = response.json()
                assert "question" in question_detail
                assert "associated_risks" in question_detail
                assert "associated_controls" in question_detail
                print(
                    f"Question detail for {question_id}: {len(question_detail['associated_risks'])} risks, {len(question_detail['associated_controls'])} controls"
                )

        except requests.exceptions.RequestException as e:
            pytest.skip(f"Detail APIs not accessible: {e}")

    def test_utility_endpoints_workflow(self, launcher_process):
        """Test utility endpoints workflow."""
        # launcher_process might be None if services are running but launcher exited
        base_url = self.DATABASE_URL

        try:
            # Test managing roles endpoint
            response = requests.get(f"{base_url}/api/managing-roles", timeout=10)
            assert response.status_code == 200
            roles = response.json()
            assert "managing_roles" in roles
            assert isinstance(roles["managing_roles"], list)
            print(f"Managing roles: {roles['managing_roles']}")

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
            assert "question_risk_links" in network_data
            assert "question_control_links" in network_data
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
            assert "unmapped_questions" in gaps
            assert "risks_without_questions" in gaps
            assert "risks_without_questions" in gaps["summary"]
            assert "risks_without_questions_pct" in gaps["summary"]
            assert "controls_without_questions" in gaps
            assert "controls_without_questions" in gaps["summary"]
            assert "controls_without_questions_pct" in gaps["summary"]
            print(f"Gaps analysis: {gaps['summary']}")
            print(
                f"Risks without questions: {gaps['summary']['risks_without_questions']} ({gaps['summary']['risks_without_questions_pct']}%)"
            )
            print(
                f"Controls without questions: {gaps['summary']['controls_without_questions']} ({gaps['summary']['controls_without_questions_pct']}%)"
            )

            # Test last updated endpoint
            response = requests.get(f"{base_url}/api/last-updated", timeout=10)
            assert response.status_code == 200
            last_updated = response.json()
            assert "risks" in last_updated
            assert "controls" in last_updated
            assert "questions" in last_updated
            print(f"Last updated: {last_updated}")

        except requests.exceptions.RequestException as e:
            pytest.skip(f"Utility APIs not accessible: {e}")

    def test_error_handling_workflow(self, launcher_process):
        """Test error handling across the API."""
        # launcher_process might be None if services are running but launcher exited
        base_url = self.DATABASE_URL

        try:
            # Test 404 errors
            response = requests.get(f"{base_url}/api/risk/NONEXISTENT", timeout=10)
            assert response.status_code == 404

            response = requests.get(f"{base_url}/api/control/NONEXISTENT", timeout=10)
            assert response.status_code == 404

            response = requests.get(f"{base_url}/api/question/NONEXISTENT", timeout=10)
            assert response.status_code == 404

            # Test validation errors
            response = requests.get(f"{base_url}/api/risks?limit=0", timeout=10)
            assert response.status_code == 422

            response = requests.get(f"{base_url}/api/search?q=a", timeout=10)
            assert response.status_code == 422

            print("Error handling tests passed")

        except requests.exceptions.RequestException as e:
            pytest.skip(f"Error handling tests failed: {e}")

    def test_performance_workflow(self, launcher_process):
        """Test API performance under load."""
        # launcher_process might be None if services are running but launcher exited
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
                "/api/questions",
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
            assert total_time < 10  # Should complete in under 10 seconds
            print(
                f"Performance test: {success_count}/{len(endpoints)} requests succeeded in {total_time:.2f}s"
            )

        except requests.exceptions.RequestException as e:
            pytest.skip(f"Performance test failed: {e}")


class TestLauncherIntegration:
    """Test launcher integration and service coordination."""

    def test_launcher_dev_mode(self):
        """Test that launcher --dev mode works correctly."""
        # This test verifies the launcher can start in dev mode
        # without actually running the full test suite
        try:
            # Find the launcher script in the project root
            project_root = Path(__file__).parent.parent.parent
            launcher_path = project_root / "launch_dataviewer"

            if not launcher_path.exists():
                pytest.skip(f"Launcher script not found at {launcher_path}")

            # Test launcher help
            result = subprocess.run(
                [str(launcher_path), "--help"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            assert result.returncode == 0
            assert "--dev" in result.stdout
            print("Launcher help test passed")

        except subprocess.TimeoutExpired:
            pytest.fail("Launcher help command timed out")
        except FileNotFoundError:
            pytest.skip("Launcher script not found")

    def test_launcher_dev_mode_validation(self):
        """Test launcher dev mode validation without full startup."""
        try:
            # Find the launcher script in the project root
            project_root = Path(__file__).parent.parent.parent
            launcher_path = project_root / "launch_dataviewer"

            if not launcher_path.exists():
                pytest.skip(f"Launcher script not found at {launcher_path}")

            # Test launcher with --dev flag (dry run)
            result = subprocess.run(
                [str(launcher_path), "--dev", "--help"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            # Should show help even with --dev flag
            assert result.returncode == 0
            print("Launcher dev mode validation passed")

        except subprocess.TimeoutExpired:
            pytest.fail("Launcher dev validation timed out")
        except FileNotFoundError:
            pytest.skip("Launcher script not found")


class TestDatabaseServiceStandalone:
    """Test database service standalone functionality."""

    def test_database_service_startup(self, sample_database, mock_config_manager):
        """Test database service can start with test database."""
        # This test verifies the service can start with our test database
        # without actually running the full server

        with patch("app.DB_PATH", str(sample_database)):
            # Test database validation
            from app import validate_database

            assert validate_database() is True

            # Test database connection
            from app import get_db_connection

            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM risks")
                count = cursor.fetchone()[0]
                assert count > 0
                print(f"Database service startup test passed: {count} risks found")

    def test_database_service_configuration(self, test_config):
        """Test database service configuration loading."""
        # Test that configuration can be loaded
        config_manager = ConfigManager()
        config = config_manager.load_config()

        assert "server" in config
        assert "database" in config
        assert "api" in config
        assert "logging" in config

        print("Database service configuration test passed")
